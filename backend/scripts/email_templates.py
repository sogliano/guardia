"""Realistic email templates for Guard-IA pipeline simulation.

Each template generates a complete RFC 5322 email with realistic headers,
including Authentication-Results (SPF/DKIM/DMARC) that the heuristic
engine parses.

Production flow (Google Workspace):
  External sender → MX → Guard-IA gateway:2525 → pipeline → relay to Gmail

Local simulation:
  simulate_email.py → smtplib → Guard-IA gateway:2525 → pipeline → (no relay)
"""

from datetime import datetime, timezone
from email.message import EmailMessage
from email.policy import SMTP as SMTP_POLICY
from email.utils import format_datetime, make_msgid
from uuid import uuid4
import random


def _build_email(
    sender_name: str,
    sender_email: str,
    recipient: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    reply_to: str | None = None,
    cc: list[str] | None = None,
    auth_spf: str = "pass",
    auth_dkim: str = "pass",
    auth_dmarc: str = "pass",
    urls: list[str] | None = None,
    has_attachment: bool = False,
    attachment_name: str = "document.pdf",
) -> EmailMessage:
    """Build a fully-formed RFC 5322 EmailMessage."""
    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime.now(timezone.utc))
    msg["Message-ID"] = make_msgid(domain=sender_email.split("@")[1])
    msg["MIME-Version"] = "1.0"

    if reply_to:
        msg["Reply-To"] = reply_to
    if cc:
        msg["Cc"] = ", ".join(cc)

    # Simulate Google Workspace Authentication-Results header
    auth_header = (
        f"mx.google.com; "
        f"spf={auth_spf} (google.com: domain of {sender_email}); "
        f"dkim={auth_dkim}; "
        f"dmarc={auth_dmarc} (p=REJECT)"
    )
    msg["Authentication-Results"] = auth_header

    # X-Google headers (simulate Google Workspace)
    msg["X-Google-SMTP-Source"] = f"AGHT+{uuid4().hex[:24]}"
    msg["X-Received"] = (
        f"by 2002:a17:90a:{random.randint(1000,9999)} with SMTP id "
        f"{uuid4().hex[:8]}; {format_datetime(datetime.now(timezone.utc))}"
    )

    # Return-Path
    msg["Return-Path"] = f"<{sender_email}>"

    # Simulate Received header chain (external → Guard-IA → Google)
    msg["Received"] = (
        f"from mail.{sender_email.split('@')[1]} "
        f"(mail.{sender_email.split('@')[1]} [203.0.113.42]) "
        f"by guardia.strike.sh with ESMTPS; "
        f"{format_datetime(datetime.now(timezone.utc))}"
    )

    # User-Agent (suspicious if not legitimate)
    if auth_spf != "pass":
        msg["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    else:
        msg["User-Agent"] = "Microsoft Outlook 16.0"

    # Precedence (newsletters)
    if "newsletter" in subject.lower() or "digest" in subject.lower():
        msg["Precedence"] = "bulk"
        msg["List-Unsubscribe"] = f"<mailto:unsubscribe@{sender_email.split('@')[1]}>"

    # Inject URLs into body if provided
    if urls:
        url_section = "\n\nPlease visit: " + " ".join(urls)
        body_text += url_section
        if body_html:
            links = " ".join(f'<a href="{u}">{u}</a>' for u in urls)
            body_html += f"<p>Please visit: {links}</p>"

    if body_html:
        msg.set_content(body_text)
        msg.add_alternative(body_html, subtype="html")
    else:
        msg.set_content(body_text)

    # Simulate attachment (metadata only — no real binary payload)
    if has_attachment:
        msg.add_attachment(
            b"PK\x03\x04simulated-content",
            maintype="application",
            subtype="pdf",
            filename=attachment_name,
        )

    return msg


# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

def clean_business_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate business email — should score LOW and be ALLOWED."""
    return _build_email(
        sender_name="Carlos Rodriguez",
        sender_email="carlos.rodriguez@partnercompany.com",
        recipient=recipient,
        subject="Q4 Partnership Review — Meeting Notes",
        body_text=(
            "Hi team,\n\n"
            "Attached are the meeting notes from our Q4 partnership review. "
            "Key takeaways:\n\n"
            "1. Revenue targets exceeded by 12%\n"
            "2. New product integration on track for March\n"
            "3. Next review scheduled for January 15th\n\n"
            "Please review and let me know if you have any questions.\n\n"
            "Best regards,\n"
            "Carlos Rodriguez\n"
            "VP of Partnerships\n"
            "Partner Company Inc."
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
    )


def credential_phishing_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Credential phishing — fake Microsoft login page. Should score HIGH."""
    return _build_email(
        sender_name="Microsoft 365 Security",
        sender_email="security-alert@m1cr0s0ft-verify.com",
        recipient=recipient,
        subject="[URGENT] Unusual sign-in activity on your account",
        body_text=(
            "Dear User,\n\n"
            "We detected unusual sign-in activity on your Microsoft 365 account.\n\n"
            "Someone tried to access your account from:\n"
            "Location: Moscow, Russia\n"
            "IP Address: 185.220.101.42\n"
            "Time: Today at 3:42 AM\n\n"
            "If this wasn't you, your account may be compromised.\n"
            "Please verify your identity immediately to prevent account suspension.\n\n"
            "VERIFY YOUR ACCOUNT NOW\n\n"
            "If you don't verify within 24 hours, your account will be permanently locked.\n\n"
            "Microsoft Account Security Team"
        ),
        body_html=(
            "<div style='font-family:Segoe UI,sans-serif;max-width:600px'>"
            "<img src='https://m1cr0s0ft-verify.com/logo.png' width='120'>"
            "<h2 style='color:#d32f2f'>Unusual Sign-in Activity Detected</h2>"
            "<p>Dear User,</p>"
            "<p>We detected <strong>unusual sign-in activity</strong> on your account.</p>"
            "<table style='border-collapse:collapse;margin:16px 0'>"
            "<tr><td style='padding:4px 12px'>Location:</td><td><b>Moscow, Russia</b></td></tr>"
            "<tr><td style='padding:4px 12px'>IP Address:</td><td>185.220.101.42</td></tr>"
            "<tr><td style='padding:4px 12px'>Time:</td><td>Today at 3:42 AM</td></tr>"
            "</table>"
            "<p>If this wasn't you, verify your identity <strong>immediately</strong>.</p>"
            "<a href='https://m1cr0s0ft-verify.com/login/verify?token=abc123' "
            "style='display:inline-block;background:#0078d4;color:#fff;padding:12px 32px;"
            "border-radius:4px;text-decoration:none;font-weight:600'>"
            "Verify Your Account</a>"
            "<p style='color:#666;font-size:12px;margin-top:24px'>"
            "If you don't verify within 24 hours, your account will be permanently locked.</p>"
            "</div>"
        ),
        reply_to="no-reply@m1cr0s0ft-verify.com",
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=[
            "https://m1cr0s0ft-verify.com/login/verify?token=abc123",
            "https://bit.ly/3xFakeLink",
        ],
    )


def bec_impersonation_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Business Email Compromise — CEO impersonation. Should score HIGH."""
    return _build_email(
        sender_name="Martin Garcia - CEO",
        sender_email="martin.garcia@strikesecurlty.com",  # typosquat: 'i' → 'l'
        recipient=recipient,
        subject="Urgent wire transfer needed — confidential",
        body_text=(
            "Hi,\n\n"
            "I need you to process an urgent wire transfer today. "
            "This is time-sensitive and confidential — please don't discuss "
            "with anyone else until it's completed.\n\n"
            "Amount: $47,500 USD\n"
            "Beneficiary: Global Partners LLC\n"
            "Account: 4829-3847-2910\n"
            "Bank: First International Bank, Cayman Islands\n"
            "Reference: INV-2025-CONF\n\n"
            "Please confirm once the transfer is initiated. "
            "I'm in meetings all day so email is best.\n\n"
            "Thanks,\n"
            "Martin"
        ),
        reply_to="martin.garcia.private@gmail.com",
        auth_spf="softfail",
        auth_dkim="fail",
        auth_dmarc="fail",
    )


def malware_payload_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Email with suspicious attachment — malware vector. Should score HIGH."""
    return _build_email(
        sender_name="Shipping Department",
        sender_email="shipping@fedex-tracking-update.com",
        recipient=recipient,
        subject="Your package delivery has been delayed — Action Required",
        body_text=(
            "Dear Customer,\n\n"
            "Your FedEx package (Tracking #: 7489-2839-4721) has been delayed "
            "due to an incorrect delivery address.\n\n"
            "Please download and review the attached shipping label to confirm "
            "your address details. You must respond within 48 hours or your "
            "package will be returned to sender.\n\n"
            "Download your updated shipping label from the attachment.\n\n"
            "FedEx Customer Service"
        ),
        auth_spf="fail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://fedex-tracking-update.com/label/download?id=7489"],
        has_attachment=True,
        attachment_name="shipping_label_update.pdf.exe",
    )


