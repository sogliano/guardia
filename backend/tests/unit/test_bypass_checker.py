"""Tests for pipeline bypass checker."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.pipeline.bypass_checker import BypassChecker


def _email(sender="user@strike.sh", spf="pass", dkim="pass", dmarc="pass"):
    return {
        "sender_email": sender,
        "auth_results": {"spf": spf, "dkim": dkim, "dmarc": dmarc},
    }


@pytest.fixture
def checker():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=AsyncMock(all=lambda: []))
    return BypassChecker(db)


@pytest.mark.asyncio
@patch("app.services.pipeline.bypass_checker.settings")
async def test_domain_match(mock_settings, checker):
    mock_settings.allowlist_domains_set = {"strike.sh"}
    mock_settings.allowlist_require_spf = True
    mock_settings.allowlist_require_dkim = False
    mock_settings.allowlist_require_dmarc = False
    bypassed, reason = await checker.should_bypass(_email())
    assert bypassed is True
    assert "strike.sh" in reason


@pytest.mark.asyncio
@patch("app.services.pipeline.bypass_checker.settings")
async def test_subdomain_match(mock_settings, checker):
    mock_settings.allowlist_domains_set = {"strike.sh"}
    mock_settings.allowlist_require_spf = True
    mock_settings.allowlist_require_dkim = False
    mock_settings.allowlist_require_dmarc = False
    bypassed, _ = await checker.should_bypass(_email(sender="noreply@mail.strike.sh"))
    assert bypassed is True


@pytest.mark.asyncio
@patch("app.services.pipeline.bypass_checker.settings")
async def test_domain_not_in_list(mock_settings, checker):
    mock_settings.allowlist_domains_set = {"strike.sh"}
    bypassed, reason = await checker.should_bypass(_email(sender="attacker@evil.com"))
    assert bypassed is False
    assert "not in allowlist" in reason


@pytest.mark.asyncio
@patch("app.services.pipeline.bypass_checker.settings")
async def test_spf_fail_denied(mock_settings, checker):
    mock_settings.allowlist_domains_set = {"strike.sh"}
    mock_settings.allowlist_require_spf = True
    mock_settings.allowlist_require_dkim = False
    mock_settings.allowlist_require_dmarc = False
    bypassed, reason = await checker.should_bypass(_email(spf="fail"))
    assert bypassed is False
    assert "SPF" in reason


@pytest.mark.asyncio
@patch("app.services.pipeline.bypass_checker.settings")
async def test_dkim_required_but_fails(mock_settings, checker):
    mock_settings.allowlist_domains_set = {"strike.sh"}
    mock_settings.allowlist_require_spf = True
    mock_settings.allowlist_require_dkim = True
    mock_settings.allowlist_require_dmarc = False
    bypassed, reason = await checker.should_bypass(_email(dkim="fail", dmarc="none"))
    assert bypassed is False
    assert "auth failed" in reason.lower()


@pytest.mark.asyncio
@patch("app.services.pipeline.bypass_checker.settings")
async def test_dkim_or_dmarc_one_passes(mock_settings, checker):
    mock_settings.allowlist_domains_set = {"strike.sh"}
    mock_settings.allowlist_require_spf = True
    mock_settings.allowlist_require_dkim = True
    mock_settings.allowlist_require_dmarc = True
    bypassed, _ = await checker.should_bypass(_email(dkim="fail", dmarc="pass"))
    assert bypassed is True


@pytest.mark.asyncio
async def test_empty_sender():
    db = AsyncMock()
    checker = BypassChecker(db)
    bypassed, reason = await checker.should_bypass({"sender_email": "", "auth_results": {}})
    assert bypassed is False
    assert "Invalid" in reason


@pytest.mark.asyncio
async def test_no_at_sign():
    db = AsyncMock()
    checker = BypassChecker(db)
    bypassed, reason = await checker.should_bypass(
        {"sender_email": "no-at-sign", "auth_results": {}}
    )
    assert bypassed is False
    assert "Invalid" in reason
