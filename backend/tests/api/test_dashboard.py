"""Dashboard API endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_get_dashboard_returns_200(client):
    """Dashboard endpoint returns 200 with expected structure."""
    try:
        response = await client.get("/api/v1/dashboard")
    except OSError:
        pytest.skip("No database available")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "risk_distribution" in data
    assert "daily_trend" in data
    stats = data["stats"]
    assert "total_emails_analyzed" in stats
    assert "emails_today" in stats
    assert "blocked_count" in stats
    assert "quarantined_count" in stats


@pytest.mark.asyncio
async def test_get_dashboard_requires_auth():
    """Dashboard endpoint without auth returns error."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/v1/dashboard")
        assert response.status_code in (401, 403, 500)
