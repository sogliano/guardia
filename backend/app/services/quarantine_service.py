"""Quarantine service: manage quarantined emails (release, keep, delete)."""

from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import CaseStatus, QuarantineAction, Verdict
from app.gateway.relay import RelayClient
from app.gateway.storage import EmailStorage
from app.models.case import Case
from app.models.email import Email
from app.models.quarantine_action import QuarantineActionRecord

logger = structlog.get_logger()


class QuarantineService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.storage = EmailStorage()
        self.relay = RelayClient()

    async def list_quarantined(
        self,
        page: int = 1,
        size: int = 20,
        date_from: str | None = None,
        date_to: str | None = None,
        sender: str | None = None,
    ) -> dict:
        """List all quarantined cases with pagination, including email data."""
        query = select(Case).where(
            Case.status == CaseStatus.QUARANTINED
        ).options(selectinload(Case.email))

        if date_from:
            query = query.where(Case.created_at >= date_from)
        if date_to:
            query = query.where(Case.created_at <= date_to)
        if sender:
            safe = sender.replace("%", "\\%").replace("_", "\\_")
            query = query.join(Case.email).where(
                Email.sender_email.ilike(f"%{safe}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(Case.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        cases = result.scalars().all()

        items = []
        for case in cases:
            items.append({
                "id": case.id,
                "email_id": case.email_id,
                "status": case.status,
                "final_score": case.final_score,
                "risk_level": case.risk_level,
                "verdict": case.verdict,
                "threat_category": case.threat_category,
                "pipeline_duration_ms": case.pipeline_duration_ms,
                "resolved_by": case.resolved_by,
                "resolved_at": case.resolved_at,
                "created_at": case.created_at,
                "updated_at": case.updated_at,
                "email_subject": case.email.subject if case.email else None,
                "email_sender": case.email.sender_email if case.email else None,
                "email_received_at": (
                    case.email.received_at if case.email else None
                ),
            })

        return {"items": items, "total": total, "page": page, "size": size}

    async def get_email_detail(self, case_id: UUID) -> dict | None:
        """Get full email detail for a quarantined case."""
        stmt = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.email),
                selectinload(Case.analyses),
            )
        )
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case or not case.email:
            return None

        email = case.email

        # Find LLM analysis explanation if available
        llm_explanation = None
        for analysis in (case.analyses or []):
            if analysis.stage == "llm" and analysis.explanation:
                llm_explanation = analysis.explanation
                break

        return {
            "case_id": str(case.id),
            "subject": email.subject,
            "sender_email": email.sender_email,
            "sender_name": email.sender_name,
            "recipient_email": email.recipient_email,
            "reply_to": email.reply_to,
            "received_at": email.received_at,
            "message_id": email.message_id,
            "auth_results": email.auth_results or {},
            "body_preview": (
                (email.body_text or "")[:500] if email.body_text else None
            ),
            "urls": email.urls or [],
            "attachments": email.attachments or [],
            "risk_level": case.risk_level,
            "final_score": case.final_score,
            "threat_category": case.threat_category,
            "ai_explanation": llm_explanation,
        }

    async def release(
        self, case_id: UUID, user_id: UUID, reason: str | None = None
    ) -> Case | None:
        """Release a quarantined email: forward to Google and update status."""
        case = await self._get_quarantined_case(case_id)
        if not case:
            return None

        # Retrieve raw email from storage
        raw_data = await self.storage.retrieve(str(case_id))
        if not raw_data:
            logger.error("quarantine_release_no_raw_data", case_id=str(case_id))
            return None

        # Load email record for sender/recipients
        email = await self._load_email(case.email_id)
        if not email:
            return None

        # Forward to Google
        forwarded = await self.relay.deferred_forward(
            raw_data=raw_data,
            sender=email.sender_email,
            recipients=[email.recipient_email],
            case_id=str(case_id),
        )

        if not forwarded:
            logger.error("quarantine_release_forward_failed", case_id=str(case_id))
            return None

        # Update case
        case.status = CaseStatus.RESOLVED
        case.verdict = Verdict.ALLOWED

        # Record action
        action = QuarantineActionRecord(
            case_id=case_id,
            action=QuarantineAction.RELEASED,
            reason=reason,
            performed_by=user_id,
        )
        self.db.add(action)

        # Clean up storage
        await self.storage.delete(str(case_id))
        await self.db.flush()

        logger.info("quarantine_released", case_id=str(case_id), user_id=str(user_id))
        return case

    async def keep(
        self, case_id: UUID, user_id: UUID, reason: str | None = None
    ) -> Case | None:
        """Keep email quarantined (confirm the quarantine decision)."""
        case = await self._get_quarantined_case(case_id)
        if not case:
            return None

        case.status = CaseStatus.RESOLVED
        case.verdict = Verdict.BLOCKED

        action = QuarantineActionRecord(
            case_id=case_id,
            action=QuarantineAction.KEPT,
            reason=reason,
            performed_by=user_id,
        )
        self.db.add(action)
        await self.db.flush()

        logger.info("quarantine_kept", case_id=str(case_id), user_id=str(user_id))
        return case

    async def delete_quarantined(
        self, case_id: UUID, user_id: UUID, reason: str | None = None
    ) -> Case | None:
        """Delete quarantined email from storage and resolve case."""
        case = await self._get_quarantined_case(case_id)
        if not case:
            return None

        case.status = CaseStatus.RESOLVED
        case.verdict = Verdict.BLOCKED

        action = QuarantineActionRecord(
            case_id=case_id,
            action=QuarantineAction.DELETED,
            reason=reason,
            performed_by=user_id,
        )
        self.db.add(action)

        await self.storage.delete(str(case_id))
        await self.db.flush()

        logger.info("quarantine_deleted", case_id=str(case_id), user_id=str(user_id))
        return case

    async def _get_quarantined_case(self, case_id: UUID) -> Case | None:
        stmt = select(Case).where(
            Case.id == case_id, Case.status == CaseStatus.QUARANTINED
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_email(self, email_id: UUID) -> Email | None:
        stmt = select(Email).where(Email.id == email_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
