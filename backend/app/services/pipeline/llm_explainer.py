"""Layer 3: LLM Analyst (~2-3s).

Provider: OpenAI GPT (structured output via response_format).

The LLM provides an independent risk assessment: a phishing score (0.0-1.0)
and a human-readable explanation. Its score is weighted into the final
pipeline score alongside heuristic and ML scores.

Temperature is set to 0 for deterministic scoring.
"""

import json
import re
import time

import openai
import structlog

from app.config import settings
from app.services.pipeline.models import EvidenceItem, LLMResult

logger = structlog.get_logger()

_SYSTEM_PROMPT = """\
You are Guard-IA's LLM Analyst — a corporate email-fraud detection module specialized in phishing, BEC, credential theft, and impersonation.

## Organization Context
Protected organization: **Strike Security** (cybersecurity company).
- Primary domain: **strike.sh**
- Employee email pattern: firstname.lastname@strike.sh (e.g. jane.doe@strike.sh, john.smith@strike.sh)
- Internal notification senders: addresses ending in @strike.sh (e.g. security@strike.sh, noreply@strike.sh)
- Lookalike domains to watch: any domain resembling "strike" that is NOT exactly strike.sh (e.g. strikesecurity.com, strike-security.com, strikesecurity-it.com, str1ke.sh)

When an email originates from @strike.sh with valid authentication, weigh this strongly toward legitimacy. When an email uses a lookalike domain, treat it as a high-risk impersonation signal regardless of content.

## Score Calibration
# NOTE: These thresholds are deliberately independent from pipeline thresholds
# (THRESHOLD_ALLOW/WARN/QUARANTINE in config). The LLM scores independently.
0.00–0.15  Clearly legitimate — known sender, full auth pass, benign content
0.15–0.30  Low risk — minor anomalies only (e.g. missing DKIM on known platform)
0.30–0.50  Moderate — mixed signals, manual review warranted
0.50–0.70  Suspicious — multiple fraud indicators present
0.70–0.85  High risk — strong phishing / BEC pattern
0.85–1.00  Near-certain threat — converging critical signals

IMPORTANT: Do NOT inflate scores based on single weak signals. Authentication gaps alone (e.g. missing DKIM/DMARC on an otherwise normal email with no malicious URLs, no attachments, and no social engineering) should not push a score above 0.30. Reserve scores above 0.50 for emails where multiple independent threat signals converge.

Score differentiation guide — before finalizing your score, verify:
- Would this email fool a trained security analyst? If yes, score 0.70+
- Would it fool a careful regular user? If yes, score 0.50-0.70
- Is it obviously suspicious to most users? Score 0.30-0.50
- Is it a lazy mass-phishing attempt with obvious red flags? Score 0.15-0.30

## Output Format
Plain text with **bold** and bullet points only. No markdown headers (#).

1. **Opening** (2–3 sentences): Overall threat level, primary attack vector, most critical signals.
2. **Findings** — only include relevant bullets:
   - **Authentication:** SPF/DKIM/DMARC assessment and what it means
   - **Sender Domain:** Typosquatting, lookalike, suspicious TLD, or known legitimate
   - **Social Engineering:** Urgency, pressure, fear, authority impersonation
   - **Body Content:** Analyze message tone, requests for action, embedded credentials requests, social engineering tactics
   - **Links / Reply-To:** Mismatches, shorteners, IP-based URLs, suspicious destinations
   - **Attachments:** Dangerous extensions, double extensions, executable types
   - **Impersonation:** Brand, executive, or vendor impersonation patterns
   - **Automated Correlation:** Agreement or divergence with heuristic/ML scores
3. **Closing** (1–2 sentences): Risk summary and recommended action (allow / monitor / quarantine / block).

## Rules
- Be factual; cite specific evidence from the data provided.
- Bold key technical terms and domain names.
- When body content is provided, analyze it for social engineering tactics, mismatches between subject and body, and requests for sensitive actions.
- Your score is independent — you may agree or disagree with heuristic/ML.
- Reflect uncertainty when evidence is weak or contradictory.
- For legitimate emails, explain concisely why they are safe — do not pad with unnecessary caveats.
- English, professional tone, 200–400 words.

## Examples

**Example 1 — Clear phishing (score: 0.92)**
Input: From security@paypa1-security.com, Subject "Urgent: Account Suspended", SPF=fail, DKIM=fail, DMARC=fail, 2 URLs (bit.ly shorteners), heuristic 0.72, ML 0.88.
Output: {"score": 0.92, "explanation": "This email is a **high-confidence credential phishing** attempt impersonating PayPal. The domain **paypa1-security.com** uses typosquatting (numeral 1 replacing l) and all authentication checks failed.\\n\\n- **Authentication:** Triple failure (SPF=fail, DKIM=fail, DMARC=fail) confirms the sender is unauthorized.\\n- **Sender Domain:** **paypa1-security.com** employs character substitution to mimic paypal.com.\\n- **Social Engineering:** Subject uses fear and urgency ('Account Suspended') to pressure immediate action.\\n- **Links / Reply-To:** Two **bit.ly** shorteners obscure actual destinations, a common filter-evasion technique.\\n- **Automated Correlation:** Both stages scored high (heuristic: 0.72, ML: 0.88), strongly aligned.\\n\\nThis email should be **blocked** immediately."}

**Example 2 — Legitimate (score: 0.05)**
Input: From notifications@vercel.com, Subject "Deployment successful: guardia-frontend", SPF=pass, DKIM=pass, DMARC=pass, 1 URL (vercel.com), heuristic 0.05, ML 0.03.
Output: {"score": 0.05, "explanation": "This is a **legitimate deployment notification** from **Vercel**, a well-known cloud platform. All authentication passed and the content is a routine CI/CD alert.\\n\\n- **Authentication:** Full pass (SPF, DKIM, DMARC) confirms authorized origin.\\n- **Sender Domain:** **vercel.com** is a recognized hosting provider.\\n- **Automated Correlation:** Both stages scored very low (heuristic: 0.05, ML: 0.03), consistent.\\n\\nThis email should be **allowed** without restrictions."}

**Example 3 — Internal notification (score: 0.08)**
Input: From security@strike.sh, Subject "Password changed successfully", SPF=pass, DKIM=pass, DMARC=pass, 0 URLs, 0 attachments, heuristic 0.04, ML 0.06.
Output: {"score": 0.08, "explanation": "This is a **legitimate internal notification** from Strike Security's own domain **strike.sh**. The email is a standard password-change confirmation with no suspicious elements.\\n\\n- **Authentication:** Full pass (SPF, DKIM, DMARC) confirms the email originates from Strike's authorized mail infrastructure.\\n- **Sender Domain:** **strike.sh** is the protected organization's primary domain. The sender address security@strike.sh matches known internal notification patterns.\\n- **Automated Correlation:** Both stages scored very low (heuristic: 0.04, ML: 0.06), consistent with legitimate internal traffic.\\n\\nThis email should be **allowed**. It is a routine internal IT notification."}

**Example 4 — Ambiguous (score: 0.45)**
Input: From contracts@vendor-payments-portal.net, Subject "Invoice #4892 - Payment Due", SPF=pass, DKIM=none, DMARC=none, 1 attachment (invoice_4892.pdf), heuristic 0.38, ML 0.42.
Output: {"score": 0.45, "explanation": "This email presents a **moderately suspicious invoice** from an unverified vendor domain. Several characteristics warrant manual review.\\n\\n- **Authentication:** SPF passes but DKIM and DMARC are absent, reducing confidence in content integrity.\\n- **Sender Domain:** **vendor-payments-portal.net** is generic and does not identify a specific vendor — a pattern common in BEC campaigns.\\n- **Attachments:** A PDF (invoice_4892.pdf) is present. While standard for invoices, PDFs can contain embedded malicious links.\\n- **Automated Correlation:** Both stages scored moderate (heuristic: 0.38, ML: 0.42), reflecting ambiguity.\\n\\nThis email should be **monitored** and flagged for manual review."}

**Example 5 — Medium-risk vendor invoice (score: 0.55)**
Input: From billing@acme-invoices.net, Subject "Invoice #7231 - Overdue Balance", SPF=pass, DKIM=none, DMARC=none, 1 attachment (INV-7231.pdf), 1 URL (acme-invoices.net/pay), heuristic 0.35, ML 0.50.
Output: {"score": 0.55, "explanation": "This email presents a **suspicious invoice** with multiple converging risk signals that warrant elevated caution.\\n\\n- **Authentication:** SPF passes but DKIM and DMARC are absent, providing limited assurance of message integrity.\\n- **Sender Domain:** **acme-invoices.net** is a generic invoice-themed domain not tied to any known vendor. The .net TLD and generic naming pattern are commonly used in BEC invoice scams.\\n- **Social Engineering:** The subject references an 'Overdue Balance', a pressure tactic to prompt immediate payment without verification.\\n- **Links / Reply-To:** Contains a payment link on the same unverified domain.\\n- **Attachments:** PDF invoice attached. While standard for billing, this could contain embedded phishing links.\\n- **Automated Correlation:** Both stages scored moderate (heuristic: 0.35, ML: 0.50), reflecting mixed signals.\\n\\nThis email should be **quarantined** for manual verification of the vendor relationship before any payment action."}

**Example 6 — Domain lookalike with social engineering (score: 0.75)**
Input: From it-support@str1ke-security.com, Subject "Mandatory: Reset Your VPN Credentials", SPF=pass, DKIM=pass, DMARC=none, 1 URL (str1ke-security.com/reset), heuristic 0.65, ML 0.30.
Output: {"score": 0.75, "explanation": "This email is a **high-risk impersonation attack** targeting Strike Security employees through a convincing lookalike domain.\\n\\n- **Authentication:** SPF and DKIM pass, but this only confirms the email legitimately originates from **str1ke-security.com** — not from the real **strike.sh**. DMARC is absent.\\n- **Sender Domain:** **str1ke-security.com** uses character substitution ('1' for 'i') and appends '-security' to mimic the protected organization. This is a targeted lookalike domain, not the legitimate **strike.sh**.\\n- **Social Engineering:** The subject uses authority ('Mandatory') and urgency ('Reset Your VPN Credentials') to pressure credential submission. The it-support@ sender name adds false legitimacy.\\n- **Links / Reply-To:** The reset link points to the lookalike domain, likely a credential harvesting page.\\n- **Automated Correlation:** Heuristic scored high (0.65) detecting the domain lookalike, while ML scored low (0.30) seeing only benign-looking text — a known ML blind spot for domain-based attacks.\\n\\nThis email should be **blocked**. It is a targeted spear-phishing attempt impersonating the organization's IT department."}

IMPORTANT: Reserve scores above 0.85 for cases where ALL of the following are present: (1) authentication failures, (2) domain impersonation or known malicious sender, (3) social engineering content, and (4) malicious URLs or attachments."""

