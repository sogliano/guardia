"""Layer 3: LLM Analyst (~2-3s).

Primary: Claude (Anthropic API)
Fallback: GPT-4.1 (OpenAI API)

The LLM provides an independent risk assessment: a phishing score (0.0-1.0)
and a human-readable explanation. Its score is weighted into the final
pipeline score alongside heuristic and ML scores.
"""

import json
import time

import anthropic
import openai
import structlog

from app.config import settings
from app.services.pipeline.models import EvidenceItem, LLMResult

logger = structlog.get_logger()

_SYSTEM_PROMPT = """You are Guard-IA's LLM Analyst, a corporate email fraud detection system specialized in phishing, BEC (Business Email Compromise), credential theft, and impersonation attacks.

Your task: analyze the provided email evidence and produce a structured risk assessment.

Respond ONLY with valid JSON in this exact format:
{"score": 0.85, "explanation": "Your detailed markdown explanation here"}

## Score Guidelines
- **0.00 – 0.20**: Clearly legitimate — no suspicious signals detected
- **0.20 – 0.40**: Minor anomalies — likely benign, low concern
- **0.40 – 0.60**: Moderately suspicious — warrants manual review
- **0.60 – 0.80**: Highly suspicious — strong phishing/fraud indicators
- **0.80 – 1.00**: Near-certain phishing, BEC, or impersonation

## Explanation Format
Write your explanation in plain text with markdown bold (**text**) and bullet points (- item). Do NOT use markdown headers (#, ##, ###). Structure as follows:

**Opening paragraph** (2–3 sentences): State the overall threat assessment, the primary attack vector identified (e.g., credential phishing, BEC impersonation, malware delivery, invoice fraud), and a brief summary of the most critical signals.

**Key findings** as bullet points. Each bullet must start with a bold label:
- **Authentication Analysis:** Assess SPF, DKIM, DMARC results — explain what failures or passes mean for legitimacy
- **Sender Domain:** Check for typosquatting, lookalike patterns, suspicious TLDs, or legitimate known domains
- **Social Engineering Tactics:** Evaluate urgency language, pressure tactics, fear-based manipulation, authority impersonation
- **Reply-To / Links:** Flag Reply-To mismatches, suspicious URLs, URL shorteners, IP-based links, known malicious patterns
- **Attachments:** Note double extensions, executable files, or suspicious file types
- **Brand/Identity Impersonation:** Assess if email impersonates a known brand, internal executive, or trusted vendor
- **ML/Heuristic Correlation:** Note whether your assessment aligns or diverges from automated stages

Only include bullets relevant to the email — skip findings with nothing notable.

**Closing paragraph** (1–2 sentences): Summarize the risk level and recommended action (allow, monitor, quarantine, or block).

## Rules
- Be factual and cite specific evidence from the data provided
- Use **bold** for key technical terms and domain names
- Do NOT use markdown headers (#), only bold text and bullet points
- Your score is independent — you may agree or disagree with heuristic/ML stages
- If evidence is contradictory or weak, reflect uncertainty in your score
- For legitimate emails, explain clearly why they are safe
- Write in English, professional tone, 250-450 words"""


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

    url_count = len(email_data.get("urls", []))
    if url_count:
        parts.append(f"- **URLs found:** {url_count}")

    attachment_count = len(email_data.get("attachments", []))
    if attachment_count:
        parts.append(f"- **Attachments:** {attachment_count}")

    # Auth results
    auth = email_data.get("auth_results", {})
    if auth:
        parts.append(
            f"- **Auth:** SPF={auth.get('spf', 'none')}, "
            f"DKIM={auth.get('dkim', 'none')}, "
            f"DMARC={auth.get('dmarc', 'none')}"
        )

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

    LLMs sometimes return JSON like {"explanation": "line1\nline2"} with
    actual newline characters inside the string, which is invalid JSON.
    """
    import re
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
    """Generates risk assessment (score + explanation) using LLM."""

    async def explain(
        self,
        email_data: dict,
        heuristic_evidences: list[EvidenceItem],
        heuristic_score: float,
        ml_score: float,
        ml_confidence: float,
        ml_available: bool,
    ) -> LLMResult:
        """Generate risk assessment. Try Claude first, fall back to OpenAI."""
        user_prompt = _build_user_prompt(
            email_data, heuristic_evidences, heuristic_score,
            ml_score, ml_confidence, ml_available,
        )

        # Try Claude
        if settings.anthropic_api_key:
            try:
                result = await self._call_claude(user_prompt)
                if result.explanation:
                    return result
            except Exception as exc:
                logger.warning("claude_analyst_failed", error=str(exc))

        # Fallback to OpenAI
        if settings.openai_api_key:
            try:
                result = await self._call_openai(user_prompt)
                if result.explanation:
                    return result
            except Exception as exc:
                logger.warning("openai_analyst_failed", error=str(exc))

        # Both failed
        logger.error("llm_analyst_all_failed")
        return LLMResult(
            explanation="LLM analysis unavailable. Review evidence manually.",
            provider="none",
            model_used="none",
        )

    async def _call_claude(self, user_prompt: str) -> LLMResult:
        """Call Anthropic API (Claude)."""
        start = time.monotonic()
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=10.0,
        )

        raw_text = response.content[0].text if response.content else ""
        tokens = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
        elapsed = int((time.monotonic() - start) * 1000)

        score, confidence, explanation = _parse_llm_response(raw_text)

        logger.info(
            "claude_analysis_generated",
            model=settings.anthropic_model,
            score=round(score, 4),
            tokens=tokens,
            duration_ms=elapsed,
        )

        return LLMResult(
            score=score,
            confidence=confidence,
            explanation=explanation,
            provider="claude",
            model_used=settings.anthropic_model,
            tokens_used=tokens,
            execution_time_ms=elapsed,
        )

    async def _call_openai(self, user_prompt: str) -> LLMResult:
        """Call OpenAI API (GPT-4.1 fallback)."""
        start = time.monotonic()
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        response = await client.chat.completions.create(
            model=settings.openai_model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            timeout=10.0,
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
