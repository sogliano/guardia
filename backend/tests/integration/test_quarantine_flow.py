import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime


class TestQuarantineFlow:
    @pytest.mark.asyncio
    async def test_quarantine_approve_flow(self, mock_db):
        """Integration test: Quarantine approve/release flow."""
        from app.models.case import Case
        from app.models.email import Email
        from app.services.quarantine_service import QuarantineService

        # Setup: Create quarantined case
        case_id = uuid4()
        email_id = uuid4()
        user_id = uuid4()

        mock_email = Email(
            id=email_id,
            message_id="quarantine@test.sh",
            sender_email="suspicious@example.com",
            recipient_email="analyst@strike.sh",
            subject="Test Quarantine",
        )

        mock_case = Case(
            id=case_id,
            email_id=email_id,
            verdict="QUARANTINE",
            final_score=0.85,
            status="pending",
            case_number=1,
        )
        # Add email relationship
        mock_case.email = mock_email

        # Mock DB queries - first call returns case, second call returns email
        call_count = 0
        def execute_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:
                # First call: _get_quarantined_case
                mock_result.scalar_one_or_none.return_value = mock_case
            else:
                # Second call: _load_email
                mock_result.scalar_one_or_none.return_value = mock_email
            return mock_result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        # Mock httpx call to VM internal API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "released"}'
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.services.quarantine_service.httpx.AsyncClient",
                  return_value=mock_http_client),
            patch("app.services.quarantine_service.settings") as mock_settings,
        ):
            mock_settings.gateway_api_url = "http://10.0.0.1:8025"
            mock_settings.gateway_internal_token = "test-token"

            # Execute approve/release
            service = QuarantineService(mock_db)
            released_case = await service.release(
                case_id=case_id,
                user_id=user_id,
                reason="False positive - legitimate business email",
            )

            # Assertions
            assert released_case is not None

            # Verify DB operations occurred
            assert mock_db.execute.called
            assert mock_db.add.called  # QuarantineActionRecord should be added

            # Verify httpx was called with correct URL and payload
            mock_http_client.post.assert_called_once()
            call_args = mock_http_client.post.call_args
            assert f"/internal/quarantine/{case_id}/release" in call_args[0][0]
            assert call_args[1]["json"]["sender"] == "suspicious@example.com"

    @pytest.mark.asyncio
    async def test_quarantine_reject_flow(self, mock_db):
        """Integration test: Quarantine reject/delete flow."""
        from app.models.case import Case
        from app.services.quarantine_service import QuarantineService

        # Setup: Create quarantined case
        case_id = uuid4()
        email_id = uuid4()
        user_id = uuid4()

        mock_case = Case(
            id=case_id,
            email_id=email_id,
            verdict="QUARANTINE",
            final_score=0.95,
            status="pending",
            case_number=2,
        )

        # Mock DB query
        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_case
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        # Mock httpx call for delete
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "deleted"}'
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.services.quarantine_service.httpx.AsyncClient",
                  return_value=mock_http_client),
            patch("app.services.quarantine_service.settings") as mock_settings,
        ):
            mock_settings.gateway_api_url = "http://10.0.0.1:8025"
            mock_settings.gateway_internal_token = "test-token"

            # Execute reject/delete
            service = QuarantineService(mock_db)
            deleted_case = await service.delete_quarantined(
                case_id=case_id,
                user_id=user_id,
                reason="Confirmed phishing - permanent deletion",
            )

            # Assertions
            assert deleted_case is not None

            # Verify DB operations occurred
            assert mock_db.execute.called
            assert mock_db.add.called  # QuarantineActionRecord should be added

    @pytest.mark.asyncio
    async def test_quarantine_list_pending(self, mock_db):
        """Integration test: List pending quarantined cases."""
        from app.models.case import Case
        from app.services.quarantine_service import QuarantineService

        # Setup: Create multiple quarantined cases
        cases = [
            Case(
                id=uuid4(),
                email_id=uuid4(),
                verdict="QUARANTINE",
                final_score=0.85,
                status="pending",
                case_number=i,
            )
            for i in range(1, 4)
        ]

        # Mock DB query
        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = cases
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        # Execute list
        service = QuarantineService(mock_db)
        result = await service.list_quarantined(page=1, size=20)

        # Assertions
        assert result is not None
        # Verify query was executed
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_quarantine_action_record_created(self, mock_db):
        """Integration test: Verify QuarantineActionRecord is created on actions."""
        from app.models.case import Case
        from app.models.email import Email
        from app.models.quarantine_action import QuarantineActionRecord
        from app.services.quarantine_service import QuarantineService

        case_id = uuid4()
        email_id = uuid4()
        user_id = uuid4()

        mock_case = Case(
            id=case_id,
            email_id=email_id,
            verdict="QUARANTINE",
            final_score=0.90,
            status="pending",
            case_number=5,
        )

        mock_email = Email(
            id=email_id,
            message_id="test@example.com",
            sender_email="sender@example.com",
            recipient_email="recipient@strike.sh",
            subject="Test",
        )

        # Mock DB query to return both case and email
        def execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            # Return case first, then email
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1

            if execute_side_effect.call_count == 1:
                mock_result.scalar_one_or_none.return_value = mock_case
            else:
                mock_result.scalar_one_or_none.return_value = mock_email
            return mock_result

        mock_db.execute.side_effect = execute_side_effect

        # Mock httpx call to VM internal API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"status": "released"}'
        mock_http_client = AsyncMock()
        mock_http_client.post.return_value = mock_response
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.services.quarantine_service.httpx.AsyncClient",
                  return_value=mock_http_client),
            patch("app.services.quarantine_service.settings") as mock_settings,
        ):
            mock_settings.gateway_api_url = "http://10.0.0.1:8025"
            mock_settings.gateway_internal_token = "test-token"

            # Execute release
            service = QuarantineService(mock_db)
            await service.release(
                case_id=case_id,
                user_id=user_id,
                reason="Releasing for investigation",
            )

            # Verify add was called (should include QuarantineActionRecord)
            assert mock_db.add.called
