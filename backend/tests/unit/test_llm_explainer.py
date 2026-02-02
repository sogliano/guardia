"""Tests for LLM explainer (OpenAI only)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.pipeline.llm_explainer import (
    LLMExplainer,
    _build_user_prompt,
    _strip_html_tags,
    _truncate_body,
)
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
        heuristic_score=0.2,
        ml_score=0.5,
        ml_confidence=0.8,
        ml_available=True,
    )


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_openai_primary(mock_settings):
    """When OpenAI works, use it."""
    mock_settings.openai_api_key = "sk-openai"
    mock_settings.openai_model = "gpt-test"

    explainer = LLMExplainer()
    explainer._call_openai = AsyncMock(return_value=MagicMock(
        explanation="OpenAI explanation", provider="openai"
    ))

    result = await explainer.explain(**_explain_kwargs())
    assert result.explanation == "OpenAI explanation"
    explainer._call_openai.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_openai_fails_returns_fallback(mock_settings):
    """OpenAI fails → fallback message."""
    mock_settings.openai_api_key = "sk-openai"
    mock_settings.openai_model = "gpt-test"

    explainer = LLMExplainer()
    explainer._call_openai = AsyncMock(side_effect=Exception("fail"))

    result = await explainer.explain(**_explain_kwargs())
    assert "unavailable" in result.explanation.lower()
    assert result.provider == "none"


@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
async def test_no_api_key_returns_fallback(mock_settings):
    """No API key configured → skip, return fallback."""
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
        EvidenceItem(
            type="keyword_phishing", severity="high",
            description="Phishing keywords found",
        ),
    ]
    prompt = _build_user_prompt(
        email, evidences, heuristic_score=0.4, ml_score=0.75, ml_confidence=0.9, ml_available=True,
    )

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
    prompt = _build_user_prompt(email, [], heuristic_score=0.0, ml_score=0.0, ml_confidence=0.0, ml_available=False)
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
    prompt = _build_user_prompt(email, [], heuristic_score=0.1, ml_score=0.5, ml_confidence=0.8, ml_available=True)
    assert "Display Name" not in prompt
    assert "Reply-To" not in prompt
    assert "URLs found" not in prompt
    assert "Attachments" not in prompt


# ---------------------------------------------------------------------------
# Real API call mock (_call_openai)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.pipeline.llm_explainer.settings")
@patch("app.services.pipeline.llm_explainer.openai")
async def test_call_openai_real_mock(mock_openai, mock_settings):
    """Mock the OpenAI client to verify _call_openai flow."""
    mock_settings.openai_api_key = "sk-openai"
    mock_settings.openai_model = "gpt-test"

    mock_choice = MagicMock()
    mock_choice.message.content = '{"score": 0.75, "explanation": "OpenAI analysis of threats..."}'
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 80
    mock_response.usage.completion_tokens = 40

    # Make the create method properly awaitable
    async def mock_create(*args, **kwargs):
        return mock_response

    # Build the nested structure properly
    mock_completions = MagicMock()
    mock_completions.create = mock_create

    mock_chat = MagicMock()
    mock_chat.completions = mock_completions

    mock_client = MagicMock()
    mock_client.chat = mock_chat

    mock_openai.AsyncOpenAI.return_value = mock_client

    explainer = LLMExplainer()
    result = await explainer._call_openai("test prompt")

    assert result.explanation == "OpenAI analysis of threats..."
    assert result.provider == "openai"
    assert result.tokens_used == 120


# ---------------------------------------------------------------------------
# _strip_html_tags
# ---------------------------------------------------------------------------

def test_strip_html_tags_basic():
    """Strips tags, keeps text."""
    assert _strip_html_tags("<p>Hello <b>world</b></p>") == "Hello world"


def test_strip_html_tags_script_style():
    """Removes script and style blocks entirely."""
    html = "<style>body{}</style><p>Hi</p><script>alert(1)</script>"
    assert "alert" not in _strip_html_tags(html)
    assert "Hi" in _strip_html_tags(html)


def test_strip_html_tags_entities():
    """Decodes HTML entities."""
    assert _strip_html_tags("&amp; &lt; &gt; &quot;") == '& < > "'


def test_strip_html_tags_empty():
    assert _strip_html_tags("") == ""
    assert _strip_html_tags(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _truncate_body
# ---------------------------------------------------------------------------

def test_truncate_body_short():
    """Short body returned as-is."""
    assert _truncate_body("Hello world") == "Hello world"


def test_truncate_body_long():
    """Long body is truncated."""
    body = "A" * 1000
    result = _truncate_body(body, max_chars=100)
    assert len(result) <= 120  # 100 + "[... truncated]"
    assert result.endswith("[... truncated]")


def test_truncate_body_sentence_boundary():
    """Truncation respects sentence boundaries."""
    body = "First sentence. " * 60  # ~960 chars
    result = _truncate_body(body, max_chars=800)
    assert result.endswith("sentence.\n\n[... truncated]")


# ---------------------------------------------------------------------------
# _build_user_prompt — enhanced fields
# ---------------------------------------------------------------------------

def test_build_prompt_includes_body_text():
    """Body text appears in prompt."""
    email = {
        "sender_email": "a@b.com",
        "subject": "Test",
        "reply_to": None,
        "urls": [],
        "attachments": [],
        "auth_results": {},
        "body_text": "Please wire $5000 to this account.",
    }
    prompt = _build_user_prompt(
        email, [], heuristic_score=0.1, ml_score=0.5,
        ml_confidence=0.8, ml_available=True,
    )
    assert "wire $5000" in prompt
    assert "Email Body Content" in prompt


def test_build_prompt_html_fallback():
    """When body_text is empty, HTML is stripped and used."""
    email = {
        "sender_email": "a@b.com",
        "subject": "Test",
        "reply_to": None,
        "urls": [],
        "attachments": [],
        "auth_results": {},
        "body_text": "",
        "body_html": "<p>Click <a href='http://evil.com'>here</a></p>",
    }
    prompt = _build_user_prompt(
        email, [], heuristic_score=0.1, ml_score=0.5,
        ml_confidence=0.8, ml_available=True,
    )
    assert "Click" in prompt
    assert "<p>" not in prompt


def test_build_prompt_shows_urls():
    """Actual URLs appear in prompt, not just count."""
    email = {
        "sender_email": "a@b.com",
        "subject": "Test",
        "reply_to": None,
        "urls": ["https://evil.com/login", "https://bit.ly/abc"],
        "attachments": [],
        "auth_results": {},
    }
    prompt = _build_user_prompt(
        email, [], heuristic_score=0.1, ml_score=0.5,
        ml_confidence=0.8, ml_available=True,
    )
    assert "https://evil.com/login" in prompt
    assert "https://bit.ly/abc" in prompt


def test_build_prompt_shows_attachment_filenames():
    """Attachment filenames appear in prompt."""
    email = {
        "sender_email": "a@b.com",
        "subject": "Test",
        "reply_to": None,
        "urls": [],
        "attachments": [
            {"filename": "invoice.pdf.exe", "content_type": "application/octet-stream", "size": 51200},
        ],
        "auth_results": {},
    }
    prompt = _build_user_prompt(
        email, [], heuristic_score=0.1, ml_score=0.5,
        ml_confidence=0.8, ml_available=True,
    )
    assert "invoice.pdf.exe" in prompt
    assert "50.0 KB" in prompt
