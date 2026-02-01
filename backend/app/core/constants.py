from enum import StrEnum

# --- Case Flow ---

class CaseStatus(StrEnum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    QUARANTINED = "quarantined"
    RESOLVED = "resolved"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Verdict(StrEnum):
    ALLOWED = "allowed"
    WARNED = "warned"
    QUARANTINED = "quarantined"
    BLOCKED = "blocked"


# --- Pipeline ---

class PipelineStage(StrEnum):
    BYPASS = "bypass"
    HEURISTIC = "heuristic"
    ML = "ml"
    LLM = "llm"


class ThreatCategory(StrEnum):
    BEC_IMPERSONATION = "bec_impersonation"
    CREDENTIAL_PHISHING = "credential_phishing"
    MALWARE_PAYLOAD = "malware_payload"
    GENERIC_PHISHING = "generic_phishing"
    CLEAN = "clean"


class EvidenceType(StrEnum):
    # Domain
    DOMAIN_SPOOFING = "domain_spoofing"
    DOMAIN_TYPOSQUATTING = "domain_typosquatting"
    DOMAIN_BLACKLISTED = "domain_blacklisted"
    DOMAIN_SUSPICIOUS_TLD = "domain_suspicious_tld"
    # URL
    URL_SHORTENER = "url_shortener"
    URL_IP_BASED = "url_ip_based"
    URL_MISMATCH = "url_mismatch"
    URL_SUSPICIOUS = "url_suspicious"
    # Keywords
    KEYWORD_URGENCY = "keyword_urgency"
    KEYWORD_PHISHING = "keyword_phishing"
    KEYWORD_CAPS_ABUSE = "keyword_caps_abuse"
    # Auth
    AUTH_SPF_FAIL = "auth_spf_fail"
    AUTH_DKIM_FAIL = "auth_dkim_fail"
    AUTH_DMARC_FAIL = "auth_dmarc_fail"
    AUTH_DMARC_MISSING = "auth_dmarc_missing"
    AUTH_SPF_NEUTRAL = "auth_spf_neutral"
    AUTH_REPLY_TO_MISMATCH = "auth_reply_to_mismatch"
    AUTH_COMPOUND_FAILURE = "auth_compound_failure"
    # Attachments
    ATTACHMENT_SUSPICIOUS_EXT = "attachment_suspicious_ext"
    ATTACHMENT_DOUBLE_EXT = "attachment_double_ext"
    # Header analysis
    HEADER_EXCESSIVE_HOPS = "header_excessive_hops"
    HEADER_SUSPICIOUS_MAILER = "header_suspicious_mailer"
    HEADER_MSGID_MISMATCH = "header_msgid_mismatch"
    HEADER_MISSING_STANDARD = "header_missing_standard"
    # ML
    ML_HIGH_SCORE = "ml_high_score"
    # Identity
    CEO_IMPERSONATION = "ceo_impersonation"
    SENDER_IMPERSONATION = "sender_impersonation"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# --- Quarantine ---

class QuarantineAction(StrEnum):
    RELEASED = "released"
    KEPT = "kept"
    DELETED = "deleted"


# --- Policies ---

class PolicyListType(StrEnum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    ALLOWLIST = "allowlist"


class PolicyEntryType(StrEnum):
    DOMAIN = "domain"
    EMAIL = "email"
    IP = "ip"


# --- Alerts ---

class AlertChannel(StrEnum):
    EMAIL = "email"
    SLACK = "slack"


class AlertDeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


# --- Users ---

class UserRole(StrEnum):
    ADMINISTRATOR = "administrator"
    ANALYST = "analyst"
    AUDITOR = "auditor"


# --- FP Review ---

class FPReviewDecision(StrEnum):
    CONFIRMED_FP = "confirmed_fp"
    KEPT_FLAGGED = "kept_flagged"


# --- Pipeline thresholds (defaults) ---

THRESHOLD_ALLOW = 0.3
THRESHOLD_WARN = 0.6
THRESHOLD_QUARANTINE = 0.8

# Heuristic engine weights (must sum to 1.0)
HEURISTIC_WEIGHT_AUTH = 0.35       # Most reliable signal (SPF/DKIM/DMARC)
HEURISTIC_WEIGHT_DOMAIN = 0.25     # Typosquatting, blacklists, suspicious TLDs
HEURISTIC_WEIGHT_URL = 0.25        # IP-based URLs, shorteners, suspicious links
HEURISTIC_WEIGHT_KEYWORD = 0.15    # Noisiest signal, most false positives

# Correlation boost: multiple sub-engines triggering = higher confidence
HEURISTIC_CORRELATION_BOOST_3 = 1.15   # 3 sub-engines fired
HEURISTIC_CORRELATION_BOOST_4 = 1.25   # all 4 sub-engines fired

# Auth compound failure: when 2+ auth mechanisms fail simultaneously
# This adds a flat bonus ON TOP of individual auth scores, reflecting
# that multiple auth failures together are far more suspicious than isolated ones
AUTH_COMPOUND_2_BONUS = 0.15    # 2 of 3 (SPF/DKIM/DMARC) failed
AUTH_COMPOUND_3_BONUS = 0.30    # all 3 failed — extremely suspicious

# Attachment risk: additive bonus to final heuristic score
ATTACHMENT_SUSPICIOUS_BONUS = 0.10   # suspicious extension found
ATTACHMENT_DOUBLE_EXT_BONUS = 0.15   # double extension (e.g. invoice.pdf.exe)

# Pipeline score weights (final score calculation)
# 3-way: Heuristic 30% + ML 50% + LLM 20% (when all available)
# Fallback 2-way (no LLM): Heuristic 40% + ML 60%
# Fallback 2-way (no ML): Heuristic 60% + LLM 40%
SCORE_WEIGHT_HEURISTIC = 0.30
SCORE_WEIGHT_ML = 0.50
SCORE_WEIGHT_LLM = 0.20

# Fallback weights when ML or LLM unavailable
SCORE_WEIGHT_HEURISTIC_NO_LLM = 0.40  # Heuristic + ML only
SCORE_WEIGHT_ML_NO_LLM = 0.60
SCORE_WEIGHT_HEURISTIC_NO_ML = 0.60   # Heuristic + LLM only
SCORE_WEIGHT_LLM_NO_ML = 0.40

# =============================================================================
# HEURISTIC SCORING THRESHOLDS (Sub-components)
# =============================================================================

# Domain analysis
HEURISTIC_DOMAIN_SUSPICIOUS_TLD_SCORE = 0.5
HEURISTIC_DOMAIN_TYPOSQUATTING_SCORE = 0.8

# URL analysis
HEURISTIC_URL_IP_BASED_SCORE = 0.7
HEURISTIC_URL_SHORTENER_BASE = 0.4
HEURISTIC_URL_SHORTENER_INCREMENT = 0.1
HEURISTIC_URL_SUSPICIOUS_BASE = 0.3
HEURISTIC_URL_SUSPICIOUS_INCREMENT = 0.1

# Keyword analysis
HEURISTIC_KEYWORD_PHISHING_BASE = 0.3
HEURISTIC_KEYWORD_PHISHING_INCREMENT = 0.1
HEURISTIC_KEYWORD_URGENCY_BASE = 0.2
HEURISTIC_KEYWORD_URGENCY_INCREMENT = 0.05
HEURISTIC_KEYWORD_FINANCIAL_BASE = 0.15
HEURISTIC_KEYWORD_FINANCIAL_INCREMENT = 0.05
HEURISTIC_KEYWORD_CAPS_ABUSE_THRESHOLD = 0.3
HEURISTIC_KEYWORD_CAPS_ABUSE_PENALTY = 0.1

# Header analysis
HEURISTIC_HEADER_EXCESSIVE_HOPS_BONUS = 0.08
HEURISTIC_HEADER_SUSPICIOUS_MAILER_BONUS = 0.10
HEURISTIC_HEADER_MSGID_MISMATCH_BONUS = 0.12
HEURISTIC_HEADER_MISSING_GMAIL_BONUS = 0.10

# Impersonation
HEURISTIC_IMPERSONATION_BONUS = 0.10

# ML classifier
ML_CLASSIFIER_THRESHOLD_HIGH = 0.5
ML_CLASSIFIER_THRESHOLD_CRITICAL = 0.8

# --- SMTP Gateway ---

SMTP_RESPONSE_OK = "250 Message accepted for delivery"
SMTP_RESPONSE_REJECT = "550 5.7.1 Message rejected by Guard-IA: threat detected"
SMTP_RESPONSE_QUARANTINE = "250 Message accepted (quarantined for review)"
SMTP_RESPONSE_INVALID_DOMAIN = "550 5.1.1 Relay not permitted"

GUARD_IA_HEADER_PREFIX = "X-Guard-IA"
GUARD_IA_HEADER_SCORE = "X-Guard-IA-Score"
GUARD_IA_HEADER_VERDICT = "X-Guard-IA-Verdict"
GUARD_IA_HEADER_CASE_ID = "X-Guard-IA-Case-ID"
GUARD_IA_HEADER_WARNING = "X-Guard-IA-Warning"
GUARD_IA_HEADER_SPAM = "X-Guard-IA-Spam"
GUARD_IA_HEADER_VERSION = "X-Guard-IA-Version"

GUARD_IA_VERSION = "0.1.0"
