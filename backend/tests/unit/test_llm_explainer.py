"""Tests for LLM explainer fallback chain."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.pipeline.llm_explainer import LLMExplainer, _build_user_prompt
from app.services.pipeline.models import EvidenceItem


def _explain_kwargs():
    return dict(
        email_data={
            "sender_email": "test@example.com",
            "subject": "Test",
            "reply_to": None,
            "urls": [],
            "attachments": [],
            "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        },
        heuristic_evidences=[],
        ml_score=0.5,
        ml_confidence=0.8,
        ml_available=True,
    )


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_claude_primary(mock_settings):
    """When Claude works, use it."""
    mock_settings.anthropic_api_key = "sk-test"
    mock_settings.openai_api_key = ""
    mock_settings.anthropic_model = "claude-test"

    explainer = LLMExplainer()
    explainer._explain_with_claude = AsyncMock(return_value=MagicMock(
        explanation="Claude explanation", provider="claude"
    ))

    result = await explainer.explain(**_explain_kwargs())
    assert result.explanation == "Claude explanation"
    explainer._explain_with_claude.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_fallback_to_openai(mock_settings):
    """Claude fails → fallback to OpenAI."""
    mock_settings.anthropic_api_key = "sk-test"
    mock_settings.openai_api_key = "sk-openai"
    mock_settings.anthropic_model = "claude-test"
    mock_settings.openai_model = "gpt-test"

    explainer = LLMExplainer()
    explainer._explain_with_claude = AsyncMock(side_effect=Exception("Claude down"))
    explainer._explain_with_openai = AsyncMock(return_value=MagicMock(
        explanation="OpenAI explanation", provider="openai"
    ))

    result = await explainer.explain(**_explain_kwargs())
    assert result.explanation == "OpenAI explanation"


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_both_fail_returns_fallback(mock_settings):
    """Both Claude and OpenAI fail → fallback message."""
    mock_settings.anthropic_api_key = "sk-test"
    mock_settings.openai_api_key = "sk-openai"
    mock_settings.anthropic_model = "claude-test"
    mock_settings.openai_model = "gpt-test"

    explainer = LLMExplainer()
    explainer._explain_with_claude = AsyncMock(side_effect=Exception("fail"))
    explainer._explain_with_openai = AsyncMock(side_effect=Exception("fail"))

    result = await explainer.explain(**_explain_kwargs())
    assert "unavailable" in result.explanation.lower()
    assert result.provider == "none"


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_no_api_keys_returns_fallback(mock_settings):
    """No API keys configured → skip both, return fallback."""
    mock_settings.anthropic_api_key = ""
    mock_settings.openai_api_key = ""

    explainer = LLMExplainer()
    result = await explainer.explain(**_explain_kwargs())
    assert "unavailable" in result.explanation.lower()


# ---------------------------------------------------------------------------
# _build_user_prompt
# ---------------------------------------------------------------------------

def test_build_user_prompt_basic():
    """Prompt includes sender, subject, and ML info."""
    email = {
        "sender_email": "attacker@evil.com",
        "sender_name": "Evil Person",
        "subject": "Reset your password",
        "reply_to": "other@evil.com",
        "urls": ["https://evil.com/login"],
        "attachments": [{"filename": "doc.pdf"}],
        "auth_results": {"spf": "fail", "dkim": "pass", "dmarc": "none"},
    }
    evidences = [
        EvidenceItem(type="keyword_phishing", severity="high", description="Phishing keywords found"),
    ]
    prompt = _build_user_prompt(email, evidences, ml_score=0.75, ml_confidence=0.9, ml_available=True)

    assert "attacker@evil.com" in prompt
    assert "Evil Person" in prompt
    assert "Reset your password" in prompt
    assert "other@evil.com" in prompt
    assert "URLs found" in prompt
    assert "Attachments" in prompt
    assert "SPF=fail" in prompt
    assert "Phishing keywords found" in prompt
    assert "0.75" in prompt


def test_build_user_prompt_ml_unavailable():
    """When ML not available, prompt says so."""
    email = {
        "sender_email": "x@y.com",
        "subject": "Hi",
        "reply_to": None,
        "urls": [],
        "attachments": [],
        "auth_results": {},
    }
    prompt = _build_user_prompt(email, [], ml_score=0.0, ml_confidence=0.0, ml_available=False)
    assert "not available" in prompt


def test_build_user_prompt_no_optional_fields():
    """No sender_name, reply_to, urls, attachments → those sections omitted."""
    email = {
        "sender_email": "a@b.com",
        "subject": "Test",
        "reply_to": None,
        "urls": [],
        "attachments": [],
        "auth_results": {},
    }
    prompt = _build_user_prompt(email, [], ml_score=0.5, ml_confidence=0.8, ml_available=True)
    assert "Display Name" not in prompt
    assert "Reply-To" not in prompt
    assert "URLs found" not in prompt
    assert "Attachments" not in prompt


# ---------------------------------------------------------------------------
# Real API call mocks (_explain_with_claude, _explain_with_openai)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_explain_with_claude_real_mock(mock_settings):
    """Mock the Anthropic client to verify _explain_with_claude flow."""
    import sys

    mock_settings.anthropic_api_key = "sk-test"
    mock_settings.anthropic_model = "claude-test"

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This email is suspicious because...")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50

    mock_anthropic = MagicMock()
    mock_client = AsyncMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
        explainer = LLMExplainer()
        result = await explainer._explain_with_claude("test prompt")

    assert result.explanation == "This email is suspicious because..."
    assert result.provider == "claude"
    assert result.tokens_used == 150


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_explain_with_openai_real_mock(mock_settings):
    """Mock the OpenAI client to verify _explain_with_openai flow."""
    import sys

    mock_settings.openai_api_key = "sk-openai"
    mock_settings.openai_model = "gpt-test"

    mock_choice = MagicMock()
    mock_choice.message.content = "OpenAI analysis of threats..."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 80
    mock_response.usage.completion_tokens = 40

    mock_openai = MagicMock()
    mock_client = AsyncMock()
    mock_openai.AsyncOpenAI.return_value = mock_client
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.dict(sys.modules, {"openai": mock_openai}):
        explainer = LLMExplainer()
        result = await explainer._explain_with_openai("test prompt")

    assert result.explanation == "OpenAI analysis of threats..."
    assert result.provider == "openai"
    assert result.tokens_used == 120