def spear_phishing_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Spear phishing targeting the company. Should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="IT Support",
        sender_email="helpdesk@strikesecurity-it.com",  # lookalike domain
        recipient=recipient,
        subject="Password expiration notice — Reset required today",
        body_text=(
            "Hello,\n\n"
            "Your Strike Security network password will expire in 2 hours.\n\n"
            "To avoid being locked out of your account, please reset your "
            "password immediately using the secure link below:\n\n"
            "Reset Password: https://strikesecurity-it.com/reset-password\n\n"
            "This is an automated message from the IT department.\n"
            "If you did not request this, please contact IT support at ext. 4200.\n\n"
            "IT Support Team\n"
            "Strike Security"
        ),
        auth_spf="softfail",
        auth_dkim="none",
        auth_dmarc="none",
        urls=["https://strikesecurity-it.com/reset-password?uid=82918"],
    )


def newsletter_legitimate(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate newsletter/marketing — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="The Hacker News",
        sender_email="newsletter@thehackernews.com",
        recipient=recipient,
        subject="THN Weekly Digest: Top Cybersecurity Stories This Week",
        body_text=(
            "The Hacker News — Weekly Digest\n\n"
            "Top Stories This Week:\n\n"
            "1. Critical Vulnerability Found in Popular VPN Software\n"
            "2. New Ransomware Group Targets Healthcare Sector\n"
            "3. Google Patches Zero-Day Chrome Vulnerability\n"
            "4. FBI Warns of Increasing BEC Attacks\n"
            "5. Open Source Tool Detects Supply Chain Attacks\n\n"
            "Read more at https://thehackernews.com\n\n"
            "You're receiving this because you subscribed to THN Weekly.\n"
            "Unsubscribe: https://thehackernews.com/unsubscribe"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://thehackernews.com",
            "https://thehackernews.com/unsubscribe",
        ],
    )


# ---------------------------------------------------------------------------
# Wave 2 templates (10 new scenarios)
# ---------------------------------------------------------------------------

def payroll_bec_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """BEC targeting payroll/HR — bank change request. Should score HIGH."""
    return _build_email(
        sender_name="Sofia Martinez",
        sender_email="sofia.martinez@strike-security.net",  # lookalike domain
        recipient=recipient,
        subject="Update my direct deposit information",
        body_text=(
            "Hi HR team,\n\n"
            "I recently changed banks and need to update my direct deposit "
            "information before the next payroll cycle.\n\n"
            "New bank details:\n"
            "Bank: Chase\n"
            "Routing: 021000021\n"
            "Account: 893-284-1920\n"
            "Account type: Checking\n\n"
            "Can you please process this change as soon as possible? "
            "I don't want to miss the next pay period.\n\n"
            "Thanks,\n"
            "Sofia Martinez\n"
            "Engineering Team"
        ),
        reply_to="sofia.m.private@protonmail.com",
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
    )


def invoice_fraud_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake invoice / payment fraud. Should score HIGH."""
    return _build_email(
        sender_name="Accounts Payable",
        sender_email="ap@vendor-invoices-portal.com",
        recipient=recipient,
        subject="OVERDUE: Invoice #INV-20260089 — Payment Required Immediately",
        body_text=(
            "URGENT — OVERDUE INVOICE\n\n"
            "Dear Accounts Payable,\n\n"
            "This is a final reminder that Invoice #INV-20260089 for $23,750.00 "
            "is now 15 days overdue.\n\n"
            "Failure to remit payment within 24 hours will result in late fees "
            "and potential service suspension.\n\n"
            "Pay now: https://vendor-invoices-portal.com/pay/INV-20260089\n\n"
            "Wire transfer details:\n"
            "Beneficiary: Global Services LLC\n"
            "Account: 7382-4920-1847\n"
            "SWIFT: GBLSUS33\n\n"
            "Please confirm payment immediately.\n\n"
            "Accounts Payable Department\n"
            "Global Services LLC"
        ),
        auth_spf="fail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://vendor-invoices-portal.com/pay/INV-20260089"],
    )


def qr_code_phishing_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """QR code phishing (quishing) — fake MFA setup. Should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Strike Security IT",
        sender_email="it-admin@strikesecurlty.com",  # typosquat: i→l
        recipient=recipient,
        subject="Mandatory: Multi-Factor Authentication Enrollment Required",
        body_text=(
            "Hello,\n\n"
            "As part of our new security policy, all employees must enroll "
            "in Multi-Factor Authentication (MFA) by end of day.\n\n"
            "Please scan the QR code in the attached document or visit the link "
            "below to complete enrollment:\n\n"
            "https://strikesecurlty.com/mfa/enroll?user=auto\n\n"
            "If you do not complete enrollment by 5:00 PM today, your account "
            "will be temporarily suspended.\n\n"
            "IT Security Team"
        ),
        auth_spf="softfail",
        auth_dkim="fail",
        auth_dmarc="none",
        urls=["https://strikesecurlty.com/mfa/enroll?user=auto"],
        has_attachment=True,
        attachment_name="MFA_Setup_Instructions.pdf",
    )


def legitimate_github_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate GitHub notification — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="GitHub",
        sender_email="notifications@github.com",
        recipient=recipient,
        subject="[guardia] Pull request #47: Add ML pipeline confidence thresholds",
        body_text=(
            "@nicolas-sogliano requested your review on pull request #47.\n\n"
            "Add ML pipeline confidence thresholds\n\n"
            "This PR introduces configurable confidence thresholds for the "
            "DistilBERT classifier. Changes:\n\n"
            "- Added threshold_ml_confidence to config.py\n"
            "- Updated orchestrator to skip ML when confidence < threshold\n"
            "- Added 4 new unit tests\n\n"
            "Files changed: 3\n"
            "Lines: +87 -12\n\n"
            "View pull request:\n"
            "https://github.com/strike-security/guardia/pull/47\n\n"
            "---\n"
            "You are receiving this because you were requested for review.\n"
            "Unsubscribe: https://github.com/notifications/unsubscribe/abc123"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://github.com/strike-security/guardia/pull/47",
            "https://github.com/notifications/unsubscribe/abc123",
        ],
    )


