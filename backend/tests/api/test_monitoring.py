"""Monitoring API endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_get_monitoring_invalid_tab(client):
    """Invalid tab returns 400."""
    response = await client.get("/api/v1/monitoring", params={"tab": "invalid"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_monitoring_requires_auth():
    """Monitoring without auth returns error."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/monitoring", params={"tab": "llm"})
        assert response.status_code in (401, 403, 500)
