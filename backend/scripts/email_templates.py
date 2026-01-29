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


# Registry for CLI access
TEMPLATES: dict[str, tuple[callable, str]] = {
    "clean": (clean_business_email, "Legitimate business email (low score)"),
    "phishing": (credential_phishing_email, "Credential phishing — fake Microsoft (high score)"),
    "bec": (bec_impersonation_email, "BEC CEO impersonation wire transfer (high score)"),
    "malware": (malware_payload_email, "Malware payload — fake FedEx (high score)"),
    "spear": (spear_phishing_email, "Spear phishing — fake IT helpdesk (medium-high score)"),
    "newsletter": (newsletter_legitimate, "Legitimate newsletter (low score)"),
}
