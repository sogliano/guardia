"""Tests for DashboardService."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from datetime import datetime, timezone

from app.services.dashboard_service import DashboardService
from app.models.case import Case
from app.models.email import Email
from app.models.alert_event import AlertEvent
from app.models.analysis import Analysis


@pytest.fixture
def dashboard_service(mock_db):
    return DashboardService(mock_db)


class TestGetStats:
    @pytest.mark.asyncio
    async def test_get_stats_no_filters(self, dashboard_service, mock_db):
        """Get dashboard stats without filters."""
        # Setup mock results for all queries
        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()

            # Query 1: total_emails count
            if call_count == 1:
                mock_result.scalar.return_value = 100

            # Query 2: emails_today count
            elif call_count == 2:
                mock_result.scalar.return_value = 10

            # Query 3: verdict counts
            elif call_count == 3:
                mock_result.all.return_value = [
                    ("allowed", 50),
                    ("warned", 30),
                    ("quarantined", 15),
                    ("blocked", 5),
                ]

            # Query 4: pending_cases count
            elif call_count == 4:
                mock_result.scalar.return_value = 20

            # Query 5: total_cases count
            elif call_count == 5:
                mock_result.scalar.return_value = 100

            # Query 6: avg_score
            elif call_count == 6:
                mock_result.scalar.return_value = 0.4532

            # Query 7: risk_distribution
            elif call_count == 7:
                mock_result.all.return_value = [
                    ("low", 40),
                    ("medium", 35),
                    ("high", 20),
                    ("critical", 5),
                ]

            # Query 8: daily_trend
            elif call_count == 8:
                mock_row = MagicMock()
                mock_row.date = "2026-02-01"
                mock_row.count = 15
                mock_result.all.return_value = [mock_row]

            # Query 9: threat_categories
            elif call_count == 9:
                mock_result.all.return_value = [
                    ("phishing", 40),
                    ("malware", 25),
                    ("spam", 20),
                    ("clean", 15),
                ]

            # Query 10-13: pipeline_health (avg_ms, total, p95, stage_avg)
            elif call_count == 10:
                mock_row = MagicMock()
                mock_row.avg_ms = 2500.0
                mock_row.total = 100
                mock_result.first.return_value = mock_row

            elif call_count == 11:
                mock_result.scalar.return_value = 3200.0

            elif call_count == 12:
                mock_row1 = MagicMock()
                mock_row1.stage = "heuristic"
                mock_row1.avg_ms = 5.0
                mock_row2 = MagicMock()
                mock_row2.stage = "ml"
                mock_row2.avg_ms = 18.0
                mock_result.all.return_value = [mock_row1, mock_row2]

            elif call_count == 13:
                mock_result.scalar.return_value = 80

            elif call_count == 14:
                mock_result.scalar.return_value = 100

            # Query 15: recent_critical_cases
            elif call_count == 15:
                mock_case = MagicMock()
                mock_case.id = uuid4()
                mock_case.final_score = 0.85
                mock_case.verdict = "quarantined"
                mock_case.created_at = datetime.now(timezone.utc)
                mock_email = MagicMock()
                mock_email.subject = "Suspicious email"
                mock_email.sender_email = "phish@evil.com"
                mock_case.email = mock_email
                mock_result.scalars.return_value.all.return_value = [mock_case]

            # Query 16: active_alerts
            elif call_count == 16:
                mock_alert = MagicMock()
                mock_alert.id = uuid4()
                mock_alert.severity = "high"
                mock_alert.created_at = datetime.now(timezone.utc)
                mock_alert.trigger_info = {"message": "High risk detected"}
                mock_rule = MagicMock()
                mock_rule.name = "High Risk Rule"
                mock_alert.alert_rule = mock_rule
                mock_result.scalars.return_value.all.return_value = [mock_alert]

            # Query 17: top_senders
            elif call_count == 17:
                mock_row = MagicMock()
                mock_row.sender_email = "sender@example.com"
                mock_row.email_count = 25
                mock_row.avg_score = 0.2345
                mock_result.all.return_value = [mock_row]

            # Query 18: verdict_trend
            elif call_count == 18:
                mock_row = MagicMock()
                mock_row.date = "2026-02-01"
                mock_row.verdict = "allowed"
                mock_row.count = 30
                mock_result.all.return_value = [mock_row]

            # Query 19: score_distribution
            elif call_count == 19:
                mock_result.all.return_value = [
                    (MagicMock(bucket=1, count=10)),
                    (MagicMock(bucket=5, count=20)),
                    (MagicMock(bucket=9, count=15)),
                ]

            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        result = await dashboard_service.get_stats()

        assert result["stats"]["total_emails"] == 100
        assert result["stats"]["emails_today"] == 10
        assert result["stats"]["total_cases"] == 100
        assert result["stats"]["pending_cases"] == 20
        assert result["stats"]["avg_score"] == 0.4532
        assert result["stats"]["by_verdict"] == {
            "allowed": 50,
            "warned": 30,
            "quarantined": 15,
            "blocked": 5,
        }
        assert len(result["risk_distribution"]) == 4
        assert len(result["daily_trend"]) == 1
        assert len(result["threat_categories"]) == 4
        assert result["pipeline_health"]["avg_duration_ms"] == 2500.0
        assert len(result["recent_cases"]) == 1
        assert len(result["active_alerts"]) == 1
        assert len(result["top_senders"]) == 1
        assert len(result["verdict_trend"]) == 1
        assert len(result["score_distribution"]) == 10

    @pytest.mark.asyncio
    async def test_get_stats_with_sender_filter_no_results(
        self, dashboard_service, mock_db
    ):
        """Get stats with sender filter that matches no emails."""
        # Mock sender check query to return 0
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_count_result

        result = await dashboard_service.get_stats(sender="nonexistent@example.com")

        # Should return empty stats
        assert result["stats"]["total_emails"] == 0
        assert result["stats"]["total_cases"] == 0
        assert result["risk_distribution"] == []
        assert result["daily_trend"] == []

    @pytest.mark.asyncio
    async def test_get_stats_with_date_filters(self, dashboard_service, mock_db):
        """Get stats with date range filters."""
        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()

            if call_count == 1:
                mock_result.scalar.return_value = 50
            elif call_count == 2:
                mock_result.scalar.return_value = 5
            elif call_count == 3:
                mock_result.all.return_value = [("allowed", 25), ("warned", 15)]
            elif call_count == 4:
                mock_result.scalar.return_value = 10
            elif call_count == 5:
                mock_result.scalar.return_value = 50
            elif call_count == 6:
                mock_result.scalar.return_value = 0.3
            elif call_count == 7:
                mock_result.all.return_value = [("low", 30), ("medium", 20)]
            elif call_count == 8:
                mock_result.all.return_value = []
            elif call_count == 9:
                mock_result.all.return_value = [("clean", 40)]
            elif call_count == 10:
                mock_row = MagicMock()
                mock_row.avg_ms = 2000.0
                mock_row.total = 50
                mock_result.first.return_value = mock_row
            elif call_count == 11:
                mock_result.scalar.return_value = 2800.0
            elif call_count == 12:
                mock_result.all.return_value = []
            elif call_count == 13:
                mock_result.scalar.return_value = 40
            elif call_count == 14:
                mock_result.scalar.return_value = 50
            elif call_count == 15:
                mock_result.scalars.return_value.all.return_value = []
            elif call_count == 16:
                mock_result.scalars.return_value.all.return_value = []
            elif call_count == 17:
                mock_result.all.return_value = []
            elif call_count == 18:
                mock_result.all.return_value = []
            elif call_count == 19:
                mock_result.all.return_value = []

            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        result = await dashboard_service.get_stats(
            date_from="2026-02-01T00:00:00Z", date_to="2026-02-02T23:59:59Z"
        )

        assert result["stats"]["total_emails"] == 50
        assert result["stats"]["total_cases"] == 50


class TestGetDailyTrend:
    @pytest.mark.asyncio
    async def test_get_daily_trend(self, dashboard_service, mock_db):
        """Get daily trend data."""
        mock_row1 = MagicMock()
        mock_row1.date = "2026-02-01"
        mock_row1.count = 10
        mock_row2 = MagicMock()
        mock_row2.date = "2026-02-02"
        mock_row2.count = 15

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_daily_trend(
            datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        )

        assert len(result) == 2
        assert result[0]["label"] == "2026-02-01"
        assert result[0]["value"] == 10
        assert result[1]["label"] == "2026-02-02"
        assert result[1]["value"] == 15


class TestGetPipelineHealth:
    @pytest.mark.asyncio
    async def test_get_pipeline_health_with_data(self, dashboard_service, mock_db):
        """Get pipeline health metrics."""
        call_count = 0

        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()

            if call_count == 1:
                # avg_ms query
                mock_row = MagicMock()
                mock_row.avg_ms = 2500.0
                mock_row.total = 100
                mock_result.first.return_value = mock_row
            elif call_count == 2:
                # p95 query
                mock_result.scalar.return_value = 3200.0
            elif call_count == 3:
                # stage averages
                mock_row1 = MagicMock()
                mock_row1.stage = "heuristic"
                mock_row1.avg_ms = 5.0
                mock_row2 = MagicMock()
                mock_row2.stage = "ml"
                mock_row2.avg_ms = 18.0
                mock_row3 = MagicMock()
                mock_row3.stage = "llm"
                mock_row3.avg_ms = 2400.0
                mock_result.all.return_value = [mock_row1, mock_row2, mock_row3]
            elif call_count == 4:
                # analyzed count
                mock_result.scalar.return_value = 80
            elif call_count == 5:
                # total count
                mock_result.scalar.return_value = 100

            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        result = await dashboard_service._get_pipeline_health()

        assert result is not None
        assert result["avg_duration_ms"] == 2500.0
        assert result["p95_duration_ms"] == 3200.0
        assert result["success_rate"] == 0.8
        assert result["stage_avg_ms"]["heuristic"] == 5.0
        assert result["stage_avg_ms"]["ml"] == 18.0
        assert result["stage_avg_ms"]["llm"] == 2400.0

    @pytest.mark.asyncio
    async def test_get_pipeline_health_no_data(self, dashboard_service, mock_db):
        """Get pipeline health when no data available."""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_pipeline_health()

        assert result is None


class TestGetRecentCriticalCases:
    @pytest.mark.asyncio
    async def test_get_recent_critical_cases(self, dashboard_service, mock_db):
        """Get recent critical cases."""
        case_id = uuid4()
        mock_case = MagicMock()
        mock_case.id = case_id
        mock_case.final_score = 0.85
        mock_case.verdict = "quarantined"
        mock_case.created_at = datetime.now(timezone.utc)
        mock_email = MagicMock()
        mock_email.subject = "Urgent: Update your password"
        mock_email.sender_email = "phisher@evil.com"
        mock_case.email = mock_email

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_case]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_recent_critical_cases(limit=10)

        assert len(result) == 1
        assert result[0]["id"] == str(case_id)
        assert result[0]["subject"] == "Urgent: Update your password"
        assert result[0]["sender"] == "phisher@evil.com"
        assert result[0]["score"] == 0.85
        assert result[0]["verdict"] == "quarantined"

    @pytest.mark.asyncio
    async def test_get_recent_critical_cases_no_email(self, dashboard_service, mock_db):
        """Get recent cases when email is None."""
        mock_case = MagicMock()
        mock_case.id = uuid4()
        mock_case.final_score = 0.75
        mock_case.verdict = "warned"
        mock_case.created_at = datetime.now(timezone.utc)
        mock_case.email = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_case]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_recent_critical_cases()

        assert len(result) == 1
        assert result[0]["subject"] is None
        assert result[0]["sender"] == "unknown"


class TestGetActiveAlerts:
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, dashboard_service, mock_db):
        """Get active alerts."""
        alert_id = uuid4()
        mock_alert = MagicMock()
        mock_alert.id = alert_id
        mock_alert.severity = "critical"
        mock_alert.created_at = datetime.now(timezone.utc)
        mock_alert.trigger_info = {"message": "Multiple high-risk emails detected"}
        mock_rule = MagicMock()
        mock_rule.name = "High Risk Threshold"
        mock_alert.alert_rule = mock_rule

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_alert]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_active_alerts(limit=10)

        assert len(result) == 1
        assert result[0]["id"] == str(alert_id)
        assert result[0]["rule_name"] == "High Risk Threshold"
        assert result[0]["severity"] == "critical"
        assert result[0]["message"] == "Multiple high-risk emails detected"

    @pytest.mark.asyncio
    async def test_get_active_alerts_no_rule(self, dashboard_service, mock_db):
        """Get alerts when alert_rule is None."""
        mock_alert = MagicMock()
        mock_alert.id = uuid4()
        mock_alert.severity = "medium"
        mock_alert.created_at = datetime.now(timezone.utc)
        mock_alert.trigger_info = {}
        mock_alert.alert_rule = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_alert]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_active_alerts()

        assert len(result) == 1
        assert result[0]["rule_name"] == "Unknown Rule"
        assert result[0]["message"] == "Alert triggered"


class TestGetVerdictTrend:
    @pytest.mark.asyncio
    async def test_get_verdict_trend(self, dashboard_service, mock_db):
        """Get verdict trend data."""
        mock_row1 = MagicMock()
        mock_row1.date = "2026-02-01"
        mock_row1.verdict = "allowed"
        mock_row1.count = 30

        mock_row2 = MagicMock()
        mock_row2.date = "2026-02-01"
        mock_row2.verdict = "warned"
        mock_row2.count = 15

        mock_row3 = MagicMock()
        mock_row3.date = "2026-02-02"
        mock_row3.verdict = "quarantined"
        mock_row3.count = 10

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2, mock_row3]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_verdict_trend(
            datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        )

        assert len(result) == 2
        assert result[0]["date"] == "2026-02-01"
        assert result[0]["allow"] == 30
        assert result[0]["warn"] == 15
        assert result[0]["quarantine"] == 0
        assert result[1]["date"] == "2026-02-02"
        assert result[1]["quarantine"] == 10


class TestGetScoreDistribution:
    @pytest.mark.asyncio
    async def test_get_score_distribution(self, dashboard_service, mock_db):
        """Get score distribution in buckets."""
        mock_row1 = MagicMock()
        mock_row1.bucket = 1
        mock_row1.count = 10

        mock_row2 = MagicMock()
        mock_row2.bucket = 5
        mock_row2.count = 25

        mock_row3 = MagicMock()
        mock_row3.bucket = 9
        mock_row3.count = 15

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2, mock_row3]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_score_distribution()

        assert len(result) == 10
        assert result[0]["range"] == "0.0-0.1"
        assert result[0]["count"] == 10
        assert result[4]["range"] == "0.4-0.5"
        assert result[4]["count"] == 25
        assert result[8]["range"] == "0.8-0.9"
        assert result[8]["count"] == 15
        # Empty buckets should have count 0
        assert result[1]["count"] == 0


class TestGetTopSenders:
    @pytest.mark.asyncio
    async def test_get_top_senders(self, dashboard_service, mock_db):
        """Get top senders by email count."""
        mock_row1 = MagicMock()
        mock_row1.sender_email = "user1@example.com"
        mock_row1.email_count = 50
        mock_row1.avg_score = 0.1234

        mock_row2 = MagicMock()
        mock_row2.sender_email = "user2@example.com"
        mock_row2.email_count = 30
        mock_row2.avg_score = None

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row1, mock_row2]
        mock_db.execute.return_value = mock_result

        result = await dashboard_service._get_top_senders(limit=10)

        assert len(result) == 2
        assert result[0]["sender"] == "user1@example.com"
        assert result[0]["count"] == 50
        assert result[0]["avg_score"] == 0.1234
        assert result[1]["sender"] == "user2@example.com"
        assert result[1]["avg_score"] == 0.0  # None should become 0.0
