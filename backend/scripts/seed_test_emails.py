#!/usr/bin/env python3
"""Seed 20 test emails directly into DB and run the full pipeline.

Bypasses the SMTP gateway — inserts emails via SQLAlchemy and runs
PipelineOrchestrator.analyze() on each one.

Usage:
    cd backend
    python -m scripts.seed_test_emails
"""

import asyncio
import sys
import os
import time

# Ensure backend is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.db.session import get_standalone_session
from app.gateway.parser import EmailParser
from app.models.email import Email
from app.services.pipeline.orchestrator import PipelineOrchestrator
from scripts.email_templates import TEMPLATES


# 4 additional templates to reach 20 total
EXTRA_EMAILS = [
    {
        "message_id": "<extra-legit-internal-001@strike.sh>",
        "sender_email": "martin.garcia@strike.sh",
        "sender_name": "Martin Garcia",
        "recipient_email": "analyst@strike.sh",
        "subject": "Reminder: All-hands meeting tomorrow at 10am",
        "body_text": (
            "Hey team,\n\n"
            "Just a quick reminder about our all-hands meeting tomorrow at 10am UYT.\n"
            "We'll cover Q1 goals, hiring updates, and the product roadmap.\n\n"
            "Agenda doc is in the shared drive as usual.\n\n"
            "See you there,\nMartin"
        ),
        "urls": [],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<martin.garcia@strike.sh>"},
    },
    {
        "message_id": "<extra-ambiguous-linkedin-002@linkedin.com>",
        "sender_email": "messages-noreply@linkedin.com",
        "sender_name": "LinkedIn",
        "recipient_email": "analyst@strike.sh",
        "subject": "You appeared in 14 searches this week",
        "body_text": (
            "Hi Nicolas,\n\n"
            "You appeared in 14 searches this week.\n\n"
            "People who found you work at:\n"
            "- Google\n"
            "- Microsoft\n"
            "- Amazon\n\n"
            "See all search appearances:\n"
            "https://www.linkedin.com/me/search-appearances\n\n"
            "LinkedIn Corporation, 1000 W Maude Ave, Sunnyvale, CA 94085\n"
            "Unsubscribe: https://www.linkedin.com/comm/unsubscribe"
        ),
        "urls": [
            "https://www.linkedin.com/me/search-appearances",
            "https://www.linkedin.com/comm/unsubscribe",
        ],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<bounce@linkedin.com>"},
    },
    {
        "message_id": "<extra-ambiguous-docusign-003@docusign.net>",
        "sender_email": "dse@docusign.net",
        "sender_name": "DocuSign via Strike Security",
        "recipient_email": "analyst@strike.sh",
        "subject": "Please sign: NDA - Confidentiality Agreement 2026",
        "body_text": (
            "Martin Garcia sent you a document to review and sign.\n\n"
            "REVIEW DOCUMENT\n"
            "https://app.docusign.com/sign/abc123def456\n\n"
            "Document: NDA - Confidentiality Agreement 2026\n"
            "Sender: martin.garcia@strike.sh\n\n"
            "Do not share this email. The link is unique to you.\n\n"
            "If you have questions about the document, contact the sender directly.\n"
            "If you didn't expect this, you can ignore this email.\n\n"
            "This message was sent by DocuSign Electronic Signature Service."
        ),
        "urls": ["https://app.docusign.com/sign/abc123def456"],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<dse@docusign.net>"},
    },
    {
        "message_id": "<extra-vendor-compromise-004@acme-consulting.com>",
        "sender_email": "invoicing@acme-consultiing.com",
        "sender_name": "ACME Consulting - Accounts",
        "reply_to": "payments@offshore-accounts.xyz",
        "recipient_email": "analyst@strike.sh",
        "subject": "Updated banking details for upcoming payment",
        "body_text": (
            "Dear Strike Security team,\n\n"
            "This is to inform you that ACME Consulting has changed our banking\n"
            "institution. Please update our payment information for all\n"
            "outstanding and future invoices.\n\n"
            "New banking details:\n"
            "Bank: First Caribbean International\n"
            "Account Name: ACME Global Services Ltd\n"
            "Account: 8291-4738-2019\n"
            "SWIFT: FCIBUS33\n\n"
            "Please process the pending invoice of $18,400 to the new account.\n"
            "Ignore any previous banking details we may have provided.\n\n"
            "Best regards,\n"
            "Sarah Thompson\n"
            "Head of Accounts, ACME Consulting"
        ),
        "urls": [],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<invoicing@acme-consultiing.com>"},
    },
]


