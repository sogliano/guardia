"""Tests for the heuristic analysis engine (Layer 1).

Tests all four sub-engines: domain, URL, keyword, auth.
Uses mock policies to avoid DB dependency.
"""

import pytest
from unittest.mock import AsyncMock

from app.services.pipeline.heuristics import HeuristicEngine, _levenshtein
from tests.conftest import make_mock_policies


# ---------------------------------------------------------------------------
# Levenshtein helper
# ---------------------------------------------------------------------------

def test_levenshtein_identical():
    assert _levenshtein("google.com", "google.com") == 0


def test_levenshtein_one_char_diff():
    assert _levenshtein("gooogle.com", "google.com") == 1


def test_levenshtein_two_chars():
    assert _levenshtein("gooogl.com", "google.com") == 2


def test_levenshtein_empty():
    assert _levenshtein("", "abc") == 3
    assert _levenshtein("abc", "") == 3


# ---------------------------------------------------------------------------
# Domain sub-engine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_domain_whitelisted_bypasses():
    """Whitelisted domain should always return score 0."""
    engine = HeuristicEngine(AsyncMock())
    engine._load_policies = make_mock_policies(whitelist={"strike.sh"}).__get__(engine)

    email = {"sender_email": "alice@strike.sh"}
    score, ev = await engine._analyze_domain(email)
    assert score == 0.0
    assert ev == []


@pytest.mark.asyncio
async def test_domain_blacklisted():
    """Blacklisted domain should return score 1.0."""
    engine = HeuristicEngine(AsyncMock())
    engine._blacklisted_domains = {"evil.com"}
    engine._whitelisted_domains = set()

    email = {"sender_email": "hacker@evil.com"}
    score, ev = await engine._analyze_domain(email)
    assert score == 1.0
    assert len(ev) == 1
    assert ev[0].type == "domain_blacklisted"


@pytest.mark.asyncio
async def test_domain_typosquatting():
    """Domain 1-2 edit distance from known domain → score 0.8."""
    engine = HeuristicEngine(AsyncMock())
    engine._load_policies = make_mock_policies().__get__(engine)

    email = {"sender_email": "phish@gooogle.com"}
    score, ev = await engine._analyze_domain(email)
    assert score >= 0.8
    assert any(e.type == "domain_typosquatting" for e in ev)


@pytest.mark.asyncio
async def test_domain_suspicious_tld():
    """Suspicious TLD (.xyz) → score 0.5."""
    engine = HeuristicEngine(AsyncMock())
    engine._load_policies = make_mock_policies().__get__(engine)

    email = {"sender_email": "user@random-site.xyz"}
    score, ev = await engine._analyze_domain(email)
    assert score >= 0.5
    assert any(e.type == "domain_suspicious_tld" for e in ev)


@pytest.mark.asyncio
async def test_domain_legitimate():
    """Known legitimate domain (exact match) → score 0.0."""
    engine = HeuristicEngine(AsyncMock())
    engine._load_policies = make_mock_policies().__get__(engine)

    email = {"sender_email": "user@google.com"}
    score, ev = await engine._analyze_domain(email)
    assert score == 0.0


@pytest.mark.asyncio
async def test_domain_no_sender():
    """No sender email → score 0.0, no crash."""
    engine = HeuristicEngine(AsyncMock())
    engine._load_policies = make_mock_policies().__get__(engine)

    score, ev = await engine._analyze_domain({"sender_email": ""})
    assert score == 0.0


# ---------------------------------------------------------------------------
# URL sub-engine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_url_shortener():
    """URL shortener → score >= 0.4."""
    engine = HeuristicEngine(AsyncMock())
    email = {"urls": ["https://bit.ly/abc123"]}
    score, ev = await engine._analyze_urls(email)
    assert score >= 0.4
    assert any(e.type == "url_shortener" for e in ev)


@pytest.mark.asyncio
async def test_url_ip_based():
    """IP-based URL → score >= 0.7."""
    engine = HeuristicEngine(AsyncMock())
    email = {"urls": ["http://192.168.1.1/login"]}
    score, ev = await engine._analyze_urls(email)
    assert score >= 0.7
    assert any(e.type == "url_ip_based" for e in ev)


@pytest.mark.asyncio
async def test_url_no_urls():
    """No URLs → score 0.0."""
    engine = HeuristicEngine(AsyncMock())
    score, ev = await engine._analyze_urls({"urls": []})
    assert score == 0.0
    assert ev == []


@pytest.mark.asyncio
async def test_url_multiple_shorteners_increases_score():
    """Multiple shorteners → score increases."""
    engine = HeuristicEngine(AsyncMock())
    email = {"urls": ["https://bit.ly/a", "https://tinyurl.com/b", "https://t.co/c"]}
    score, ev = await engine._analyze_urls(email)
    assert score >= 0.7


# ---------------------------------------------------------------------------
# Keyword sub-engine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_keyword_phishing_terms():
    """Phishing keywords → score > 0.3."""
    engine = HeuristicEngine(AsyncMock())
    email = {
        "subject": "verify your account",
        "body_text": "Click here to verify your identity",
    }
    score, ev = await engine._analyze_keywords(email)
    assert score > 0.3
    assert any(e.type == "keyword_phishing" for e in ev)


@pytest.mark.asyncio
async def test_keyword_urgency():
    """Urgency keywords → score > 0.2."""
    engine = HeuristicEngine(AsyncMock())
    email = {
        "subject": "urgent action required",
        "body_text": "Act now or your account will be suspended immediately.",
    }
    score, ev = await engine._analyze_keywords(email)
    assert score > 0.2
    assert any(e.type == "keyword_urgency" for e in ev)


