"""Email parser: converts raw RFC 5322 bytes into structured data for EmailIngest."""

import email
import email.utils
import re
from email import policy
from email.message import EmailMessage
from html.parser import HTMLParser

import structlog

logger = structlog.get_logger()

# Regex for extracting URLs from text
URL_REGEX = re.compile(
    r'https?://[^\s<>"\')\]},;]+',
    re.IGNORECASE,
)

# Regex for Authentication-Results parsing
AUTH_RESULT_REGEX = re.compile(
    r'\b(spf|dkim|dmarc)\s*=\s*(pass|fail|softfail|neutral|none|temperror|permerror)',
    re.IGNORECASE,
)


class _URLExtractor(HTMLParser):
    """Extracts href attributes from HTML anchor tags."""

    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []
        self._current_href: str | None = None
        self._current_text: str = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._current_text = ""
            for name, value in attrs:
                if name == "href" and value:
                    self._current_href = value

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._current_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href:
            self.urls.append(self._current_href)
            self._current_href = None
            self._current_text = ""


class EmailParser:
    """Parses raw email bytes (RFC 5322) into a structured dictionary
    compatible with the EmailIngest Pydantic schema."""

    def parse_raw(
        self,
        raw_data: bytes,
        envelope_from: str,
        envelope_to: list[str],
    ) -> dict:
        """Parse raw email bytes into a dict for EmailIngest.

        Args:
            raw_data: Raw email bytes as received via SMTP DATA command.
            envelope_from: SMTP MAIL FROM address.
            envelope_to: SMTP RCPT TO addresses.

        Returns:
            Dict with keys matching EmailIngest schema fields.
        """
        msg: EmailMessage = email.message_from_bytes(
            raw_data, policy=policy.default
        )  # type: ignore[assignment]

        sender_email, sender_name = self._parse_from(msg)
        reply_to = self._parse_reply_to(msg)
        recipients_cc = self._parse_cc(msg)
        body_text, body_html = self._extract_body(msg)
        urls = self._extract_urls(body_text, body_html)
        attachments = self._extract_attachments(msg)
        auth_results = self._parse_auth_results(msg)
        received_at = self._parse_date(msg)

        return {
            "message_id": msg.get("Message-ID", "").strip("<>") or f"no-msgid-{id(raw_data)}",
            "sender_email": sender_email or envelope_from,
            "sender_name": sender_name,
            "reply_to": reply_to,
            "recipient_email": envelope_to[0] if envelope_to else "",
            "recipients_cc": recipients_cc,
            "subject": msg.get("Subject", ""),
            "body_text": body_text,
            "body_html": body_html,
            "headers": self._extract_headers(msg),
            "urls": urls,
            "attachments": attachments,
            "auth_results": auth_results,
            "received_at": received_at,
        }

    def _parse_from(self, msg: EmailMessage) -> tuple[str, str | None]:
        """Extract sender email and display name from From header."""
        from_header = msg.get("From", "")
        name, addr = email.utils.parseaddr(from_header)
        return addr.lower(), name or None

    def _parse_reply_to(self, msg: EmailMessage) -> str | None:
        """Extract Reply-To address."""
        reply_to = msg.get("Reply-To")
        if not reply_to:
            return None
        _, addr = email.utils.parseaddr(reply_to)
        return addr.lower() if addr else None

    def _parse_cc(self, msg: EmailMessage) -> list[str]:
        """Extract CC recipients."""
        cc_header = msg.get("Cc", "")
        if not cc_header:
            return []
        addresses = email.utils.getaddresses([cc_header])
        return [addr.lower() for _, addr in addresses if addr]

    def _extract_body(self, msg: EmailMessage) -> tuple[str | None, str | None]:
        """Extract text and HTML body parts."""
        body_text: str | None = None
        body_html: str | None = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in disposition:
                    continue
                try:
                    payload = part.get_content()
                except Exception:
                    continue
                if content_type == "text/plain" and body_text is None:
                    body_text = str(payload)
                elif content_type == "text/html" and body_html is None:
                    body_html = str(payload)
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_content()
            except Exception:
                payload = ""
            if content_type == "text/plain":
                body_text = str(payload)
            elif content_type == "text/html":
                body_html = str(payload)

        return body_text, body_html

    def _extract_urls(self, body_text: str | None, body_html: str | None) -> list[str]:
        """Extract URLs from text body (regex) and HTML body (href attributes)."""
        urls: set[str] = set()

        if body_text:
            urls.update(URL_REGEX.findall(body_text))

        if body_html:
            extractor = _URLExtractor()
            try:
                extractor.feed(body_html)
                urls.update(extractor.urls)
            except Exception:
                pass
            urls.update(URL_REGEX.findall(body_html))

        return list(urls)

    def _extract_attachments(self, msg: EmailMessage) -> list[dict]:
        """Extract attachment metadata (without content)."""
        attachments: list[dict] = []
        if not msg.is_multipart():
            return attachments

        for part in msg.walk():
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" not in disposition:
                continue
            filename = part.get_filename() or "unknown"
            content_type = part.get_content_type()
            try:
                size = len(part.get_content())  # type: ignore[arg-type]
            except Exception:
                size = 0
            attachments.append({
                "filename": filename,
                "content_type": content_type,
                "size": size,
            })

        return attachments

    def _parse_auth_results(self, msg: EmailMessage) -> dict:
        """Parse Authentication-Results header for SPF/DKIM/DMARC verdicts."""
        auth_header = msg.get("Authentication-Results", "")
        if not auth_header:
            return {"spf": "none", "dkim": "none", "dmarc": "none"}

        results: dict[str, str] = {"spf": "none", "dkim": "none", "dmarc": "none"}
        for match in AUTH_RESULT_REGEX.finditer(auth_header):
            mechanism = match.group(1).lower()
            result = match.group(2).lower()
            if mechanism in results:
                results[mechanism] = result

        return results

    def _parse_date(self, msg: EmailMessage) -> str | None:
        """Parse Date header to ISO format string."""
        date_header = msg.get("Date")
        if not date_header:
            return None
        try:
            parsed = email.utils.parsedate_to_datetime(date_header)
            return parsed.isoformat()
        except Exception:
            return None

    def _extract_headers(self, msg: EmailMessage) -> dict:
        """Extract all headers as a dict (last value wins for duplicates)."""
        headers: dict[str, str] = {}
        for key in msg.keys():
            value = msg.get(key, "")
            headers[key] = str(value)
        return headers
