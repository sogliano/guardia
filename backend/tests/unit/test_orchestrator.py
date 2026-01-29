"""Tests for the pipeline orchestrator scoring, verdicts, and threat categories."""

import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.pipeline.orchestrator import PipelineOrchestrator
from app.services.pipeline.models import HeuristicResult, MLResult, LLMResult, EvidenceItem
from app.core.constants import RiskLevel, Verdict, ThreatCategory, CaseStatus


@pytest.fixture
def orchestrator(mock_db):
    return PipelineOrchestrator(mock_db)


# ---------------------------------------------------------------------------
# _calculate_final_score
# ---------------------------------------------------------------------------

def test_final_score_heuristic_only_when_ml_unavailable(orchestrator):
    """No ML → 100% heuristic score."""
    h = HeuristicResult(score=0.7)
    ml = MLResult(score=0.0, confidence=0.0, model_available=False)
    assert orchestrator._calculate_final_score(h, ml) == 0.7


def test_final_score_weighted_with_ml(orchestrator):
    """ML available → 40% heuristic + 60% ML."""
    h = HeuristicResult(score=0.5)
    ml = MLResult(score=0.8, confidence=0.9, model_available=True)
    expected = 0.5 * 0.4 + 0.8 * 0.6  # 0.2 + 0.48 = 0.68
    assert abs(orchestrator._calculate_final_score(h, ml) - expected) < 0.001


def test_final_score_clamped_to_1(orchestrator):
    """Score never exceeds 1.0."""
    h = HeuristicResult(score=1.0)
    ml = MLResult(score=1.0, confidence=1.0, model_available=True)
    assert orchestrator._calculate_final_score(h, ml) == 1.0


def test_final_score_zero_floor(orchestrator):
    """Score never goes below 0.0."""
    h = HeuristicResult(score=0.0)
    ml = MLResult(score=0.0, confidence=0.0, model_available=False)
    assert orchestrator._calculate_final_score(h, ml) == 0.0


# ---------------------------------------------------------------------------
# _determine_verdict (thresholds: allow<0.3, warn<0.6, quarantine<0.8, else blocked)
# ---------------------------------------------------------------------------

