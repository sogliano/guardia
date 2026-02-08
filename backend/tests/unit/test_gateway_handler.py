"""Tests for the SMTP gateway handler."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.constants import SMTP_RESPONSE_OK
from app.gateway.handler import GuardIAHandler


def _make_handler():
    """Create a handler with mocked dependencies."""
    handler = GuardIAHandler.__new__(GuardIAHandler)
    handler.parser = MagicMock()
    handler.relay = AsyncMock()
    handler.storage = AsyncMock()
    return handler


def _make_envelope(mail_from="sender@example.com", rcpt_tos=None):
    envelope = MagicMock()
    envelope.mail_from = mail_from
    envelope.rcpt_tos = rcpt_tos or ["recipient@strike.sh"]
    envelope.original_content = b"Subject: Test\r\n\r\nBody"
    return envelope


def _make_session(peer=("127.0.0.1", 12345)):
    session = MagicMock()
    session.peer = peer
    return session


@pytest.mark.asyncio
async def test_handle_rcpt_accepts_valid_domain():
    """RCPT TO with accepted domain returns 250 OK."""
    handler = _make_handler()
    server = MagicMock()
    session = _make_session()
    envelope = _make_envelope(rcpt_tos=[])

    with patch("app.gateway.handler.settings") as mock_settings:
        mock_settings.accepted_domains_list = ["strike.sh"]
        result = await handler.handle_RCPT(server, session, envelope, "user@strike.sh", {})

    assert result == "250 OK"
    assert "user@strike.sh" in envelope.rcpt_tos


@pytest.mark.asyncio
async def test_handle_rcpt_rejects_invalid_domain():
    """RCPT TO with non-accepted domain is rejected."""
    handler = _make_handler()
    server = MagicMock()
    session = _make_session()
    envelope = _make_envelope(rcpt_tos=[])

    with patch("app.gateway.handler.settings") as mock_settings:
        mock_settings.accepted_domains_list = ["strike.sh"]
        result = await handler.handle_RCPT(server, session, envelope, "user@evil.com", {})

    assert "550" in result or "553" in result or "invalid" in result.lower() or result != "250 OK"


@pytest.mark.asyncio
async def test_handle_data_runs_pipeline():
    """handle_DATA parses email, persists it, and runs pipeline."""
    handler = _make_handler()
    server = MagicMock()
    session = _make_session()
    envelope = _make_envelope()

    handler.parser.parse_raw.return_value = {
        "message_id": "test@example.com",
        "sender_email": "sender@example.com",
        "sender_name": "Sender",
        "reply_to": None,
        "recipient_email": "recipient@strike.sh",
        "recipients_cc": [],
        "subject": "Test",
        "body_text": "Body",
        "body_html": None,
        "headers": {},
        "urls": [],
        "attachments": [],
        "auth_results": {},
        "received_at": None,
    }

    mock_email = MagicMock()
    mock_email.id = "test-uuid"

    mock_pipeline_result = MagicMock()
    mock_pipeline_result.verdict = "allowed"
    mock_pipeline_result.final_score = 0.1
    mock_pipeline_result.case_id = "case-uuid"

    handler.relay.forward = AsyncMock(return_value=True)

    with patch("app.gateway.handler.settings") as mock_settings, \
         patch("app.gateway.handler.get_standalone_session") as mock_session_ctx, \
         patch.object(handler, "_persist_email", new_callable=AsyncMock, return_value=mock_email), \
         patch.object(handler, "_run_pipeline", new_callable=AsyncMock, return_value=mock_pipeline_result):
        mock_settings.active_users_set = set()
        mock_db = AsyncMock()
        mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await handler.handle_DATA(server, session, envelope)

    assert result == SMTP_RESPONSE_OK
    handler.relay.forward.assert_called_once()


@pytest.mark.asyncio
async def test_handle_data_fail_open_on_crash():
    """When pipeline crashes, email should be forwarded (fail-open)."""
    handler = _make_handler()
    server = MagicMock()
    session = _make_session()
    envelope = _make_envelope()

    handler.parser.parse_raw.side_effect = Exception("Parse error")
    handler.relay.forward = AsyncMock(return_value=True)

    with patch("app.gateway.handler.settings") as mock_settings:
        mock_settings.active_users_set = set()

        result = await handler.handle_DATA(server, session, envelope)

    assert result == SMTP_RESPONSE_OK
    handler.relay.forward.assert_called_once()


@pytest.mark.asyncio
async def test_handle_data_quarantines_high_score():
    """High-score emails should be quarantined."""
    handler = _make_handler()
    server = MagicMock()
    session = _make_session()
    envelope = _make_envelope()

    handler.parser.parse_raw.return_value = {
        "message_id": "test@example.com",
        "sender_email": "sender@example.com",
        "sender_name": "Sender",
        "reply_to": None,
        "recipient_email": "recipient@strike.sh",
        "recipients_cc": [],
        "subject": "Test",
        "body_text": "Body",
        "body_html": None,
        "headers": {},
        "urls": [],
        "attachments": [],
        "auth_results": {},
        "received_at": None,
    }

    mock_email = MagicMock()
    mock_email.id = "test-uuid"

    mock_pipeline_result = MagicMock()
    mock_pipeline_result.verdict = "quarantined"
    mock_pipeline_result.final_score = 0.75
    mock_pipeline_result.case_id = "case-uuid"

    with patch("app.gateway.handler.settings") as mock_settings, \
         patch("app.gateway.handler.get_standalone_session") as mock_session_ctx, \
         patch.object(handler, "_persist_email", new_callable=AsyncMock, return_value=mock_email), \
         patch.object(handler, "_run_pipeline", new_callable=AsyncMock, return_value=mock_pipeline_result):
        mock_settings.active_users_set = set()
        mock_db = AsyncMock()
        mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await handler.handle_DATA(server, session, envelope)

    assert "250" in result or "quarantine" in result.lower()
    handler.storage.store.assert_called_once()
