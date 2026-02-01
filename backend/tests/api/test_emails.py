import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4


class TestEmailsAPI:
    @pytest.mark.asyncio
    async def test_ingest_email(self, client):
        """Test email ingestion endpoint."""
        payload = {
            "message_id": "test123@strike.sh",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender",
            "recipient_email": "victim@strike.sh",
            "subject": "Test Email",
            "body_text": "This is a test email",
            "urls": [],
            "attachments": [],
            "auth_results": {"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        }

        # Mock EmailService
        mock_email = {
            "id": str(uuid4()),
            "message_id": "test123@strike.sh",
            "sender_email": "test@example.com",
            "subject": "Test Email",
            "verdict": "ALLOWED",
        }

        with patch("app.api.v1.emails.EmailService") as MockService:
            mock_svc = AsyncMock()
            mock_svc.ingest.return_value = mock_email
            MockService.return_value = mock_svc

            response = await client.post("/api/v1/emails/ingest", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert data["message_id"] == "test123@strike.sh"
            assert data["sender_email"] == "test@example.com"
            mock_svc.ingest.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_emails(self, client):
        """Test list emails endpoint."""
        mock_result = {
            "items": [
                {
                    "id": str(uuid4()),
                    "message_id": "msg1@strike.sh",
                    "sender_email": "alice@example.com",
                    "subject": "Test 1",
                    "verdict": "ALLOWED",
                },
                {
                    "id": str(uuid4()),
                    "message_id": "msg2@strike.sh",
                    "sender_email": "bob@example.com",
                    "subject": "Test 2",
                    "verdict": "WARN",
                },
            ],
            "total": 2,
            "page": 1,
            "size": 50,
            "pages": 1,
        }

        with patch("app.api.v1.emails.EmailService") as MockService:
            mock_svc = AsyncMock()
            mock_svc.list_emails.return_value = mock_result
            MockService.return_value = mock_svc

            response = await client.get("/api/v1/emails?page=1&size=50")

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 2
            assert data["total"] == 2
            assert data["page"] == 1
            mock_svc.list_emails.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_email(self, client):
        """Test get email detail endpoint."""
        email_id = uuid4()
        mock_email = {
            "id": str(email_id),
            "message_id": "detail@strike.sh",
            "sender_email": "sender@example.com",
            "subject": "Detail Test",
            "verdict": "ALLOWED",
            "body_text": "Email body content",
        }

        with patch("app.api.v1.emails.EmailService") as MockService:
            mock_svc = AsyncMock()
            mock_svc.get_email.return_value = mock_email
            MockService.return_value = mock_svc

            response = await client.get(f"/api/v1/emails/{email_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(email_id)
            assert data["message_id"] == "detail@strike.sh"
            mock_svc.get_email.assert_called_once_with(email_id)
