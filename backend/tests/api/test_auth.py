import pytest


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_get_me(self, client):
        """Test /auth/me endpoint returns current user."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
