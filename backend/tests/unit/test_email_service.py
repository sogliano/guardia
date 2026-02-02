"""Tests for EmailService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.exc import IntegrityError

from app.services.email_service import EmailService
from app.models.email import Email
from app.schemas.email import EmailIngest


@pytest.fixture
def email_service(mock_db):
    return EmailService(mock_db)


class TestIngest:
    @pytest.mark.asyncio
    async def test_ingest_new_email(self, email_service, mock_db):
        """Ingest a new email successfully."""
        email_data = EmailIngest(
            message_id="test@example.com",
            sender_email="sender@example.com",
            recipient_email="recipient@example.com",
            subject="Test",
            body_text="Body",
            urls=[],
            attachments=[],
            auth_results={},
        )

        result = await email_service.ingest(email_data)

        assert result is not None
        assert mock_db.add.called
        assert mock_db.flush.called

    @pytest.mark.asyncio
    async def test_ingest_duplicate_email(self, email_service, mock_db):
        """Ingest duplicate email returns existing."""
        email_data = EmailIngest(
            message_id="duplicate@example.com",
            sender_email="sender@example.com",
            recipient_email="recipient@example.com",
            subject="Test",
        )

        # First flush raises IntegrityError
        mock_db.flush.side_effect = IntegrityError("duplicate", None, None)

        # After rollback, query returns existing email
        mock_email = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        result = await email_service.ingest(email_data)

        assert result is mock_email
        assert mock_db.rollback.called
        assert mock_db.execute.called


class TestListEmails:
    @pytest.mark.asyncio
    async def test_list_emails_no_filters(self, email_service, mock_db):
        """List all emails without filters."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await email_service.list_emails(page=1, size=50)

        assert result["total"] == 5
        assert result["page"] == 1
        assert result["size"] == 50

    @pytest.mark.asyncio
    async def test_list_emails_with_sender_filter(self, email_service, mock_db):
        """List emails filtered by sender."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 2

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await email_service.list_emails(sender="test@example.com", page=1, size=50)

        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_list_emails_with_search(self, email_service, mock_db):
        """List emails with search term."""
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 3

        mock_list_result = MagicMock()
        mock_list_result.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [mock_count_result, mock_list_result]

        result = await email_service.list_emails(search="urgent", page=1, size=50)

        assert result["total"] == 3


class TestGetEmail:
    @pytest.mark.asyncio
    async def test_get_email_found(self, email_service, mock_db):
        """Get existing email."""
        email_id = uuid4()
        mock_email = MagicMock()
        mock_email.id = email_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email
        mock_db.execute.return_value = mock_result

        result = await email_service.get_email(email_id)

        assert result is mock_email

    @pytest.mark.asyncio
    async def test_get_email_not_found(self, email_service, mock_db):
        """Get non-existing email returns None."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await email_service.get_email(uuid4())

        assert result is None
