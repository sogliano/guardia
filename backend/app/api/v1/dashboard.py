"""Dashboard API endpoint: aggregate statistics."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: DbSession,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sender: str | None = Query(None),
):
    """Return aggregate dashboard statistics."""
    svc = DashboardService(db)
    data = await svc.get_stats(
        date_from=date_from, date_to=date_to, sender=sender,
    )

    stats_raw = data["stats"]
    by_verdict = stats_raw.get("by_verdict", {})

    return DashboardResponse(
        stats={
            "total_emails_analyzed": stats_raw["total_emails"],
            "emails_today": stats_raw["emails_today"],
            "blocked_count": by_verdict.get("blocked", 0),
            "quarantined_count": by_verdict.get("quarantined", 0),
            "warned_count": by_verdict.get("warned", 0),
            "allowed_count": by_verdict.get("allowed", 0),
            "avg_score": stats_raw["avg_score"],
            "pending_cases": stats_raw["pending_cases"],
        },
        risk_distribution=data["risk_distribution"],
        daily_trend=data["daily_trend"],
        threat_categories=data["threat_categories"],
        pipeline_health=data.get("pipeline_health"),
        recent_cases=data.get("recent_cases", []),
        active_alerts=data.get("active_alerts", []),
        top_senders=data.get("top_senders", []),
        verdict_trend=data.get("verdict_trend", []),
        score_distribution=data.get("score_distribution", []),
    )
