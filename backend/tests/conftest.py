import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient


@pytest.fixture
def mock_db():
    """AsyncSession mock that supports execute/flush/add/delete."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def clean_email_data():
    """A clean, legitimate email dict for pipeline consumption."""
    return {
        "message_id": "abc123@strike.sh",
        "sender_email": "alice@strike.sh",
        "sender_name": "Alice",
        "reply_to": None,
        "recipient_email": "bob@strike.sh",
        "recipients_cc": [],
        "subject": "Weekly sync notes",
        "body_text": "Hi Bob, here are the notes from today's meeting.",
        "body_html": None,
        "headers": {},
        "urls": [],
        "attachments": [],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
    }


@pytest.fixture
def phishing_email_data():
    """A highly suspicious phishing email dict."""
    return {
        "message_id": "phish999@evil.xyz",
        "sender_email": "security@gooogle.com",
        "sender_name": "Google Security",
        "reply_to": "attacker@evil-domain.xyz",
        "recipient_email": "victim@strike.sh",
        "recipients_cc": [],
        "subject": "Urgent: verify your account immediately",
        "body_text": (
            "Your account has been compromised. "
            "Click here to verify your identity immediately. "
            "Failure to respond within 24 hours will result in account suspension."
        ),
        "body_html": None,
        "headers": {},
        "urls": ["http://192.168.1.1/steal-creds", "https://bit.ly/fake"],
        "attachments": [],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
    }


def make_mock_policies(blacklist=None, whitelist=None):
    """Helper: patch HeuristicEngine._load_policies to set domains directly."""
    blacklist = blacklist or set()
    whitelist = whitelist or set()

    async def _fake_load(self):
        self._blacklisted_domains = blacklist
        self._whitelisted_domains = whitelist

    return _fake_load


@pytest.fixture
async def client():
    """HTTP test client for FastAPI app."""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
