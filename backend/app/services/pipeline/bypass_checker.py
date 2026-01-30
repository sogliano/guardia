"""Pipeline bypass checker for trusted organizational emails.

Emails from allowlisted domains with valid authentication bypass the
full 3-stage pipeline (heuristic → ML → LLM), saving ~2-3s of latency
and eliminating false positives on internal traffic.

Bypass conditions (all must be met):
1. Sender domain in allowlist (config or DB PolicyEntry)
2. SPF = pass (required by default)
3. At least one of DKIM/DMARC passes (configurable)
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import PolicyListType
from app.models.policy_entry import PolicyEntry

logger = structlog.get_logger()


class BypassChecker:
    """Evaluates whether an email qualifies for pipeline bypass."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._db_allowlist: set[str] | None = None

    async def should_bypass(self, email_data: dict) -> tuple[bool, str]:
        """Check if email should bypass the full pipeline.

        Returns (should_bypass, reason).
        """
        sender_email = (email_data.get("sender_email") or "").lower()
        if not sender_email or "@" not in sender_email:
            return False, "Invalid sender email"

        sender_domain = sender_email.rsplit("@", 1)[1]

        if not await self._is_domain_allowlisted(sender_domain):
            return False, f"Domain {sender_domain} not in allowlist"

        auth = email_data.get("auth_results") or {}
        spf = (auth.get("spf") or "none").lower()
        dkim = (auth.get("dkim") or "none").lower()
        dmarc = (auth.get("dmarc") or "none").lower()

        if settings.allowlist_require_spf and spf != "pass":
            return False, f"SPF={spf} (required: pass)"

        need_extra = settings.allowlist_require_dkim or settings.allowlist_require_dmarc
        if need_extra:
            extra_ok = False
            if settings.allowlist_require_dkim and dkim == "pass":
                extra_ok = True
            if settings.allowlist_require_dmarc and dmarc == "pass":
                extra_ok = True
            if not extra_ok:
                return False, f"Additional auth failed (DKIM={dkim}, DMARC={dmarc})"

        reason = (
            f"Allowlisted domain {sender_domain} with valid auth "
            f"(SPF={spf}, DKIM={dkim}, DMARC={dmarc})"
        )
        return True, reason

    async def _is_domain_allowlisted(self, domain: str) -> bool:
        """Check config and DB allowlist. Supports subdomains."""
        for allowed in settings.allowlist_domains_set:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True

        if self._db_allowlist is None:
            await self._load_db_allowlist()

        for allowed in self._db_allowlist:  # type: ignore[union-attr]
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True

        return False

    async def _load_db_allowlist(self) -> None:
        stmt = select(PolicyEntry.value).where(
            PolicyEntry.list_type == PolicyListType.ALLOWLIST,
            PolicyEntry.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        self._db_allowlist = {v.lower() for (v,) in result.all()}
