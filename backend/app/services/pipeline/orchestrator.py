"""Pipeline Orchestrator: coordinates the 3-layer detection pipeline.

Flow: Load email → Create case → Heuristics → ML → Final score →
      Verdict → LLM explainer → Persist all results.
"""

import time
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import (
    SCORE_WEIGHT_HEURISTIC,
    SCORE_WEIGHT_ML,
    CaseStatus,
    PipelineStage,
    RiskLevel,
    ThreatCategory,
    Verdict,
)
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.email import Email
from app.models.evidence import Evidence
from app.services.pipeline.heuristics import HeuristicEngine
from app.services.pipeline.llm_explainer import LLMExplainer
from app.services.pipeline.ml_classifier import get_ml_classifier
from app.services.pipeline.models import (
    EvidenceItem,
    HeuristicResult,
    LLMResult,
    MLResult,
    PipelineResult,
)

logger = structlog.get_logger()


class PipelineOrchestrator:
    """Coordinates the full detection pipeline for a single email."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analyze(self, email_id: UUID) -> PipelineResult:
        """Run the 3-layer pipeline on an email.

        1. Load email from DB
        2. Create or fetch case (status=analyzing)
        3. Run heuristic engine → persist Analysis + Evidence
        4. Run ML classifier → persist Analysis + Evidence
        5. Calculate final score (40% heuristic + 60% ML)
        6. Determine verdict and risk level
        7. Run LLM explainer → persist Analysis
        8. Update case with final results
        """
        pipeline_start = time.monotonic()

        # 1. Load email
        email_record = await self._load_email(email_id)
        email_data = self._email_to_dict(email_record)

        # 2. Create or get case
        case = await self._get_or_create_case(email_id)
        case.status = CaseStatus.ANALYZING
        await self.db.flush()

        logger.info("pipeline_started", email_id=str(email_id), case_id=str(case.id))

        # 3. Heuristic analysis
        heuristic_engine = HeuristicEngine(self.db)
        heuristic_result = await heuristic_engine.analyze(email_data)
        await self._persist_analysis(
            case_id=case.id,
            stage=PipelineStage.HEURISTIC,
            score=heuristic_result.score,
            confidence=None,
            explanation=None,
            metadata={
                "domain_score": heuristic_result.domain_score,
                "url_score": heuristic_result.url_score,
                "keyword_score": heuristic_result.keyword_score,
                "auth_score": heuristic_result.auth_score,
            },
            execution_time_ms=heuristic_result.execution_time_ms,
            evidences=heuristic_result.evidences,
        )

        # 4. ML classification
        ml_result = MLResult()
        if settings.pipeline_ml_enabled:
            ml_classifier = get_ml_classifier()
            text = self._build_ml_input(email_data)
            ml_result = await ml_classifier.predict(text)
            await self._persist_analysis(
                case_id=case.id,
                stage=PipelineStage.ML,
                score=ml_result.score,
                confidence=ml_result.confidence,
                explanation=None,
                metadata={
                    "model_available": ml_result.model_available,
                    "model_version": ml_result.model_version,
                },
                execution_time_ms=ml_result.execution_time_ms,
                evidences=ml_result.evidences,
            )

        # 5. Calculate final score
        final_score = self._calculate_final_score(heuristic_result, ml_result)

        # 6. Determine verdict and risk level
        risk_level = self._determine_risk_level(final_score)
        verdict = self._determine_verdict(final_score)
        threat_category = self._determine_threat_category(heuristic_result)

        # 7. LLM explainer (non-blocking: failure doesn't affect verdict)
        llm_result = LLMResult()
        try:
            explainer = LLMExplainer()
            llm_result = await explainer.explain(
                email_data=email_data,
                heuristic_evidences=heuristic_result.evidences,
                ml_score=ml_result.score,
                ml_confidence=ml_result.confidence,
                ml_available=ml_result.model_available,
            )
            await self._persist_analysis(
                case_id=case.id,
                stage=PipelineStage.LLM,
                score=None,
                confidence=None,
                explanation=llm_result.explanation,
                metadata={
                    "provider": llm_result.provider,
                    "model_used": llm_result.model_used,
                    "tokens_used": llm_result.tokens_used,
                },
                execution_time_ms=llm_result.execution_time_ms,
                evidences=[],
            )
        except Exception as exc:
            logger.error("llm_explainer_error", error=str(exc), case_id=str(case.id))

        # 8. Update case
        pipeline_duration = int((time.monotonic() - pipeline_start) * 1000)
        case.status = CaseStatus.ANALYZED
        case.final_score = final_score
        case.risk_level = risk_level
        case.verdict = verdict
        case.threat_category = threat_category
        case.pipeline_duration_ms = pipeline_duration

        # Auto-quarantine
        if verdict == Verdict.QUARANTINED:
            case.status = CaseStatus.QUARANTINED

        await self.db.flush()

        logger.info(
            "pipeline_completed",
            case_id=str(case.id),
            final_score=round(final_score, 4),
            risk_level=risk_level,
            verdict=verdict,
            threat_category=threat_category,
            duration_ms=pipeline_duration,
        )

        return PipelineResult(
            case_id=case.id,
            final_score=final_score,
            risk_level=risk_level,
            verdict=verdict,
            threat_category=threat_category,
            heuristic=heuristic_result,
            ml=ml_result,
            llm=llm_result,
            pipeline_duration_ms=pipeline_duration,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _load_email(self, email_id: UUID) -> Email:
        """Load email record from DB."""
        stmt = select(Email).where(Email.id == email_id)
        result = await self.db.execute(stmt)
        email = result.scalar_one_or_none()
        if not email:
            raise ValueError(f"Email {email_id} not found")
        return email

    async def _get_or_create_case(self, email_id: UUID) -> Case:
        """Get existing case or create a new one for this email."""
        stmt = select(Case).where(Case.email_id == email_id)
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        if case:
            return case

        case = Case(email_id=email_id, status=CaseStatus.PENDING)
        self.db.add(case)
        await self.db.flush()
        return case

    def _email_to_dict(self, email: Email) -> dict:
        """Convert Email ORM model to dict for pipeline consumption."""
        return {
            "message_id": email.message_id,
            "sender_email": email.sender_email,
            "sender_name": email.sender_name,
            "reply_to": email.reply_to,
            "recipient_email": email.recipient_email,
            "recipients_cc": email.recipients_cc or [],
            "subject": email.subject,
            "body_text": email.body_text,
            "body_html": email.body_html,
            "headers": email.headers or {},
            "urls": email.urls or [],
            "attachments": email.attachments or [],
            "auth_results": email.auth_results or {},
        }

    def _build_ml_input(self, email_data: dict) -> str:
        """Build text input for ML classifier: subject + body."""
        subject = email_data.get("subject") or ""
        body = email_data.get("body_text") or ""
        return f"{subject}\n{body}".strip()

    def _calculate_final_score(
        self, heuristic: HeuristicResult, ml: MLResult
    ) -> float:
        """Calculate weighted final score.

        If ML is available: 40% heuristic + 60% ML
        If ML not available: 100% heuristic
        """
        if ml.model_available and ml.confidence > 0:
            score = (
                heuristic.score * SCORE_WEIGHT_HEURISTIC
                + ml.score * SCORE_WEIGHT_ML
            )
        else:
            score = heuristic.score
        return min(1.0, max(0.0, score))

    def _determine_risk_level(self, score: float) -> str:
        """Map score to risk level."""
        if score < settings.threshold_allow:
            return RiskLevel.LOW
        elif score < settings.threshold_warn:
            return RiskLevel.MEDIUM
        elif score < settings.threshold_quarantine:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL

    def _determine_verdict(self, score: float) -> str:
        """Map score to SMTP verdict."""
        if score < settings.threshold_allow:
            return Verdict.ALLOWED
        elif score < settings.threshold_warn:
            return Verdict.WARNED
        elif score < settings.threshold_quarantine:
            return Verdict.QUARANTINED
        else:
            return Verdict.BLOCKED

    def _determine_threat_category(self, heuristic: HeuristicResult) -> str:
        """Infer threat category from heuristic evidence types."""
        types = {ev.type for ev in heuristic.evidences}

        if "ceo_impersonation" in types or "sender_impersonation" in types:
            return ThreatCategory.BEC_IMPERSONATION
        if "keyword_phishing" in types or "url_shortener" in types or "url_ip_based" in types:
            return ThreatCategory.CREDENTIAL_PHISHING
        if any(t.startswith("domain_") for t in types) or any(
            t.startswith("auth_") for t in types
        ):
            return ThreatCategory.GENERIC_PHISHING
        if heuristic.score > 0.0:
            return ThreatCategory.GENERIC_PHISHING
        return ThreatCategory.CLEAN

    async def _persist_analysis(
        self,
        case_id: UUID,
        stage: str,
        score: float | None,
        confidence: float | None,
        explanation: str | None,
        metadata: dict,
        execution_time_ms: int,
        evidences: list[EvidenceItem],
    ) -> Analysis:
        """Persist an Analysis record with its Evidence children."""
        analysis = Analysis(
            case_id=case_id,
            stage=stage,
            score=score,
            confidence=confidence,
            explanation=explanation,
            metadata_=metadata,
            execution_time_ms=execution_time_ms,
        )
        self.db.add(analysis)
        await self.db.flush()

        for ev in evidences:
            evidence = Evidence(
                analysis_id=analysis.id,
                type=ev.type,
                severity=ev.severity,
                description=ev.description,
                raw_data=ev.raw_data,
            )
            self.db.add(evidence)

        await self.db.flush()
        return analysis
