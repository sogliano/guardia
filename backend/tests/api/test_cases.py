import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4


class TestCasesAPI:
    @pytest.mark.asyncio
    async def test_list_cases(self, client):
        """Test list cases endpoint."""
        mock_result = {
            "items": [
                {
                    "id": str(uuid4()),
                    "case_number": 1,
                    "email_id": str(uuid4()),
                    "verdict": "ALLOWED",
                    "final_score": 0.15,
                    "status": "pending",
                    "risk_level": "low",
                    "threat_category": "clean",
                    "pipeline_duration_ms": 100,
                    "resolved_by": None,
                    "resolved_at": None,
                    "sender_email": "alice@example.com",
                    "subject": "Test Case 1",
                    "created_at": "2026-02-02T00:00:00Z",
                    "updated_at": "2026-02-02T00:00:00Z",
                },
                {
                    "id": str(uuid4()),
                    "case_number": 2,
                    "email_id": str(uuid4()),
                    "verdict": "WARN",
                    "final_score": 0.45,
                    "status": "pending",
                    "risk_level": "medium",
                    "threat_category": "suspicious",
                    "pipeline_duration_ms": 150,
                    "resolved_by": None,
                    "resolved_at": None,
                    "sender_email": "bob@example.com",
                    "subject": "Test Case 2",
                    "created_at": "2026-02-02T00:00:00Z",
                    "updated_at": "2026-02-02T00:00:00Z",
                },
            ],
            "total": 2,
            "page": 1,
            "size": 20,
            "pages": 1,
        }

        with patch("app.api.v1.cases.CaseService") as MockService:
            mock_svc = AsyncMock()
            mock_svc.list_cases.return_value = mock_result
            MockService.return_value = mock_svc

            response = await client.get("/api/v1/cases?page=1&size=20")

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 2
            assert data["total"] == 2
            assert data["page"] == 1
            mock_svc.list_cases.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_case_detail(self, client):
        """Test get case detail endpoint."""
        case_id = uuid4()
        email_id = uuid4()
        mock_case = {
            "id": str(case_id),
            "case_number": 1,
            "email_id": str(email_id),
            "verdict": "QUARANTINE",
            "final_score": 0.85,
            "status": "pending",
            "email": {
                "id": str(email_id),
                "message_id": "test@strike.sh",
                "sender_email": "phishing@evil.com",
                "subject": "Urgent: Verify Your Account",
            },
            "analyses": [
                {
                    "id": str(uuid4()),
                    "stage": "heuristic",
                    "score": 0.75,
                    "evidences": [],
                }
            ],
            "notes": [],
            "fp_reviews": [],
        }

        with patch("app.api.v1.cases.CaseService") as MockService:
            mock_svc = AsyncMock()
            mock_svc.get_case_detail.return_value = mock_case
            MockService.return_value = mock_svc

            response = await client.get(f"/api/v1/cases/{case_id}/detail")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(case_id)
            assert data["verdict"] == "QUARANTINE"
            assert data["final_score"] == 0.85
            assert "email" in data
            assert "analyses" in data
            mock_svc.get_case_detail.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_case(self, client):
        """Test resolve case endpoint."""
        case_id = uuid4()
        user_id = uuid4()
        payload = {
            "verdict": "allowed",
        }

        mock_case = {
            "id": str(case_id),
            "case_number": 1,
            "status": "resolved",
            "verdict": "ALLOWED",
            "resolution": "approve",
        }

        with (
            patch("app.api.v1.cases.CaseService") as MockService,
            patch("app.api.deps.get_current_user") as MockUser,
        ):
            mock_svc = AsyncMock()
            mock_svc.resolve_case.return_value = mock_case
            MockService.return_value = mock_svc
            MockUser.return_value = {"id": str(user_id)}

            response = await client.post(f"/api/v1/cases/{case_id}/resolve", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "resolved"
            assert data["resolution"] == "approve"