def crypto_scam_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Crypto/investment scam — should score HIGH."""
    return _build_email(
        sender_name="Binance Security",
        sender_email="alert@binance-wallet-verify.xyz",
        recipient=recipient,
        subject="ACTION REQUIRED: Unauthorized withdrawal detected on your wallet",
        body_text=(
            "SECURITY ALERT\n\n"
            "An unauthorized withdrawal of 2.4 BTC ($147,832.00) was detected "
            "from your Binance account.\n\n"
            "Transaction details:\n"
            "Amount: 2.4 BTC\n"
            "Destination: bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh\n"
            "Status: PENDING (can be cancelled within 12 hours)\n\n"
            "If you did NOT authorize this transaction, cancel it immediately:\n"
            "https://binance-wallet-verify.xyz/cancel-withdrawal\n\n"
            "DO NOT IGNORE THIS MESSAGE. Failure to respond will result in "
            "permanent loss of funds.\n\n"
            "Binance Security Team"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=[
            "https://binance-wallet-verify.xyz/cancel-withdrawal",
            "http://192.168.44.12/redirect",
        ],
    )


def legitimate_calendar_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Google Calendar invite — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Google Calendar",
        sender_email="calendar-notification@google.com",
        recipient=recipient,
        subject="Invitation: Sprint Planning — Wed Jan 29, 2026 10:00 AM",
        body_text=(
            "Sprint Planning\n\n"
            "When: Wednesday, January 29, 2026 10:00 AM - 11:00 AM (UYT)\n"
            "Where: Google Meet — https://meet.google.com/abc-defg-hij\n"
            "Calendar: nicolas.sogliano@strike.sh\n\n"
            "Organizer: martin.garcia@strike.sh\n\n"
            "Attendees:\n"
            "- nicolas.sogliano@strike.sh\n"
            "- sofia.martinez@strike.sh\n"
            "- dev-team@strike.sh\n\n"
            "Going? Yes — Maybe — No\n"
            "https://calendar.google.com/calendar/event?action=RESPOND&eid=abc123\n\n"
            "---\n"
            "Forwarding this invitation could allow any recipient to send a "
            "response to the organizer."
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://meet.google.com/abc-defg-hij",
            "https://calendar.google.com/calendar/event?action=RESPOND&eid=abc123",
        ],
    )


def tax_scam_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Tax/government impersonation scam. Should score HIGH."""
    return _build_email(
        sender_name="DGI Uruguay - Notificaciones",
        sender_email="notificaciones@dgi-uruguay-gov.com",  # fake gov domain
        recipient=recipient,
        subject="AVISO: Irregularidades detectadas en su declaracion jurada",
        body_text=(
            "DIRECCION GENERAL IMPOSITIVA\n"
            "REPUBLICA ORIENTAL DEL URUGUAY\n\n"
            "Estimado contribuyente,\n\n"
            "Se han detectado irregularidades en su declaracion jurada "
            "correspondiente al ejercicio fiscal 2025.\n\n"
            "Monto adeudado: $UY 847,320.00\n"
            "Fecha limite: 48 horas desde la recepcion de este aviso\n\n"
            "De no regularizar su situacion en el plazo indicado, se procedera "
            "a iniciar acciones legales y embargo de bienes.\n\n"
            "Para regularizar su situacion, acceda al siguiente enlace:\n"
            "https://dgi-uruguay-gov.com/regularizar?rut=auto\n\n"
            "IMPORTANTE: Este tramite es urgente e intransferible.\n\n"
            "DGI - Departamento de Fiscalizacion"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://dgi-uruguay-gov.com/regularizar?rut=auto"],
    )


def shared_doc_phishing_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake Google Docs shared document. Should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Martin Garcia via Google Drive",
        sender_email="drive-shares@g00gle-docs.com",  # fake google domain
        recipient=recipient,
        subject='Martin Garcia shared "Q1 2026 Budget Forecast" with you',
        body_text=(
            "Martin Garcia has shared a document with you.\n\n"
            "Q1 2026 Budget Forecast\n\n"
            "Martin Garcia (martin.garcia@strike.sh) has invited you to view "
            "the following document:\n\n"
            "Open in Google Docs:\n"
            "https://g00gle-docs.com/document/d/1aBcDeFgHiJkL/edit\n\n"
            "Note: This document requires you to sign in with your company "
            "Google account to view.\n\n"
            "Google Drive: Create, share, and keep all your files in one place."
        ),
        body_html=(
            "<div style='font-family:Google Sans,Roboto,sans-serif;max-width:500px;"
            "margin:0 auto;padding:24px'>"
            "<img src='https://g00gle-docs.com/images/drive-logo.png' width='40'>"
            "<h2>Martin Garcia shared a document</h2>"
            "<div style='background:#f8f9fa;border-radius:8px;padding:16px;margin:16px 0'>"
            "<p style='font-size:18px;margin:0'>Q1 2026 Budget Forecast</p>"
            "<p style='color:#5f6368;margin:4px 0'>Google Docs</p>"
            "</div>"
            "<a href='https://g00gle-docs.com/document/d/1aBcDeFgHiJkL/edit' "
            "style='display:inline-block;background:#1a73e8;color:white;padding:10px 24px;"
            "border-radius:4px;text-decoration:none;font-weight:500'>Open in Docs</a>"
            "<p style='color:#5f6368;font-size:12px;margin-top:24px'>"
            "Google LLC, 1600 Amphitheatre Parkway, Mountain View, CA 94043</p>"
            "</div>"
        ),
        auth_spf="fail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://g00gle-docs.com/document/d/1aBcDeFgHiJkL/edit"],
    )


def legitimate_aws_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate AWS billing notification — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Amazon Web Services",
        sender_email="no-reply@amazonaws.com",
        recipient=recipient,
        subject="AWS Billing: Your January 2026 invoice is available",
        body_text=(
            "Hello,\n\n"
            "Your AWS account 4829-3120-9981 invoice for January 2026 is now "
            "available.\n\n"
            "Account: 4829-3120-9981\n"
            "Period: January 1 - January 31, 2026\n"
            "Total: $342.18 USD\n\n"
            "You can view your bill and manage payment methods in the AWS "
            "Billing Console:\n"
            "https://console.aws.amazon.com/billing/home\n\n"
            "If you have questions about your bill, visit AWS Support:\n"
            "https://aws.amazon.com/support\n\n"
            "Thanks,\n"
            "Amazon Web Services"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://console.aws.amazon.com/billing/home",
            "https://aws.amazon.com/support",
        ],
    )


