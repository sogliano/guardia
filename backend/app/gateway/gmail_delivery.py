"""Gmail API delivery: imports emails into user inboxes via Gmail API.

Uses a service account with domain-wide delegation to impersonate
each recipient and import the raw MIME message into their inbox
via users.messages.import.
"""

import asyncio
import base64

import structlog
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.insert"]

logger = structlog.get_logger()


class GmailDeliveryService:
    """Delivers emails via Gmail API users.messages.import.

    Uses service account with domain-wide delegation to impersonate
    each recipient and import raw MIME into their inbox.
    """

    def __init__(self, service_account_file: str) -> None:
        self._base_credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES,
        )
        logger.info(
            "gmail_delivery_initialized",
            service_account_file=service_account_file,
        )

    def _import_sync(self, recipient: str, raw_mime: bytes) -> bool:
        """Synchronous Gmail API call (runs in thread executor)."""
        try:
            creds = self._base_credentials.with_subject(recipient)
            service = build(
                "gmail", "v1", credentials=creds, cache_discovery=False,
            )
            encoded = base64.urlsafe_b64encode(raw_mime).decode("ascii")
            service.users().messages().import_(
                userId="me",
                body={"raw": encoded, "labelIds": ["INBOX", "UNREAD"]},
                neverMarkSpam=True,
                processForCalendar=True,
            ).execute()
            return True
        except HttpError as exc:
            logger.error(
                "gmail_api_error",
                recipient=recipient,
                status=exc.resp.status if exc.resp else None,
                error=str(exc),
            )
            return False
        except Exception as exc:
            logger.error(
                "gmail_delivery_error",
                recipient=recipient,
                error=str(exc),
            )
            return False

    async def deliver(self, recipient: str, raw_mime: bytes) -> bool:
        """Import raw MIME into a single recipient's inbox (async)."""
        return await asyncio.to_thread(self._import_sync, recipient, raw_mime)

    async def deliver_multi(self, recipients: list[str], raw_mime: bytes) -> bool:
        """Import into multiple inboxes. Returns True if ALL succeed."""
        if not recipients:
            return False
        tasks = [self.deliver(r, raw_mime) for r in recipients]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_ok = all(r is True for r in results)
        if not all_ok:
            failed = [
                recipients[i] for i, r in enumerate(results) if r is not True
            ]
            logger.error(
                "gmail_delivery_partial_failure",
                failed_recipients=failed,
            )
        return all_ok
