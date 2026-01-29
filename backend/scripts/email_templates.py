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

    # Simulate Received header chain (external → Guard-IA → Google)
    msg["Received"] = (
        f"from mail.{sender_email.split('@')[1]} "
        f"(mail.{sender_email.split('@')[1]} [203.0.113.42]) "
        f"by guardia.strike.sh with ESMTPS; "
        f"{format_datetime(datetime.now(timezone.utc))}"
    )

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


# Registry for CLI access
TEMPLATES: dict[str, tuple[callable, str]] = {
    "clean": (clean_business_email, "Legitimate business email (low score)"),
    "phishing": (credential_phishing_email, "Credential phishing — fake Microsoft (high score)"),
    "bec": (bec_impersonation_email, "BEC CEO impersonation wire transfer (high score)"),
    "malware": (malware_payload_email, "Malware payload — fake FedEx (high score)"),
    "spear": (spear_phishing_email, "Spear phishing — fake IT helpdesk (medium-high score)"),
    "newsletter": (newsletter_legitimate, "Legitimate newsletter (low score)"),
    # Wave 2
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
}
