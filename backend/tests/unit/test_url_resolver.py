"""Tests for URL shortener resolver with SSRF protection."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.pipeline.url_resolver import (
    URLResolver,
    _is_private_ip,
    _is_safe_url,
    is_shortener,
)


# ---------------------------------------------------------------------------
# is_shortener
# ---------------------------------------------------------------------------

def test_shortener_detection():
    assert is_shortener("https://bit.ly/abc123") is True
    assert is_shortener("https://t.co/xyz") is True
    assert is_shortener("https://google.com/search") is False


# ---------------------------------------------------------------------------
# _is_private_ip
# ---------------------------------------------------------------------------

def test_private_ip():
    assert _is_private_ip("192.168.1.1") is True
    assert _is_private_ip("10.0.0.1") is True
    assert _is_private_ip("127.0.0.1") is True
    assert _is_private_ip("169.254.169.254") is True
    assert _is_private_ip("8.8.8.8") is False


# ---------------------------------------------------------------------------
# _is_safe_url
# ---------------------------------------------------------------------------

@patch("app.services.pipeline.url_resolver.socket.getaddrinfo")
def test_safe_url_public(mock_dns):
    mock_dns.return_value = [(2, 1, 0, "", ("93.184.216.34", 0))]
    safe, _ = _is_safe_url("https://example.com/page")
    assert safe is True


@patch("app.services.pipeline.url_resolver.socket.getaddrinfo")
def test_safe_url_resolves_private(mock_dns):
    mock_dns.return_value = [(2, 1, 0, "", ("192.168.1.1", 0))]
    safe, reason = _is_safe_url("https://evil.com/steal")
    assert safe is False
    assert "private" in reason.lower()


def test_safe_url_direct_private_ip():
    safe, reason = _is_safe_url("http://192.168.1.1/admin")
    assert safe is False


def test_safe_url_localhost():
    safe, _ = _is_safe_url("http://127.0.0.1/")
    assert safe is False


# ---------------------------------------------------------------------------
# URLResolver.resolve
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_simple_redirect():
    resolver = URLResolver()

    redirect_response = httpx.Response(
        302,
        headers={"location": "https://example.com/final"},
        request=httpx.Request("HEAD", "https://bit.ly/abc"),
    )
    final_response = httpx.Response(
        200,
        request=httpx.Request("HEAD", "https://example.com/final"),
    )

    with patch("app.services.pipeline.url_resolver._is_safe_url", return_value=(True, "")):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(side_effect=[redirect_response, final_response])
            mock_client_cls.return_value = mock_client

            resolved, error = await resolver.resolve("https://bit.ly/abc")
            assert resolved == "https://example.com/final"
            assert error is None


@pytest.mark.asyncio
async def test_max_redirects_exceeded():
    resolver = URLResolver()

    redirect = httpx.Response(
        302,
        headers={"location": "https://hop.com/next"},
        request=httpx.Request("HEAD", "https://bit.ly/loop"),
    )

    with patch("app.services.pipeline.url_resolver._is_safe_url", return_value=(True, "")):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(return_value=redirect)
            mock_client_cls.return_value = mock_client

            resolved, error = await resolver.resolve("https://bit.ly/loop")
            assert resolved is None
            assert "Exceeded" in error


@pytest.mark.asyncio
async def test_timeout():
    resolver = URLResolver()

    with patch("app.services.pipeline.url_resolver._is_safe_url", return_value=(True, "")):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.head = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_cls.return_value = mock_client

            resolved, error = await resolver.resolve("https://bit.ly/slow")
            assert resolved is None
            assert "Timeout" in error


@pytest.mark.asyncio
async def test_private_ip_blocked():
    resolver = URLResolver()
    with patch(
        "app.services.pipeline.url_resolver._is_safe_url",
        return_value=(False, "Private IP: 192.168.1.1"),
    ):
        resolved, error = await resolver.resolve("http://192.168.1.1/admin")
        assert resolved is None
        assert "Blocked" in error
