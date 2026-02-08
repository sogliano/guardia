"""Layer 1: Heuristic analysis engine (~5ms).

Four weighted sub-engines + attachment/impersonation/header bonuses:
- Auth analysis  (35%): SPF/DKIM/DMARC failures, DMARC missing, compound failures, reply-to mismatch
- Domain analysis (25%): blacklist (DB), typosquatting, suspicious TLDs
- URL analysis    (25%): shorteners, IP-based URLs, suspicious TLD links
- Keyword analysis(15%): urgency, phishing terms, CAPS abuse, financial/BEC

Additive bonuses (on top of weighted score):
- Attachment risk: suspicious extensions, double extensions
- Header analysis: Received chain hops, suspicious mailers, Message-ID mismatch
- Correlation boost: 3+ sub-engines firing simultaneously

Security design: this is a pre-delivery email security gateway.
False negatives (missing threats) are worse than false positives.
Scoring is intentionally aggressive on auth failures.
"""

import asyncio
import re
import time
from urllib.parse import urlparse

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import (
    ATTACHMENT_DOUBLE_EXT_BONUS,
    ATTACHMENT_SUSPICIOUS_BONUS,
    AUTH_COMPOUND_2_BONUS,
    AUTH_COMPOUND_3_BONUS,
    HEURISTIC_AUTH_DKIM_ERROR_SCORE,
    HEURISTIC_AUTH_DKIM_FAIL_SCORE,
    HEURISTIC_AUTH_DMARC_ERROR_SCORE,
    HEURISTIC_AUTH_DMARC_FAIL_SCORE,
    HEURISTIC_AUTH_DMARC_NONE_SCORE,
    HEURISTIC_AUTH_HEADER_MAX_BONUS,
    HEURISTIC_AUTH_KNOWN_DOMAIN_MULTIPLIER,
    HEURISTIC_AUTH_LOOKALIKE_DOMAIN_MULTIPLIER,
    HEURISTIC_AUTH_REPLY_TO_MISMATCH_SCORE,
    HEURISTIC_AUTH_SPF_ERROR_SCORE,
    HEURISTIC_AUTH_SPF_FAIL_SCORE,
    HEURISTIC_AUTH_SPF_NEUTRAL_SCORE,
    HEURISTIC_AUTH_SPF_SOFTFAIL_SCORE,
    HEURISTIC_CORRELATION_BOOST_3,
    HEURISTIC_CORRELATION_BOOST_4,
    HEURISTIC_DOMAIN_LOOKALIKE_SCORE,
    HEURISTIC_DOMAIN_SUSPICIOUS_TLD_SCORE,
    HEURISTIC_DOMAIN_TYPOSQUATTING_SCORE,
    HEURISTIC_HEADER_EXCESSIVE_HOPS_BONUS,
    HEURISTIC_HEADER_MISSING_GMAIL_BONUS,
    HEURISTIC_HEADER_MSGID_MISMATCH_BONUS,
    HEURISTIC_HEADER_SUSPICIOUS_MAILER_BONUS,
    HEURISTIC_IMPERSONATION_BONUS,
    HEURISTIC_KEYWORD_CAPS_ABUSE_PENALTY,
    HEURISTIC_KEYWORD_CAPS_ABUSE_THRESHOLD,
    HEURISTIC_KEYWORD_FINANCIAL_BASE,
    HEURISTIC_KEYWORD_FINANCIAL_INCREMENT,
    HEURISTIC_KEYWORD_PHISHING_BASE,
    HEURISTIC_KEYWORD_PHISHING_INCREMENT,
    HEURISTIC_KEYWORD_URGENCY_BASE,
    HEURISTIC_KEYWORD_URGENCY_INCREMENT,
    HEURISTIC_URL_IP_BASED_SCORE,
    HEURISTIC_URL_SHORTENER_BASE,
    HEURISTIC_URL_SHORTENER_INCREMENT,
    HEURISTIC_URL_SUSPICIOUS_BASE,
    HEURISTIC_URL_SUSPICIOUS_INCREMENT,
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
    DOUBLE_EXTENSION_PATTERN,
    FINANCIAL_KEYWORDS,
    IMPERSONATION_TITLES,
    KNOWN_DOMAINS,
    MAX_EXPECTED_HOPS,
    MSGID_DOMAIN_MAP,
    PHISHING_KEYWORDS,
    SUSPICIOUS_EXTENSIONS,
    SUSPICIOUS_MAILERS,
    SUSPICIOUS_TLDS,
    URGENCY_KEYWORDS,
    URL_SHORTENER_DOMAINS,
)
from app.services.pipeline.models import EvidenceItem, HeuristicResult
from app.services.pipeline.url_resolver import URLResolver, is_shortener

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


# Character substitution map for brand lookalike detection
_CHAR_SUBSTITUTIONS: dict[str, list[str]] = {
    "i": ["1", "l", "!"],
    "e": ["3"],
    "a": ["@", "4"],
    "o": ["0"],
    "s": ["5", "$"],
    "t": ["7"],
    "l": ["1", "i"],
}