def _template_to_dict(template_name: str) -> dict:
    """Convert an EmailMessage template to a dict suitable for Email model."""
    factory, _ = TEMPLATES[template_name]
    msg = factory("analyst@strike.sh")

    parser = EmailParser()
    raw_bytes = msg.as_bytes()
    parsed = parser.parse_raw(raw_bytes, msg["From"], ["analyst@strike.sh"])
    return parsed


async def seed_and_analyze():
    """Insert 20 emails and run the pipeline on each."""
    print(f"\n{'='*70}")
    print("  Guard-IA Pipeline Test — 20 emails (LLM Analyst enabled)")
    print(f"  DB: {settings.database_url[:50]}...")
    print(f"  OpenAI model: {settings.openai_model}")
    print(f"  Anthropic model: {settings.anthropic_model}")
    print(f"  Anthropic key set: {bool(settings.anthropic_api_key)}")
    print(f"  OpenAI key set: {bool(settings.openai_api_key)}")
    print(f"{'='*70}\n")

    # Build all 20 email dicts
    all_emails: list[dict] = []

    # 16 from existing templates
    template_names = list(TEMPLATES.keys())
    for name in template_names:
        data = _template_to_dict(name)
        all_emails.append(data)

    # 4 extra
    for extra in EXTRA_EMAILS:
        all_emails.append(extra)

    total = len(all_emails)
    results = []

    for i, email_data in enumerate(all_emails, 1):
        subject = email_data.get("subject", "(no subject)")[:60]
        sender = email_data.get("sender_email", "unknown")
        print(f"[{i:2d}/{total}] {sender}")
        print(f"         Subject: {subject}")

        start = time.monotonic()

        async with get_standalone_session() as db:
            # Insert email
            email_record = Email(
                message_id=email_data["message_id"],
                sender_email=email_data.get("sender_email", ""),
                sender_name=email_data.get("sender_name"),
                reply_to=email_data.get("reply_to"),
                recipient_email=email_data.get("recipient_email", "analyst@strike.sh"),
                recipients_cc=email_data.get("recipients_cc", []),
                subject=email_data.get("subject"),
                body_text=email_data.get("body_text"),
                body_html=email_data.get("body_html"),
                headers=email_data.get("headers", {}),
                urls=email_data.get("urls", []),
                attachments=email_data.get("attachments", []),
                auth_results=email_data.get("auth_results", {}),
            )
            db.add(email_record)
            await db.flush()

            # Run pipeline
            orchestrator = PipelineOrchestrator(db)
            try:
                result = await orchestrator.analyze(email_record.id)
                elapsed = int((time.monotonic() - start) * 1000)

                llm_info = ""
                if result.llm.provider:
                    llm_info = f" | LLM: {result.llm.score:.2f} ({result.llm.provider}/{result.llm.model_used})"

                print(
                    f"         Score: {result.final_score:.4f} | "
                    f"Verdict: {result.verdict:<12s} | "
                    f"Risk: {result.risk_level:<8s} | "
                    f"Time: {elapsed}ms{llm_info}"
                )

                results.append({
                    "subject": subject,
                    "score": result.final_score,
                    "verdict": result.verdict,
                    "risk": result.risk_level,
                    "heuristic": result.heuristic.score,
                    "llm_score": result.llm.score,
                    "llm_provider": result.llm.provider,
                    "duration_ms": elapsed,
                })
            except Exception as exc:
                print(f"         ERROR: {exc}")
                results.append({
                    "subject": subject,
                    "score": -1,
                    "verdict": "ERROR",
                    "risk": "ERROR",
                    "heuristic": 0,
                    "llm_score": 0,
                    "llm_provider": "",
                    "duration_ms": 0,
                })

        print()

    # Summary
    print(f"\n{'='*70}")
    print("  SUMMARY")
    print(f"{'='*70}")
    print(f"  {'Subject':<45s} {'Score':>6s} {'Verdict':<12s} {'LLM':>5s} {'Provider':<10s}")
    print(f"  {'-'*45} {'-'*6} {'-'*12} {'-'*5} {'-'*10}")
    for r in results:
        print(
            f"  {r['subject']:<45s} "
            f"{r['score']:>6.3f} "
            f"{r['verdict']:<12s} "
            f"{r['llm_score']:>5.2f} "
            f"{r['llm_provider']:<10s}"
        )

    allowed = sum(1 for r in results if r["verdict"] == "allowed")
    warned = sum(1 for r in results if r["verdict"] == "warned")
    quarantined = sum(1 for r in results if r["verdict"] == "quarantined")
    blocked = sum(1 for r in results if r["verdict"] == "blocked")
    errors = sum(1 for r in results if r["verdict"] == "ERROR")

    print(f"\n  Allowed: {allowed} | Warned: {warned} | Quarantined: {quarantined} | Blocked: {blocked} | Errors: {errors}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(seed_and_analyze())
