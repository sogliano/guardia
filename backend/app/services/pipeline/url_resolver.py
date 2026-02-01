"""URL shortener resolver with SSRF protection.

Resolves shortened URLs (bit.ly, t.co, etc.) to their final destinations
by following redirects manually. Blocks private/internal IPs to prevent SSRF.
"""

import ipaddress
import socket
from urllib.parse import urlparse

import httpx
import structlog

logger = structlog.get_logger()

MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 3.0

# Known URL shortener domains
URL_SHORTENER_DOMAINS = frozenset({
    "bit.ly", "bitly.com", "t.co", "goo.gl", "tinyurl.com",
    "ow.ly", "is.gd", "buff.ly", "rebrand.ly", "rb.gy",
    "cutt.ly", "shorturl.at", "tiny.cc", "lnkd.in", "surl.li",
})


def is_shortener(url: str) -> bool:
    """Check if a URL belongs to a known shortener domain."""
    try:
        hostname = urlparse(url).hostname or ""
        return hostname.lower() in URL_SHORTENER_DOMAINS
    except Exception:
        return False


def _is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is private, loopback, link-local, or metadata."""
    try:
        addr = ipaddress.ip_address(ip_str)
        return (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or ip_str == "169.254.169.254"  # cloud metadata
        )
    except ValueError:
        return False


def _is_safe_url(url: str) -> tuple[bool, str]:
    """Validate URL is safe to request (not pointing to internal resources)."""
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False, "No hostname"

        # Block IP-based URLs directly
        try:
            if _is_private_ip(hostname):
                return False, f"Private IP: {hostname}"
        except ValueError:
            pass

        # Resolve hostname and check IPs
        try:
            results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in results:
                ip = sockaddr[0]
                if _is_private_ip(ip):
                    return False, f"Hostname {hostname} resolves to private IP {ip}"
        except socket.gaierror:
            return False, f"DNS resolution failed for {hostname}"

        return True, ""
    except Exception as exc:
        return False, str(exc)


class URLResolver:
    """Resolves shortened URLs by following redirects with SSRF protection."""

    async def resolve(self, url: str) -> tuple[str | None, str | None]:
        """Resolve a URL, following redirects up to MAX_REDIRECTS hops.

        Returns (resolved_url, error_message).
        On success: (final_url, None)
        On failure: (None, error_reason)
        """
        current_url = url

        for hop in range(MAX_REDIRECTS):
            safe, reason = _is_safe_url(current_url)
            if not safe:
                logger.warning(
                    "url_resolve_blocked", url=current_url, reason=reason, hop=hop
                )
                return None, f"Blocked: {reason}"

            try:
                response_data = await self._safe_http_request(current_url)

                if response_data["status"] in (301, 302, 303, 307, 308):
                    location = response_data["location"]
                    if not location:
                        return current_url, None

                    # Handle relative redirects
                    if location.startswith("/"):
                        parsed = urlparse(current_url)
                        location = f"{parsed.scheme}://{parsed.netloc}{location}"

                    current_url = location
                    continue

                # Non-redirect response — this is the final URL
                return current_url, None

            except httpx.TimeoutException:
                logger.warning("url_resolve_timeout", url=current_url, hop=hop)
                return None, "Timeout"
            except Exception as exc:
                logger.warning(
                    "url_resolve_error", url=current_url, hop=hop, error=str(exc)
                )
                return None, str(exc)

        # Exceeded max redirects
        logger.warning(
            "url_resolve_max_redirects", url=url, final=current_url, hops=MAX_REDIRECTS
        )
        return None, f"Exceeded {MAX_REDIRECTS} redirects"

    async def _safe_http_request(self, url: str) -> dict:
        """Safe HTTP request that respects cancellation.

        Returns dict with status and location headers to avoid
        keeping connection open after task cancellation.
        """
        async with httpx.AsyncClient(
            follow_redirects=False,
            timeout=TIMEOUT_SECONDS,
            verify=False,
        ) as client:
            response = await client.head(url)
            return {
                "status": response.status_code,
                "location": response.headers.get("location"),
            }
