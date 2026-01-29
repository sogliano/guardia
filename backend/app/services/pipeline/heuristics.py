"""Layer 1: Heuristic analysis engine (~5ms).

Four sub-engines, each weighted 25%:
- Domain analysis: blacklist (DB), typosquatting, suspicious TLDs
- URL analysis: shorteners, IP-based URLs, display/href mismatch
- Keyword analysis: urgency, phishing terms, CAPS abuse, financial
- Auth analysis: SPF/DKIM/DMARC failures, reply-to mismatch
"""

import re
import time
from urllib.parse import urlparse

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    HEURISTIC_WEIGHT_AUTH,
    HEURISTIC_WEIGHT_DOMAIN,
    HEURISTIC_WEIGHT_KEYWORD,
    HEURISTIC_WEIGHT_URL,
    EvidenceType,
    PolicyListType,
    Severity,
)
from app.models.policy_entry import PolicyEntry
from app.services.pipeline.heuristic_data import (
    FINANCIAL_KEYWORDS,
    KNOWN_DOMAINS,
    PHISHING_KEYWORDS,
    SUSPICIOUS_EXTENSIONS,
    SUSPICIOUS_TLDS,
    URGENCY_KEYWORDS,
    URL_SHORTENER_DOMAINS,
)
from app.services.pipeline.models import EvidenceItem, HeuristicResult

logger = structlog.get_logger()

# Regex for IP-based URLs (http://192.168.1.1/... or http://[::1]/...)
_IP_URL_REGEX = re.compile(
    r"https?://(\d{1,3}\.){3}\d{1,3}",
    re.IGNORECASE,
)


def _levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            cost = 0 if c1 == c2 else 1
            curr_row.append(min(
                curr_row[j] + 1,
                prev_row[j + 1] + 1,
                prev_row[j] + cost,
            ))
        prev_row = curr_row
    return prev_row[-1]