@pytest.mark.asyncio
async def test_keyword_caps_abuse():
    """More than 30% uppercase words (>10 words) → CAPS abuse evidence."""
    engine = HeuristicEngine(AsyncMock())
    email = {
        "subject": "",
        "body_text": "THIS IS VERY IMPORTANT PLEASE READ NOW okay thanks a lot really appreciate it",
    }
    score, ev = await engine._analyze_keywords(email)
    assert any(e.type == "keyword_caps_abuse" for e in ev)


@pytest.mark.asyncio
async def test_keyword_clean():
    """Clean email → score 0.0."""
    engine = HeuristicEngine(AsyncMock())
    email = {
        "subject": "Weekly sync notes",
        "body_text": "Here are the notes from our meeting today.",
    }
    score, ev = await engine._analyze_keywords(email)
    assert score == 0.0
    assert ev == []


@pytest.mark.asyncio
async def test_keyword_empty_body():
    """Empty subject and body → score 0.0."""
    engine = HeuristicEngine(AsyncMock())
    score, ev = await engine._analyze_keywords({"subject": "", "body_text": ""})
    assert score == 0.0


# ---------------------------------------------------------------------------
# Auth sub-engine
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_spf_fail():
    """SPF fail → +0.35."""
    engine = HeuristicEngine(AsyncMock())
    email = {"auth_results": {"spf": "fail", "dkim": "pass", "dmarc": "pass"}, "sender_email": "x@a.com"}
    score, ev = await engine._analyze_auth(email)
    assert abs(score - 0.35) < 0.01
    assert any(e.type == "auth_spf_fail" for e in ev)


@pytest.mark.asyncio
async def test_auth_all_fail():
    """SPF + DKIM + DMARC all fail → score = 1.0 (capped)."""
    engine = HeuristicEngine(AsyncMock())
    email = {"auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"}, "sender_email": "x@a.com"}
    score, ev = await engine._analyze_auth(email)
    assert score == pytest.approx(1.0)
    assert len(ev) == 3


@pytest.mark.asyncio
async def test_auth_all_pass():
    """All pass → score 0.0."""
    engine = HeuristicEngine(AsyncMock())
    email = {"auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"}, "sender_email": "x@a.com"}
    score, ev = await engine._analyze_auth(email)
    assert score == 0.0
    assert ev == []


@pytest.mark.asyncio
async def test_auth_reply_to_mismatch():
    """Reply-To domain != sender domain → +0.3."""
    engine = HeuristicEngine(AsyncMock())
    email = {
        "auth_results": {},
        "sender_email": "ceo@company.com",
        "reply_to": "hacker@evil.com",
    }
    score, ev = await engine._analyze_auth(email)
    assert score >= 0.3
    assert any(e.type == "auth_reply_to_mismatch" for e in ev)


# ---------------------------------------------------------------------------
# Full analyze (weighted composite)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_clean_email(mock_db, clean_email_data):
    """Clean email through full pipeline → low score."""
    engine = HeuristicEngine(mock_db)
    engine._load_policies = make_mock_policies().__get__(engine)

    result = await engine.analyze(clean_email_data)
    assert result.score < 0.3
    assert len(result.evidences) == 0


@pytest.mark.asyncio
async def test_analyze_phishing_email(mock_db, phishing_email_data):
    """Phishing email through full pipeline → high score with evidences."""
    engine = HeuristicEngine(mock_db)
    engine._load_policies = make_mock_policies().__get__(engine)

    result = await engine.analyze(phishing_email_data)
    assert result.score > 0.5
    assert len(result.evidences) > 3
    assert result.execution_time_ms >= 0


@pytest.mark.asyncio
async def test_analyze_score_clamped():
    """Score is always clamped between 0.0 and 1.0."""
    engine = HeuristicEngine(AsyncMock())
    engine._load_policies = make_mock_policies(blacklist={"evil.xyz"}).__get__(engine)

    email = {
        "sender_email": "x@evil.xyz",
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "reply_to": "y@other.com",
        "urls": ["http://192.168.1.1/x"],
        "subject": "urgent verify your account",
        "body_text": "verify your account immediately act now",
    }
    result = await engine.analyze(email)
    assert 0.0 <= result.score <= 1.0


# ---------------------------------------------------------------------------
# Additional branch coverage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_url_suspicious_tld_in_url():
    """URL with suspicious TLD (.xyz) → url_suspicious evidence."""
    engine = HeuristicEngine(AsyncMock())
    email = {"urls": ["https://malicious-site.xyz/phish"]}
    score, ev = await engine._analyze_urls(email)
    assert score >= 0.3
    assert any(e.type == "url_suspicious" for e in ev)


@pytest.mark.asyncio
async def test_url_unparseable_skipped():
    """Malformed URL doesn't crash, gets skipped."""
    engine = HeuristicEngine(AsyncMock())
    email = {"urls": ["not-a-valid-url://[broken", "https://bit.ly/ok"]}
    score, ev = await engine._analyze_urls(email)
    # Should still find the shortener
    assert any(e.type == "url_shortener" for e in ev)


@pytest.mark.asyncio
async def test_keyword_financial():
    """Financial/BEC keywords → score increase."""
    engine = HeuristicEngine(AsyncMock())
    email = {
        "subject": "invoice attached",
        "body_text": "Please process the wire transfer to the updated bank details.",
    }
    score, ev = await engine._analyze_keywords(email)
    assert score > 0.1


@pytest.mark.asyncio
async def test_auth_spf_softfail():
    """SPF softfail also triggers."""
    engine = HeuristicEngine(AsyncMock())
    email = {"auth_results": {"spf": "softfail", "dkim": "pass", "dmarc": "pass"}, "sender_email": "x@a.com"}
    score, ev = await engine._analyze_auth(email)
    assert score >= 0.35
    assert any(e.type == "auth_spf_fail" for e in ev)
