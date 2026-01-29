"""Layer 3: LLM Explainer (~2-3s).

Primary: Claude (Anthropic API)
Fallback: GPT-4.1 (OpenAI API)

The LLM does NOT make decisions. It generates human-readable
explanations based on the evidence collected by the heuristic
and ML stages. This is a defensive design choice to prevent
the LLM from being manipulated via prompt injection.
"""

import time

import structlog

from app.config import settings
from app.services.pipeline.models import EvidenceItem, LLMResult

logger = structlog.get_logger()

_SYSTEM_PROMPT = """You are Guard-IA, a corporate email fraud detection system.
Your role is to explain WHY an email was flagged, based on the evidence provided.

Rules:
- You do NOT decide if the email is phishing. The pipeline already made that decision.
- You explain the evidence in clear, concise language for a security analyst.
- Write in English. Be factual and specific.
- If evidence is weak, say so honestly.
- Structure your response as: a brief summary (1-2 sentences), then bullet points for each signal.
- Maximum 200 words.
- Do NOT suggest actions. Only explain what was detected."""


def _build_user_prompt(
    email_data: dict,
    heuristic_evidences: list[EvidenceItem],
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
        parts.append("\n## Heuristic Evidence")
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
        "Explain the detection signals above to a security analyst. "
        "Focus on what makes this email suspicious or legitimate."
    )
    return "\n".join(parts)


class LLMExplainer:
    """Generates explanations using LLM based on pipeline evidence."""

    async def explain(
        self,
        email_data: dict,
        heuristic_evidences: list[EvidenceItem],
        ml_score: float,
        ml_confidence: float,
        ml_available: bool,
    ) -> LLMResult:
        """Generate explanation. Try Claude first, fall back to OpenAI."""
        user_prompt = _build_user_prompt(
            email_data, heuristic_evidences, ml_score, ml_confidence, ml_available
        )

        # Try Claude
        if settings.anthropic_api_key:
            try:
                result = await self._explain_with_claude(user_prompt)
                if result.explanation:
                    return result
            except Exception as exc:
                logger.warning("claude_explainer_failed", error=str(exc))

        # Fallback to OpenAI
        if settings.openai_api_key:
            try:
                result = await self._explain_with_openai(user_prompt)
                if result.explanation:
                    return result
            except Exception as exc:
                logger.warning("openai_explainer_failed", error=str(exc))

        # Both failed
        logger.error("llm_explainer_all_failed")
        return LLMResult(
            explanation="LLM explanation unavailable. Review evidence manually.",
            provider="none",
            model_used="none",
        )

    async def _explain_with_claude(self, user_prompt: str) -> LLMResult:
        """Call Anthropic API (Claude)."""
        import anthropic

        start = time.monotonic()
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=10.0,
        )

        explanation = response.content[0].text if response.content else ""
        tokens = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
        elapsed = int((time.monotonic() - start) * 1000)

        logger.info(
            "claude_explanation_generated",
            model=settings.anthropic_model,
            tokens=tokens,
            duration_ms=elapsed,
        )

        return LLMResult(
            explanation=explanation,
            provider="claude",
            model_used=settings.anthropic_model,
            tokens_used=tokens,
            execution_time_ms=elapsed,
        )

    async def _explain_with_openai(self, user_prompt: str) -> LLMResult:
        """Call OpenAI API (GPT-4.1 fallback)."""
        import openai

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

        explanation = ""
        if response.choices:
            explanation = response.choices[0].message.content or ""

        tokens = 0
        if response.usage:
            tokens = (response.usage.prompt_tokens or 0) + (
                response.usage.completion_tokens or 0
            )

        elapsed = int((time.monotonic() - start) * 1000)

        logger.info(
            "openai_explanation_generated",
            model=settings.openai_model,
            tokens=tokens,
            duration_ms=elapsed,
        )

        return LLMResult(
            explanation=explanation,
            provider="openai",
            model_used=settings.openai_model,
            tokens_used=tokens,
            execution_time_ms=elapsed,
        )
