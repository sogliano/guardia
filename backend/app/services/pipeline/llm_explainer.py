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

_SYSTEM_PROMPT = """You are Guard-IA, a corporate email fraud detection system.
Analyze the email evidence and provide:
1. A phishing risk score from 0.0 (legitimate) to 1.0 (certain phishing)
2. A concise explanation of your assessment

Respond ONLY with valid JSON in this exact format:
{"score": 0.85, "explanation": "Brief explanation here..."}

Scoring guidelines:
- 0.0-0.2: Clearly legitimate, no suspicious signals
- 0.2-0.4: Minor suspicious signals, likely benign
- 0.4-0.6: Moderately suspicious, warrants review
- 0.6-0.8: Highly suspicious, likely phishing or fraud
- 0.8-1.0: Almost certainly phishing, BEC, or impersonation

Rules:
- Be factual and cite specific evidence from the data provided
- Maximum 200 words for the explanation
- Consider ALL evidence: heuristic signals, ML score, email metadata, auth results
- Your score is an independent assessment — you may agree or disagree with other stages
- If evidence is weak or contradictory, reflect that uncertainty in your score
- Structure explanation as: brief summary, then bullet points for key signals"""


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
        score = float(data.get("score", 0.0))
        score = min(1.0, max(0.0, score))
        explanation = str(data.get("explanation", ""))
        # Confidence is 1.0 if we got a valid score
        return score, 1.0, explanation
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning("llm_response_parse_failed", response_preview=text[:200])
        return 0.0, 0.0, text


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
            max_tokens=512,
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
            max_tokens=512,
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
