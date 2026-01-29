"""Slack delivery service: sends alert notifications via Incoming Webhooks."""

from datetime import datetime, timezone

import httpx
import structlog

from app.config import settings
from app.core.constants import AlertDeliveryStatus

logger = structlog.get_logger()

SEVERITY_EMOJI = {
    "low": ":large_blue_circle:",
    "medium": ":warning:",
    "high": ":large_orange_circle:",
    "critical": ":rotating_light:",
}

VERDICT_EMOJI = {
    "allowed": ":white_check_mark:",
    "warned": ":warning:",
    "quarantined": ":package:",
    "blocked": ":no_entry:",
}

THREAT_LABELS = {
    "bec_impersonation": "BEC / Impersonation",
    "credential_phishing": "Credential Phishing",
    "malware_payload": "Malware Payload",
    "generic_phishing": "Generic Phishing",
    "clean": "Clean",
}


def _score_bar(score: float) -> str:
    """Visual score bar: filled/empty blocks out of 10."""
    filled = round(score * 10)
    return "`" + "\u2588" * filled + "\u2591" * (10 - filled) + f"` *{score:.0%}*"


def _build_payload(event) -> dict:
    """Build Slack Block Kit payload from an AlertEvent."""
    info = event.trigger_info or {}
    severity = (event.severity or "medium").lower()
    verdict = (info.get("verdict") or "unknown").lower()
    score = info.get("final_score") or 0.0
    risk_level = (info.get("risk_level") or "unknown").lower()
    threat = info.get("threat_category") or "unknown"
    rule_name = info.get("rule_name") or "Alert"
    case_id = info.get("case_id", "N/A")
    case_number = info.get("case_number")
    sender_email = info.get("sender_email") or "Unknown"
    sender_name = info.get("sender_name")
    subject = info.get("subject") or "(no subject)"
    recipient = info.get("recipient_email") or "Unknown"

    sev_emoji = SEVERITY_EMOJI.get(severity, ":grey_question:")
    ver_emoji = VERDICT_EMOJI.get(verdict, ":grey_question:")
    threat_label = THREAT_LABELS.get(threat, threat.replace("_", " ").title())
    case_label = f"#{case_number}" if case_number else f"`{case_id[:8]}...`"
    case_url = f"{settings.frontend_base_url.rstrip('/')}/cases/{case_id}"
    sender_display = f"{sender_name} <{sender_email}>" if sender_name else sender_email

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{sev_emoji} {rule_name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*From:* {sender_display}\n"
                    f"*To:* {recipient}\n"
                    f"*Subject:* {subject}"
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Verdict:*\n{ver_emoji} {verdict.upper()}"},
                {"type": "mrkdwn", "text": f"*Severity:*\n{sev_emoji} {severity.upper()}"},
                {"type": "mrkdwn", "text": f"*Threat:*\n{threat_label}"},
                {"type": "mrkdwn", "text": f"*Risk:*\n{risk_level.upper()}"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Score:* {_score_bar(score)}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":mag: View Case", "emoji": True},
                    "url": case_url,
                    "style": "primary",
                },
            ],
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f":shield: *Guard-IA* | Case {case_label} | "
                        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
                    ),
                }
            ],
        },
    ]

    return {"blocks": blocks}


class SlackDeliveryService:
    """Delivers alert events to Slack via Incoming Webhook."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or settings.slack_webhook_url

    async def deliver(self, event) -> bool:
        """Send a single AlertEvent to Slack. Returns True on success."""
        if not self.webhook_url:
            logger.warning("slack_webhook_not_configured")
            event.delivery_status = AlertDeliveryStatus.FAILED
            return False

        payload = _build_payload(event)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.webhook_url, json=payload)

            if resp.status_code == 200:
                event.delivery_status = AlertDeliveryStatus.DELIVERED
                event.delivered_at = datetime.now(timezone.utc)
                info = event.trigger_info or {}
                logger.info(
                    "slack_alert_delivered",
                    case_id=info.get("case_id"),
                    rule=info.get("rule_name"),
                )
                return True

            event.delivery_status = AlertDeliveryStatus.FAILED
            logger.error(
                "slack_alert_failed",
                status=resp.status_code,
                body=resp.text[:200],
            )
            return False

        except Exception as exc:
            event.delivery_status = AlertDeliveryStatus.FAILED
            logger.error("slack_alert_error", error=str(exc))
            return False
