"""Static data for the heuristic detection engine.

Contains curated lists of suspicious indicators used by the
HeuristicEngine to score emails. These lists are deliberately
kept small and high-confidence to minimize false positives.
"""

# --- Suspicious TLDs ---
# TLDs disproportionately used in phishing campaigns (source: APWG, Spamhaus)
SUSPICIOUS_TLDS: set[str] = {
    ".xyz", ".top", ".buzz", ".club", ".work", ".click",
    ".link", ".info", ".biz", ".online", ".site", ".icu",
    ".rest", ".gq", ".ml", ".cf", ".ga", ".tk",
    ".cam", ".live", ".stream", ".download", ".racing",
    ".win", ".review", ".accountant", ".loan", ".date",
}

# --- URL Shorteners ---
URL_SHORTENER_DOMAINS: set[str] = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
    "is.gd", "buff.ly", "rebrand.ly", "bl.ink", "shorturl.at",
    "cutt.ly", "tiny.cc", "rb.gy", "surl.li", "v.gd",
    "qr.ae", "t.ly", "lnkd.in",
}

# --- Urgency Keywords ---
# Phrases that create artificial time pressure (common in phishing)
URGENCY_KEYWORDS: list[str] = [
    "urgent", "immediately", "right away", "act now",
    "expires today", "last chance", "final warning",
    "within 24 hours", "within 48 hours", "time sensitive",
    "deadline", "suspended", "deactivated", "locked",
    "unauthorized access", "security alert", "action required",
    "verify immediately", "confirm your identity",
    "your account will be", "failure to respond",
]

# --- Phishing Keywords ---
# Terms strongly associated with credential phishing
PHISHING_KEYWORDS: list[str] = [
    "verify your account", "confirm your password",
    "update your payment", "click here to verify",
    "your account has been", "unusual activity",
    "login attempt", "reset your password",
    "confirm your email", "verify your identity",
    "social security number", "bank account details",
    "credit card number", "wire transfer",
    "bitcoin wallet", "cryptocurrency",
    "inheritance", "lottery winner",
    "congratulations you won",
]

# --- Financial / BEC Keywords ---
# Terms associated with Business Email Compromise (CEO fraud, invoice scams)
FINANCIAL_KEYWORDS: list[str] = [
    "wire transfer", "bank transfer", "routing number",
    "invoice attached", "payment due", "overdue payment",
    "updated bank details", "new account number",
    "change of payment", "vendor payment",
    "purchase order", "gift card", "itunes card",
    "google play card", "prepaid card",
    "w-2 form", "tax document", "payroll",
    "direct deposit change",
]

# --- Known Legitimate Domains ---
# Used for typosquatting detection (Levenshtein distance)
KNOWN_DOMAINS: set[str] = {
    # Tech
    "google.com", "microsoft.com", "apple.com", "amazon.com",
    "facebook.com", "meta.com", "twitter.com", "linkedin.com",
    "github.com", "dropbox.com", "zoom.us", "slack.com",
    # Email providers
    "gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
    "protonmail.com", "icloud.com",
    # Finance
    "paypal.com", "stripe.com", "chase.com", "bankofamerica.com",
    "wellsfargo.com", "citibank.com", "americanexpress.com",
    # Cloud / SaaS
    "salesforce.com", "adobe.com", "office365.com", "office.com",
    "onedrive.com", "sharepoint.com",
    # Shipping
    "fedex.com", "ups.com", "usps.com", "dhl.com",
    # Strike Security (our domain — always legitimate)
    "strike.sh",
}

# --- Display name impersonation patterns ---
# Common CEO/executive titles used in BEC attacks
IMPERSONATION_TITLES: list[str] = [
    "ceo", "cfo", "cto", "coo", "president",
    "vice president", "director", "managing director",
    "chief executive", "chief financial",
    "head of", "founder",
]

# --- Suspicious attachment extensions ---
SUSPICIOUS_EXTENSIONS: set[str] = {
    ".exe", ".scr", ".bat", ".cmd", ".com", ".pif",
    ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
    ".ps1", ".msi", ".dll", ".hta", ".cpl",
    ".iso", ".img",  # Disk images (used to bypass Mark-of-the-Web)
}

# Double extension patterns (e.g., "invoice.pdf.exe")
DOUBLE_EXTENSION_PATTERN = r"\.\w{2,5}\.(exe|scr|bat|cmd|com|pif|vbs|js|ps1|msi|hta)$"

# --- Header Analysis ---
# Suspicious X-Mailer / User-Agent values (mass-mailing tools)
SUSPICIOUS_MAILERS: set[str] = {
    "phpmailer", "swiftmailer", "phpmail", "leaf phpmailer",
    "mail.php", "sendmail", "postfix-mta", "mass mailer",
    "bulk mailer", "email blaster", "turbo mailer",
    "atomic mail sender", "group mail", "mail merge",
    "gammadyne mailer", "mailchimp-mandrill",  # mandrill abused
    "sendinblue", "mailgun",  # legitimate but watch context
}

# Known legitimate mail platform signatures in Message-ID
# Format: if sender claims to be from X, Message-ID should contain one of these
MSGID_DOMAIN_MAP: dict[str, set[str]] = {
    "gmail.com": {"mail.gmail.com", "google.com"},
    "outlook.com": {"outlook.com", "microsoft.com", "hotmail.com"},
    "hotmail.com": {"outlook.com", "microsoft.com", "hotmail.com"},
    "yahoo.com": {"yahoo.com", "mail.yahoo.com"},
    "icloud.com": {"icloud.com", "me.com", "apple.com"},
    "protonmail.com": {"protonmail.com", "proton.me"},
}

# Maximum expected hop count for common providers
MAX_EXPECTED_HOPS = 5