class HeuristicEngine:
    """Rule-based detection engine.

    Constructor receives an AsyncSession to query policy_entries
    (whitelist/blacklist) from the database.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._blacklisted_domains: set[str] | None = None
        self._whitelisted_domains: set[str] | None = None

    async def _load_policies(self) -> None:
        """Load whitelist/blacklist from DB (cached per analysis run)."""
        if self._blacklisted_domains is not None:
            return

        stmt = select(PolicyEntry).where(PolicyEntry.is_active.is_(True))
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        self._blacklisted_domains = set()
        self._whitelisted_domains = set()

        for entry in entries:
            value = entry.value.lower()
            if entry.list_type == PolicyListType.BLACKLIST:
                self._blacklisted_domains.add(value)
            elif entry.list_type == PolicyListType.WHITELIST:
                self._whitelisted_domains.add(value)

    async def analyze(self, email_data: dict) -> HeuristicResult:
        """Run all four sub-engines and compute weighted score."""
        start = time.monotonic()
        await self._load_policies()

        result = HeuristicResult()
        evidences: list[EvidenceItem] = []

        domain_score, domain_ev = await self._analyze_domain(email_data)
        url_score, url_ev = await self._analyze_urls(email_data)
        keyword_score, keyword_ev = await self._analyze_keywords(email_data)
        auth_score, auth_ev = await self._analyze_auth(email_data)

        result.domain_score = domain_score
        result.url_score = url_score
        result.keyword_score = keyword_score
        result.auth_score = auth_score
        evidences.extend(domain_ev)
        evidences.extend(url_ev)
        evidences.extend(keyword_ev)
        evidences.extend(auth_ev)

        result.score = (
            result.domain_score * HEURISTIC_WEIGHT_DOMAIN
            + result.url_score * HEURISTIC_WEIGHT_URL
            + result.keyword_score * HEURISTIC_WEIGHT_KEYWORD
            + result.auth_score * HEURISTIC_WEIGHT_AUTH
        )
        result.score = min(1.0, max(0.0, result.score))
        result.evidences = evidences
        result.execution_time_ms = int((time.monotonic() - start) * 1000)

        logger.info(
            "heuristic_analysis_complete",
            score=result.score,
            domain=result.domain_score,
            url=result.url_score,
            keyword=result.keyword_score,
            auth=result.auth_score,
            evidence_count=len(evidences),
            duration_ms=result.execution_time_ms,
        )
        return result

    # ------------------------------------------------------------------
    # Sub-engine 1: Domain Analysis
    # ------------------------------------------------------------------

    async def _analyze_domain(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Check sender domain against blacklist, typosquatting, and suspicious TLDs."""
        evidences: list[EvidenceItem] = []
        score = 0.0

        sender = email_data.get("sender_email", "").lower()
        if not sender or "@" not in sender:
            return 0.0, []

        domain = sender.rsplit("@", 1)[1]

        # Whitelist bypass: if domain is whitelisted, skip domain analysis
        if self._whitelisted_domains and domain in self._whitelisted_domains:
            return 0.0, []

        # 1. Blacklist check (DB)
        if self._blacklisted_domains and domain in self._blacklisted_domains:
            score = 1.0
            evidences.append(EvidenceItem(
                type=EvidenceType.DOMAIN_BLACKLISTED,
                severity=Severity.CRITICAL,
                description=f"Sender domain '{domain}' is blacklisted",
                raw_data={"domain": domain},
            ))
            return score, evidences

        # 2. Suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                score = max(score, 0.5)
                evidences.append(EvidenceItem(
                    type=EvidenceType.DOMAIN_SUSPICIOUS_TLD,
                    severity=Severity.MEDIUM,
                    description=f"Sender domain uses suspicious TLD '{tld}'",
                    raw_data={"domain": domain, "tld": tld},
                ))
                break

        # 3. Typosquatting: Levenshtein distance to known domains
        for known in KNOWN_DOMAINS:
            if domain == known:
                break
            dist = _levenshtein(domain, known)
            if 1 <= dist <= 2:
                score = max(score, 0.8)
                evidences.append(EvidenceItem(
                    type=EvidenceType.DOMAIN_TYPOSQUATTING,
                    severity=Severity.HIGH,
                    description=f"Domain '{domain}' looks like '{known}' (distance={dist})",
                    raw_data={"domain": domain, "similar_to": known, "distance": dist},
                ))
                break

        return min(1.0, score), evidences

    # ------------------------------------------------------------------
    # Sub-engine 2: URL Analysis
    # ------------------------------------------------------------------

    async def _analyze_urls(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Analyze URLs for shorteners, IP-based, suspicious patterns."""
        evidences: list[EvidenceItem] = []
        urls: list[str] = email_data.get("urls", [])

        if not urls:
            return 0.0, []

        shortener_count = 0
        ip_count = 0
        suspicious_count = 0

        for url in urls:
            try:
                parsed = urlparse(url)
                hostname = (parsed.hostname or "").lower()
            except Exception:
                continue

            # 1. URL shortener
            if hostname in URL_SHORTENER_DOMAINS:
                shortener_count += 1
                evidences.append(EvidenceItem(
                    type=EvidenceType.URL_SHORTENER,
                    severity=Severity.MEDIUM,
                    description=f"URL uses shortener service: {hostname}",
                    raw_data={"url": url, "shortener": hostname},
                ))

            # 2. IP-based URL
            if _IP_URL_REGEX.match(url):
                ip_count += 1
                evidences.append(EvidenceItem(
                    type=EvidenceType.URL_IP_BASED,
                    severity=Severity.HIGH,
                    description=f"URL uses IP address instead of domain: {hostname}",
                    raw_data={"url": url},
                ))

            # 3. Suspicious TLD in URL
            for tld in SUSPICIOUS_TLDS:
                if hostname.endswith(tld.lstrip(".")):
                    suspicious_count += 1
                    evidences.append(EvidenceItem(
                        type=EvidenceType.URL_SUSPICIOUS,
                        severity=Severity.MEDIUM,
                        description=f"URL domain uses suspicious TLD: {hostname}",
                        raw_data={"url": url, "tld": tld},
                    ))
                    break

        # Score: combine signals
        score = 0.0
        if ip_count > 0:
            score = max(score, 0.7)
        if shortener_count > 0:
            score = max(score, 0.4 + 0.1 * min(shortener_count, 3))
        if suspicious_count > 0:
            score = max(score, 0.3 + 0.1 * min(suspicious_count, 3))

        return min(1.0, score), evidences

    # ------------------------------------------------------------------
    # Sub-engine 3: Keyword Analysis
    # ------------------------------------------------------------------

    async def _analyze_keywords(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Scan subject + body for urgency, phishing, and financial keywords."""
        evidences: list[EvidenceItem] = []

        subject = (email_data.get("subject") or "").lower()
        body = (email_data.get("body_text") or "").lower()
        combined = f"{subject} {body}"

        if not combined.strip():
            return 0.0, []

        urgency_hits: list[str] = []
        phishing_hits: list[str] = []
        financial_hits: list[str] = []

        for kw in URGENCY_KEYWORDS:
            if kw in combined:
                urgency_hits.append(kw)

        for kw in PHISHING_KEYWORDS:
            if kw in combined:
                phishing_hits.append(kw)

        for kw in FINANCIAL_KEYWORDS:
            if kw in combined:
                financial_hits.append(kw)

        # Evidence generation
        if urgency_hits:
            evidences.append(EvidenceItem(
                type=EvidenceType.KEYWORD_URGENCY,
                severity=Severity.MEDIUM,
                description=f"Urgency keywords detected: {', '.join(urgency_hits[:5])}",
                raw_data={"keywords": urgency_hits},
            ))

        if phishing_hits:
            evidences.append(EvidenceItem(
                type=EvidenceType.KEYWORD_PHISHING,
                severity=Severity.HIGH,
                description=f"Phishing keywords detected: {', '.join(phishing_hits[:5])}",
                raw_data={"keywords": phishing_hits},
            ))

        # CAPS abuse: more than 30% uppercase words (excluding short emails)
        original_body = email_data.get("body_text") or ""
        words = original_body.split()
        if len(words) > 10:
            caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
            caps_ratio = caps_words / len(words)
            if caps_ratio > 0.3:
                evidences.append(EvidenceItem(
                    type=EvidenceType.KEYWORD_CAPS_ABUSE,
                    severity=Severity.LOW,
                    description=f"Excessive uppercase: {caps_ratio:.0%} of words",
                    raw_data={"caps_ratio": round(caps_ratio, 3), "caps_words": caps_words},
                ))

        # Score: weighted combination
        score = 0.0
        if phishing_hits:
            score += 0.3 + 0.1 * min(len(phishing_hits), 4)
        if urgency_hits:
            score += 0.2 + 0.05 * min(len(urgency_hits), 4)
        if financial_hits:
            score += 0.15 + 0.05 * min(len(financial_hits), 3)
        if len(words) > 10 and caps_ratio > 0.3:  # type: ignore[possibly-undefined]
            score += 0.1

        return min(1.0, score), evidences

    # ------------------------------------------------------------------
    # Sub-engine 4: Authentication Analysis
    # ------------------------------------------------------------------

    async def _analyze_auth(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Check SPF/DKIM/DMARC results and reply-to mismatch."""
        evidences: list[EvidenceItem] = []
        auth: dict = email_data.get("auth_results", {})
        score = 0.0

        # SPF
        spf = auth.get("spf", "none").lower()
        if spf in ("fail", "softfail"):
            score += 0.35
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_SPF_FAIL,
                severity=Severity.HIGH if spf == "fail" else Severity.MEDIUM,
                description=f"SPF check result: {spf}",
                raw_data={"spf": spf},
            ))

        # DKIM
        dkim = auth.get("dkim", "none").lower()
        if dkim == "fail":
            score += 0.3
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DKIM_FAIL,
                severity=Severity.HIGH,
                description=f"DKIM check result: {dkim}",
                raw_data={"dkim": dkim},
            ))

        # DMARC
        dmarc = auth.get("dmarc", "none").lower()
        if dmarc == "fail":
            score += 0.35
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DMARC_FAIL,
                severity=Severity.CRITICAL,
                description=f"DMARC check result: {dmarc}",
                raw_data={"dmarc": dmarc},
            ))

        # Reply-To mismatch: reply_to domain ≠ sender domain
        sender = email_data.get("sender_email", "")
        reply_to = email_data.get("reply_to", "")
        if reply_to and sender:
            sender_domain = sender.rsplit("@", 1)[-1].lower() if "@" in sender else ""
            reply_domain = reply_to.rsplit("@", 1)[-1].lower() if "@" in reply_to else ""
            if sender_domain and reply_domain and sender_domain != reply_domain:
                score += 0.3
                evidences.append(EvidenceItem(
                    type=EvidenceType.AUTH_REPLY_TO_MISMATCH,
                    severity=Severity.HIGH,
                    description=(
                        f"Reply-To domain ({reply_domain}) differs from "
                        f"sender domain ({sender_domain})"
                    ),
                    raw_data={
                        "sender_domain": sender_domain,
                        "reply_to_domain": reply_domain,
                    },
                ))

        return min(1.0, score), evidences
