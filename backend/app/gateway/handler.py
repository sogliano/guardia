"""SMTP handler: the core entry point for Guard-IA email processing.

Receives emails via aiosmtpd, runs the detection pipeline,
and makes SMTP-level decisions (accept/quarantine/reject).
"""

from uuid import UUID

import structlog
from aiosmtpd.smtp import Envelope, Session, SMTP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import (
    SMTP_RESPONSE_INVALID_DOMAIN,
    SMTP_RESPONSE_OK,
    SMTP_RESPONSE_QUARANTINE,
    SMTP_RESPONSE_REJECT,
    Verdict,
)
from app.db.session import get_standalone_session
from app.gateway.parser import EmailParser
from app.gateway.relay import RelayClient
from app.gateway.storage import EmailStorage
from app.models.email import Email
from app.schemas.email import EmailIngest
from app.services.pipeline.orchestrator import PipelineOrchestrator

logger = structlog.get_logger()


class GuardIAHandler:
    """aiosmtpd handler for Guard-IA SMTP gateway.

    Orchestrates: parse → persist → pipeline → decision → forward/reject.
    """

    def __init__(
        self,
        parser: EmailParser | None = None,
        relay: RelayClient | None = None,
        storage: EmailStorage | None = None,
    ) -> None:
        self.parser = parser or EmailParser()
        self.relay = relay or RelayClient()
        self.storage = storage or EmailStorage()

    async def handle_EHLO(
        self, server: SMTP, session: Session, envelope: Envelope, hostname: str, responses: list
    ) -> list:
        """Respond to EHLO with our domain."""
        session.host_name = hostname  # type: ignore[attr-defined]
        return responses

    async def handle_RCPT(
        self,
        server: SMTP,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: list,
    ) -> str:
        """Validate recipient domain is in accepted_domains."""
        domain = address.rsplit("@", 1)[-1].lower() if "@" in address else ""
        if domain not in settings.accepted_domains_list:
            logger.warning("rejected_rcpt", address=address, domain=domain)
            return SMTP_RESPONSE_INVALID_DOMAIN
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(
        self, server: SMTP, session: Session, envelope: Envelope
    ) -> str:
        """Main processing entry point.

        1. Parse raw email
        2. Persist email + create case in DB
        3. Run detection pipeline
        4. Make SMTP decision based on verdict
        5. Forward to Google or quarantine locally
        """
        peer = session.peer  # type: ignore[attr-defined]
        sender = envelope.mail_from or ""
        recipients = list(envelope.rcpt_tos)
        raw_data = envelope.original_content  # type: ignore[attr-defined]

        logger.info(
            "smtp_data_received",
            sender=sender,
            recipients=recipients,
            peer=peer,
            size=len(raw_data) if raw_data else 0,
        )

        # User-level filter: if active_users is configured, only run pipeline
        # for emails addressed to those users. Others get forwarded directly.
        active = settings.active_users_set
        if active and not any(r.lower() in active for r in recipients):
            logger.info(
                "bypass_pipeline_inactive_users",
                sender=sender,
                recipients=recipients,
            )
            try:
                await self.relay.forward(
                    raw_data=raw_data, sender=sender, recipients=recipients,
                )
            except Exception as exc:
                logger.error(
                    "relay_forward_failed_inactive",
                    error=str(exc),
                    sender=sender,
                    recipients=recipients,
                )
            return SMTP_RESPONSE_OK

        try:
            # 1. Parse email
            parsed = self.parser.parse_raw(raw_data, sender, recipients)

            # 2. Persist email and create case
            async with get_standalone_session() as db:
                email_record = await self._persist_email(db, parsed)
                email_id = email_record.id

                # 3. Run pipeline
                pipeline_result = await self._run_pipeline(db, email_id)

                # 4. Decision
                verdict = pipeline_result.verdict if pipeline_result else Verdict.ALLOWED
                score = pipeline_result.final_score if pipeline_result else 0.0
                case_id = str(pipeline_result.case_id) if pipeline_result else None

            # 5. Act on decision
            return await self._execute_decision(
                verdict=verdict,
                score=score,
                case_id=case_id,
                raw_data=raw_data,
                sender=sender,
                recipients=recipients,
            )

        except Exception as exc:
            # FAIL-OPEN: if pipeline crashes, forward email to avoid blocking legitimate mail
            logger.error("pipeline_crash_failopen", error=str(exc), sender=sender)
            try:
                await self.relay.forward(
                    raw_data=raw_data,
                    sender=sender,
                    recipients=recipients,
                )
            except Exception as exc:
                logger.error(
                    "relay_forward_failed_failopen",
                    error=str(exc),
                    sender=sender,
                )
            return SMTP_RESPONSE_OK

    async def _persist_email(self, db: AsyncSession, parsed: dict) -> Email:
        """Create Email record in database."""
        # Check for duplicate message_id
        stmt = select(Email).where(Email.message_id == parsed["message_id"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        email_data = EmailIngest(**parsed)
        email_record = EmailModel(
            message_id=email_data.message_id,
            sender_email=email_data.sender_email,
            sender_name=email_data.sender_name,
            reply_to=email_data.reply_to,
            recipient_email=email_data.recipient_email,
            recipients_cc=email_data.recipients_cc,
            subject=email_data.subject,
            body_text=email_data.body_text,
            body_html=email_data.body_html,
            headers=email_data.headers,
            urls=email_data.urls,
            attachments=email_data.attachments,
            auth_results=email_data.auth_results,
            received_at=email_data.received_at,
        )
        db.add(email_record)
        await db.flush()
        return email_record

    async def _run_pipeline(self, db: AsyncSession, email_id: UUID):
        """Run the detection pipeline. Returns PipelineResult or None."""
        try:
            orchestrator = PipelineOrchestrator(db)
            return await orchestrator.analyze(email_id)
        except Exception as exc:
            logger.error("pipeline_error", error=str(exc), email_id=str(email_id))
            return None

    async def _execute_decision(
        self,
        verdict: str,
        score: float,
        case_id: str | None,
        raw_data: bytes,
        sender: str,
        recipients: list[str],
    ) -> str:
        """Execute SMTP decision based on pipeline verdict."""
        if verdict == Verdict.BLOCKED:
            logger.info("email_blocked", score=score, case_id=case_id, sender=sender)
            return SMTP_RESPONSE_REJECT

        if verdict == Verdict.QUARANTINED:
            # Store raw email for potential later release
            if case_id:
                await self.storage.store(case_id, raw_data)
            logger.info("email_quarantined", score=score, case_id=case_id, sender=sender)
            return SMTP_RESPONSE_QUARANTINE

        # ALLOWED or WARNED: forward to Google
        warn = verdict == Verdict.WARNED
        forwarded = await self.relay.forward(
            raw_data=raw_data,
            sender=sender,
            recipients=recipients,
            case_id=case_id,
            score=score,
            verdict=verdict,
            warn=warn,
        )

        if not forwarded:
            logger.error("forward_failed_accepting", case_id=case_id, sender=sender)

        logger.info(
            "email_accepted",
            verdict=verdict,
            score=score,
            case_id=case_id,
            sender=sender,
            forwarded=forwarded,
        )
        return SMTP_RESPONSE_OK
