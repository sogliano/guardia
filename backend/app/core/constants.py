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
    AUTH_REPLY_TO_MISMATCH = "auth_reply_to_mismatch"
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


# --- Notifications ---

class NotificationType(StrEnum):
    CRITICAL_THREAT = "critical_threat"
    QUARANTINE_PENDING = "quarantine_pending"
    FALSE_POSITIVE = "false_positive"
    PIPELINE_HEALTH = "pipeline_health"
    SYSTEM = "system"


class NotificationSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


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

# Heuristic engine weights
HEURISTIC_WEIGHT_DOMAIN = 0.25
HEURISTIC_WEIGHT_URL = 0.25
HEURISTIC_WEIGHT_KEYWORD = 0.25
HEURISTIC_WEIGHT_AUTH = 0.25

# Pipeline score weights (final score calculation)
SCORE_WEIGHT_HEURISTIC = 0.40
SCORE_WEIGHT_ML = 0.60

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
