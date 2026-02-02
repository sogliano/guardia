"""Tests for JWT (Clerk) verification."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from unittest.mock import patch

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
