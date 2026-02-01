"""Monitoring API endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.monitoring import (
    HeuristicsMonitoringResponse,
    MLMonitoringResponse,
    MonitoringResponse,
)
from app.services.monitoring_service import MonitoringService

router = APIRouter()


@router.get("")
async def get_monitoring(
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
