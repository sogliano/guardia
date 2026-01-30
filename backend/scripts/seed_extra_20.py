#!/usr/bin/env python3
"""Seed 20 EXTRA test emails (case IDs > 20).

Usage:
    cd backend
    python -m scripts.seed_extra_20
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.db.session import get_standalone_session
from app.models.email import Email
from app.services.pipeline.orchestrator import PipelineOrchestrator

EMAILS = [
    # ── Phishing / Malicious ──
    {
        "message_id": "<extra2-paypal-001@paypa1-security.com>",
        "sender_email": "security@paypa1-security.com",
        "sender_name": "PayPal Security Team",
        "recipient_email": "analyst@strike.sh",
        "subject": "Your PayPal account has been limited — Verify now",
        "body_text": (
            "Dear Customer,\n\n"
            "We've noticed unusual activity in your PayPal account. Your account has been temporarily limited.\n\n"
            "To restore full access, please verify your identity within 24 hours:\n"
            "https://paypa1-security.com/verify?id=usr_29381\n\n"
            "If you don't verify within 24 hours, your account will be permanently suspended.\n\n"
            "PayPal Security Team\n"
            "This is an automated message — do not reply."
        ),
        "urls": ["https://paypa1-security.com/verify?id=usr_29381"],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<bounce@paypa1-security.com>"},
    },
    {
        "message_id": "<extra2-ceo-wire-002@strlke-security.com>",
        "sender_email": "martin.garcia@strlke-security.com",
        "sender_name": "Martin Garcia",
        "reply_to": "martin.g.private@protonmail.ch",
        "recipient_email": "analyst@strike.sh",
        "subject": "Confidential — Acquisition payment needed today",
        "body_text": (
            "Hi,\n\n"
            "We're closing the acquisition of CyberDefend Ltd today and I need you to process a payment.\n\n"
            "Amount: $142,000 USD\n"
            "Bank: HSBC Hong Kong\n"
            "Account: 789-421-6653\n"
            "SWIFT: HSBCHKHH\n\n"
            "This is extremely confidential — board hasn't announced yet. Don't mention to anyone.\n"
            "I'm in the signing meeting so only email.\n\n"
            "Thanks,\nMartin"
        ),
        "urls": [],
        "auth_results": {"spf": "softfail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<martin.garcia@strlke-security.com>"},
    },
    {
        "message_id": "<extra2-dropbox-003@dr0pbox-share.com>",
        "sender_email": "noreply@dr0pbox-share.com",
        "sender_name": "Dropbox",
        "recipient_email": "analyst@strike.sh",
        "subject": "Nicolas shared 'Salary_Review_2026.xlsx' with you",
        "body_text": (
            "Nicolas Sogliano shared a file with you.\n\n"
            "Salary_Review_2026.xlsx\n"
            "This document contains sensitive information.\n\n"
            "View file: https://dr0pbox-share.com/s/salary-review-2026\n\n"
            "Dropbox — Keep everything organized."
        ),
        "urls": ["https://dr0pbox-share.com/s/salary-review-2026"],
        "auth_results": {"spf": "fail", "dkim": "none", "dmarc": "fail"},
        "headers": {"Return-Path": "<noreply@dr0pbox-share.com>"},
    },
    {
        "message_id": "<extra2-tax-004@irs-gov-refund.com>",
        "sender_email": "refunds@irs-gov-refund.com",
        "sender_name": "Internal Revenue Service",
        "recipient_email": "analyst@strike.sh",
        "subject": "Tax Refund Notification — $4,287.00 pending",
        "body_text": (
            "Dear Taxpayer,\n\n"
            "After reviewing your tax return, we have determined that you are eligible for a refund of $4,287.00.\n\n"
            "To claim your refund, please verify your identity:\n"
            "https://irs-gov-refund.com/claim?ref=TX2026-8291\n\n"
            "You must complete verification within 48 hours or the refund will be forfeited.\n\n"
            "Internal Revenue Service\n"
            "Department of the Treasury"
        ),
        "urls": ["https://irs-gov-refund.com/claim?ref=TX2026-8291"],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<refunds@irs-gov-refund.com>"},
    },
    {
        "message_id": "<extra2-zoom-005@zo0m-meeting.com>",
        "sender_email": "meetings@zo0m-meeting.com",
        "sender_name": "Zoom Meetings",
        "recipient_email": "analyst@strike.sh",
        "subject": "HR has invited you: Performance Review — Join Now",
        "body_text": (
            "Hi,\n\n"
            "Your manager has scheduled an urgent performance review meeting.\n\n"
            "Topic: Q1 Performance Review & Compensation Discussion\n"
            "Date: Today\n"
            "Time: In 15 minutes\n\n"
            "Join Meeting: https://zo0m-meeting.com/j/892741?pwd=review2026\n\n"
            "Please join on time. This meeting is mandatory.\n\n"
            "Zoom Video Communications"
        ),
        "urls": ["https://zo0m-meeting.com/j/892741?pwd=review2026"],
        "auth_results": {"spf": "fail", "dkim": "none", "dmarc": "fail"},
        "headers": {"Return-Path": "<meetings@zo0m-meeting.com>"},
    },
    {
        "message_id": "<extra2-invoice-006@vendor-payments-portal.net>",
        "sender_email": "accounting@vendor-payments-portal.net",
        "sender_name": "CloudFlare Billing",
        "reply_to": "wire@offshore-billing.xyz",
        "recipient_email": "analyst@strike.sh",
        "subject": "PAST DUE: Invoice #CF-2026-4419 — Service suspension imminent",
        "body_text": (
            "Dear Strike Security,\n\n"
            "Your Cloudflare Enterprise invoice #CF-2026-4419 ($8,750.00) is 30 days past due.\n\n"
            "If payment is not received by end of business today, your services will be suspended.\n\n"
            "Pay now: https://vendor-payments-portal.net/pay/CF-2026-4419\n\n"
            "Wire transfer details:\n"
            "Bank: First National Cyprus\n"
            "Account: 4421-8892-1100\n"
            "SWIFT: FNCYCY2N\n\n"
            "Cloudflare Accounts Receivable"
        ),
        "urls": ["https://vendor-payments-portal.net/pay/CF-2026-4419"],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<accounting@vendor-payments-portal.net>"},
    },
    {
        "message_id": "<extra2-crypto-007@wallet-metamask-verify.io>",
        "sender_email": "security@wallet-metamask-verify.io",
        "sender_name": "MetaMask Wallet",
        "recipient_email": "analyst@strike.sh",
        "subject": "ALERT: Your wallet will be deactivated in 12 hours",
        "body_text": (
            "Dear MetaMask User,\n\n"
            "Due to our new KYC compliance requirements, all wallets must be re-verified.\n\n"
            "Your wallet (0x7f4a...8e21) holds 3.7 ETH ($12,419.00).\n"
            "If not verified within 12 hours, funds will be locked.\n\n"
            "Verify now: https://wallet-metamask-verify.io/kyc?wallet=0x7f4a\n\n"
            "MetaMask — A ConsenSys Formation"
        ),
        "urls": ["https://wallet-metamask-verify.io/kyc?wallet=0x7f4a"],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<security@wallet-metamask-verify.io>"},
    },
    {
        "message_id": "<extra2-sharepoint-008@sharepointt-online.com>",
        "sender_email": "share@sharepointt-online.com",
        "sender_name": "SharePoint Online",
        "recipient_email": "analyst@strike.sh",
        "subject": "Document shared: 'Board_Meeting_Minutes_Confidential.docx'",
        "body_text": (
            "Martin Garcia shared a document with you.\n\n"
            "Board_Meeting_Minutes_Confidential.docx\n\n"
            "Open document: https://sharepointt-online.com/d/board-minutes-2026\n\n"
            "Note: You need to sign in with your Microsoft 365 credentials to access this file.\n\n"
            "Microsoft SharePoint"
        ),
        "urls": ["https://sharepointt-online.com/d/board-minutes-2026"],
        "auth_results": {"spf": "fail", "dkim": "none", "dmarc": "fail"},
        "headers": {"Return-Path": "<share@sharepointt-online.com>"},
    },
    {
        "message_id": "<extra2-dhl-009@dhl-delivery-notification.xyz>",
        "sender_email": "tracking@dhl-delivery-notification.xyz",
        "sender_name": "DHL Express",
        "recipient_email": "analyst@strike.sh",
        "subject": "Your DHL shipment is on hold — customs clearance required",
        "body_text": (
            "Dear Customer,\n\n"
            "Your DHL Express shipment (AWB: 4829-1100-7742) is on hold at customs.\n\n"
            "A customs duty of $23.50 must be paid before delivery.\n\n"
            "Pay customs fee: https://dhl-delivery-notification.xyz/customs/pay?awb=4829\n\n"
            "If not paid within 48 hours, the package will be returned to sender.\n\n"
            "DHL Express — Excellence. Simply Delivered."
        ),
        "urls": ["https://dhl-delivery-notification.xyz/customs/pay?awb=4829"],
        "attachments": [{"filename": "customs_form.pdf.exe", "content_type": "application/pdf", "size": 15}],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<tracking@dhl-delivery-notification.xyz>"},
    },
    {
        "message_id": "<extra2-hr-010@strike-hr-portal.com>",
        "sender_email": "hr@strike-hr-portal.com",
        "sender_name": "Strike Security HR",
        "recipient_email": "analyst@strike.sh",
        "subject": "Action Required: Update your W-2 tax information",
        "body_text": (
            "Hi Team,\n\n"
            "As part of our annual payroll audit, we need all employees to verify their W-2 tax information.\n\n"
            "Please update your details by clicking below:\n"
            "https://strike-hr-portal.com/tax-update?emp=auto\n\n"
            "Required information: SSN, bank account, routing number.\n\n"
            "This must be completed by Friday or your January paycheck may be delayed.\n\n"
            "Best,\nHR Department\nStrike Security"
        ),
        "urls": ["https://strike-hr-portal.com/tax-update?emp=auto"],
        "auth_results": {"spf": "softfail", "dkim": "fail", "dmarc": "none"},
        "headers": {"Return-Path": "<hr@strike-hr-portal.com>"},
    },
    # ── Legitimate / Clean ──
    {
        "message_id": "<extra2-legit-jira-011@atlassian.net>",
        "sender_email": "jira@strike-security.atlassian.net",
        "sender_name": "Jira",
        "recipient_email": "analyst@strike.sh",
        "subject": "[GUARD-142] ML pipeline timeout increased to 30s",
        "body_text": (
            "Nicolas Sogliano updated GUARD-142:\n\n"
            "Status: In Progress → Done\n"
            "Resolution: Fixed\n\n"
            "Comment: Increased ML pipeline timeout from 15s to 30s to handle edge cases "
            "with large email bodies. Tested with 500+ samples, no timeouts observed.\n\n"
            "View issue: https://strike-security.atlassian.net/browse/GUARD-142\n\n"
            "This message was sent by Atlassian Jira (v9.12.0#912000)"
        ),
        "urls": ["https://strike-security.atlassian.net/browse/GUARD-142"],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<jira@strike-security.atlassian.net>"},
    },
    {
        "message_id": "<extra2-legit-stripe-012@stripe.com>",
        "sender_email": "receipts+acct_1N4x@stripe.com",
        "sender_name": "Stripe",
        "recipient_email": "analyst@strike.sh",
        "subject": "Your receipt from Strike Security (#1842-9910)",
        "body_text": (
            "Receipt from Strike Security\n\n"
            "Amount paid: $299.00\n"
            "Date: January 29, 2026\n"
            "Payment method: Visa ending in 4242\n\n"
            "Description: Guard-IA Platform — Pro Plan (Monthly)\n\n"
            "Receipt #1842-9910\n"
            "View receipt: https://pay.stripe.com/receipts/1842-9910\n\n"
            "If you have questions, contact Strike Security at billing@strike.sh\n"
            "Stripe, 354 Oyster Point Blvd, South San Francisco, CA 94080"
        ),
        "urls": ["https://pay.stripe.com/receipts/1842-9910"],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<receipts@stripe.com>"},
    },
    {
        "message_id": "<extra2-legit-vercel-013@vercel.com>",
        "sender_email": "notifications@vercel.com",
        "sender_name": "Vercel",
        "recipient_email": "analyst@strike.sh",
        "subject": "Deployment succeeded: guardia-frontend (production)",
        "body_text": (
            "Deployment Summary\n\n"
            "Project: guardia-frontend\n"
            "Environment: Production\n"
            "Status: Ready\n"
            "URL: https://guardia.strike.sh\n\n"
            "Commit: fix(pipeline): increase ML timeout to 30s\n"
            "Branch: main\n"
            "Duration: 42s\n\n"
            "View deployment: https://vercel.com/strike-security/guardia-frontend/deployments\n\n"
            "Vercel Inc."
        ),
        "urls": [
            "https://guardia.strike.sh",
            "https://vercel.com/strike-security/guardia-frontend/deployments",
        ],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<notifications@vercel.com>"},
    },
    {
        "message_id": "<extra2-legit-slack-014@slack.com>",
        "sender_email": "notification@slack.com",
        "sender_name": "Slack",
        "recipient_email": "analyst@strike.sh",
        "subject": "New message in #security-alerts",
        "body_text": (
            "New message from @nicolas.sogliano in #security-alerts:\n\n"
            "\"Just deployed v2.1.0 of the heuristic engine. False positive rate dropped "
            "from 3.2% to 1.8%. Full report in the shared channel.\"\n\n"
            "Reply in Slack: https://strike-security.slack.com/archives/C04SECURITY/p1706556000\n\n"
            "You're receiving this because you're in #security-alerts.\n"
            "Manage notifications: https://strike-security.slack.com/account/notifications"
        ),
        "urls": [
            "https://strike-security.slack.com/archives/C04SECURITY/p1706556000",
            "https://strike-security.slack.com/account/notifications",
        ],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<notification@slack.com>"},
    },
    {
        "message_id": "<extra2-legit-sentry-015@sentry.io>",
        "sender_email": "noreply@md.getsentry.com",
        "sender_name": "Sentry",
        "recipient_email": "analyst@strike.sh",
        "subject": "[Guard-IA] TimeoutError: ML inference exceeded 15s",
        "body_text": (
            "New issue in guardia-backend:\n\n"
            "TimeoutError: ML inference exceeded 15s\n"
            "app/services/pipeline/ml_classifier.py in predict, line 89\n\n"
            "This issue has occurred 3 times in the last hour.\n"
            "First seen: 2 hours ago\n"
            "Last seen: 5 minutes ago\n\n"
            "View issue: https://strike-security.sentry.io/issues/4829100\n\n"
            "Sentry — Error tracking that helps developers fix bugs faster."
        ),
        "urls": ["https://strike-security.sentry.io/issues/4829100"],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<noreply@md.getsentry.com>"},
    },
    # ── Ambiguous / Edge Cases ──
    {
        "message_id": "<extra2-ambig-vendor-016@trusted-vendor.com>",
        "sender_email": "contracts@trusted-vendor.com",
        "sender_name": "Ana Torres — Legal",
        "reply_to": "ana.torres@trusted-vendor.com",
        "recipient_email": "analyst@strike.sh",
        "subject": "RE: Service Agreement Renewal — Updated terms attached",
        "body_text": (
            "Hi Strike Security team,\n\n"
            "Following up on our call yesterday, I've attached the updated service agreement "
            "with the revised pricing for 2026.\n\n"
            "Key changes:\n"
            "- Annual fee adjusted from $45,000 to $42,500 (5.5% reduction)\n"
            "- SLA response time improved from 4h to 2h\n"
            "- Added 24/7 support coverage\n\n"
            "Please review and sign by January 31st to lock in the rate.\n\n"
            "Best regards,\n"
            "Ana Torres\nHead of Legal\nTrusted Vendor Inc."
        ),
        "urls": [],
        "attachments": [{"filename": "Service_Agreement_2026_v2.pdf", "content_type": "application/pdf", "size": 245000}],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<contracts@trusted-vendor.com>"},
    },
    {
        "message_id": "<extra2-ambig-password-017@strike.sh>",
        "sender_email": "security@strike.sh",
        "sender_name": "Strike Security IT",
        "recipient_email": "analyst@strike.sh",
        "subject": "Password change confirmation",
        "body_text": (
            "Hello,\n\n"
            "Your Strike Security account password was changed successfully.\n\n"
            "If you did not make this change, please contact IT security immediately "
            "at security@strike.sh or call ext. 4200.\n\n"
            "Change details:\n"
            "Time: January 29, 2026 at 14:32 UTC\n"
            "IP Address: 190.64.72.118 (Montevideo, UY)\n\n"
            "IT Security Team\nStrike Security"
        ),
        "urls": [],
        "auth_results": {"spf": "softfail", "dkim": "none", "dmarc": "none"},
        "headers": {"Return-Path": "<security@strike.sh>"},
    },
    {
        "message_id": "<extra2-ambig-survey-018@surveymonkey.com>",
        "sender_email": "surveys@surveymonkey.com",
        "sender_name": "SurveyMonkey",
        "recipient_email": "analyst@strike.sh",
        "subject": "Strike Security Employee Satisfaction Survey 2026",
        "body_text": (
            "Hi,\n\n"
            "You've been invited to participate in the Strike Security Employee "
            "Satisfaction Survey.\n\n"
            "This survey takes approximately 10 minutes and your responses are anonymous.\n\n"
            "Take survey: https://www.surveymonkey.com/r/strike-2026\n\n"
            "The survey closes on February 15, 2026.\n\n"
            "Thank you for your feedback!\n"
            "HR Team — Strike Security"
        ),
        "urls": ["https://www.surveymonkey.com/r/strike-2026"],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<surveys@surveymonkey.com>"},
    },
    {
        "message_id": "<extra2-legit-gcp-019@google.com>",
        "sender_email": "cloud-noreply@google.com",
        "sender_name": "Google Cloud Platform",
        "recipient_email": "analyst@strike.sh",
        "subject": "Your GCP billing summary for January 2026",
        "body_text": (
            "Google Cloud Platform — Billing Summary\n\n"
            "Account: Strike Security (guardia-prod)\n"
            "Billing period: January 1-29, 2026\n\n"
            "Current charges: $1,247.83\n"
            "- Compute Engine: $892.10\n"
            "- Cloud SQL: $198.40\n"
            "- Cloud Run: $87.33\n"
            "- Cloud Storage: $42.00\n"
            "- Other: $28.00\n\n"
            "View billing: https://console.cloud.google.com/billing\n\n"
            "Google Cloud Platform"
        ),
        "urls": ["https://console.cloud.google.com/billing"],
        "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        "headers": {"Return-Path": "<cloud-noreply@google.com>"},
    },
    {
        "message_id": "<extra2-phish-teams-020@micros0ft-teams.com>",
        "sender_email": "teams@micros0ft-teams.com",
        "sender_name": "Microsoft Teams",
        "recipient_email": "analyst@strike.sh",
        "subject": "You have 3 missed messages from Martin Garcia (CEO)",
        "body_text": (
            "You have 3 new missed messages.\n\n"
            "Martin Garcia (CEO) sent you a message:\n"
            "\"Hey, are you available? I need to discuss something urgent and confidential. "
            "Can't use Teams right now, please reply to my personal email: "
            "martin.g.ceo@gmail.com\"\n\n"
            "View messages: https://micros0ft-teams.com/chat/1/messages\n\n"
            "You're receiving this because you're a member of Strike Security.\n"
            "Microsoft Teams — Be together, even when you're apart."
        ),
        "urls": ["https://micros0ft-teams.com/chat/1/messages"],
        "auth_results": {"spf": "fail", "dkim": "fail", "dmarc": "fail"},
        "headers": {"Return-Path": "<teams@micros0ft-teams.com>"},
    },
]


async def seed():
    """Insert 20 extra emails and run the pipeline on each."""
    print(f"\n{'='*70}")
    print("  Guard-IA — 20 EXTRA emails (IDs > 20)")
    print(f"  DB: {settings.database_url[:50]}...")
    print(f"  ML enabled: {settings.pipeline_ml_enabled}")
    print(f"  OpenAI model: {settings.openai_model}")
    print(f"{'='*70}\n")

    total = len(EMAILS)
    results = []

    for i, email_data in enumerate(EMAILS, 1):
        subject = email_data.get("subject", "(no subject)")[:65]
        sender = email_data.get("sender_email", "unknown")
        print(f"[{i:2d}/{total}] {sender}")
        print(f"         Subject: {subject}")

        start = time.monotonic()

        async with get_standalone_session() as db:
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

            orchestrator = PipelineOrchestrator(db)
            try:
                result = await orchestrator.analyze(email_record.id)
                elapsed = int((time.monotonic() - start) * 1000)

                ml_info = ""
                if result.ml.model_available:
                    ml_info = f" | ML: {result.ml.score:.2f}"

                llm_info = ""
                if result.llm.provider:
                    llm_info = f" | LLM: {result.llm.score:.2f} ({result.llm.provider})"

                print(
                    f"         Score: {result.final_score:.4f} | "
                    f"Verdict: {result.verdict:<12s} | "
                    f"Risk: {result.risk_level:<8s} | "
                    f"Time: {elapsed}ms{ml_info}{llm_info}"
                )

                results.append({
                    "subject": subject,
                    "score": result.final_score,
                    "verdict": result.verdict,
                    "risk": result.risk_level,
                    "duration_ms": elapsed,
                })
            except Exception as exc:
                print(f"         ERROR: {exc}")
                results.append({
                    "subject": subject,
                    "score": -1,
                    "verdict": "ERROR",
                    "risk": "ERROR",
                    "duration_ms": 0,
                })

        print()

    # Summary
    print(f"\n{'='*70}")
    print("  SUMMARY — 20 Extra Emails")
    print(f"{'='*70}")
    allowed = sum(1 for r in results if r["verdict"] == "allowed")
    warned = sum(1 for r in results if r["verdict"] == "warned")
    quarantined = sum(1 for r in results if r["verdict"] == "quarantined")
    blocked = sum(1 for r in results if r["verdict"] == "blocked")
    errors = sum(1 for r in results if r["verdict"] == "ERROR")
    print(f"  Allowed: {allowed} | Warned: {warned} | Quarantined: {quarantined} | Blocked: {blocked} | Errors: {errors}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(seed())
