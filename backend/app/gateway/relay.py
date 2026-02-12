"""SMTP relay client: forwards accepted emails to Google Workspace.

Uses Gmail API when google_service_account_json is configured,
falls back to SMTP relay otherwise.
"""

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
    """Async client for delivering emails to Google Workspace.

    Uses Gmail API when google_service_account_json is configured,
    falls back to SMTP relay otherwise.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        self.host = host or settings.google_relay_host
        self.port = port or settings.google_relay_port
        self._gmail = None

        if settings.google_service_account_json:
            try:
                from app.gateway.gmail_delivery import GmailDeliveryService

                self._gmail = GmailDeliveryService(settings.google_service_account_json)
                logger.info("relay_using_gmail_api")
            except Exception as exc:
                logger.error(
                    "gmail_delivery_init_failed",
                    error=str(exc),
                    msg="Falling back to SMTP relay",
                )

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
        """Forward email to Google Workspace.

        Injects X-Guard-IA-* headers before forwarding.
        Uses Gmail API if configured, otherwise SMTP relay.

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

            if self._gmail:
                return await self._forward_gmail_api(modified_data, sender, recipients)
            return await self._forward_smtp(modified_data, sender, recipients)

        except Exception as exc:
            logger.error(
                "relay_unexpected_error",
                error=str(exc),
                sender=sender,
                recipients=recipients,
            )
            return False

    async def _forward_gmail_api(
        self, modified_data: bytes, sender: str, recipients: list[str],
    ) -> bool:
        """Forward via Gmail API users.messages.import."""
        success = await self._gmail.deliver_multi(recipients, modified_data)
        if success:
            logger.info(
                "email_forwarded",
                sender=sender,
                recipients=recipients,
                method="gmail_api",
            )
        else:
            logger.error(
                "gmail_api_forward_failed",
                sender=sender,
                recipients=recipients,
            )
        return success

    async def _forward_smtp(
        self, modified_data: bytes, sender: str, recipients: list[str],
    ) -> bool:
        """Forward via SMTP relay (fallback)."""
        try:
            send_kwargs: dict = {
                "hostname": self.host,
                "port": self.port,
                "start_tls": True,
                "local_hostname": settings.smtp_domain,
            }
            if settings.google_relay_user and settings.google_relay_password:
                send_kwargs["username"] = settings.google_relay_user
                send_kwargs["password"] = settings.google_relay_password

            await aiosmtplib.send(
                modified_data,
                sender=sender,
                recipients=recipients,
                **send_kwargs,
            )

            logger.info(
                "email_forwarded",
                sender=sender,
                recipients=recipients,
                method="smtp_relay",
                host=self.host,
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