# OpenAI response_format JSON schema for structured output
_OPENAI_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "risk_assessment",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "explanation": {"type": "string"},
            },
            "required": ["score", "explanation"],
            "additionalProperties": False,
        },
    },
}


def _strip_html_tags(html: str) -> str:
    """Strip HTML tags and convert to plain text."""
    if not html:
        return ""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n\n+", "\n\n", text)
    return text.strip()


def _truncate_body(body: str, max_chars: int = 800) -> str:
    """Truncate body text, breaking at sentence boundary when possible."""
    if len(body) <= max_chars:
        return body
    truncated = body[:max_chars]
    sentence_end = max(
        truncated.rfind(". "),
        truncated.rfind("! "),
        truncated.rfind("? "),
        truncated.rfind(".\n"),
    )
    if sentence_end > max_chars * 0.7:
        truncated = truncated[: sentence_end + 1]
    return truncated.rstrip() + "\n\n[... truncated]"


def _build_user_prompt(
    email_data: dict,
    heuristic_evidences: list[EvidenceItem],
    heuristic_score: float,
    ml_score: float,
    ml_confidence: float,
    ml_available: bool,
) -> str:
    """Build the user prompt with email context and evidence."""
    parts: list[str] = []

    parts.append("## Email Summary")
    parts.append(f"- **From:** {email_data.get('sender_email', 'unknown')}")
    if email_data.get("sender_name"):
        parts.append(f"- **Display Name:** {email_data['sender_name']}")
    parts.append(f"- **Subject:** {email_data.get('subject', '(no subject)')}")
    if email_data.get("reply_to"):
        parts.append(f"- **Reply-To:** {email_data['reply_to']}")

    # URLs — show actual list (up to 5)
    urls = email_data.get("urls", [])
    if urls:
        parts.append(f"- **URLs found:** {len(urls)}")
        for url in urls[:5]:
            parts.append(f"  - {url}")
        if len(urls) > 5:
            parts.append(f"  - ... and {len(urls) - 5} more")

    # Attachments — show filenames
    attachments = email_data.get("attachments", [])
    if attachments:
        parts.append(f"- **Attachments:** {len(attachments)}")
        for att in attachments[:5]:
            fname = att.get("filename", "unknown")
            ctype = att.get("content_type", "")
            size_kb = (att.get("size", 0) or 0) / 1024
            parts.append(f"  - {fname} ({ctype}, {size_kb:.1f} KB)")
        if len(attachments) > 5:
            parts.append(f"  - ... and {len(attachments) - 5} more")

    # Auth results
    auth = email_data.get("auth_results", {})
    if auth:
        parts.append(
            f"- **Auth:** SPF={auth.get('spf', 'none')}, "
            f"DKIM={auth.get('dkim', 'none')}, "
            f"DMARC={auth.get('dmarc', 'none')}"
        )

    # Body content
    body_text = email_data.get("body_text") or ""
    if not body_text:
        body_html = email_data.get("body_html") or ""
        if body_html:
            body_text = _strip_html_tags(body_html)
    if body_text:
        parts.append(f"\n## Email Body Content\n```\n{_truncate_body(body_text)}\n```")

    # Heuristic evidence
    if heuristic_evidences:
        parts.append(f"\n## Heuristic Engine (score: {heuristic_score:.4f})")
        for ev in heuristic_evidences:
            parts.append(f"- [{ev.severity.upper()}] {ev.description}")

    # ML result
    parts.append("\n## ML Classifier")
    if ml_available:
        parts.append(f"- Score: {ml_score:.4f} (confidence: {ml_confidence:.4f})")
    else:
        parts.append("- Model not available (heuristics-only mode)")

    parts.append(
        "\n## Task\n"
        "Based on all evidence above, provide your independent risk assessment "
        "as JSON with a score (0.0-1.0) and explanation."
    )
    return "\n".join(parts)


