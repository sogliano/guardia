"""Tests for alert rule matching logic and evaluate_and_fire."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from app.services.alert_service import AlertService


def _make_rule(
    conditions=None,
    channels=None,
    is_active=True,
):
    """Create a mock AlertRule."""
    rule = MagicMock()
    rule.conditions = conditions or {}
    rule.channels = channels or ["email"]
    rule.is_active = is_active
    rule.id = "rule-1"
    rule.name = "Test Rule"
    rule.severity = "high"
    return rule


def _make_case(
    final_score=0.5,
    verdict="warned",
    risk_level="medium",
    threat_category="generic_phishing",
):
    """Create a mock Case."""
    case = MagicMock()
    case.final_score = final_score
    case.verdict = verdict
    case.risk_level = risk_level
    case.threat_category = threat_category
    case.id = "case-1"
    return case


# ---------------------------------------------------------------------------
# _matches tests
# ---------------------------------------------------------------------------

def test_matches_min_score_pass():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"min_score": 0.8})
    case = _make_case(final_score=0.9)
    assert svc._matches(rule, case) is True


def test_matches_min_score_fail():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"min_score": 0.8})
    case = _make_case(final_score=0.5)
    assert svc._matches(rule, case) is False


def test_matches_verdict_pass():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"verdicts": ["blocked"]})
    case = _make_case(verdict="blocked")
    assert svc._matches(rule, case) is True


def test_matches_verdict_fail():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"verdicts": ["blocked"]})
    case = _make_case(verdict="warned")
    assert svc._matches(rule, case) is False


def test_matches_risk_level_pass():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"risk_levels": ["critical"]})
    case = _make_case(risk_level="critical")
    assert svc._matches(rule, case) is True


def test_matches_risk_level_fail():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"risk_levels": ["critical"]})
    case = _make_case(risk_level="low")
    assert svc._matches(rule, case) is False


def test_matches_multiple_conditions_and():
    """All conditions must pass (AND logic)."""
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={
        "min_score": 0.8,
        "verdicts": ["blocked"],
        "risk_levels": ["critical"],
    })
    case = _make_case(final_score=0.9, verdict="blocked", risk_level="critical")
    assert svc._matches(rule, case) is True


def test_matches_multiple_conditions_partial_fail():
    """One condition fails → no match."""
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={
        "min_score": 0.8,
        "verdicts": ["blocked"],
    })
    case = _make_case(final_score=0.9, verdict="warned")
    assert svc._matches(rule, case) is False


def test_matches_empty_conditions():
    """No conditions → always matches."""
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={})
    case = _make_case()
    assert svc._matches(rule, case) is True


def test_matches_threat_category():
    svc = AlertService(MagicMock())
    rule = _make_rule(conditions={"threat_categories": ["bec_impersonation"]})
    case = _make_case(threat_category="bec_impersonation")
    assert svc._matches(rule, case) is True

    case2 = _make_case(threat_category="clean")
    assert svc._matches(rule, case2) is False


# ---------------------------------------------------------------------------
# evaluate_and_fire
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_evaluate_and_fire_matching_rule():
    """Matching rule fires AlertEvents for each channel."""
    db = AsyncMock()
    db.add = MagicMock()

    rule = _make_rule(
        conditions={"min_score": 0.5},
        channels=["email", "slack"],
    )
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [rule]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    db.execute.return_value = mock_result

    case = _make_case(final_score=0.9, verdict="blocked", risk_level="critical")

    svc = AlertService(db)
    fired = await svc.evaluate_and_fire(case)

    assert len(fired) == 2  # one per channel
    assert db.add.call_count == 2
    db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_evaluate_and_fire_no_match():
    """No matching rules → no events fired."""
    db = AsyncMock()
    db.add = MagicMock()

    rule = _make_rule(conditions={"min_score": 0.9})
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [rule]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    db.execute.return_value = mock_result

    case = _make_case(final_score=0.1)

    svc = AlertService(db)
    fired = await svc.evaluate_and_fire(case)

    assert len(fired) == 0
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_evaluate_and_fire_no_rules():
    """No active rules → no events."""
    db = AsyncMock()
    db.add = MagicMock()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    db.execute.return_value = mock_result

    svc = AlertService(db)
    fired = await svc.evaluate_and_fire(_make_case())

    assert len(fired) == 0