def supply_chain_attack_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Supply chain / vendor compromise email. Should score HIGH."""
    return _build_email(
        sender_name="Slack Support",
        sender_email="billing@slack-enterprise-upgrade.com",  # fake slack domain
        recipient=recipient,
        subject="Action needed: Your Slack Enterprise plan payment failed",
        body_text=(
            "Hi Strike Security admin,\n\n"
            "We were unable to process the payment for your Slack Enterprise Grid "
            "plan (Workspace: strike-security.slack.com).\n\n"
            "Plan: Enterprise Grid\n"
            "Amount due: $4,200.00/mo\n"
            "Next retry: Tomorrow\n\n"
            "If payment fails again, your workspace will be downgraded to the "
            "Free plan and all Enterprise features (SSO, DLP, compliance exports) "
            "will be disabled.\n\n"
            "Update your payment method now:\n"
            "https://slack-enterprise-upgrade.com/billing/update?ws=strike\n\n"
            "If you believe this is an error, contact our billing team.\n\n"
            "Slack Billing Team"
        ),
        reply_to="billing-support@slack-enterprise-upgrade.com",
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=[
            "https://slack-enterprise-upgrade.com/billing/update?ws=strike",
            "https://bit.ly/slack-billing-help",
        ],
    )


# ---------------------------------------------------------------------------
# Wave 3 templates (34 new scenarios)
# ---------------------------------------------------------------------------

# Legítimos adicionales (9)

def legitimate_slack_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Slack notification — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Slack",
        sender_email="notifications@slack.com",
        recipient=recipient,
        subject="[strike-security] New message in #engineering",
        body_text=(
            "New message in #engineering\n\n"
            "Nicolas Sogliano: @here Quick update - the ML pipeline refactor "
            "is complete. All tests passing. Ready for review.\n\n"
            "View in Slack: https://strike-security.slack.com/archives/C123/p1234567890\n\n"
            "---\n"
            "You're receiving this because you're a member of #engineering.\n"
            "Manage your notification preferences: "
            "https://strike-security.slack.com/account/notifications"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://strike-security.slack.com/archives/C123/p1234567890",
            "https://strike-security.slack.com/account/notifications",
        ],
    )


def legitimate_jira_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Jira ticket assignment — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Jira",
        sender_email="jira@strike.atlassian.net",
        recipient=recipient,
        subject="[GUARD-247] Pipeline timeout on large email attachments",
        body_text=(
            "Nicolas Sogliano assigned GUARD-247 to you\n\n"
            "Pipeline timeout on large email attachments\n\n"
            "Priority: High\n"
            "Type: Bug\n"
            "Sprint: Sprint 12\n\n"
            "Description:\n"
            "Pipeline times out when processing emails with attachments >5MB. "
            "Need to implement streaming parser or increase timeout threshold.\n\n"
            "Acceptance criteria:\n"
            "- Process 10MB attachments without timeout\n"
            "- Add integration test with large attachment\n\n"
            "View issue: https://strike.atlassian.net/browse/GUARD-247\n\n"
            "---\n"
            "This message was sent by Atlassian Jira"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://strike.atlassian.net/browse/GUARD-247"],
    )


def legitimate_confluence_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Confluence page shared — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Confluence",
        sender_email="confluence@strike.atlassian.net",
        recipient=recipient,
        subject="Martin Garcia shared 'Q1 2026 Roadmap' with you",
        body_text=(
            "Martin Garcia shared a page with you\n\n"
            "Q1 2026 Roadmap\n\n"
            "Space: Engineering\n"
            "Last updated: Today at 9:42 AM\n\n"
            "Preview:\n"
            "Our Q1 priorities focus on three key areas:\n"
            "1. ML model accuracy improvements (target: 95% precision)\n"
            "2. Dashboard UX redesign\n"
            "3. Multi-tenancy preparation\n\n"
            "View page: https://strike.atlassian.net/wiki/spaces/ENG/pages/123456\n\n"
            "---\n"
            "Manage your notifications: "
            "https://strike.atlassian.net/wiki/settings/notifications"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://strike.atlassian.net/wiki/spaces/ENG/pages/123456",
            "https://strike.atlassian.net/wiki/settings/notifications",
        ],
    )


def legitimate_linkedin_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate LinkedIn connection request — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="LinkedIn",
        sender_email="notifications@linkedin.com",
        recipient=recipient,
        subject="Ana Rodriguez wants to connect on LinkedIn",
        body_text=(
            "Ana Rodriguez\n"
            "Security Engineer at Google\n\n"
            "I'd like to add you to my professional network on LinkedIn.\n\n"
            "View invitation:\n"
            "https://www.linkedin.com/comm/mynetwork/discovery-see-all?"
            "usecase=PEOPLE_FOLLOWS&followMember=ana-rodriguez\n\n"
            "---\n"
            "You're receiving this email because Ana Rodriguez invited you to "
            "connect on LinkedIn.\n\n"
            "Unsubscribe: https://www.linkedin.com/e/v2?e=abc123"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://www.linkedin.com/comm/mynetwork/discovery-see-all?usecase=PEOPLE_FOLLOWS&followMember=ana-rodriguez",
            "https://www.linkedin.com/e/v2?e=abc123",
        ],
    )


def legitimate_docusign_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate DocuSign document ready — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="DocuSign",
        sender_email="dse@docusign.net",
        recipient=recipient,
        subject="Please DocuSign: NDA - Strike Security Partnership Agreement",
        body_text=(
            "Please DocuSign: NDA - Strike Security Partnership Agreement\n\n"
            "Martin Garcia (martin.garcia@strike.sh) has sent you a document to "
            "review and sign.\n\n"
            "Document: NDA - Strike Security Partnership Agreement\n"
            "Due date: February 8, 2026\n\n"
            "Review and sign:\n"
            "https://www.docusign.net/Member/PowerFormSigning.aspx?PowerFormId=abc123\n\n"
            "---\n"
            "DocuSign, Inc.\n"
            "221 Main Street, Suite 1000\n"
            "San Francisco, CA 94105"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://www.docusign.net/Member/PowerFormSigning.aspx?PowerFormId=abc123"],
    )


def legitimate_zoom_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Zoom meeting invitation — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Zoom",
        sender_email="no-reply@zoom.us",
        recipient=recipient,
        subject="Invitation: Client Demo - Feb 5, 2026 @ 3:00 PM (UYT)",
        body_text=(
            "You are invited to a scheduled Zoom meeting.\n\n"
            "Topic: Client Demo - Guard-IA Platform\n"
            "Time: Feb 5, 2026 03:00 PM Montevideo\n"
            "Duration: 1 hour\n\n"
            "Join Zoom Meeting:\n"
            "https://us02web.zoom.us/j/1234567890?pwd=abcdef123456\n\n"
            "Meeting ID: 123 456 7890\n"
            "Passcode: 847291\n\n"
            "One tap mobile:\n"
            "+1 646 558 8656,,1234567890#,,,,*847291# US (New York)\n\n"
            "---\n"
            "Zoom Communications, Inc."
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://us02web.zoom.us/j/1234567890?pwd=abcdef123456"],
    )


def legitimate_salesforce_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Salesforce lead notification — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Salesforce",
        sender_email="lead-notification@salesforce.com",
        recipient=recipient,
        subject="New lead assigned: TechCorp - Enterprise Security",
        body_text=(
            "New lead assigned to you\n\n"
            "Lead: TechCorp - Enterprise Security\n"
            "Company: TechCorp International\n"
            "Contact: Sarah Johnson\n"
            "Email: sarah.johnson@techcorp.com\n"
            "Phone: +1 (555) 123-4567\n"
            "Lead source: Website demo request\n"
            "Status: New\n\n"
            "Notes:\n"
            "Interested in enterprise email security solution for 500+ employees. "
            "Looking for phishing detection and BEC prevention. Budget approved.\n\n"
            "View lead in Salesforce:\n"
            "https://strike.lightning.force.com/lightning/r/Lead/00Q123456789/view\n\n"
            "---\n"
            "Salesforce.com, Inc."
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://strike.lightning.force.com/lightning/r/Lead/00Q123456789/view"],
    )


def legitimate_stripe_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate Stripe payment receipt — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Stripe",
        sender_email="receipts@stripe.com",
        recipient=recipient,
        subject="Receipt from Strike Security [Receipt #1234-5678]",
        body_text=(
            "Receipt from Strike Security\n\n"
            "Amount paid: $299.00 USD\n"
            "Date paid: February 1, 2026\n"
            "Payment method: Visa ending in 4242\n\n"
            "DESCRIPTION                    AMOUNT\n"
            "Monthly subscription            $299.00\n"
            "Guard-IA Enterprise Plan\n"
            "February 1 - March 1, 2026\n\n"
            "Total: $299.00 USD\n\n"
            "View receipt online:\n"
            "https://invoice.stripe.com/i/acct_123/inv_abc123\n\n"
            "Questions about your receipt? Contact Strike Security at "
            "billing@strike.sh\n\n"
            "---\n"
            "Stripe, Inc.\n"
            "510 Townsend Street, San Francisco, CA 94103"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://invoice.stripe.com/i/acct_123/inv_abc123"],
    )


def legitimate_hubspot_notification(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legitimate HubSpot email notification — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="HubSpot",
        sender_email="notifications@hubspot.com",
        recipient=recipient,
        subject="New form submission: Contact Us - Guard-IA Demo Request",
        body_text=(
            "New form submission\n\n"
            "Form: Contact Us - Guard-IA Demo Request\n"
            "Submitted: Today at 10:23 AM\n\n"
            "Submission details:\n"
            "Name: Carlos Martinez\n"
            "Email: carlos.martinez@globalcorp.com\n"
            "Company: Global Corp\n"
            "Phone: +598 99 123 456\n"
            "Message: Interested in scheduling a demo of Guard-IA for our team. "
            "We're looking for a solution to prevent phishing attacks.\n\n"
            "View submission:\n"
            "https://app.hubspot.com/contacts/123456/contact/789012\n\n"
            "---\n"
            "HubSpot, Inc.\n"
            "25 First Street, Cambridge, MA 02141"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://app.hubspot.com/contacts/123456/contact/789012"],
    )


# Phishing Credenciales adicionales (6)

def fake_apple_phishing(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake Apple ID verification — should score HIGH."""
    return _build_email(
        sender_name="Apple",
        sender_email="no-reply@app1e-id-verify.com",
        recipient=recipient,
        subject="Your Apple ID has been locked",
        body_text=(
            "Dear Apple Customer,\n\n"
            "Your Apple ID has been locked for security reasons.\n\n"
            "We detected suspicious activity on your account:\n"
            "- Failed sign-in attempt from unknown device\n"
            "- Location: Shanghai, China\n"
            "- Device: Unknown Android device\n\n"
            "To unlock your account, verify your identity immediately:\n"
            "https://app1e-id-verify.com/unlock?id=auto\n\n"
            "If you don't verify within 24 hours, your account will be "
            "permanently disabled and all purchases will be lost.\n\n"
            "Apple Support Team"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://app1e-id-verify.com/unlock?id=auto"],
    )


def fake_google_workspace_phishing(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake Google Workspace admin alert — should score HIGH."""
    return _build_email(
        sender_name="Google Workspace Admin",
        sender_email="admin-alert@g00gleworkspace.com",
        recipient=recipient,
        subject="Action required: Admin privileges will be revoked",
        body_text=(
            "Important notice from Google Workspace\n\n"
            "Your administrator privileges for strike.sh domain will be "
            "revoked in 24 hours due to security policy violations.\n\n"
            "Violations detected:\n"
            "- Unauthorized API access\n"
            "- Suspicious login patterns\n"
            "- Failed 2FA attempts\n\n"
            "To maintain your admin access, verify your identity:\n"
            "https://g00gleworkspace.com/admin/verify?domain=strike.sh\n\n"
            "This is an automated security measure to protect your organization.\n\n"
            "Google Workspace Security Team"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://g00gleworkspace.com/admin/verify?domain=strike.sh"],
    )


def fake_office365_storage_phishing(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake Office 365 storage full — should score HIGH."""
    return _build_email(
        sender_name="Microsoft 365",
        sender_email="storage-alert@0ffice365-cloud.com",
        recipient=recipient,
        subject="Your mailbox is full — Emails are being rejected",
        body_text=(
            "Your Microsoft 365 mailbox is full\n\n"
            "Your mailbox has exceeded its storage limit (50 GB).\n\n"
            "Current usage: 50.2 GB / 50 GB\n\n"
            "Incoming emails are currently being rejected. To restore email "
            "service, you must:\n\n"
            "1. Delete old emails, or\n"
            "2. Upgrade your storage plan\n\n"
            "Upgrade storage now:\n"
            "https://0ffice365-cloud.com/upgrade-storage?user=auto\n\n"
            "If you don't take action within 6 hours, your account will be "
            "suspended.\n\n"
            "Microsoft 365 Support"
        ),
        auth_spf="fail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://0ffice365-cloud.com/upgrade-storage?user=auto"],
    )


def fake_dropbox_phishing(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake Dropbox file shared — should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Dropbox",
        sender_email="no-reply@dr0pbox-files.com",
        recipient=recipient,
        subject="Carlos Rodriguez shared 'Contract_Q1_2026.pdf' with you",
        body_text=(
            "Carlos Rodriguez shared a file with you\n\n"
            "Contract_Q1_2026.pdf\n"
            "Size: 2.4 MB\n\n"
            "Carlos Rodriguez (carlos.rodriguez@partnercompany.com) shared a "
            "document with you on Dropbox.\n\n"
            "View file:\n"
            "https://dr0pbox-files.com/sh/abc123/Contract_Q1_2026.pdf\n\n"
            "Note: You need to sign in to view this file.\n\n"
            "Dropbox"
        ),
        auth_spf="softfail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://dr0pbox-files.com/sh/abc123/Contract_Q1_2026.pdf"],
    )