@patch("app.services.pipeline.orchestrator.settings")
def test_verdict_allowed(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_verdict(0.1) == Verdict.ALLOWED
    assert orchestrator._determine_verdict(0.29) == Verdict.ALLOWED


@patch("app.services.pipeline.orchestrator.settings")
def test_verdict_warned(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_verdict(0.3) == Verdict.WARNED
    assert orchestrator._determine_verdict(0.59) == Verdict.WARNED


@patch("app.services.pipeline.orchestrator.settings")
def test_verdict_quarantined(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_verdict(0.6) == Verdict.QUARANTINED
    assert orchestrator._determine_verdict(0.79) == Verdict.QUARANTINED


@patch("app.services.pipeline.orchestrator.settings")
def test_verdict_blocked(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_verdict(0.8) == Verdict.BLOCKED
    assert orchestrator._determine_verdict(0.95) == Verdict.BLOCKED


# ---------------------------------------------------------------------------
# _determine_risk_level
# ---------------------------------------------------------------------------

@patch("app.services.pipeline.orchestrator.settings")
def test_risk_level_low(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_risk_level(0.1) == RiskLevel.LOW


@patch("app.services.pipeline.orchestrator.settings")
def test_risk_level_medium(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_risk_level(0.45) == RiskLevel.MEDIUM


@patch("app.services.pipeline.orchestrator.settings")
def test_risk_level_high(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_risk_level(0.7) == RiskLevel.HIGH


@patch("app.services.pipeline.orchestrator.settings")
def test_risk_level_critical(mock_settings, orchestrator):
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8
    assert orchestrator._determine_risk_level(0.9) == RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# _determine_threat_category
# ---------------------------------------------------------------------------

def test_threat_category_bec(orchestrator):
    """Evidence with CEO impersonation → BEC."""
    h = HeuristicResult(
        score=0.8,
        evidences=[EvidenceItem(type="ceo_impersonation", severity="high", description="x")]
    )
    assert orchestrator._determine_threat_category(h) == ThreatCategory.BEC_IMPERSONATION


def test_threat_category_credential_phishing(orchestrator):
    """Evidence with phishing keyword or URL shortener → credential phishing."""
    h = HeuristicResult(
        score=0.6,
        evidences=[EvidenceItem(type="keyword_phishing", severity="high", description="x")]
    )
    assert orchestrator._determine_threat_category(h) == ThreatCategory.CREDENTIAL_PHISHING


def test_threat_category_generic_from_domain(orchestrator):
    """Domain evidence → generic phishing."""
    h = HeuristicResult(
        score=0.5,
        evidences=[EvidenceItem(type="domain_typosquatting", severity="high", description="x")]
    )
    assert orchestrator._determine_threat_category(h) == ThreatCategory.GENERIC_PHISHING


def test_threat_category_clean(orchestrator):
    """No evidence, score 0 → clean."""
    h = HeuristicResult(score=0.0, evidences=[])
    assert orchestrator._determine_threat_category(h) == ThreatCategory.CLEAN


def test_threat_category_nonzero_score_no_specific_evidence(orchestrator):
    """Score > 0 but no specific evidence type → generic phishing."""
    h = HeuristicResult(score=0.1, evidences=[])
    assert orchestrator._determine_threat_category(h) == ThreatCategory.GENERIC_PHISHING


# ---------------------------------------------------------------------------
# _build_ml_input
# ---------------------------------------------------------------------------

def test_build_ml_input(orchestrator):
    data = {"subject": "Hello", "body_text": "World"}
    assert orchestrator._build_ml_input(data) == "Hello\nWorld"


def test_build_ml_input_empty(orchestrator):
    data = {"subject": None, "body_text": None}
    assert orchestrator._build_ml_input(data) == ""


def test_build_ml_input_subject_only(orchestrator):
    data = {"subject": "Only subject", "body_text": ""}
    assert orchestrator._build_ml_input(data) == "Only subject"


# ---------------------------------------------------------------------------
# _email_to_dict
# ---------------------------------------------------------------------------

def test_email_to_dict(orchestrator):
    """Converts ORM email to pipeline dict."""
    email = MagicMock()
    email.message_id = "msg-1"
    email.sender_email = "a@b.com"
    email.sender_name = "A"
    email.reply_to = None
    email.recipient_email = "c@d.com"
    email.recipients_cc = ["e@f.com"]
    email.subject = "Test"
    email.body_text = "Body"
    email.body_html = "<p>Body</p>"
    email.headers = {"X-Custom": "1"}
    email.urls = ["https://example.com"]
    email.attachments = []
    email.auth_results = {"spf": "pass", "dkim": "pass", "dmarc": "pass"}

    result = orchestrator._email_to_dict(email)
    assert result["sender_email"] == "a@b.com"
    assert result["subject"] == "Test"
    assert result["urls"] == ["https://example.com"]
    assert result["recipients_cc"] == ["e@f.com"]


def test_email_to_dict_nulls(orchestrator):
    """Handles None fields with fallback to empty."""
    email = MagicMock()
    email.message_id = "msg-2"
    email.sender_email = "x@y.com"
    email.sender_name = None
    email.reply_to = None
    email.recipient_email = "z@w.com"
    email.recipients_cc = None
    email.subject = ""
    email.body_text = None
    email.body_html = None
    email.headers = None
    email.urls = None
    email.attachments = None
    email.auth_results = None

    result = orchestrator._email_to_dict(email)
    assert result["recipients_cc"] == []
    assert result["headers"] == {}
    assert result["urls"] == []
    assert result["auth_results"] == {}


# ---------------------------------------------------------------------------
# _load_email
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_load_email_not_found(mock_db):
    """Missing email raises ValueError."""
    orch = PipelineOrchestrator(mock_db)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(ValueError, match="not found"):
        await orch._load_email(uuid4())


@pytest.mark.asyncio
async def test_load_email_found(mock_db):
    """Existing email is returned."""
    orch = PipelineOrchestrator(mock_db)
    fake_email = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_email
    mock_db.execute.return_value = mock_result

    result = await orch._load_email(uuid4())
    assert result is fake_email


# ---------------------------------------------------------------------------
# _get_or_create_case
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_or_create_case_existing(mock_db):
    """Returns existing case if one exists for email_id."""
    orch = PipelineOrchestrator(mock_db)
    existing_case = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_case
    mock_db.execute.return_value = mock_result

    result = await orch._get_or_create_case(uuid4())
    assert result is existing_case


@pytest.mark.asyncio
async def test_get_or_create_case_new(mock_db):
    """Creates new case if none exists."""
    orch = PipelineOrchestrator(mock_db)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await orch._get_or_create_case(uuid4())
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited()


# ---------------------------------------------------------------------------
# _persist_analysis
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_persist_analysis(mock_db):
    """Persist creates Analysis and Evidence records."""
    orch = PipelineOrchestrator(mock_db)
    evidences = [
        EvidenceItem(type="test_type", severity="high", description="d1"),
        EvidenceItem(type="test_type2", severity="low", description="d2"),
    ]

    await orch._persist_analysis(
        case_id=uuid4(),
        stage="heuristic",
        score=0.5,
        confidence=None,
        explanation=None,
        metadata={"key": "val"},
        execution_time_ms=10,
        evidences=evidences,
    )
    # 1 Analysis + 2 Evidence = 3 calls to db.add
    assert mock_db.add.call_count == 3
    assert mock_db.flush.await_count == 2


# ---------------------------------------------------------------------------
# Full analyze() flow (mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("app.services.pipeline.orchestrator.settings")
@patch("app.services.pipeline.orchestrator.LLMExplainer")
@patch("app.services.pipeline.orchestrator.get_ml_classifier")
@patch("app.services.pipeline.orchestrator.HeuristicEngine")
async def test_analyze_full_flow(
    MockHeuristic, MockMLGetter, MockLLMExplainer, mock_settings, mock_db
):
    """Full analyze() with mocked stages runs without error."""
    mock_settings.pipeline_ml_enabled = True
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8

    email_id = uuid4()
    fake_email = MagicMock()
    fake_email.message_id = "m1"
    fake_email.sender_email = "a@b.com"
    fake_email.sender_name = None
    fake_email.reply_to = None
    fake_email.recipient_email = "c@d.com"
    fake_email.recipients_cc = []
    fake_email.subject = "Hi"
    fake_email.body_text = "Body"
    fake_email.body_html = None
    fake_email.headers = {}
    fake_email.urls = []
    fake_email.attachments = []
    fake_email.auth_results = {}

    fake_case = MagicMock()
    fake_case.id = uuid4()

    # DB: first call = _load_email, second call = _get_or_create_case
    mock_result_email = MagicMock()
    mock_result_email.scalar_one_or_none.return_value = fake_email
    mock_result_case = MagicMock()
    mock_result_case.scalar_one_or_none.return_value = fake_case
    mock_db.execute.side_effect = [mock_result_email, mock_result_case]

    # Heuristic
    h_result = HeuristicResult(score=0.2, evidences=[])
    MockHeuristic.return_value.analyze = AsyncMock(return_value=h_result)

    # ML
    ml_result = MLResult(score=0.3, confidence=0.9, model_available=True, model_version="v1")
    MockMLGetter.return_value.predict = AsyncMock(return_value=ml_result)

    # LLM
    llm_result = LLMResult(explanation="Looks ok", provider="claude", model_used="c", tokens_used=10)
    MockLLMExplainer.return_value.explain = AsyncMock(return_value=llm_result)

    orch = PipelineOrchestrator(mock_db)
    result = await orch.analyze(email_id)

    assert result.case_id == fake_case.id
    assert 0.0 <= result.final_score <= 1.0
    assert result.verdict in [v.value for v in Verdict]
    assert result.risk_level in [r.value for r in RiskLevel]


@pytest.mark.asyncio
@patch("app.services.pipeline.orchestrator.settings")
@patch("app.services.pipeline.orchestrator.LLMExplainer")
@patch("app.services.pipeline.orchestrator.HeuristicEngine")
async def test_analyze_llm_failure_continues(
    MockHeuristic, MockLLMExplainer, mock_settings, mock_db
):
    """LLM explainer failing doesn't break the pipeline."""
    mock_settings.pipeline_ml_enabled = False
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8

    email_id = uuid4()
    fake_email = MagicMock()
    fake_email.message_id = "m1"
    fake_email.sender_email = "a@b.com"
    fake_email.sender_name = None
    fake_email.reply_to = None
    fake_email.recipient_email = "c@d.com"
    fake_email.recipients_cc = []
    fake_email.subject = "Hi"
    fake_email.body_text = "Body"
    fake_email.body_html = None
    fake_email.headers = {}
    fake_email.urls = []
    fake_email.attachments = []
    fake_email.auth_results = {}

    fake_case = MagicMock()
    fake_case.id = uuid4()

    mock_result_email = MagicMock()
    mock_result_email.scalar_one_or_none.return_value = fake_email
    mock_result_case = MagicMock()
    mock_result_case.scalar_one_or_none.return_value = fake_case
    mock_db.execute.side_effect = [mock_result_email, mock_result_case]

    MockHeuristic.return_value.analyze = AsyncMock(
        return_value=HeuristicResult(score=0.1, evidences=[])
    )
    MockLLMExplainer.return_value.explain = AsyncMock(side_effect=RuntimeError("LLM down"))

    orch = PipelineOrchestrator(mock_db)
    result = await orch.analyze(email_id)

    # Pipeline completes despite LLM failure
    assert result.verdict == Verdict.ALLOWED
    assert result.llm.explanation == ""


@pytest.mark.asyncio
@patch("app.services.pipeline.orchestrator.settings")
@patch("app.services.pipeline.orchestrator.LLMExplainer")
@patch("app.services.pipeline.orchestrator.HeuristicEngine")
async def test_analyze_auto_quarantine(
    MockHeuristic, MockLLMExplainer, mock_settings, mock_db
):
    """High score → quarantined verdict → case status set to QUARANTINED."""
    mock_settings.pipeline_ml_enabled = False
    mock_settings.threshold_allow = 0.3
    mock_settings.threshold_warn = 0.6
    mock_settings.threshold_quarantine = 0.8

    email_id = uuid4()
    fake_email = MagicMock()
    fake_email.message_id = "m1"
    fake_email.sender_email = "x@y.com"
    fake_email.sender_name = None
    fake_email.reply_to = None
    fake_email.recipient_email = "z@w.com"
    fake_email.recipients_cc = []
    fake_email.subject = "S"
    fake_email.body_text = "B"
    fake_email.body_html = None
    fake_email.headers = {}
    fake_email.urls = []
    fake_email.attachments = []
    fake_email.auth_results = {}

    fake_case = MagicMock()
    fake_case.id = uuid4()

    mock_result_email = MagicMock()
    mock_result_email.scalar_one_or_none.return_value = fake_email
    mock_result_case = MagicMock()
    mock_result_case.scalar_one_or_none.return_value = fake_case
    mock_db.execute.side_effect = [mock_result_email, mock_result_case]

    MockHeuristic.return_value.analyze = AsyncMock(
        return_value=HeuristicResult(score=0.75, evidences=[
            EvidenceItem(type="domain_blacklisted", severity="critical", description="x"),
        ])
    )
    MockLLMExplainer.return_value.explain = AsyncMock(return_value=LLMResult())

    orch = PipelineOrchestrator(mock_db)
    result = await orch.analyze(email_id)

    assert result.verdict == Verdict.QUARANTINED
    assert fake_case.status == CaseStatus.QUARANTINED