def _parse_llm_response(text: str) -> tuple[float, float, str]:
    """Parse LLM JSON response. Returns (score, confidence, explanation).

    If parsing fails, returns (0.0, 0.0, original_text).
    """
    text = text.strip()

    # Try to extract JSON from response (handle markdown code blocks)
    if "```" in text:
        for block in text.split("```"):
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            if block.startswith("{"):
                text = block
                break

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError, TypeError):
        # LLMs often put literal newlines inside JSON string values — fix them
        try:
            fixed = _fix_json_newlines(text)
            data = json.loads(fixed)
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("llm_response_parse_failed", response_preview=text[:200])
            return 0.0, 0.0, text

    score = float(data.get("score", 0.0))
    score = min(1.0, max(0.0, score))
    explanation = str(data.get("explanation", ""))
    return score, 1.0, explanation


def _fix_json_newlines(text: str) -> str:
    """Fix literal newlines inside JSON string values.

    LLMs sometimes return JSON like {"explanation": "line1\\nline2"} with
    actual newline characters inside the string, which is invalid JSON.
    """
    # Find content between the outermost { }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return text
    raw = match.group(0)
    # Replace literal newlines inside strings with \\n
    # Strategy: replace all newlines with \\n, which works because
    # JSON keys/structure don't contain newlines
    return raw.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


