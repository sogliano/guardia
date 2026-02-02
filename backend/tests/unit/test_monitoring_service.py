"""Tests for MonitoringService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.monitoring_service import MonitoringService


@pytest.fixture
def monitoring_service(mock_db):
    return MonitoringService(mock_db)


class TestGetLLMStats:
    @pytest.mark.asyncio
    async def test_get_llm_stats_with_data(self, monitoring_service, mock_db):
        """Get LLM stats with mocked query results."""
        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                mock_result = MagicMock()
                mock_result.one.return_value = MagicMock(
                    total=100,
                    avg_ms=2000.0,
                    p95_ms=3500.0,
                    total_tokens=50000,
                )
                return mock_result
            elif call_count == 2:
                mock_result = MagicMock()
                mock_result.scalar.return_value = 5
                return mock_result
            elif call_count == 3:
                mock_result = MagicMock()
                mock_result.scalar.return_value = 80
                return mock_result
            elif call_count == 4:
                mock_result = MagicMock()
                mock_result.all.return_value = []
                return mock_result
            elif call_count == 5:
                mock_result = MagicMock()
                mock_result.all.return_value = []
                return mock_result
            elif call_count == 6:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                return mock_result
            elif call_count == 7:
                mock_result = MagicMock()
                mock_result.all.return_value = []
                return mock_result
            else:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = []
                return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await monitoring_service.get_llm_stats()

        assert "kpi" in result
        assert "token_trend" in result
        assert "latency_distribution" in result
        assert "score_agreement" in result
        assert "cost_breakdown" in result
        assert "recent_analyses" in result

    @pytest.mark.asyncio
    async def test_get_llm_stats_with_date_range(self, monitoring_service, mock_db):
        """Get LLM stats with custom date range."""
        date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 1, 31, tzinfo=timezone.utc)

        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.one.return_value = MagicMock(
                    total=50,
                    avg_ms=1800.0,
                    p95_ms=3000.0,
                    total_tokens=25000,
                )
            elif call_count <= 3:
                mock_result.scalar.return_value = 0
            else:
                mock_result.all.return_value = []
                mock_result.scalars.return_value.all.return_value = []
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result = await monitoring_service.get_llm_stats(
            date_from=date_from, date_to=date_to
        )

        assert result is not None
        assert "kpi" in result


class TestGetKPI:
    @pytest.mark.asyncio
    async def test_get_kpi_with_data(self, monitoring_service, mock_db):
        """Get KPI metrics with mocked data."""
        from datetime import timedelta

        date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 1, 31, tzinfo=timezone.utc)
        prev_duration = date_to - date_from
        prev_from = date_from - prev_duration
        prev_to = date_from

        call_count = 0

        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                mock_result.one.return_value = MagicMock(
                    total=100,
                    avg_ms=2000.0,
                    p95_ms=3500.0,
                    total_tokens=50000,
                )
            else:
                mock_result.scalar.return_value = 10
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        def llm_filter(q):
            return q

        result = await monitoring_service._get_kpi(llm_filter, prev_from, prev_to)

        assert result is not None
        assert "avg_latency_ms" in result
        assert "error_count" in result


class TestGetRecentAnalyses:
    @pytest.mark.asyncio
    async def test_get_recent_analyses(self, monitoring_service, mock_db):
        """Get recent analyses successfully."""
        mock_analysis = MagicMock()
        mock_analysis.id = uuid4()
        mock_analysis.case_id = uuid4()
        mock_analysis.stage = "llm"
        mock_analysis.score = 0.85
        mock_analysis.execution_time_ms = 2000

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_analysis]
        mock_db.execute = AsyncMock(return_value=mock_result)

        date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 1, 31, tzinfo=timezone.utc)

        result = await monitoring_service._get_recent_analyses(date_from, date_to)

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_recent_analyses_empty(self, monitoring_service, mock_db):
        """Get recent analyses with no data."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        date_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
        date_to = datetime(2026, 1, 31, tzinfo=timezone.utc)

        result = await monitoring_service._get_recent_analyses(date_from, date_to)

        assert result == []