def fake_linkedin_security_phishing(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake LinkedIn security alert — should score HIGH."""
    return _build_email(
        sender_name="LinkedIn Security",
        sender_email="security@linkedin-account-verify.net",
        recipient=recipient,
        subject="Unusual activity detected on your LinkedIn account",
        body_text=(
            "LinkedIn Security Alert\n\n"
            "We detected unusual activity on your LinkedIn account:\n\n"
            "- Location: Lagos, Nigeria\n"
            "- IP: 197.210.55.78\n"
            "- Time: Today at 4:32 AM\n"
            "- Action: Profile data download requested\n\n"
            "If this wasn't you, secure your account immediately:\n"
            "https://linkedin-account-verify.net/secure?token=abc123\n\n"
            "Failure to verify within 12 hours may result in:\n"
            "- Account suspension\n"
            "- Loss of connections and messages\n"
            "- Permanent data loss\n\n"
            "LinkedIn Trust & Safety Team"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://linkedin-account-verify.net/secure?token=abc123"],
    )


def fake_paypal_phishing(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake PayPal payment issue — should score HIGH."""
    return _build_email(
        sender_name="PayPal",
        sender_email="service@paypa1-resolution.com",
        recipient=recipient,
        subject="Action Required: Unusual payment activity detected",
        body_text=(
            "PayPal Security Alert\n\n"
            "We've detected unusual payment activity on your PayPal account.\n\n"
            "Transaction details:\n"
            "Amount: $847.99 USD\n"
            "Merchant: ElectronicsGlobal\n"
            "Status: PENDING REVIEW\n\n"
            "If you did NOT authorize this payment, cancel it immediately:\n"
            "https://paypa1-resolution.com/dispute/cancel?tx=ABC123\n\n"
            "If we don't hear from you within 6 hours, the payment will be "
            "processed and funds will be transferred.\n\n"
            "PayPal Customer Service"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://paypa1-resolution.com/dispute/cancel?tx=ABC123"],
    )


# BEC/Impersonation adicionales (4)

def cfo_urgent_bec(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """CFO urgent request — should score HIGH."""
    return _build_email(
        sender_name="Patricia Lopez - CFO",
        sender_email="patricia.lopez@strike-sec.com",
        recipient=recipient,
        subject="URGENT: Vendor payment - wire transfer needed today",
        body_text=(
            "Hi,\n\n"
            "I need you to process an urgent wire transfer today for a vendor payment. "
            "This is time-sensitive as we risk losing the contract.\n\n"
            "Payment details:\n"
            "Beneficiary: Tech Solutions Global Ltd\n"
            "Amount: $127,500.00 USD\n"
            "Bank: HSBC Hong Kong\n"
            "Account: HK-2893-8472-1920\n"
            "SWIFT: HSBCHKHH\n"
            "Reference: INV-Q1-2026-URGENT\n\n"
            "Please process immediately and confirm. I'm traveling today so "
            "email is the best way to reach me.\n\n"
            "Thanks,\n"
            "Patricia Lopez\n"
            "CFO, Strike Security"
        ),
        reply_to="p.lopez.external@gmail.com",
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
    )


def vendor_payment_change_bec(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Vendor payment change request — should score HIGH."""
    return _build_email(
        sender_name="Carlos Rodriguez",
        sender_email="carlos.rodriguez@partnercompany.co",
        recipient=recipient,
        subject="Updated payment information for Invoice #2026-Q1-089",
        body_text=(
            "Hi Finance Team,\n\n"
            "We've recently updated our banking information. Please use the "
            "following details for all future payments:\n\n"
            "Company: Partner Company Inc.\n"
            "New bank: First Atlantic Bank\n"
            "Account name: Partner Company International\n"
            "Account number: 4829-3847-2910\n"
            "Routing: 026009593\n"
            "SWIFT: FABUS33\n\n"
            "Please update your records and use this information for the pending "
            "Invoice #2026-Q1-089 ($45,200.00).\n\n"
            "Thanks for your cooperation.\n\n"
            "Best regards,\n"
            "Carlos Rodriguez\n"
            "VP of Partnerships"
        ),
        reply_to="c.rodriguez.temp@protonmail.com",
        auth_spf="softfail",
        auth_dkim="fail",
        auth_dmarc="fail",
    )


def executive_gift_card_bec(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Executive gift card request — should score HIGH."""
    return _build_email(
        sender_name="Martin Garcia",
        sender_email="m.garcia@strikesecurlty.com",
        recipient=recipient,
        subject="Quick favor needed",
        body_text=(
            "Hi,\n\n"
            "I need a quick favor. Can you purchase 10x $100 Amazon gift cards "
            "for me? They're for employee appreciation gifts and I need them "
            "today for our team meeting.\n\n"
            "Total: $1,000\n\n"
            "Please buy them online and email me the codes ASAP. I'll reimburse "
            "you immediately.\n\n"
            "I'm in back-to-back meetings all day so email is best.\n\n"
            "Thanks!\n"
            "Martin"
        ),
        reply_to="martin.g.personal@gmail.com",
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
    )


def legal_urgent_signature_bec(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Legal department urgent signature — should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Legal Department",
        sender_email="legal@strike-security.net",
        recipient=recipient,
        subject="URGENT: Signature required for partnership agreement",
        body_text=(
            "Dear Executive Team,\n\n"
            "We need your immediate signature on the attached partnership "
            "agreement. The client requires executed documents by end of day "
            "or the deal will be cancelled.\n\n"
            "Agreement: Strategic Partnership - TechCorp International\n"
            "Value: $2.5M over 3 years\n"
            "Deadline: Today, 5:00 PM\n\n"
            "Please review and sign electronically:\n"
            "https://strike-security.net/legal/sign?doc=partnership-2026-01\n\n"
            "If you have questions, call the legal team immediately at ext. 5100.\n\n"
            "Legal Department\n"
            "Strike Security"
        ),
        auth_spf="softfail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://strike-security.net/legal/sign?doc=partnership-2026-01"],
    )


# Malware/Attachments adicionales (4)

def fake_irs_refund_malware(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake IRS tax refund — should score HIGH."""
    return _build_email(
        sender_name="IRS Tax Refund",
        sender_email="refund@irs-treasury-gov.com",
        recipient=recipient,
        subject="Tax Refund Notification - $1,847.00 Approved",
        body_text=(
            "Internal Revenue Service\n"
            "United States Department of the Treasury\n\n"
            "Tax Refund Approved\n\n"
            "Taxpayer: [Your Name]\n"
            "Tax Year: 2025\n"
            "Refund Amount: $1,847.00\n"
            "Status: APPROVED - Action Required\n\n"
            "Your federal tax refund has been approved. To receive your refund, "
            "you must complete the attached verification form.\n\n"
            "Download and complete: IRS_Refund_Verification_Form.pdf\n\n"
            "Submit the form within 48 hours to avoid processing delays.\n\n"
            "IRS Refund Processing Department\n"
            "www.irs.gov"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://irs-treasury-gov.com/refund/verify?id=auto"],
        has_attachment=True,
        attachment_name="IRS_Refund_Verification_Form.pdf.exe",
    )


def fake_ups_delivery_malware(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake UPS delivery notification — should score HIGH."""
    return _build_email(
        sender_name="UPS Delivery",
        sender_email="delivery@ups-tracking-service.com",
        recipient=recipient,
        subject="UPS Delivery Failed - Rescheduling Required",
        body_text=(
            "UPS Delivery Notification\n\n"
            "We attempted to deliver your package but no one was available.\n\n"
            "Tracking: 1Z999AA10123456784\n"
            "Delivery attempts: 2\n"
            "Status: DELIVERY FAILED\n\n"
            "Your package will be returned to sender unless you reschedule "
            "delivery within 24 hours.\n\n"
            "To reschedule, download and print the attached delivery authorization:\n"
            "UPS_Delivery_Authorization.pdf\n\n"
            "Or reschedule online:\n"
            "https://ups-tracking-service.com/reschedule?pkg=1Z999AA10123456784\n\n"
            "UPS Customer Service"
        ),
        auth_spf="fail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://ups-tracking-service.com/reschedule?pkg=1Z999AA10123456784"],
        has_attachment=True,
        attachment_name="UPS_Delivery_Authorization.pdf.exe",
    )


def fake_voicemail_malware(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake voicemail notification — should score HIGH."""
    return _build_email(
        sender_name="Voicemail System",
        sender_email="voicemail@strike-pbx-system.com",
        recipient=recipient,
        subject="New voicemail from +1 (555) 847-2910",
        body_text=(
            "You have 1 new voicemail message\n\n"
            "From: +1 (555) 847-2910\n"
            "Duration: 1:23\n"
            "Received: Today at 9:42 AM\n"
            "Priority: HIGH\n\n"
            "To listen to your voicemail, download the attached audio file:\n"
            "Voicemail_555-847-2910.mp3\n\n"
            "Or listen online:\n"
            "https://strike-pbx-system.com/voicemail/play?id=vm_82910\n\n"
            "Strike Security PBX System"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://strike-pbx-system.com/voicemail/play?id=vm_82910"],
        has_attachment=True,
        attachment_name="Voicemail_555-847-2910.mp3.exe",
    )


def fake_scanner_document_malware(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake scanned document from copier — should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Office Copier",
        sender_email="scanner@copier.strike.local",
        recipient=recipient,
        subject="Scanned document from MFP-Floor3-Copier01",
        body_text=(
            "Scanned Document\n\n"
            "From: MFP-Floor3-Copier01\n"
            "Pages: 8\n"
            "Resolution: 300 DPI\n"
            "Format: PDF\n"
            "Date: February 1, 2026 10:15 AM\n\n"
            "Document scanned by: Unknown User\n\n"
            "Attached: Scanned_Document_20260201_101523.pdf\n\n"
            "This is an automated message from the office multifunction printer.\n"
        ),
        auth_spf="softfail",
        auth_dkim="none",
        auth_dmarc="none",
        has_attachment=True,
        attachment_name="Scanned_Document_20260201_101523.pdf.exe",
    )


# Scams adicionales (3)

def romance_scam_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Romance scam — should score HIGH."""
    return _build_email(
        sender_name="Jennifer Thompson",
        sender_email="jennifer.thompson.usa@gmail.com",
        recipient=recipient,
        subject="Hello from Jennifer - I saw your profile",
        body_text=(
            "Hello,\n\n"
            "My name is Jennifer Thompson. I'm a 34-year-old nurse from Texas. "
            "I came across your profile and felt a connection.\n\n"
            "I'm currently working overseas in Syria helping refugees. It's "
            "rewarding work but very lonely here.\n\n"
            "I'd love to get to know you better. Would you be interested in "
            "chatting? You can see my photos here:\n"
            "https://jennifer-photos-gallery.com/album/jt2026\n\n"
            "I hope to hear from you soon.\n\n"
            "Warmly,\n"
            "Jennifer"
        ),
        auth_spf="softfail",
        auth_dkim="none",
        auth_dmarc="none",
        urls=["https://jennifer-photos-gallery.com/album/jt2026"],
    )


def job_offer_scam_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Job offer scam — should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Sarah Mitchell - Recruitment",
        sender_email="recruitment@google-careers-hiring.com",
        recipient=recipient,
        subject="Job Offer: Senior Security Engineer at Google - $240K/year",
        body_text=(
            "Dear Candidate,\n\n"
            "Congratulations! After reviewing your LinkedIn profile, we'd like "
            "to offer you a position at Google.\n\n"
            "Position: Senior Security Engineer\n"
            "Location: Remote (US-based)\n"
            "Salary: $240,000/year + stock options\n"
            "Benefits: Full health, 401k, unlimited PTO\n\n"
            "This is a limited-time offer. To accept, complete the online "
            "background check form (requires $150 processing fee, refundable "
            "on first paycheck):\n\n"
            "https://google-careers-hiring.com/offer-accept?id=GCS2026089\n\n"
            "Respond within 48 hours or the offer will be withdrawn.\n\n"
            "Best regards,\n"
            "Sarah Mitchell\n"
            "Senior Recruiter, Google Inc."
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://google-careers-hiring.com/offer-accept?id=GCS2026089"],
    )


def tech_support_scam_email(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Tech support scam (fake Microsoft) — should score HIGH."""
    return _build_email(
        sender_name="Microsoft Support",
        sender_email="support@microsoft-security-center.com",
        recipient=recipient,
        subject="CRITICAL: Your computer is infected with viruses",
        body_text=(
            "MICROSOFT SECURITY ALERT\n\n"
            "Our automated monitoring system detected that your computer is "
            "infected with multiple viruses and malware.\n\n"
            "Threats detected:\n"
            "- Trojan:Win32/Malware.A\n"
            "- Ransomware.Generic\n"
            "- Keylogger.Stealer\n\n"
            "Your personal data, passwords, and banking information are at risk.\n\n"
            "IMMEDIATE ACTION REQUIRED:\n"
            "Call Microsoft Support: +1-800-FAKE-NUM\n"
            "Or visit: https://microsoft-security-center.com/support/remove-virus\n\n"
            "DO NOT ignore this warning. Failure to act will result in:\n"
            "- Identity theft\n"
            "- Financial loss\n"
            "- Permanent data loss\n\n"
            "Microsoft Security Center\n"
            "Available 24/7"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://microsoft-security-center.com/support/remove-virus"],
    )


# Spear Phishing adicionales (2)

def fake_hr_policy_spear(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake HR policy update — should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="HR Department",
        sender_email="hr@strikesecurlty.com",
        recipient=recipient,
        subject="MANDATORY: New remote work policy - Acknowledgment required",
        body_text=(
            "Dear Strike Security Team,\n\n"
            "Effective immediately, all employees must acknowledge the updated "
            "Remote Work Policy.\n\n"
            "Key changes:\n"
            "- New VPN requirements\n"
            "- Updated security protocols\n"
            "- Equipment return procedures\n\n"
            "All employees must:\n"
            "1. Review the policy document\n"
            "2. Complete the acknowledgment form\n"
            "3. Submit by February 5, 2026\n\n"
            "Failure to comply will result in revoked remote work privileges.\n\n"
            "Access policy and acknowledgment form:\n"
            "https://strikesecurlty.com/hr/remote-work-policy-2026\n\n"
            "HR Department\n"
            "Strike Security"
        ),
        auth_spf="softfail",
        auth_dkim="fail",
        auth_dmarc="none",
        urls=["https://strikesecurlty.com/hr/remote-work-policy-2026"],
    )


def fake_acquisition_spear(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Fake company acquisition announcement — should score MEDIUM-HIGH."""
    return _build_email(
        sender_name="Martin Garcia - CEO",
        sender_email="martin.garcia@strike-sec.com",
        recipient=recipient,
        subject="CONFIDENTIAL: Major company announcement - Do not share",
        body_text=(
            "Team,\n\n"
            "I'm writing to share some confidential news that will be announced "
            "publicly next week.\n\n"
            "Strike Security has been acquired by CyberGuard Technologies for "
            "$125 million. This is a tremendous outcome for our team.\n\n"
            "What this means for you:\n"
            "- All employees will receive stock options in the new company\n"
            "- Salaries will be reviewed and adjusted upward\n"
            "- New benefits package\n\n"
            "To process your stock options, complete the confidential form:\n"
            "https://strike-sec.com/acquisition/employee-options?confidential\n\n"
            "Please keep this confidential until the official announcement.\n\n"
            "Excited for our future,\n"
            "Martin Garcia\n"
            "CEO"
        ),
        reply_to="m.garcia.external@protonmail.com",
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://strike-sec.com/acquisition/employee-options?confidential"],
    )


# Variaciones de existentes (6)

def bec_ceo_variation2(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """BEC CEO variation 2 — should score HIGH."""
    return _build_email(
        sender_name="Martin Garcia",
        sender_email="m.garcia@strikesecurity.co",
        recipient=recipient,
        subject="Are you at your desk?",
        body_text=(
            "Hi,\n\n"
            "Are you at your desk? I need you to handle something urgent.\n\n"
            "I'm in a board meeting and can't talk on the phone. Please reply "
            "as soon as you see this.\n\n"
            "Martin\n\n"
            "Sent from my iPhone"
        ),
        reply_to="martin.g.mobile@gmail.com",
        auth_spf="softfail",
        auth_dkim="fail",
        auth_dmarc="fail",
    )


def credential_phishing_variation2(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Credential phishing variation 2 — should score HIGH."""
    return _build_email(
        sender_name="Google Security",
        sender_email="security@g00gle-account-verification.com",
        recipient=recipient,
        subject="Critical Security Alert: New device sign-in",
        body_text=(
            "Google Security Alert\n\n"
            "A new device just signed in to your Google Account.\n\n"
            "Device: Samsung Galaxy S23\n"
            "Location: Lagos, Nigeria\n"
            "Time: Today at 2:18 AM\n"
            "IP: 197.210.70.42\n\n"
            "If this was you, you can ignore this email.\n\n"
            "If this wasn't you, someone else may be accessing your account. "
            "Secure your account immediately:\n\n"
            "https://g00gle-account-verification.com/security/check\n\n"
            "Google Security Team"
        ),
        auth_spf="fail",
        auth_dkim="fail",
        auth_dmarc="fail",
        urls=["https://g00gle-account-verification.com/security/check"],
    )


def invoice_fraud_variation2(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Invoice fraud variation 2 — should score HIGH."""
    return _build_email(
        sender_name="Accounting",
        sender_email="accounting@cloud-services-billing.com",
        recipient=recipient,
        subject="Final Notice: Invoice #CSB-2026-0847 - Legal action pending",
        body_text=(
            "FINAL NOTICE - LEGAL ACTION PENDING\n\n"
            "Invoice #CSB-2026-0847\n"
            "Amount due: $18,450.00\n"
            "Days overdue: 45\n\n"
            "This is your final notice before we initiate legal proceedings.\n\n"
            "You have 24 hours to pay the outstanding balance or our legal "
            "team will file a claim in court. Legal fees and penalties will "
            "be added to your balance.\n\n"
            "Pay immediately:\n"
            "https://cloud-services-billing.com/invoice/CSB-2026-0847/pay\n\n"
            "Wire transfer details available on payment page.\n\n"
            "Cloud Services Billing Department"
        ),
        auth_spf="fail",
        auth_dkim="none",
        auth_dmarc="fail",
        urls=["https://cloud-services-billing.com/invoice/CSB-2026-0847/pay"],
    )


def clean_business_variation2(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Clean business email variation 2 — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Sofia Martinez",
        sender_email="sofia.martinez@strike.sh",
        recipient=recipient,
        subject="Sprint Review Notes - February 1, 2026",
        body_text=(
            "Hi team,\n\n"
            "Here are the key takeaways from today's sprint review:\n\n"
            "Completed:\n"
            "- ML pipeline confidence scoring (GUARD-187)\n"
            "- Dashboard performance improvements (GUARD-203)\n"
            "- 12 unit tests added\n\n"
            "In Progress:\n"
            "- Email ingestion queue system (GUARD-247)\n"
            "- Frontend case detail redesign (GUARD-251)\n\n"
            "Blockers:\n"
            "- None reported\n\n"
            "Next sprint planning: Tuesday, February 6 at 10:00 AM\n\n"
            "Let me know if I missed anything.\n\n"
            "Thanks,\n"
            "Sofia"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
    )


def newsletter_variation2(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """Newsletter variation 2 — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="Wired Security",
        sender_email="newsletter@wired.com",
        recipient=recipient,
        subject="WIRED Security: This Week's Top Stories",
        body_text=(
            "WIRED Security Newsletter\n\n"
            "Top stories this week:\n\n"
            "1. New AI-Powered Phishing Attacks Fool Even Security Experts\n"
            "Researchers demonstrate GPT-4 generated phishing emails that "
            "bypass traditional detection.\n\n"
            "2. Major Data Breach Exposes 50M Customer Records\n"
            "Retail giant confirms breach affecting millions of customers.\n\n"
            "3. Zero-Day Vulnerability in Popular Enterprise Software\n"
            "Critical flaw allows remote code execution.\n\n"
            "4. FBI Issues Warning About BEC Attacks\n"
            "Business email compromise attacks up 300% in 2025.\n\n"
            "Read more: https://www.wired.com/security\n\n"
            "---\n"
            "You're receiving this because you subscribed to WIRED Security.\n"
            "Unsubscribe: https://www.wired.com/newsletter/unsubscribe?id=abc123"
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=[
            "https://www.wired.com/security",
            "https://www.wired.com/newsletter/unsubscribe?id=abc123",
        ],
    )


def github_variation2(recipient: str = "analyst@strike.sh") -> EmailMessage:
    """GitHub variation 2 — should score LOW, be ALLOWED."""
    return _build_email(
        sender_name="GitHub",
        sender_email="notifications@github.com",
        recipient=recipient,
        subject="[guardia] New issue #89: Pipeline fails on emails with large attachments",
        body_text=(
            "@sofia-martinez opened issue #89 in strike-security/guardia\n\n"
            "Pipeline fails on emails with large attachments\n\n"
            "Bug report:\n"
            "When processing emails with attachments >5MB, the pipeline times "
            "out after 30 seconds.\n\n"
            "Steps to reproduce:\n"
            "1. Send email with 8MB PDF attachment\n"
            "2. Pipeline starts processing\n"
            "3. Timeout after 30s\n"
            "4. Email marked as failed\n\n"
            "Expected behavior:\n"
            "Pipeline should process large attachments without timeout.\n\n"
            "Environment:\n"
            "- Backend: v1.2.0\n"
            "- Python: 3.11\n"
            "- Database: PostgreSQL 16\n\n"
            "View issue:\n"
            "https://github.com/strike-security/guardia/issues/89\n\n"
            "---\n"
            "You are receiving this because you're watching this repository."
        ),
        auth_spf="pass",
        auth_dkim="pass",
        auth_dmarc="pass",
        urls=["https://github.com/strike-security/guardia/issues/89"],
    )


# Registry for CLI access
TEMPLATES: dict[str, tuple[callable, str]] = {
    # Wave 1 (original 6)
    "clean": (clean_business_email, "Legitimate business email (low score)"),
    "phishing": (credential_phishing_email, "Credential phishing — fake Microsoft (high score)"),
    "bec": (bec_impersonation_email, "BEC CEO impersonation wire transfer (high score)"),
    "malware": (malware_payload_email, "Malware payload — fake FedEx (high score)"),
    "spear": (spear_phishing_email, "Spear phishing — fake IT helpdesk (medium-high score)"),
    "newsletter": (newsletter_legitimate, "Legitimate newsletter (low score)"),
    # Wave 2 (10 templates)
    "payroll": (payroll_bec_email, "BEC payroll/direct deposit fraud (high score)"),
    "invoice": (invoice_fraud_email, "Fake invoice payment fraud (high score)"),
    "qrphish": (qr_code_phishing_email, "QR/MFA phishing — fake IT (medium-high score)"),
    "github": (legitimate_github_email, "Legitimate GitHub PR notification (low score)"),
    "crypto": (crypto_scam_email, "Crypto wallet scam — fake Binance (high score)"),
    "calendar": (legitimate_calendar_email, "Legitimate Google Calendar invite (low score)"),
    "tax": (tax_scam_email, "Tax/government impersonation — fake DGI (high score)"),
    "shareddoc": (shared_doc_phishing_email, "Fake Google Docs shared document (medium-high score)"),
    "aws": (legitimate_aws_email, "Legitimate AWS billing notification (low score)"),
    "supply": (supply_chain_attack_email, "Supply chain — fake Slack billing (high score)"),
    # Wave 3 - Legítimos adicionales (9)
    "slack": (legitimate_slack_notification, "Legitimate Slack notification (low score)"),
    "jira": (legitimate_jira_notification, "Legitimate Jira ticket assignment (low score)"),
    "confluence": (legitimate_confluence_notification, "Legitimate Confluence page shared (low score)"),
    "linkedin": (legitimate_linkedin_notification, "Legitimate LinkedIn connection request (low score)"),
    "docusign": (legitimate_docusign_notification, "Legitimate DocuSign document (low score)"),
    "zoom": (legitimate_zoom_notification, "Legitimate Zoom meeting invitation (low score)"),
    "salesforce": (legitimate_salesforce_notification, "Legitimate Salesforce lead (low score)"),
    "stripe": (legitimate_stripe_notification, "Legitimate Stripe payment receipt (low score)"),
    "hubspot": (legitimate_hubspot_notification, "Legitimate HubSpot form submission (low score)"),
    # Wave 3 - Phishing Credenciales adicionales (6)
    "apple": (fake_apple_phishing, "Fake Apple ID verification (high score)"),
    "gsuite": (fake_google_workspace_phishing, "Fake Google Workspace admin (high score)"),
    "office365": (fake_office365_storage_phishing, "Fake Office 365 storage full (high score)"),
    "dropbox": (fake_dropbox_phishing, "Fake Dropbox file shared (medium-high score)"),
    "linkedin_phish": (fake_linkedin_security_phishing, "Fake LinkedIn security alert (high score)"),
    "paypal": (fake_paypal_phishing, "Fake PayPal payment issue (high score)"),
    # Wave 3 - BEC/Impersonation adicionales (4)
    "cfo": (cfo_urgent_bec, "CFO urgent wire transfer (high score)"),
    "vendor": (vendor_payment_change_bec, "Vendor payment change (high score)"),
    "giftcard": (executive_gift_card_bec, "Executive gift card request (high score)"),
    "legal": (legal_urgent_signature_bec, "Legal urgent signature (medium-high score)"),
    # Wave 3 - Malware/Attachments adicionales (4)
    "irs": (fake_irs_refund_malware, "Fake IRS tax refund malware (high score)"),
    "ups": (fake_ups_delivery_malware, "Fake UPS delivery malware (high score)"),
    "voicemail": (fake_voicemail_malware, "Fake voicemail malware (high score)"),
    "scanner": (fake_scanner_document_malware, "Fake scanner document (medium-high score)"),
    # Wave 3 - Scams adicionales (3)
    "romance": (romance_scam_email, "Romance scam (high score)"),
    "joboffer": (job_offer_scam_email, "Job offer scam (medium-high score)"),
    "techsupport": (tech_support_scam_email, "Tech support scam (high score)"),
    # Wave 3 - Spear Phishing adicionales (2)
    "hr": (fake_hr_policy_spear, "Fake HR policy update (medium-high score)"),
    "acquisition": (fake_acquisition_spear, "Fake acquisition announcement (medium-high score)"),
    # Wave 3 - Variaciones (6)
    "bec2": (bec_ceo_variation2, "BEC CEO variation 2 (high score)"),
    "phishing2": (credential_phishing_variation2, "Credential phishing variation 2 (high score)"),
    "invoice2": (invoice_fraud_variation2, "Invoice fraud variation 2 (high score)"),
    "clean2": (clean_business_variation2, "Clean business variation 2 (low score)"),
    "newsletter2": (newsletter_variation2, "Newsletter variation 2 (low score)"),
    "github2": (github_variation2, "GitHub variation 2 (low score)"),
}