class LLMExplainer:
    """Generates risk assessment (score + explanation) using OpenAI GPT."""

    async def explain(
        self,
        email_data: dict,
        heuristic_evidences: list[EvidenceItem],
        heuristic_score: float,
        ml_score: float,
        ml_confidence: float,
        ml_available: bool,
    ) -> LLMResult:
        """Generate risk assessment using OpenAI.

        SECURITY NOTE: Logs only primitive values (timestamps, token counts, scores).
        Full API responses are never logged to prevent potential key exposure.
        """
        user_prompt = _build_user_prompt(
            email_data, heuristic_evidences, heuristic_score,
            ml_score, ml_confidence, ml_available,
        )

        if settings.openai_api_key:
            try:
                result = await self._call_openai(user_prompt)
                if result.explanation:
                    return result
            except Exception as exc:
                logger.warning("openai_analyst_failed", error=str(exc))

        # Failed
        logger.error("llm_analyst_failed")
        return LLMResult(
            explanation="LLM analysis unavailable. Review evidence manually.",
            provider="none",
            model_used="none",
        )

    async def _call_openai(self, user_prompt: str) -> LLMResult:
        """Call OpenAI API with structured output."""
        start = time.monotonic()
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        response = await client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=1024,
            temperature=0,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format=_OPENAI_RESPONSE_FORMAT,
            timeout=15.0,
        )

        raw_text = ""
        if response.choices:
            raw_text = response.choices[0].message.content or ""

        tokens = 0
        if response.usage:
            tokens = (response.usage.prompt_tokens or 0) + (
                response.usage.completion_tokens or 0
            )

        elapsed = int((time.monotonic() - start) * 1000)

        # Structured output guarantees valid JSON, but keep fallback
        score, confidence, explanation = _parse_llm_response(raw_text)

        logger.info(
            "openai_analysis_generated",
            model=settings.openai_model,
            score=round(score, 4),
            tokens=tokens,
            duration_ms=elapsed,
        )

        return LLMResult(
            score=score,
            confidence=confidence,
            explanation=explanation,
            provider="openai",
            model_used=settings.openai_model,
            tokens_used=tokens,
            execution_time_ms=elapsed,
        )
