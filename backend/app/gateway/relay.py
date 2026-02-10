"""SMTP relay client: forwards accepted emails to Google Workspace."""

import email as email_lib
from email import policy

import aiosmtplib
import structlog

from app.config import settings
from app.core.constants import (
    GUARD_IA_HEADER_CASE_ID,
    GUARD_IA_HEADER_SCORE,
    GUARD_IA_HEADER_VERDICT,
    GUARD_IA_HEADER_VERSION,
    GUARD_IA_HEADER_WARNING,
    GUARD_IA_VERSION,
)

logger = structlog.get_logger()


class RelayClient:
    """Async SMTP client for relaying emails to Google Workspace."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        self.host = host or settings.google_relay_host
        self.port = port or settings.google_relay_port

    async def forward(
        self,
        raw_data: bytes,
        sender: str,
        recipients: list[str],
        case_id: str | None = None,
        score: float | None = None,
        verdict: str | None = None,
        warn: bool = False,
    ) -> bool:
        """Forward email to Google Workspace via SMTP relay.

        Injects X-Guard-IA-* headers before forwarding.

        Returns True on success, False on failure.
        """
        try:
            msg = email_lib.message_from_bytes(raw_data, policy=policy.default)

            # Inject Guard-IA headers
            msg[GUARD_IA_HEADER_VERSION] = GUARD_IA_VERSION
            if score is not None:
                msg[GUARD_IA_HEADER_SCORE] = f"{score:.4f}"
            if verdict:
                msg[GUARD_IA_HEADER_VERDICT] = verdict
            if case_id:
                msg[GUARD_IA_HEADER_CASE_ID] = case_id
            if warn:
                msg[GUARD_IA_HEADER_WARNING] = "true"

            modified_data = msg.as_bytes()

            await aiosmtplib.send(
                modified_data,
                sender=sender,
                recipients=recipients,
                hostname=self.host,
                port=self.port,
                start_tls=True,
                source_address=(settings.smtp_domain, 0),
            )

            logger.info(
                "email_forwarded",
                sender=sender,
                recipients=recipients,
                host=self.host,
                score=score,
                verdict=verdict,
            )
            return True

        except aiosmtplib.SMTPException as exc:
            logger.error(
                "relay_smtp_error",
                error=str(exc),
                sender=sender,
                recipients=recipients,
                host=self.host,
            )
            return False
        except Exception as exc:
            logger.error(
                "relay_unexpected_error",
                error=str(exc),
                sender=sender,
                recipients=recipients,
            )
            return False

    async def deferred_forward(
        self,
        raw_data: bytes,
        sender: str,
        recipients: list[str],
        case_id: str,
    ) -> bool:
        """Forward a previously quarantined email after CISO release."""
        logger.info("deferred_forward_start", case_id=case_id)
        return await self.forward(
            raw_data=raw_data,
            sender=sender,
            recipients=recipients,
            case_id=case_id,
            verdict="released",
        )
