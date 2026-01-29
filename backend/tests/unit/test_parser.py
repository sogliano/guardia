"""Tests for the email parser (RFC 5322 → structured dict)."""

import pytest
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from app.gateway.parser import EmailParser


@pytest.fixture
def parser():
    return EmailParser()


def _make_simple_email(
    from_addr="alice@example.com",
    to_addr="bob@example.com",
    subject="Hello",
    body="This is a test email.",
    reply_to=None,
    cc=None,
    auth_results=None,
):
    msg = MIMEText(body)
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Message-ID"] = "<test123@example.com>"
    if reply_to:
        msg["Reply-To"] = reply_to
    if cc:
        msg["Cc"] = cc
    if auth_results:
        msg["Authentication-Results"] = auth_results
    return msg.as_bytes()


def _make_multipart_email(text_body="Plain text", html_body="<p>HTML</p>"):
    msg = MIMEMultipart("alternative")
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = "Multipart test"
    msg["Message-ID"] = "<multi123@example.com>"
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))
    return msg.as_bytes()


def _make_email_with_attachment(filename="invoice.pdf"):
    msg = MIMEMultipart()
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = "With attachment"
    msg["Message-ID"] = "<attach123@example.com>"
    msg.attach(MIMEText("See attached."))
    att = MIMEBase("application", "octet-stream")
    att.set_payload(b"fake content bytes")
    encoders.encode_base64(att)
    att.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(att)
    return msg.as_bytes()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_parse_simple_email(parser):
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "alice@example.com", ["bob@example.com"])

    assert result["sender_email"] == "alice@example.com"
    assert result["subject"] == "Hello"
    assert "test email" in result["body_text"]
    assert result["message_id"] == "test123@example.com"


def test_parse_sender_name(parser):
    raw = _make_simple_email(from_addr="Alice Smith <alice@example.com>")
    result = parser.parse_raw(raw, "alice@example.com", ["bob@example.com"])

    assert result["sender_email"] == "alice@example.com"
    assert result["sender_name"] == "Alice Smith"


def test_parse_multipart(parser):
    raw = _make_multipart_email(text_body="Plain version", html_body="<b>HTML version</b>")
    result = parser.parse_raw(raw, "sender@example.com", ["recipient@example.com"])

    assert result["body_text"] is not None
    assert "Plain version" in result["body_text"]
    assert result["body_html"] is not None
    assert "HTML version" in result["body_html"]


def test_extract_urls_from_text(parser):
    raw = _make_simple_email(body="Visit https://example.com/page and http://test.org/path")
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert any("example.com" in u for u in result["urls"])
    assert any("test.org" in u for u in result["urls"])


def test_extract_urls_from_html(parser):
    html = '<a href="https://evil.com/login">Click here</a>'
    raw = _make_multipart_email(html_body=html)
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert any("evil.com" in u for u in result["urls"])


def test_parse_auth_results_spf_dkim_dmarc(parser):
    auth = "mx.google.com; spf=pass; dkim=fail; dmarc=none"
    raw = _make_simple_email(auth_results=auth)
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["auth_results"]["spf"] == "pass"
    assert result["auth_results"]["dkim"] == "fail"
    assert result["auth_results"]["dmarc"] == "none"


def test_parse_auth_results_missing(parser):
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["auth_results"] == {"spf": "none", "dkim": "none", "dmarc": "none"}


def test_parse_reply_to(parser):
    raw = _make_simple_email(reply_to="other@domain.com")
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["reply_to"] == "other@domain.com"


def test_parse_cc(parser):
    raw = _make_simple_email(cc="cc1@a.com, cc2@b.com")
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert "cc1@a.com" in result["recipients_cc"]
    assert "cc2@b.com" in result["recipients_cc"]


def test_parse_attachment_metadata(parser):
    raw = _make_email_with_attachment("report.xlsx")
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert len(result["attachments"]) == 1
    assert result["attachments"][0]["filename"] == "report.xlsx"
    assert result["attachments"][0]["size"] > 0


def test_no_message_id_fallback(parser):
    msg = MIMEText("body")
    msg["From"] = "a@a.com"
    msg["To"] = "b@b.com"
    msg["Subject"] = "No ID"
    raw = msg.as_bytes()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["message_id"]  # should have some fallback value


def test_parse_date_header(parser):
    """Date header is parsed to ISO format."""
    msg = MIMEText("body")
    msg["From"] = "a@a.com"
    msg["To"] = "b@b.com"
    msg["Subject"] = "Dated"
    msg["Message-ID"] = "<dated@test.com>"
    msg["Date"] = "Wed, 29 Jan 2025 10:30:00 +0000"
    raw = msg.as_bytes()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["received_at"] is not None
    assert "2025-01-29" in result["received_at"]


def test_parse_date_header_missing(parser):
    """No Date header → received_at is None."""
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])
    # MIMEText doesn't add Date by default
    assert result["received_at"] is None


def test_parse_date_header_invalid(parser):
    """Invalid Date header → received_at is None."""
    msg = MIMEText("body")
    msg["From"] = "a@a.com"
    msg["To"] = "b@b.com"
    msg["Subject"] = "Bad date"
    msg["Message-ID"] = "<baddate@test.com>"
    msg["Date"] = "not-a-date"
    raw = msg.as_bytes()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["received_at"] is None


def test_parse_html_only_email(parser):
    """HTML-only (non-multipart) email."""
    msg = MIMEText("<p>HTML only</p>", "html")
    msg["From"] = "a@a.com"
    msg["To"] = "b@b.com"
    msg["Subject"] = "HTML"
    msg["Message-ID"] = "<html@test.com>"
    raw = msg.as_bytes()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["body_text"] is None
    assert result["body_html"] is not None
    assert "HTML only" in result["body_html"]


def test_extract_headers(parser):
    """All headers are extracted."""
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert "From" in result["headers"]
    assert "Subject" in result["headers"]


def test_empty_envelope_to(parser):
    """Empty envelope_to list → recipient_email is empty string."""
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "a@a.com", [])

    assert result["recipient_email"] == ""


def test_no_reply_to(parser):
    """No Reply-To → None."""
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["reply_to"] is None


def test_empty_cc(parser):
    """No CC header → empty list."""
    raw = _make_simple_email()
    result = parser.parse_raw(raw, "a@a.com", ["b@b.com"])

    assert result["recipients_cc"] == []
