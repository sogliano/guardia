"""
Dataset of 50 diverse emails for Guard-IA testing and ingestion.

Distribution:
- Legítimos: 15 (30%)
- Phishing Credenciales: 12 (24%)
- BEC/Impersonation: 8 (16%)
- Malware/Attachments: 6 (12%)
- Scams: 5 (10%)
- Spear Phishing: 4 (8%)

Total: 50 emails
"""

from typing import TypedDict


class EmailDatasetEntry(TypedDict):
    """Single email entry in the dataset."""

    template_name: str
    recipient: str
    expected_verdict: str  # allowed, warned, quarantined, blocked
    expected_risk: str  # low, medium, high, critical
    category: str  # legitimate, phishing, bec, malware, scam, spear
    description: str


# Dataset of 50 emails
DATASET_50: list[EmailDatasetEntry] = [
    # ===== Legítimos (15) =====
    {
        "template_name": "clean",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate business partnership email",
    },
    {
        "template_name": "newsletter",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate newsletter from The Hacker News",
    },
    {
        "template_name": "github",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate GitHub pull request notification",
    },
    {
        "template_name": "calendar",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Google Calendar meeting invite",
    },
    {
        "template_name": "aws",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate AWS billing notification",
    },
    {
        "template_name": "slack",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Slack channel message notification",
    },
    {
        "template_name": "jira",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Jira ticket assignment",
    },
    {
        "template_name": "confluence",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Confluence page shared",
    },
    {
        "template_name": "linkedin",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate LinkedIn connection request",
    },
    {
        "template_name": "docusign",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate DocuSign document to sign",
    },
    {
        "template_name": "zoom",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Zoom meeting invitation",
    },
    {
        "template_name": "salesforce",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Salesforce lead notification",
    },
    {
        "template_name": "stripe",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate Stripe payment receipt",
    },
    {
        "template_name": "hubspot",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate HubSpot form submission",
    },
    {
        "template_name": "clean2",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate internal sprint review notes",
    },
    # ===== Phishing Credenciales (12) =====
    {
        "template_name": "phishing",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Credential phishing - fake Microsoft login",
    },
    {
        "template_name": "shareddoc",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake Google Docs shared document",
    },
    {
        "template_name": "apple",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake Apple ID verification",
    },
    {
        "template_name": "gsuite",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake Google Workspace admin alert",
    },
    {
        "template_name": "office365",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake Office 365 storage full",
    },
    {
        "template_name": "dropbox",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "phishing",
        "description": "Fake Dropbox file shared",
    },
    {
        "template_name": "linkedin_phish",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake LinkedIn security alert",
    },
    {
        "template_name": "paypal",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake PayPal payment issue",
    },
    {
        "template_name": "phishing2",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Fake Google security alert - new device signin",
    },
    {
        "template_name": "qrphish",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "phishing",
        "description": "QR code phishing - fake MFA enrollment",
    },
    {
        "template_name": "spear",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "phishing",
        "description": "Spear phishing - fake IT helpdesk password reset",
    },
    {
        "template_name": "supply",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "phishing",
        "description": "Supply chain attack - fake Slack billing",
    },
    # ===== BEC/Impersonation (8) =====
    {
        "template_name": "bec",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "bec",
        "description": "BEC CEO impersonation - wire transfer",
    },
    {
        "template_name": "payroll",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "bec",
        "description": "BEC payroll - direct deposit change",
    },
    {
        "template_name": "cfo",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "bec",
        "description": "CFO urgent vendor payment request",
    },
    {
        "template_name": "vendor",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "bec",
        "description": "Vendor payment information change",
    },
    {
        "template_name": "giftcard",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "bec",
        "description": "Executive gift card request fraud",
    },
    {
        "template_name": "legal",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "bec",
        "description": "Fake legal department urgent signature",
    },
    {
        "template_name": "bec2",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "bec",
        "description": "BEC CEO variation - 'are you at your desk'",
    },
    {
        "template_name": "acquisition",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "bec",
        "description": "Fake company acquisition announcement",
    },
    # ===== Malware/Attachments (6) =====
    {
        "template_name": "malware",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "malware",
        "description": "Malware payload - fake FedEx shipping",
    },
    {
        "template_name": "irs",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "malware",
        "description": "Fake IRS tax refund with malware",
    },
    {
        "template_name": "ups",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "malware",
        "description": "Fake UPS delivery with malware",
    },
    {
        "template_name": "voicemail",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "malware",
        "description": "Fake voicemail notification with malware",
    },
    {
        "template_name": "scanner",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "malware",
        "description": "Fake scanned document from office copier",
    },
    {
        "template_name": "invoice",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "malware",
        "description": "Fake invoice payment fraud",
    },
    # ===== Scams (5) =====
    {
        "template_name": "crypto",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "scam",
        "description": "Crypto scam - fake Binance alert",
    },
    {
        "template_name": "tax",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "scam",
        "description": "Tax scam - fake DGI Uruguay",
    },
    {
        "template_name": "romance",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "scam",
        "description": "Romance scam email",
    },
    {
        "template_name": "joboffer",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "scam",
        "description": "Fake job offer scam",
    },
    {
        "template_name": "techsupport",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "scam",
        "description": "Tech support scam - fake Microsoft",
    },
    # ===== Spear Phishing (4) =====
    {
        "template_name": "hr",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "warned",
        "expected_risk": "medium",
        "category": "spear",
        "description": "Fake HR remote work policy update",
    },
    {
        "template_name": "invoice2",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "quarantined",
        "expected_risk": "high",
        "category": "spear",
        "description": "Invoice fraud variation 2 - legal action threat",
    },
    {
        "template_name": "newsletter2",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate newsletter from WIRED Security",
    },
    {
        "template_name": "github2",
        "recipient": "analyst@strike.sh",
        "expected_verdict": "allowed",
        "expected_risk": "low",
        "category": "legitimate",
        "description": "Legitimate GitHub issue notification",
    },
]


def get_dataset() -> list[EmailDatasetEntry]:
    """Return the complete dataset of 50 emails."""
    return DATASET_50


def get_by_category(category: str) -> list[EmailDatasetEntry]:
    """Filter dataset by category (legitimate, phishing, bec, malware, scam, spear)."""
    return [entry for entry in DATASET_50 if entry["category"] == category]


def get_dataset_stats() -> dict[str, int]:
    """Get statistics about the dataset distribution."""
    stats: dict[str, int] = {}
    for entry in DATASET_50:
        category = entry["category"]
        stats[category] = stats.get(category, 0) + 1
    return stats
