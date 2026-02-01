"""Monitoring API endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import limiter
from app.schemas.monitoring import (
    HeuristicsMonitoringResponse,
    MLMonitoringResponse,
    MonitoringResponse,
    ScoreAnalysisResponse,
)
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("")
@limiter.limit("30/minute")
async def get_monitoring(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    tab: str = Query("llm"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
):
    """Get monitoring metrics for specified tab (llm, ml, or heuristics)."""
    parsed_from = (
        datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        if date_from else None
    )
    parsed_to = (
        datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
        if date_to else None
    )
    svc = MonitoringService(db)

    if tab == "llm":
        data = await svc.get_llm_stats(date_from=parsed_from, date_to=parsed_to)
        return MonitoringResponse(**data)
    elif tab == "ml":
        data = await svc.get_ml_stats(date_from=parsed_from, date_to=parsed_to)
        return MLMonitoringResponse(**data)
    elif tab == "heuristics":
        data = await svc.get_heuristics_stats(date_from=parsed_from, date_to=parsed_to)
        return HeuristicsMonitoringResponse(**data)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tab parameter: {tab}. Must be 'llm', 'ml', or 'heuristics'."
        )


@router.get("/score-analysis", response_model=ScoreAnalysisResponse)
@limiter.limit("40/minute")
async def get_score_analysis(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    include_metrics: bool = Query(True),
    db: DbSession = ...,
    user: CurrentUser = ...,
):
    """Get detailed score breakdown for recent cases with engine agreement metrics."""
    svc = MonitoringService(db)
    return await svc.get_score_analysis(limit=limit, include_metrics=include_metrics)