# Common brand suffixes used in lookalike domains
_BRAND_SUFFIXES = [
    "-security", "-sec", "-it", "-tech", "-mail",
    "-support", "-team", "-corp", "-inc", "-group",
    "security", "sec",
]


def _generate_brand_variants(brand: str) -> set[str]:
    """Generate common character substitution variants of a brand name."""
    variants = {brand}
    for i, char in enumerate(brand):
        if char in _CHAR_SUBSTITUTIONS:
            for sub in _CHAR_SUBSTITUTIONS[char]:
                variant = brand[:i] + sub + brand[i + 1:]
                variants.add(variant)
    return variants


def _is_brand_lookalike(domain: str, protected_domains: set[str]) -> tuple[bool, str]:
    """Check if domain is a lookalike of any protected domain's brand.

    Returns (is_lookalike, matched_protected_domain).
    """
    for protected in protected_domains:
        brand = protected.split(".")[0]
        if len(brand) < 3:
            continue

        if domain == protected:
            return False, ""

        variants = _generate_brand_variants(brand)
        domain_lower = domain.lower()
        domain_name = domain_lower.split(".")[0]

        for variant in variants:
            if variant in domain_lower:
                return True, protected

        for suffix in _BRAND_SUFFIXES:
            for variant in variants:
                stripped = suffix.lstrip("-")
                if domain_name in (f"{variant}{suffix}", f"{stripped}{variant}"):
                    return True, protected

    return False, ""


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
        """Run all sub-engines and compute weighted score with bonuses."""
        start = time.monotonic()
        await self._load_policies()

        result = HeuristicResult()
        evidences: list[EvidenceItem] = []

        domain_score, domain_ev = await self._analyze_domain(email_data)
        url_score, url_ev = await self._analyze_urls(email_data)
        keyword_score, keyword_ev = await self._analyze_keywords(email_data)
        auth_score, auth_ev = await self._analyze_auth(email_data)
        attach_bonus, attach_ev = self._analyze_attachments(email_data)
        impersonation_ev = self._analyze_impersonation(email_data)
        header_bonus, header_ev = self._analyze_headers(email_data)

        result.domain_score = domain_score
        result.url_score = url_score
        result.keyword_score = keyword_score
        result.auth_score = auth_score
        evidences.extend(domain_ev)
        evidences.extend(url_ev)
        evidences.extend(keyword_ev)
        evidences.extend(auth_ev)
        evidences.extend(attach_ev)
        evidences.extend(impersonation_ev)
        evidences.extend(header_ev)

        # Weighted score from 4 main sub-engines
        weighted = (
            result.domain_score * HEURISTIC_WEIGHT_DOMAIN
            + result.url_score * HEURISTIC_WEIGHT_URL
            + result.keyword_score * HEURISTIC_WEIGHT_KEYWORD
            + result.auth_score * HEURISTIC_WEIGHT_AUTH
        )

        # Correlation boost: multiple sub-engines firing = higher confidence
        active_engines = sum(1 for s in [
            result.domain_score, result.url_score,
            result.keyword_score, result.auth_score,
        ] if s > 0)
        if active_engines >= 4:
            weighted *= HEURISTIC_CORRELATION_BOOST_4
        elif active_engines >= 3:
            weighted *= HEURISTIC_CORRELATION_BOOST_3

        # Additive bonuses (attachment risk + header anomalies)
        weighted += attach_bonus
        weighted += header_bonus

        # Impersonation signals boost keyword weight (BEC indicator)
        if impersonation_ev:
            weighted += HEURISTIC_IMPERSONATION_BONUS

        result.score = min(1.0, max(0.0, weighted))
        result.evidences = evidences
        result.execution_time_ms = int((time.monotonic() - start) * 1000)

        logger.info(
            "heuristic_analysis_complete",
            score=result.score,
            domain=result.domain_score,
            url=result.url_score,
            keyword=result.keyword_score,
            auth=result.auth_score,
            active_engines=active_engines,
            attach_bonus=attach_bonus,
            header_bonus=header_bonus,
            impersonation=len(impersonation_ev),
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
                description=(
                    f"The sender domain '{domain}' is on the organization's "
                    f"blocklist of known malicious domains. Emails from this "
                    f"domain should be treated as high-risk threats."
                ),
                raw_data={"domain": domain},
            ))
            return score, evidences

        # 2. Suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                score = max(score, HEURISTIC_DOMAIN_SUSPICIOUS_TLD_SCORE)
                evidences.append(EvidenceItem(
                    type=EvidenceType.DOMAIN_SUSPICIOUS_TLD,
                    severity=Severity.MEDIUM,
                    description=(
                        f"The sender domain '{domain}' uses the TLD "
                        f"'{tld}', which is commonly associated with "
                        f"phishing and spam campaigns due to low "
                        f"registration barriers."
                    ),
                    raw_data={"domain": domain, "tld": tld},
                ))
                break

        # 3. Typosquatting: Levenshtein distance to known domains
        for known in KNOWN_DOMAINS:
            if domain == known:
                break

            # Early exit: if length difference > 2, impossible Levenshtein <= 2
            len_diff = abs(len(domain) - len(known))
            if len_diff > 2:
                continue

            # Early exit: if domains don't share first char and have len diff,
            # very likely dist > 2 (heuristic optimization)
            if len(domain) > 0 and len(known) > 0:
                if domain[0] != known[0] and len_diff > 0:
                    continue

            dist = _levenshtein(domain, known)
            if 1 <= dist <= 2:
                score = max(score, HEURISTIC_DOMAIN_TYPOSQUATTING_SCORE)
                evidences.append(EvidenceItem(
                    type=EvidenceType.DOMAIN_TYPOSQUATTING,
                    severity=Severity.HIGH,
                    description=(
                        f"The domain '{domain}' is suspiciously similar "
                        f"to the legitimate domain '{known}' (edit "
                        f"distance: {dist}). This is a common "
                        f"typosquatting technique used to impersonate "
                        f"trusted organizations."
                    ),
                    raw_data={"domain": domain, "similar_to": known, "distance": dist},
                ))
                break

        # 4. Brand lookalike detection (protected domain impersonation)
        if not any(e.type == EvidenceType.DOMAIN_TYPOSQUATTING for e in evidences):
            protected_domains = {
                d.strip().lower()
                for d in settings.accepted_domains.split(",")
                if d.strip()
            }
            protected_domains |= settings.allowlist_domains_set

            is_lookalike, matched_domain = _is_brand_lookalike(
                domain, protected_domains
            )
            if is_lookalike:
                score = max(score, HEURISTIC_DOMAIN_LOOKALIKE_SCORE)
                evidences.append(EvidenceItem(
                    type=EvidenceType.DOMAIN_LOOKALIKE,
                    severity=Severity.HIGH,
                    description=(
                        f"The domain '{domain}' appears to be a lookalike "
                        f"of the protected domain '{matched_domain}'. "
                        f"It contains the organization's brand name or a "
                        f"close variant, which is a common impersonation "
                        f"technique in targeted phishing attacks."
                    ),
                    raw_data={
                        "domain": domain,
                        "protected_domain": matched_domain,
                    },
                ))

        return min(1.0, score), evidences

    # ------------------------------------------------------------------
    # Sub-engine 2: URL Analysis
    # ------------------------------------------------------------------

    async def _analyze_urls(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Analyze URLs for shorteners, IP-based, suspicious patterns.

        Shortened URLs are resolved to their final destination and the
        resolved URL is also checked for IP-based, suspicious TLD, etc.
        """
        evidences: list[EvidenceItem] = []
        urls: list[str] = email_data.get("urls", [])

        if not urls:
            return 0.0, []

        # Resolve shortened URLs concurrently (5s global timeout)
        resolver = URLResolver()
        resolve_tasks: dict[str, asyncio.Task] = {}
        for url in urls:
            if is_shortener(url):
                resolve_tasks[url] = asyncio.create_task(resolver.resolve(url))

        resolved_map: dict[str, str | None] = {}
        if resolve_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*resolve_tasks.values(), return_exceptions=True),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                logger.warning("url_resolution_global_timeout")
                # Cancel all pending tasks to prevent resource leaks
                for task in resolve_tasks.values():
                    if not task.done():
                        task.cancel()
                # Wait for tasks to clean up properly
                try:
                    await asyncio.gather(*resolve_tasks.values(), return_exceptions=True)
                except asyncio.CancelledError:
                    pass

            # Collect results from completed tasks only
            for url, task in resolve_tasks.items():
                if task.done() and not task.cancelled():
                    try:
                        result = task.result()
                        if isinstance(result, tuple):
                            resolved_map[url] = result[0]  # resolved_url or None
                        else:
                            resolved_map[url] = None
                    except asyncio.CancelledError:
                        pass

        shortener_count = 0
        ip_count = 0
        suspicious_count = 0

        for url in urls:
            try:
                parsed = urlparse(url)
                hostname = (parsed.hostname or "").lower()
            except Exception:
                continue

            # 1. URL shortener detection + resolution
            if hostname in URL_SHORTENER_DOMAINS:
                shortener_count += 1
                resolved_url = resolved_map.get(url)
                resolved_host = ""
                if resolved_url:
                    try:
                        resolved_host = (urlparse(resolved_url).hostname or "").lower()
                    except Exception:
                        pass

                desc = (
                    f"A URL in the email uses the shortener service "
                    f"'{hostname}', which can be used to hide the "
                    f"true destination of malicious links."
                )
                raw = {"url": url, "shortener": hostname}
                if resolved_url:
                    desc += f" Resolved destination: {resolved_url}"
                    raw["resolved_url"] = resolved_url
                    raw["resolved_hostname"] = resolved_host

                evidences.append(EvidenceItem(
                    type=EvidenceType.URL_SHORTENER,
                    severity=Severity.MEDIUM,
                    description=desc,
                    raw_data=raw,
                ))

                # Check resolved URL for additional threats
                if resolved_url and resolved_host:
                    ip_c, sus_c = self._check_resolved_url(
                        resolved_url, resolved_host, url, evidences
                    )
                    ip_count += ip_c
                    suspicious_count += sus_c
                continue

            # 2. IP-based URL
            if _IP_URL_REGEX.match(url):
                ip_count += 1
                evidences.append(EvidenceItem(
                    type=EvidenceType.URL_IP_BASED,
                    severity=Severity.HIGH,
                    description=(
                        f"A URL points directly to an IP address "
                        f"({hostname}) instead of a domain name. "
                        f"Legitimate services rarely use raw IP "
                        f"addresses, making this a strong indicator "
                        f"of a phishing or malware delivery link."
                    ),
                    raw_data={"url": url},
                ))

            # 3. Suspicious TLD in URL
            for tld in SUSPICIOUS_TLDS:
                if hostname.endswith(tld.lstrip(".")):
                    suspicious_count += 1
                    evidences.append(EvidenceItem(
                        type=EvidenceType.URL_SUSPICIOUS,
                        severity=Severity.MEDIUM,
                        description=(
                            f"A URL in the email points to '{hostname}', "
                            f"which uses a TLD commonly associated with "
                            f"malicious activity. Links to these domains "
                            f"carry elevated risk."
                        ),
                        raw_data={"url": url, "tld": tld},
                    ))
                    break

        # Score: combine signals (elevated scores for threats behind shorteners)
        score = 0.0
        if ip_count > 0:
            score = max(score, HEURISTIC_URL_IP_BASED_SCORE)
        if shortener_count > 0:
            score = max(
                score,
                HEURISTIC_URL_SHORTENER_BASE + HEURISTIC_URL_SHORTENER_INCREMENT * min(shortener_count, 3)
            )
        if suspicious_count > 0:
            score = max(
                score,
                HEURISTIC_URL_SUSPICIOUS_BASE + HEURISTIC_URL_SUSPICIOUS_INCREMENT * min(suspicious_count, 3)
            )

        return min(1.0, score), evidences

    def _check_resolved_url(
        self,
        resolved_url: str,
        resolved_host: str,
        original_url: str,
        evidences: list[EvidenceItem],
    ) -> tuple[int, int]:
        """Check a resolved URL for IP-based and suspicious TLD patterns.

        Returns (ip_count, suspicious_count) added.
        """
        ip_count = 0
        suspicious_count = 0

        if _IP_URL_REGEX.match(resolved_url):
            ip_count += 1
            evidences.append(EvidenceItem(
                type=EvidenceType.URL_IP_BASED,
                severity=Severity.HIGH,
                description=(
                    f"A shortened URL ({original_url}) resolves to an "
                    f"IP-based destination ({resolved_host}). This is a "
                    f"strong phishing indicator — the shortener hides "
                    f"a raw IP address."
                ),
                raw_data={
                    "url": resolved_url,
                    "original_url": original_url,
                },
            ))

        for tld in SUSPICIOUS_TLDS:
            if resolved_host.endswith(tld.lstrip(".")):
                suspicious_count += 1
                evidences.append(EvidenceItem(
                    type=EvidenceType.URL_SUSPICIOUS,
                    severity=Severity.HIGH,
                    description=(
                        f"A shortened URL ({original_url}) resolves to "
                        f"'{resolved_host}', which uses a suspicious TLD. "
                        f"The shortener obscures a potentially malicious "
                        f"destination."
                    ),
                    raw_data={
                        "url": resolved_url,
                        "original_url": original_url,
                        "tld": tld,
                    },
                ))
                break

        return ip_count, suspicious_count

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
                description=(
                    f"The email contains {len(urgency_hits)} urgency "
                    f"keyword(s): {', '.join(urgency_hits[:5])}. "
                    f"Attackers often create a false sense of urgency "
                    f"to pressure victims into acting without thinking."
                ),
                raw_data={"keywords": urgency_hits},
            ))

        if phishing_hits:
            evidences.append(EvidenceItem(
                type=EvidenceType.KEYWORD_PHISHING,
                severity=Severity.HIGH,
                description=(
                    f"The email contains {len(phishing_hits)} "
                    f"phishing-related keyword(s): "
                    f"{', '.join(phishing_hits[:5])}. These terms are "
                    f"frequently found in credential theft and social "
                    f"engineering attacks."
                ),
                raw_data={"keywords": phishing_hits},
            ))

        # CAPS abuse: more than 30% uppercase words (excluding short emails)
        original_body = email_data.get("body_text") or ""
        words = original_body.split()
        caps_ratio = 0.0
        if len(words) > 10:
            caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
            caps_ratio = caps_words / len(words)
            if caps_ratio > HEURISTIC_KEYWORD_CAPS_ABUSE_THRESHOLD:
                evidences.append(EvidenceItem(
                    type=EvidenceType.KEYWORD_CAPS_ABUSE,
                    severity=Severity.LOW,
                    description=(
                        f"The email body contains {caps_ratio:.0%} "
                        f"uppercase words ({caps_words} of "
                        f"{len(words)}). Excessive use of capital "
                        f"letters is a social engineering tactic to "
                        f"convey urgency and grab attention."
                    ),
                    raw_data={"caps_ratio": round(caps_ratio, 3), "caps_words": caps_words},
                ))

        # Score: weighted combination
        score = 0.0
        if phishing_hits:
            score += HEURISTIC_KEYWORD_PHISHING_BASE + HEURISTIC_KEYWORD_PHISHING_INCREMENT * min(len(phishing_hits), 4)
        if urgency_hits:
            score += HEURISTIC_KEYWORD_URGENCY_BASE + HEURISTIC_KEYWORD_URGENCY_INCREMENT * min(len(urgency_hits), 4)
        if financial_hits:
            score += HEURISTIC_KEYWORD_FINANCIAL_BASE + HEURISTIC_KEYWORD_FINANCIAL_INCREMENT * min(len(financial_hits), 3)
        if len(words) > 10 and caps_ratio > HEURISTIC_KEYWORD_CAPS_ABUSE_THRESHOLD:
            score += HEURISTIC_KEYWORD_CAPS_ABUSE_PENALTY

        return min(1.0, score), evidences

    # ------------------------------------------------------------------
    # Sub-engine 4: Authentication Analysis
    # ------------------------------------------------------------------

    async def _analyze_auth(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Check SPF/DKIM/DMARC results, compound failures, and reply-to mismatch.

        Scoring rationale (max 1.0):
          DMARC fail    = 0.45 (strongest signal, combines SPF+DKIM policy)
          DMARC none    = 0.15 (no policy = no protection, suspicious)
          SPF fail      = 0.30
          SPF softfail  = 0.15
          SPF neutral   = 0.08 (inconclusive, slight risk)
          DKIM fail     = 0.25
          Reply-To      = 0.20 (BEC indicator)

        Compound auth failures add a bonus:
          2 of 3 mechanisms failed = +0.15
          3 of 3 mechanisms failed = +0.30

        Possible auth results per RFC 8601:
          pass, fail, softfail, neutral, none, temperror, permerror
        """
        evidences: list[EvidenceItem] = []
        auth: dict = email_data.get("auth_results", {})
        score = 0.0

        # Track individual mechanism failures for compound detection
        spf_failed = False
        dkim_failed = False
        dmarc_failed = False

        # --- SPF ---
        spf = auth.get("spf", "none").lower()
        if spf == "fail":
            score += HEURISTIC_AUTH_SPF_FAIL_SCORE
            spf_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_SPF_FAIL,
                severity=Severity.HIGH,
                description=(
                    "SPF verification returned 'fail'. The sending server is not authorized "
                    "to send email on behalf of this domain, which is a strong indicator of "
                    "email spoofing."
                ),
                raw_data={"spf": spf},
            ))
        elif spf == "softfail":
            score += HEURISTIC_AUTH_SPF_SOFTFAIL_SCORE
            spf_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_SPF_FAIL,
                severity=Severity.MEDIUM,
                description=(
                    "SPF verification returned 'softfail'. The sending "
                    "server is weakly authorized to send email on "
                    "behalf of this domain. While not a hard failure, "
                    "this indicates the domain owner has not fully "
                    "authorized this server, which may indicate "
                    "spoofing."
                ),
                raw_data={"spf": spf},
            ))
        elif spf == "neutral":
            score += HEURISTIC_AUTH_SPF_NEUTRAL_SCORE
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_SPF_NEUTRAL,
                severity=Severity.LOW,
                description=(
                    "SPF verification returned 'neutral'. The domain "
                    "owner has explicitly stated that no assertion "
                    "can be made about the sender's authorization. "
                    "This provides no protection against spoofing."
                ),
                raw_data={"spf": spf},
            ))
        elif spf in ("temperror", "permerror"):
            score += HEURISTIC_AUTH_SPF_ERROR_SCORE
            spf_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_SPF_FAIL,
                severity=Severity.MEDIUM,
                description=(
                    f"SPF verification returned '{spf}'. "
                    f"A {'temporary' if spf == 'temperror' else 'permanent'} error occurred "
                    f"during SPF validation, preventing "
                    f"authentication of the sender. This may "
                    f"indicate a misconfigured or intentionally "
                    f"broken SPF record."
                ),
                raw_data={"spf": spf},
            ))

        # --- DKIM ---
        dkim = auth.get("dkim", "none").lower()
        if dkim == "fail":
            score += HEURISTIC_AUTH_DKIM_FAIL_SCORE
            dkim_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DKIM_FAIL,
                severity=Severity.HIGH,
                description=(
                    "DKIM signature verification failed. The email's cryptographic signature "
                    "does not match, indicating the message may have been tampered with in transit "
                    "or the sender is not who they claim to be."
                ),
                raw_data={"dkim": dkim},
            ))
        elif dkim in ("temperror", "permerror"):
            score += HEURISTIC_AUTH_DKIM_ERROR_SCORE
            dkim_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DKIM_FAIL,
                severity=Severity.MEDIUM,
                description=(
                    f"DKIM verification returned '{dkim}'. "
                    f"A {'temporary' if dkim == 'temperror' else 'permanent'} error occurred "
                    f"during DKIM validation. The email's integrity "
                    f"could not be verified."
                ),
                raw_data={"dkim": dkim},
            ))

        # --- DMARC ---
        dmarc = auth.get("dmarc", "none").lower()
        if dmarc == "fail":
            score += HEURISTIC_AUTH_DMARC_FAIL_SCORE
            dmarc_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DMARC_FAIL,
                severity=Severity.CRITICAL,
                description=(
                    "DMARC policy validation failed. The domain's authentication policy (combining "
                    "SPF and DKIM) was not satisfied, strongly suggesting this email may be a "
                    "spoofed or forged message impersonating the sender's domain."
                ),
                raw_data={"dmarc": dmarc},
            ))
        elif dmarc == "none":
            score += HEURISTIC_AUTH_DMARC_NONE_SCORE
            dmarc_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DMARC_MISSING,
                severity=Severity.MEDIUM,
                description=(
                    "No DMARC policy is published for the sender's domain. Without DMARC, "
                    "there is no domain-level policy to prevent email spoofing. Legitimate "
                    "organizations typically publish DMARC records to protect their domain."
                ),
                raw_data={"dmarc": dmarc},
            ))
        elif dmarc in ("temperror", "permerror"):
            score += HEURISTIC_AUTH_DMARC_ERROR_SCORE
            dmarc_failed = True
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_DMARC_FAIL,
                severity=Severity.MEDIUM,
                description=(
                    f"DMARC verification returned '{dmarc}'. "
                    f"A {'temporary' if dmarc == 'temperror' else 'permanent'} error prevented "
                    f"DMARC policy evaluation. The domain's "
                    f"anti-spoofing policy could not be enforced."
                ),
                raw_data={"dmarc": dmarc},
            ))

        # --- Compound auth failure bonus ---
        failed_count = sum([spf_failed, dkim_failed, dmarc_failed])
        if failed_count >= 3:
            score += AUTH_COMPOUND_3_BONUS
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_COMPOUND_FAILURE,
                severity=Severity.CRITICAL,
                description=(
                    "All three email authentication mechanisms (SPF, DKIM, DMARC) failed or are "
                    "absent. This combination is extremely rare for legitimate email and is a very "
                    "strong indicator of a spoofed or malicious message."
                ),
                raw_data={
                    "spf": spf, "dkim": dkim, "dmarc": dmarc,
                    "failed_count": failed_count,
                },
            ))
        elif failed_count >= 2:
            score += AUTH_COMPOUND_2_BONUS
            evidences.append(EvidenceItem(
                type=EvidenceType.AUTH_COMPOUND_FAILURE,
                severity=Severity.HIGH,
                description=(
                    f"Multiple email authentication mechanisms failed ({failed_count} of 3). "
                    f"The combination of authentication failures significantly increases the "
                    f"likelihood that this email is spoofed or malicious."
                ),
                raw_data={
                    "spf": spf, "dkim": dkim, "dmarc": dmarc,
                    "failed_count": failed_count,
                },
            ))

        # --- Reply-To mismatch ---
        sender = email_data.get("sender_email", "")
        reply_to = email_data.get("reply_to", "")
        if reply_to and sender:
            sender_domain = sender.rsplit("@", 1)[-1].lower() if "@" in sender else ""
            reply_domain = reply_to.rsplit("@", 1)[-1].lower() if "@" in reply_to else ""
            if sender_domain and reply_domain and sender_domain != reply_domain:
                score += HEURISTIC_AUTH_REPLY_TO_MISMATCH_SCORE
                evidences.append(EvidenceItem(
                    type=EvidenceType.AUTH_REPLY_TO_MISMATCH,
                    severity=Severity.HIGH,
                    description=(
                        f"The Reply-To header points to "
                        f"'{reply_domain}' while the sender domain "
                        f"is '{sender_domain}'. This mismatch is a "
                        f"common indicator of BEC (Business Email "
                        f"Compromise) attacks, where replies are "
                        f"routed to an attacker-controlled address."
                    ),
                    raw_data={
                        "sender_domain": sender_domain,
                        "reply_to_domain": reply_domain,
                    },
                ))

        # --- Auth contextual modifier ---
        # Auth failures from known brands or protected domain lookalikes
        # are more suspicious than from unknown domains
        if score > 0:
            auth_sender = email_data.get("sender_email", "").lower()
            if auth_sender and "@" in auth_sender:
                auth_domain = auth_sender.rsplit("@", 1)[1]
                protected_domains = {
                    d.strip().lower()
                    for d in settings.accepted_domains.split(",")
                    if d.strip()
                }
                protected_domains |= settings.allowlist_domains_set
                is_lookalike, _ = _is_brand_lookalike(auth_domain, protected_domains)

                if is_lookalike:
                    score *= HEURISTIC_AUTH_LOOKALIKE_DOMAIN_MULTIPLIER
                elif auth_domain in KNOWN_DOMAINS:
                    score *= HEURISTIC_AUTH_KNOWN_DOMAIN_MULTIPLIER

        return min(1.0, score), evidences

    # ------------------------------------------------------------------
    # Sub-engine 5: Attachment Analysis (additive bonus)
    # ------------------------------------------------------------------

    def _analyze_attachments(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Check attachments for suspicious extensions and double extensions."""
        evidences: list[EvidenceItem] = []
        attachments: list[dict] = email_data.get("attachments", [])
        bonus = 0.0

        if not attachments:
            return 0.0, []

        for att in attachments:
            filename = (att.get("filename") or "").lower()
            if not filename:
                continue

            # Double extension (e.g., invoice.pdf.exe) — most dangerous
            if re.search(DOUBLE_EXTENSION_PATTERN, filename, re.IGNORECASE):
                bonus = max(bonus, ATTACHMENT_DOUBLE_EXT_BONUS)
                evidences.append(EvidenceItem(
                    type=EvidenceType.ATTACHMENT_DOUBLE_EXT,
                    severity=Severity.CRITICAL,
                    description=(
                        f"The attachment '{filename}' uses a double extension, a technique "
                        f"where a dangerous file type is disguised as a safe one (e.g., "
                        f"'document.pdf.exe'). This is a strong indicator of malware delivery."
                    ),
                    raw_data={"filename": filename},
                ))
                continue

            # Suspicious extension
            for ext in SUSPICIOUS_EXTENSIONS:
                if filename.endswith(ext):
                    bonus = max(bonus, ATTACHMENT_SUSPICIOUS_BONUS)
                    evidences.append(EvidenceItem(
                        type=EvidenceType.ATTACHMENT_SUSPICIOUS_EXT,
                        severity=Severity.HIGH,
                        description=(
                            f"The attachment '{filename}' has the extension '{ext}', which is "
                            f"an executable or script file type commonly used to deliver malware. "
                            f"Legitimate business emails rarely include these file types."
                        ),
                        raw_data={"filename": filename, "extension": ext},
                    ))
                    break

        return bonus, evidences

    # ------------------------------------------------------------------
    # Sub-engine 6: Display Name Impersonation (additive bonus)
    # ------------------------------------------------------------------

    def _analyze_impersonation(
        self, email_data: dict
    ) -> list[EvidenceItem]:
        """Detect display name impersonation patterns (BEC/CEO fraud)."""
        evidences: list[EvidenceItem] = []

        display_name = (email_data.get("sender_name") or "").lower()
        if not display_name:
            return []

        # Check for executive title impersonation
        for title in IMPERSONATION_TITLES:
            if title in display_name:
                evidences.append(EvidenceItem(
                    type=EvidenceType.CEO_IMPERSONATION,
                    severity=Severity.HIGH,
                    description=(
                        f"The sender's display name contains '{title}', an executive title "
                        f"commonly used in Business Email Compromise (BEC) attacks. Attackers "
                        f"impersonate executives to trick employees into unauthorized actions."
                    ),
                    raw_data={"display_name": display_name, "title_match": title},
                ))
                break

        # Check if display name contains a known domain brand
        # (e.g., "Google Support <fake@evil.com>")
        sender_email = (email_data.get("sender_email") or "").lower()
        if sender_email and "@" in sender_email:
            sender_domain = sender_email.rsplit("@", 1)[1]
            for known in KNOWN_DOMAINS:
                brand = known.split(".")[0]
                if (
                    len(brand) >= 4
                    and brand in display_name
                    and brand not in sender_domain
                ):
                    evidences.append(EvidenceItem(
                        type=EvidenceType.SENDER_IMPERSONATION,
                        severity=Severity.HIGH,
                        description=(
                            f"The display name references '{brand}' but the sender's actual "
                            f"domain is '{sender_domain}'. This is a common impersonation "
                            f"technique where attackers use trusted brand names in the display "
                            f"name to deceive recipients."
                        ),
                        raw_data={
                            "display_name": display_name,
                            "brand": brand,
                            "sender_domain": sender_domain,
                        },
                    ))
                    break

        return evidences

    # ------------------------------------------------------------------
    # Sub-engine 7: Header Analysis (additive bonus)
    # ------------------------------------------------------------------

    def _analyze_headers(
        self, email_data: dict
    ) -> tuple[float, list[EvidenceItem]]:
        """Analyze email headers beyond SPF/DKIM/DMARC.

        Checks:
        1. Received chain hop count (excessive hops = relay through suspicious infra)
        2. X-Mailer / User-Agent (mass-mailing tools)
        3. Message-ID domain vs sender domain consistency
        4. Missing standard headers for known providers
        """
        evidences: list[EvidenceItem] = []
        headers: dict = email_data.get("headers", {})
        bonus = 0.0

        if not headers:
            return 0.0, []

        # 1. Received chain analysis
        received = headers.get("received", [])
        if isinstance(received, list) and len(received) > MAX_EXPECTED_HOPS:
            hop_count = len(received)
            bonus += HEURISTIC_HEADER_EXCESSIVE_HOPS_BONUS
            evidences.append(EvidenceItem(
                type=EvidenceType.HEADER_EXCESSIVE_HOPS,
                severity=Severity.MEDIUM,
                description=(
                    f"The email passed through {hop_count} mail servers "
                    f"(expected ≤{MAX_EXPECTED_HOPS}). An unusually long "
                    f"relay chain may indicate routing through anonymous "
                    f"or compromised infrastructure to obscure the true "
                    f"origin of the message."
                ),
                raw_data={"hop_count": hop_count, "max_expected": MAX_EXPECTED_HOPS},
            ))

        # 2. X-Mailer / User-Agent analysis
        mailer = (
            headers.get("x-mailer", "")
            or headers.get("user-agent", "")
        ).lower()
        if mailer:
            for suspicious in SUSPICIOUS_MAILERS:
                if suspicious in mailer:
                    bonus += HEURISTIC_HEADER_SUSPICIOUS_MAILER_BONUS
                    evidences.append(EvidenceItem(
                        type=EvidenceType.HEADER_SUSPICIOUS_MAILER,
                        severity=Severity.HIGH,
                        description=(
                            f"The email was sent using '{mailer}', a tool "
                            f"commonly associated with mass-mailing or "
                            f"phishing campaigns. Legitimate business "
                            f"emails are typically sent from standard "
                            f"email clients or enterprise platforms."
                        ),
                        raw_data={"mailer": mailer, "matched": suspicious},
                    ))
                    break

        # 3. Message-ID domain vs sender domain consistency
        message_id = headers.get("message-id", "")
        sender_email = (email_data.get("sender_email") or "").lower()
        if message_id and sender_email and "@" in sender_email:
            sender_domain = sender_email.rsplit("@", 1)[1]
            # Extract domain from Message-ID (format: <random@domain>)
            msgid_domain = ""
            if "@" in message_id:
                msgid_part = message_id.split("@")[-1].strip().rstrip(">")
                msgid_domain = msgid_part.lower()

            if msgid_domain and sender_domain in MSGID_DOMAIN_MAP:
                expected_domains = MSGID_DOMAIN_MAP[sender_domain]
                if not any(exp in msgid_domain for exp in expected_domains):
                    bonus += HEURISTIC_HEADER_MSGID_MISMATCH_BONUS
                    evidences.append(EvidenceItem(
                        type=EvidenceType.HEADER_MSGID_MISMATCH,
                        severity=Severity.HIGH,
                        description=(
                            f"The Message-ID header domain '{msgid_domain}' "
                            f"does not match the expected infrastructure "
                            f"for sender domain '{sender_domain}'. "
                            f"Legitimate emails from {sender_domain} should "
                            f"have Message-IDs from "
                            f"{', '.join(sorted(expected_domains))}. "
                            f"This mismatch suggests the email did not "
                            f"originate from the claimed mail system."
                        ),
                        raw_data={
                            "message_id_domain": msgid_domain,
                            "sender_domain": sender_domain,
                            "expected": sorted(expected_domains),
                        },
                    ))

        # 4. Missing standard headers for known providers
        # Gmail always adds X-Google-DKIM-Signature
        if sender_email and "@" in sender_email:
            sender_domain = sender_email.rsplit("@", 1)[1]
            if sender_domain in ("gmail.com", "googlemail.com"):
                if not headers.get("x-google-dkim-signature"):
                    bonus += HEURISTIC_HEADER_MISSING_GMAIL_BONUS
                    evidences.append(EvidenceItem(
                        type=EvidenceType.HEADER_MISSING_STANDARD,
                        severity=Severity.HIGH,
                        description=(
                            "The email claims to be from Gmail but is "
                            "missing the X-Google-DKIM-Signature header, "
                            "which is always present in authentic Gmail "
                            "messages. This strongly suggests the email "
                            "did not originate from Google's mail servers."
                        ),
                        raw_data={"sender_domain": sender_domain},
                    ))

        return min(HEURISTIC_AUTH_HEADER_MAX_BONUS, bonus), evidences
