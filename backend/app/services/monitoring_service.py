"""Monitoring service — LLM performance, cost, and quality metrics."""

from datetime import datetime, timedelta, timezone

import numpy as np
import structlog
from sqlalchemy import Integer, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import PipelineStage
from app.models.analysis import Analysis
from app.models.case import Case

logger = structlog.get_logger()

# Pricing per 1M tokens (input/output blended estimate)
MODEL_COST_PER_1M_TOKENS: dict[str, float] = {
    "gpt-4.1": 8.0,
    "gpt-4.1-mini": 1.6,
    "gpt-4.1-nano": 0.4,
    "gpt-4o": 5.0,
    "gpt-4o-mini": 0.3,
}
DEFAULT_COST_PER_1M = 5.0


class MonitoringService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_llm_stats(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict:
        if date_from is None:
            date_from = datetime.now(timezone.utc) - timedelta(days=7)
        if date_to is None:
            date_to = datetime.now(timezone.utc)

        prev_duration = date_to - date_from
        prev_from = date_from - prev_duration
        prev_to = date_from

        def _llm_filter(q):
            q = q.where(Analysis.stage == PipelineStage.LLM)
            q = q.where(Analysis.created_at >= date_from)
            q = q.where(Analysis.created_at <= date_to)
            return q

        kpi = await self._get_kpi(_llm_filter, prev_from, prev_to)
        token_trend = await self._get_token_trend(_llm_filter)
        latency_dist = await self._get_latency_distribution(_llm_filter)
        score_agreement = await self._get_score_agreement(_llm_filter)
        cost_breakdown = await self._get_cost_breakdown(_llm_filter)
        recent = await self._get_recent_analyses(date_from, date_to)

        return {
            "kpi": kpi,
            "token_trend": token_trend,
            "latency_distribution": latency_dist,
            "score_agreement": score_agreement,
            "cost_breakdown": cost_breakdown,
            "recent_analyses": recent,
        }

    async def _get_kpi(self, llm_filter, prev_from, prev_to) -> dict:
        # Current period
        q = llm_filter(select(
            func.count().label("total"),
            func.avg(Analysis.execution_time_ms).label("avg_ms"),
            func.percentile_cont(0.95).within_group(
                Analysis.execution_time_ms
            ).label("p95_ms"),
            func.sum(
                cast(Analysis.metadata_["tokens_used"].as_string(), Integer)
            ).label("total_tokens"),
        ))
        row = (await self.db.execute(q)).one()
        total = row.total or 0
        avg_ms = float(row.avg_ms or 0)
        p95_ms = float(row.p95_ms or 0)
        total_tokens = int(row.total_tokens or 0)

        # Error count: analyses where score is NULL (LLM failed/timeout)
        err_q = llm_filter(select(func.count())).where(Analysis.score.is_(None))
        error_count = (await self.db.execute(err_q)).scalar() or 0

        # Previous period total for comparison
        prev_q = (
            select(func.count())
            .where(Analysis.stage == PipelineStage.LLM)
            .where(Analysis.created_at >= prev_from)
            .where(Analysis.created_at <= prev_to)
        )
        prev_total = (await self.db.execute(prev_q)).scalar() or 0

        # Estimate cost
        estimated_cost = self._estimate_cost_total(total_tokens)

        return {
            "total_calls": total,
            "avg_latency_ms": round(avg_ms, 1),
            "p95_latency_ms": round(p95_ms, 1),
            "total_tokens": total_tokens,
            "estimated_cost": round(estimated_cost, 2),
            "error_count": error_count,
            "error_rate": round(error_count / total * 100, 1) if total else 0.0,
            "prev_total_calls": prev_total,
        }

    async def _get_token_trend(self, llm_filter) -> list[dict]:
        q = llm_filter(select(
            func.date(Analysis.created_at).label("day"),
            func.sum(
                cast(Analysis.metadata_["tokens_used"].as_string(), Integer)
            ).label("total_tokens"),
        )).group_by(text("day")).order_by(text("day"))

        rows = (await self.db.execute(q)).all()
        result = []
        for r in rows:
            total = int(r.total_tokens or 0)
            # Approximate split: ~70% prompt, ~30% completion
            prompt = int(total * 0.7)
            completion = total - prompt
            result.append({
                "date": str(r.day),
                "prompt_tokens": prompt,
                "completion_tokens": completion,
            })
        return result

    async def _get_latency_distribution(self, llm_filter) -> list[dict]:
        buckets = [
            ("<1s", 0, 1000),
            ("1-2s", 1000, 2000),
            ("2-3s", 2000, 3000),
            ("3-5s", 3000, 5000),
            (">5s", 5000, None),
        ]
        result = []
        for label, low, high in buckets:
            q = llm_filter(select(func.count()))
            q = q.where(Analysis.execution_time_ms.is_not(None))
            q = q.where(Analysis.execution_time_ms >= low)
            if high is not None:
                q = q.where(Analysis.execution_time_ms < high)
            count = (await self.db.execute(q)).scalar() or 0
            result.append({"range": label, "count": count})
        return result

    async def _get_score_agreement(self, llm_filter) -> dict:
        q = llm_filter(
            select(Analysis.score, Case.final_score)
            .join(Case, Analysis.case_id == Case.id)
        ).where(
            Analysis.score.is_not(None),
            Case.final_score.is_not(None),
        )
        rows = (await self.db.execute(q)).all()
        total = len(rows)
        if total == 0:
            return {
                "agree_pct": 0, "minor_diff_pct": 0,
                "major_divergence_pct": 0, "total": 0,
            }

        agree = minor = major = 0
        for llm_score, final_score in rows:
            diff = abs(llm_score - final_score)
            if diff < 0.15:
                agree += 1
            elif diff < 0.30:
                minor += 1
            else:
                major += 1

        return {
            "agree_pct": round(agree / total * 100, 1),
            "minor_diff_pct": round(minor / total * 100, 1),
            "major_divergence_pct": round(major / total * 100, 1),
            "total": total,
        }

    async def _get_cost_breakdown(self, llm_filter) -> list[dict]:
        q = llm_filter(select(
            func.date(Analysis.created_at).label("day"),
            Analysis.metadata_["model_used"].as_string().label("model"),
            func.sum(
                cast(Analysis.metadata_["tokens_used"].as_string(), Integer)
            ).label("tokens"),
        )).group_by(text("day"), text("model")).order_by(text("day"))

        rows = (await self.db.execute(q)).all()
        result = []
        for r in rows:
            model = r.model or "unknown"
            tokens = int(r.tokens or 0)
            rate = MODEL_COST_PER_1M_TOKENS.get(model, DEFAULT_COST_PER_1M)
            cost = tokens / 1_000_000 * rate
            result.append({
                "date": str(r.day),
                "model": model,
                "cost": round(cost, 4),
            })
        return result

    async def _get_recent_analyses(
        self, date_from: datetime, date_to: datetime,
    ) -> list[dict]:
        q = (
            select(Analysis)
            .options(
                selectinload(Analysis.case).selectinload(Case.email),
            )
            .where(Analysis.stage == PipelineStage.LLM)
            .where(Analysis.created_at >= date_from)
            .where(Analysis.created_at <= date_to)
            .order_by(Analysis.created_at.desc())
            .limit(20)
        )
        rows = (await self.db.execute(q)).scalars().all()
        result = []
        for a in rows:
            tokens = (a.metadata_ or {}).get("tokens_used")
            model = (a.metadata_ or {}).get("model_used")
            explanation = (a.metadata_ or {}).get("explanation", "")
            status = "error" if a.score is None else "success"
            if a.execution_time_ms and a.execution_time_ms > 10000:
                status = "timeout"

            # Truncate explanation to first sentence for summary
            explanation_summary = None
            if explanation:
                first_sentence = explanation.split('.')[0]
                if first_sentence:
                    explanation_summary = first_sentence[:100] + ('...' if len(first_sentence) > 100 else '.')

            result.append({
                "time": a.created_at,
                "case_number": a.case.case_number if a.case else None,
                "sender": a.case.email.sender_email if a.case and a.case.email else None,
                "llm_score": a.score,
                "final_score": a.case.final_score if a.case else None,
                "tokens": int(tokens) if tokens is not None else None,
                "latency_ms": a.execution_time_ms,
                "status": status,
                "model": model,
                "threat_category": a.case.threat_category if a.case else None,
                "explanation_summary": explanation_summary,
            })
        return result

    def _estimate_cost_total(self, total_tokens: int) -> float:
        """Rough cost estimate using default blended rate."""
        return total_tokens / 1_000_000 * DEFAULT_COST_PER_1M

    async def get_ml_stats(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict:
        if date_from is None:
            date_from = datetime.now(timezone.utc) - timedelta(days=7)
        if date_to is None:
            date_to = datetime.now(timezone.utc)

        prev_duration = date_to - date_from
        prev_from = date_from - prev_duration
        prev_to = date_from

        def _ml_filter(q):
            q = q.where(Analysis.stage == PipelineStage.ML)
            q = q.where(Analysis.created_at >= date_from)
            q = q.where(Analysis.created_at <= date_to)
            return q

        kpi = await self._get_ml_kpi(_ml_filter, prev_from, prev_to)
        score_dist = await self._get_ml_score_distribution(_ml_filter)
        conf_acc = await self._get_ml_confidence_accuracy(_ml_filter)
        latency_trend = await self._get_ml_latency_trend(_ml_filter)
        score_agreement = await self._get_ml_score_agreement(_ml_filter)
        recent = await self._get_recent_ml_analyses(date_from, date_to)

        return {
            "kpi": kpi,
            "score_distribution": score_dist,
            "confidence_accuracy": conf_acc,
            "latency_trend": latency_trend,
            "score_agreement": score_agreement,
            "recent_analyses": recent,
        }

    async def _get_ml_kpi(self, ml_filter, prev_from, prev_to) -> dict:
        q = ml_filter(select(
            func.count().label("total"),
            func.avg(Analysis.execution_time_ms).label("avg_ms"),
            func.percentile_cont(0.95).within_group(
                Analysis.execution_time_ms
            ).label("p95_ms"),
            func.avg(Analysis.confidence).label("avg_conf"),
        ))
        row = (await self.db.execute(q)).one()
        total = row.total or 0
        avg_ms = float(row.avg_ms or 0)
        p95_ms = float(row.p95_ms or 0)
        avg_conf = float(row.avg_conf or 0)

        err_q = ml_filter(select(func.count())).where(Analysis.score.is_(None))
        error_count = (await self.db.execute(err_q)).scalar() or 0

        prev_q = (
            select(func.count())
            .where(Analysis.stage == PipelineStage.ML)
            .where(Analysis.created_at >= prev_from)
            .where(Analysis.created_at <= prev_to)
        )
        prev_total = (await self.db.execute(prev_q)).scalar() or 0

        return {
            "total_calls": total,
            "avg_latency_ms": round(avg_ms, 1),
            "p95_latency_ms": round(p95_ms, 1),
            "avg_confidence": round(avg_conf, 3),
            "error_count": error_count,
            "error_rate": round(error_count / total * 100, 1) if total else 0.0,
            "prev_total_calls": prev_total,
        }

    async def _get_ml_score_distribution(self, ml_filter) -> list[dict]:
        buckets = [
            ("0.0-0.1", 0.0, 0.1),
            ("0.1-0.2", 0.1, 0.2),
            ("0.2-0.3", 0.2, 0.3),
            ("0.3-0.4", 0.3, 0.4),
            ("0.4-0.5", 0.4, 0.5),
            ("0.5-0.6", 0.5, 0.6),
            ("0.6-0.7", 0.6, 0.7),
            ("0.7-0.8", 0.7, 0.8),
            ("0.8-0.9", 0.8, 0.9),
            ("0.9-1.0", 0.9, 1.0),
        ]
        result = []
        for label, low, high in buckets:
            q = ml_filter(select(func.count()))
            q = q.where(Analysis.score.is_not(None))
            q = q.where(Analysis.score >= low)
            q = q.where(Analysis.score < high) if high < 1.0 else q.where(
                Analysis.score <= high
            )
            count = (await self.db.execute(q)).scalar() or 0
            result.append({"range": label, "count": count})
        return result

    async def _get_ml_confidence_accuracy(self, ml_filter) -> list[dict]:
        q = ml_filter(
            select(
                Analysis.confidence,
                Analysis.score,
                Case.final_score,
            ).join(Case, Analysis.case_id == Case.id)
        ).where(
            Analysis.score.is_not(None),
            Analysis.confidence.is_not(None),
            Case.final_score.is_not(None),
        )
        rows = (await self.db.execute(q)).all()
        result = []
        for conf, ml_score, final_score in rows:
            accuracy = 1.0 - min(abs(ml_score - final_score), 1.0)
            result.append({
                "confidence": round(conf, 3),
                "accuracy": round(accuracy, 3),
            })
        return result

    async def _get_ml_latency_trend(self, ml_filter) -> list[dict]:
        q = ml_filter(select(
            func.date(Analysis.created_at).label("day"),
            func.avg(Analysis.execution_time_ms).label("avg_ms"),
        )).group_by(text("day")).order_by(text("day"))

        rows = (await self.db.execute(q)).all()
        return [
            {
                "date": str(r.day),
                "avg_latency_ms": round(float(r.avg_ms or 0), 1),
            }
            for r in rows
        ]

    async def _get_ml_score_agreement(self, ml_filter) -> dict:
        q = ml_filter(
            select(Analysis.score, Case.final_score)
            .join(Case, Analysis.case_id == Case.id)
        ).where(
            Analysis.score.is_not(None),
            Case.final_score.is_not(None),
        )
        rows = (await self.db.execute(q)).all()
        total = len(rows)
        if total == 0:
            return {
                "agree_pct": 0, "minor_diff_pct": 0,
                "major_divergence_pct": 0, "total": 0,
            }

        agree = minor = major = 0
        for ml_score, final_score in rows:
            diff = abs(ml_score - final_score)
            if diff < 0.15:
                agree += 1
            elif diff < 0.30:
                minor += 1
            else:
                major += 1

        return {
            "agree_pct": round(agree / total * 100, 1),
            "minor_diff_pct": round(minor / total * 100, 1),
            "major_divergence_pct": round(major / total * 100, 1),
            "total": total,
        }

    async def _get_recent_ml_analyses(
        self, date_from: datetime, date_to: datetime,
    ) -> list[dict]:
        q = (
            select(Analysis)
            .options(
                selectinload(Analysis.case).selectinload(Case.email),
            )
            .where(Analysis.stage == PipelineStage.ML)
            .where(Analysis.created_at >= date_from)
            .where(Analysis.created_at <= date_to)
            .order_by(Analysis.created_at.desc())
            .limit(20)
        )
        rows = (await self.db.execute(q)).scalars().all()
        result = []
        for a in rows:
            status = "error" if a.score is None else "success"
            if a.execution_time_ms and a.execution_time_ms > 1000:
                status = "timeout"
            result.append({
                "time": a.created_at,
                "case_number": a.case.case_number if a.case else None,
                "sender": a.case.email.sender_email if a.case and a.case.email else None,
                "ml_score": a.score,
                "final_score": a.case.final_score if a.case else None,
                "confidence": a.confidence,
                "latency_ms": a.execution_time_ms,
                "status": status,
            })
        return result

    async def get_heuristics_stats(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> dict:
        if date_from is None:
            date_from = datetime.now(timezone.utc) - timedelta(days=7)
        if date_to is None:
            date_to = datetime.now(timezone.utc)

        prev_duration = date_to - date_from
        prev_from = date_from - prev_duration
        prev_to = date_from

        def _heur_filter(q):
            q = q.where(Analysis.stage == PipelineStage.HEURISTIC)
            q = q.where(Analysis.created_at >= date_from)
            q = q.where(Analysis.created_at <= date_to)
            return q

        kpi = await self._get_heuristics_kpi(_heur_filter, prev_from, prev_to)
        top_rules = await self._get_top_triggered_rules(_heur_filter)
        score_dist = await self._get_heuristics_score_distribution(_heur_filter)
        score_agreement = await self._get_heuristics_score_agreement(_heur_filter)
        recent = await self._get_recent_heuristics_analyses(date_from, date_to)

        return {
            "kpi": kpi,
            "top_triggered_rules": top_rules,
            "score_distribution": score_dist,
            "score_agreement": score_agreement,
            "recent_analyses": recent,
        }

    async def _get_heuristics_kpi(self, heur_filter, prev_from, prev_to) -> dict:
        q = heur_filter(select(
            func.count().label("total"),
            func.avg(Analysis.execution_time_ms).label("avg_ms"),
            func.percentile_cont(0.95).within_group(
                Analysis.execution_time_ms
            ).label("p95_ms"),
        ))
        row = (await self.db.execute(q)).one()
        total = row.total or 0
        avg_ms = float(row.avg_ms or 0)
        p95_ms = float(row.p95_ms or 0)

        high_score_q = heur_filter(select(func.count())).where(
            Analysis.score.is_not(None),
            Analysis.score >= 0.6,
        )
        high_score_count = (await self.db.execute(high_score_q)).scalar() or 0

        zero_score_q = heur_filter(select(func.count())).where(
            Analysis.score == 0.0,
        )
        zero_score_count = (await self.db.execute(zero_score_q)).scalar() or 0

        prev_q = (
            select(func.count())
            .where(Analysis.stage == PipelineStage.HEURISTIC)
            .where(Analysis.created_at >= prev_from)
            .where(Analysis.created_at <= prev_to)
        )
        prev_total = (await self.db.execute(prev_q)).scalar() or 0

        return {
            "total_runs": total,
            "avg_latency_ms": round(avg_ms, 1),
            "p95_latency_ms": round(p95_ms, 1),
            "high_score_rate": round(high_score_count / total * 100, 1) if total else 0.0,
            "zero_score_rate": round(zero_score_count / total * 100, 1) if total else 0.0,
            "prev_total_runs": prev_total,
        }

    async def _get_top_triggered_rules(self, heur_filter) -> list[dict]:
        q = heur_filter(
            select(Analysis.metadata_)
        ).where(
            Analysis.metadata_.is_not(None),
        )
        rows = (await self.db.execute(q)).scalars().all()

        rule_counts: dict[str, int] = {}
        for metadata in rows:
            if not metadata:
                continue
            triggered_rules = metadata.get("triggered_rules", [])
            if isinstance(triggered_rules, list):
                for rule in triggered_rules:
                    rule_counts[rule] = rule_counts.get(rule, 0) + 1

        sorted_rules = sorted(
            rule_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return [
            {"rule_name": rule, "count": count}
            for rule, count in sorted_rules
        ]

    async def _get_heuristics_score_distribution(self, heur_filter) -> list[dict]:
        buckets = [
            ("0.0-0.1", 0.0, 0.1),
            ("0.1-0.2", 0.1, 0.2),
            ("0.2-0.3", 0.2, 0.3),
            ("0.3-0.4", 0.3, 0.4),
            ("0.4-0.5", 0.4, 0.5),
            ("0.5-0.6", 0.5, 0.6),
            ("0.6-0.7", 0.6, 0.7),
            ("0.7-0.8", 0.7, 0.8),
            ("0.8-0.9", 0.8, 0.9),
            ("0.9-1.0", 0.9, 1.0),
        ]
        result = []
        for label, low, high in buckets:
            q = heur_filter(select(func.count()))
            q = q.where(Analysis.score.is_not(None))
            q = q.where(Analysis.score >= low)
            q = q.where(Analysis.score < high) if high < 1.0 else q.where(
                Analysis.score <= high
            )
            count = (await self.db.execute(q)).scalar() or 0
            result.append({"range": label, "count": count})
        return result

    async def _get_heuristics_score_agreement(self, heur_filter) -> dict:
        q = heur_filter(
            select(Analysis.score, Case.final_score)
            .join(Case, Analysis.case_id == Case.id)
        ).where(
            Analysis.score.is_not(None),
            Case.final_score.is_not(None),
        )
        rows = (await self.db.execute(q)).all()
        total = len(rows)
        if total == 0:
            return {
                "agree_pct": 0, "minor_diff_pct": 0,
                "major_divergence_pct": 0, "total": 0,
            }

        agree = minor = major = 0
        for heur_score, final_score in rows:
            diff = abs(heur_score - final_score)
            if diff < 0.15:
                agree += 1
            elif diff < 0.30:
                minor += 1
            else:
                major += 1

        return {
            "agree_pct": round(agree / total * 100, 1),
            "minor_diff_pct": round(minor / total * 100, 1),
            "major_divergence_pct": round(major / total * 100, 1),
            "total": total,
        }

    async def _get_recent_heuristics_analyses(
        self, date_from: datetime, date_to: datetime,
    ) -> list[dict]:
        q = (
            select(Analysis)
            .options(
                selectinload(Analysis.case).selectinload(Case.email),
            )
            .where(Analysis.stage == PipelineStage.HEURISTIC)
            .where(Analysis.created_at >= date_from)
            .where(Analysis.created_at <= date_to)
            .order_by(Analysis.created_at.desc())
            .limit(20)
        )
        rows = (await self.db.execute(q)).scalars().all()
        result = []
        for a in rows:
            triggered_rules = []
            if a.metadata_:
                rules = a.metadata_.get("triggered_rules", [])
                if isinstance(rules, list):
                    triggered_rules = rules

            result.append({
                "time": a.created_at,
                "case_number": a.case.case_number if a.case else None,
                "sender": a.case.email.sender_email if a.case and a.case.email else None,
                "heuristic_score": a.score,
                "final_score": a.case.final_score if a.case else None,
                "triggered_rules": triggered_rules,
                "latency_ms": a.execution_time_ms,
            })
        return result

    async def get_score_analysis(
        self,
        limit: int = 50,
        include_metrics: bool = True,
    ) -> dict:
        """Get detailed score breakdown for recent cases."""
        cases = await self._get_cases_with_scores(limit)

        metrics = None
        if include_metrics and cases:
            metrics = self._calculate_aggregate_metrics(cases)

        breakdown = []
        for case_data in cases:
            scores = [
                case_data["heuristic_score"],
                case_data["ml_score"],
                case_data["llm_score"],
            ]
            scores_valid = [s for s in scores if s is not None]

            std_dev = float(np.std(scores_valid)) if len(scores_valid) >= 2 else 0.0
            agreement_level = self._get_agreement_level(std_dev)

            breakdown.append({
                "case_number": case_data["case_number"],
                "email_sender": case_data["email_sender"],
                "email_received_at": case_data["email_received_at"],
                "heuristic_score": case_data["heuristic_score"],
                "ml_score": case_data["ml_score"],
                "llm_score": case_data["llm_score"],
                "final_score": case_data["final_score"],
                "std_dev": round(std_dev, 3),
                "agreement_level": agreement_level,
            })

        return {
            "metrics": metrics,
            "cases": breakdown,
        }

    async def _get_cases_with_scores(self, limit: int) -> list[dict]:
        """Query recent cases with all three engine scores."""
        q = (
            select(Case)
            .options(selectinload(Case.email))
            .where(Case.final_score.is_not(None))
            .order_by(Case.created_at.desc())
            .limit(limit)
        )
        cases = (await self.db.execute(q)).scalars().all()

        result = []
        for case in cases:
            heur_analysis = await self._get_analysis_score(case.id, PipelineStage.HEURISTIC)
            ml_analysis = await self._get_analysis_score(case.id, PipelineStage.ML)
            llm_analysis = await self._get_analysis_score(case.id, PipelineStage.LLM)

            result.append({
                "case_number": case.case_number,
                "email_sender": case.email.sender_email if case.email else "unknown",
                "email_received_at": case.email.received_at if case.email else case.created_at,
                "heuristic_score": heur_analysis,
                "ml_score": ml_analysis,
                "llm_score": llm_analysis,
                "final_score": case.final_score,
            })

        return result

    async def _get_analysis_score(self, case_id: int, stage: PipelineStage) -> float | None:
        """Get score for a specific analysis stage."""
        q = (
            select(Analysis.score)
            .where(Analysis.case_id == case_id)
            .where(Analysis.stage == stage)
        )
        score = (await self.db.execute(q)).scalar_one_or_none()
        return score

    def _calculate_aggregate_metrics(self, cases: list[dict]) -> dict:
        """Calculate correlation, agreement rate, avg std dev."""
        complete_cases = [
            c for c in cases
            if c["heuristic_score"] is not None
            and c["ml_score"] is not None
            and c["llm_score"] is not None
        ]

        if not complete_cases:
            return {
                "agreement_rate": 0.0,
                "avg_std_dev": 0.0,
                "correlation_heur_ml": 0.0,
                "correlation_heur_llm": 0.0,
                "correlation_ml_llm": 0.0,
                "total_cases_analyzed": 0,
            }

        heur_scores = [c["heuristic_score"] for c in complete_cases]
        ml_scores = [c["ml_score"] for c in complete_cases]
        llm_scores = [c["llm_score"] for c in complete_cases]

        corr_heur_ml = float(np.corrcoef(heur_scores, ml_scores)[0, 1])
        corr_heur_llm = float(np.corrcoef(heur_scores, llm_scores)[0, 1])
        corr_ml_llm = float(np.corrcoef(ml_scores, llm_scores)[0, 1])

        def get_risk_category(score: float) -> str:
            if score < 0.3:
                return "low"
            if score < 0.6:
                return "medium"
            if score < 0.8:
                return "high"
            return "critical"

        agreements = 0
        std_devs = []

        for case in complete_cases:
            cat_heur = get_risk_category(case["heuristic_score"])
            cat_ml = get_risk_category(case["ml_score"])
            cat_llm = get_risk_category(case["llm_score"])

            if cat_heur == cat_ml == cat_llm:
                agreements += 1

            std_dev = np.std([
                case["heuristic_score"],
                case["ml_score"],
                case["llm_score"],
            ])
            std_devs.append(std_dev)

        agreement_rate = (agreements / len(complete_cases)) * 100
        avg_std_dev = float(np.mean(std_devs))

        return {
            "agreement_rate": round(agreement_rate, 2),
            "avg_std_dev": round(avg_std_dev, 3),
            "correlation_heur_ml": round(corr_heur_ml, 3),
            "correlation_heur_llm": round(corr_heur_llm, 3),
            "correlation_ml_llm": round(corr_ml_llm, 3),
            "total_cases_analyzed": len(complete_cases),
        }

    def _get_agreement_level(self, std_dev: float) -> str:
        """Map std dev to agreement level."""
        if std_dev < 0.1:
            return "high"
        elif std_dev < 0.2:
            return "moderate"
        else:
            return "low"
