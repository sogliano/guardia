import pytest


class TestAuthAPI:
    async def test_login(self, client):
        # TODO: Test login endpoint
        pass

    async def test_logout(self, client):
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
