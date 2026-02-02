"""Tests for user sync service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.user_sync_service import sync_clerk_user
from app.core.exceptions import UnauthorizedError
from app.models.user import User


class TestSyncClerkUser:
    @pytest.mark.asyncio
    @patch("app.services.user_sync_service.httpx.AsyncClient")
    async def test_sync_clerk_user_success(self, mock_http_client, mock_db):
        """Sync Clerk user successfully creates local user."""
        clerk_id = "clerk_test_123"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": clerk_id,
            "email_addresses": [
                {"id": "email_1", "email_address": "test@strike.sh"}
            ],
            "primary_email_address_id": "email_1",
            "first_name": "Test",
            "last_name": "User",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_http_client.return_value = mock_client_instance

        result = await sync_clerk_user(mock_db, clerk_id)

        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    @patch("app.services.user_sync_service.httpx.AsyncClient")
    async def test_sync_clerk_user_no_email(self, mock_http_client, mock_db):
        """Sync Clerk user with no email address."""
        clerk_id = "clerk_no_email"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": clerk_id,
            "email_addresses": [],
            "first_name": "No",
            "last_name": "Email",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_http_client.return_value = mock_client_instance

        with pytest.raises(UnauthorizedError):
            await sync_clerk_user(mock_db, clerk_id)

    @pytest.mark.asyncio
    @patch("app.services.user_sync_service.httpx.AsyncClient")
    async def test_sync_clerk_user_duplicate(self, mock_http_client, mock_db):
        """Sync Clerk user with duplicate handling."""
        clerk_id = "clerk_duplicate"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": clerk_id,
            "email_addresses": [
                {"id": "email_1", "email_address": "dup@strike.sh"}
            ],
            "primary_email_address_id": "email_1",
            "first_name": "Duplicate",
            "last_name": "User",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_http_client.return_value = mock_client_instance

        mock_db.commit.side_effect = Exception("Duplicate key")

        mock_user = MagicMock()
        mock_user.clerk_id = clerk_id
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await sync_clerk_user(mock_db, clerk_id)

        assert result is mock_user
        assert mock_db.rollback.called

    @pytest.mark.asyncio
    @patch("app.services.user_sync_service.httpx.AsyncClient")
    async def test_sync_clerk_user_with_secondary_email(self, mock_http_client, mock_db):
        """Sync Clerk user using secondary email when primary not set."""
        clerk_id = "clerk_secondary"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": clerk_id,
            "email_addresses": [
                {"id": "email_2", "email_address": "secondary@strike.sh"}
            ],
            "primary_email_address_id": None,
            "first_name": "Secondary",
            "last_name": "User",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_http_client.return_value = mock_client_instance

        result = await sync_clerk_user(mock_db, clerk_id)

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    @patch("app.services.user_sync_service.httpx.AsyncClient")
    async def test_sync_clerk_user_no_name_defaults_to_email(
        self, mock_http_client, mock_db
    ):
        """Sync Clerk user with no name uses email prefix."""
        clerk_id = "clerk_no_name"

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": clerk_id,
            "email_addresses": [
                {"id": "email_1", "email_address": "noname@strike.sh"}
            ],
            "primary_email_address_id": "email_1",
            "first_name": "",
            "last_name": "",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_http_client.return_value = mock_client_instance

        result = await sync_clerk_user(mock_db, clerk_id)

        assert result is not None
        assert mock_db.add.called
