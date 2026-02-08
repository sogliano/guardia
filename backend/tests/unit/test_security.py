"""Tests for JWT (Clerk) verification and config security validators."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pydantic import ValidationError
from unittest.mock import patch

from app.config import Settings
from app.core.security import verify_clerk_token


def _generate_rsa_keypair():
    """Generate an RSA keypair for testing."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


PRIVATE_PEM, PUBLIC_PEM = _generate_rsa_keypair()


def _make_token(payload=None, key=PRIVATE_PEM, algorithm="RS256"):
    base = {
        "sub": "user_123",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "nbf": int(time.time()) - 10,
    }
    if payload:
        base.update(payload)
    return jwt.encode(base, key, algorithm=algorithm)


@patch("app.core.security.settings")
def test_valid_token(mock_settings):
    mock_settings.clerk_pem_public_key = PUBLIC_PEM.decode()
    mock_settings.app_env = "development"  # Disable aud verification
    token = _make_token()
    result = verify_clerk_token(token)
    assert result["sub"] == "user_123"


@patch("app.core.security.settings")
def test_expired_token(mock_settings):
    mock_settings.clerk_pem_public_key = PUBLIC_PEM.decode()
    token = _make_token({"exp": int(time.time()) - 100})
    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        verify_clerk_token(token)


@patch("app.core.security.settings")
def test_invalid_signature(mock_settings):
    """Token signed with different key → fails."""
    other_private, _ = _generate_rsa_keypair()
    mock_settings.clerk_pem_public_key = PUBLIC_PEM.decode()
    token = _make_token(key=other_private)
    with pytest.raises(jwt.exceptions.InvalidSignatureError):
        verify_clerk_token(token)


def test_garbage_token():
    with pytest.raises(Exception):
        verify_clerk_token("not.a.jwt")


@patch("app.core.security.settings")
def test_valid_token_production_with_issuer(mock_settings):
    """Production mode with correct issuer → accepted."""
    mock_settings.clerk_pem_public_key = PUBLIC_PEM.decode()
    mock_settings.app_env = "production"
    mock_settings.clerk_issuer_url = "https://clerk.example.com"
    token = _make_token({"iss": "https://clerk.example.com"})
    result = verify_clerk_token(token)
    assert result["sub"] == "user_123"


@patch("app.core.security.settings")
def test_wrong_issuer_production_rejected(mock_settings):
    """Production mode with wrong issuer → rejected."""
    mock_settings.clerk_pem_public_key = PUBLIC_PEM.decode()
    mock_settings.app_env = "production"
    mock_settings.clerk_issuer_url = "https://clerk.example.com"
    token = _make_token({"iss": "https://attacker.example.com"})
    with pytest.raises(jwt.exceptions.InvalidIssuerError):
        verify_clerk_token(token)


@patch("app.core.security.settings")
def test_local_skips_issuer_check(mock_settings):
    """Local mode skips issuer check even if issuer_url is set."""
    mock_settings.clerk_pem_public_key = PUBLIC_PEM.decode()
    mock_settings.app_env = "local"
    mock_settings.clerk_issuer_url = "https://clerk.example.com"
    token = _make_token({"iss": "https://different-issuer.com"})
    result = verify_clerk_token(token)
    assert result["sub"] == "user_123"


def test_config_rejects_default_secret_in_production():
    """Production env with default secret key must fail."""
    with pytest.raises(ValidationError, match="app_secret_key"):
        Settings(
            app_env="production",
            app_secret_key="change-me-in-production",
            _env_file=None,
        )


def test_config_accepts_custom_secret_in_production():
    """Production env with custom secret key must succeed."""
    s = Settings(
        app_env="production",
        app_secret_key="my-real-production-secret-key-2026",
        cors_origins="https://guardia.strike.sh",
        _env_file=None,
    )
    assert s.app_secret_key == "my-real-production-secret-key-2026"


def test_config_allows_default_secret_in_local():
    """Local env with default secret key is fine."""
    s = Settings(
        app_env="local",
        app_secret_key="change-me-in-production",
        _env_file=None,
    )
    assert s.app_secret_key == "change-me-in-production"
