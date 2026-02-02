"""Tests for CaseService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.services.case_service import CaseService
from app.models.case import Case
from app.models.email import Email


@pytest.fixture
def case_service(mock_db):
    return CaseService(mock_db)


class TestListCases:
    @pytest.mark.asyncio
    async def test_list_cases_no_filters(self, case_service, mock_db):
        """List all cases without filters."""
        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10

        # Mock list query
        mock_case = MagicMock()
        mock_case.id = uuid4()
        mock_case.status = "pending"

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = [mock_case]

        # First call = count, second call = list
        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await case_service.list_cases(page=1, size=20)

        assert result["total"] == 10
        assert len(result["items"]) == 1
        assert result["page"] == 1
        assert result["size"] == 20

    @pytest.mark.asyncio
    async def test_list_cases_with_status_filter(self, case_service, mock_db):
        """List cases filtered by status."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await case_service.list_cases(status="quarantined", page=1, size=20)

        assert result["total"] == 5
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_list_cases_with_multiple_filters(self, case_service, mock_db):
        """List cases with multiple filters."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await case_service.list_cases(
            status="pending",
            risk_level="high",
            verdict="quarantined",
            sender="evil@example.com",
            page=1,
            size=10,
        )

        assert result["total"] == 2
        assert result["size"] == 10


class TestGetCase:
    @pytest.mark.asyncio
    async def test_get_case_found(self, case_service, mock_db):
        """Get existing case."""
        case_id = uuid4()
        mock_case = MagicMock()
        mock_case.id = case_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_case
        mock_db.execute.return_value = mock_result

        result = await case_service.get_case(case_id)

        assert result is mock_case
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_case_not_found(self, case_service, mock_db):
        """Get non-existing case returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await case_service.get_case(uuid4())

        assert result is None


class TestGetCaseDetail:
    @pytest.mark.asyncio
    async def test_get_case_detail_with_relations(self, case_service, mock_db):
        """Get case detail with email and analyses."""
        case_id = uuid4()
        mock_case = MagicMock()
        mock_case.id = case_id
        mock_case.email = MagicMock()
        mock_case.analyses = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_case
        mock_db.execute.return_value = mock_result

        result = await case_service.get_case_detail(case_id)

        assert result is mock_case
        assert mock_db.execute.called


class TestResolveCase:
    @pytest.mark.asyncio
    async def test_resolve_case_success(self, case_service, mock_db):
        """Resolve a case successfully."""
        case_id = uuid4()
        user_id = uuid4()

        mock_case = MagicMock()
        mock_case.id = case_id
        mock_case.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_case
        mock_db.execute.return_value = mock_result

        result = await case_service.resolve_case(case_id, "allowed", user_id)

        assert result is mock_case
        assert mock_db.flush.called

    @pytest.mark.asyncio
    async def test_resolve_case_not_found(self, case_service, mock_db):
        """Resolve non-existing case returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await case_service.resolve_case(uuid4(), "allowed", uuid4())

        assert result is None


class TestAddNote:
    @pytest.mark.asyncio
    async def test_add_note_success(self, case_service, mock_db):
        """Add note to case."""
        case_id = uuid4()
        user_id = uuid4()

        # First query: get case
        mock_case = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_case
        mock_db.execute.return_value = mock_result

        note = await case_service.add_note(case_id, user_id, "Test note", private=False)

        assert note is not None
        assert mock_db.add.called
        assert mock_db.flush.called

    @pytest.mark.asyncio
    async def test_add_note_case_not_found(self, case_service, mock_db):
        """Add note to non-existing case returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        note = await case_service.add_note(uuid4(), uuid4(), "Test note", False)

        assert note is None
