"""
API endpoints for email ingestion control.

Allows starting, stopping, and monitoring the gradual ingestion of email datasets.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.rate_limit import limiter
from app.api.deps import CurrentUser, RequireAdmin
from app.services.ingestion.queue import get_queue
from backend.scripts.datasets.email_dataset_50 import (
    get_dataset,
    get_by_category,
    get_dataset_stats,
)


router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


class StartIngestionRequest(BaseModel):
    """Request body for starting ingestion."""

    category: str | None = Field(
        None,
        description="Filter by category: legitimate, phishing, bec, malware, scam, spear",
    )
    interval_seconds: float = Field(
        5.0,
        ge=0.1,
        le=60.0,
        description="Time between emails (seconds)",
    )


class IngestionStatusResponse(BaseModel):
    """Response for ingestion status."""

    is_running: bool
    total: int
    processed: int
    failed: int
    queue_remaining: int
    started_at: str | None
    completed_at: str | None


class DatasetStatsResponse(BaseModel):
    """Response for dataset statistics."""

    total: int
    categories: dict[str, int]


@router.post("/start")
@limiter.limit("5/minute")
async def start_ingestion(
    request: Request,
    body: StartIngestionRequest,
    user: RequireAdmin,
) -> dict:
    """
    Start gradual ingestion of email dataset.

    Loads emails into queue and processes them in the background
    at the specified interval (default: 1 email every 5 seconds).

    Only admins can start ingestion.
    """
    queue = get_queue()

    if queue.is_running:
        raise HTTPException(status_code=400, detail="Ingestion already running")

    # Load dataset
    if body.category:
        dataset = get_by_category(body.category)
        if not dataset:
            raise HTTPException(
                status_code=404, detail=f"Category '{body.category}' not found"
            )
    else:
        dataset = get_dataset()

    if not dataset:
        raise HTTPException(status_code=400, detail="No emails in dataset")

    # Configure interval
    queue.interval_seconds = body.interval_seconds
    queue.load_dataset(dataset)

    # Start background processing
    await queue.start()

    return {
        "message": "Ingestion started",
        "total_emails": len(dataset),
        "interval_seconds": body.interval_seconds,
        "category": body.category or "all",
    }


@router.post("/stop")
@limiter.limit("10/minute")
async def stop_ingestion(
    request: Request,
    user: RequireAdmin,
) -> dict:
    """
    Stop ongoing ingestion.

    Cancels the background task and returns final statistics.
    """
    queue = get_queue()

    if not queue.is_running:
        raise HTTPException(status_code=400, detail="No ingestion running")

    await queue.stop()

    return {
        "message": "Ingestion stopped",
        "stats": queue.get_stats(),
    }


@router.get("/status", response_model=IngestionStatusResponse)
@limiter.limit("60/minute")
async def get_ingestion_status(
    request: Request,
    user: CurrentUser,
) -> IngestionStatusResponse:
    """
    Get current ingestion status.

    Returns queue statistics including progress, failures, and timing.
    """
    queue = get_queue()
    stats = queue.get_stats()

    return IngestionStatusResponse(
        is_running=stats["is_running"],
        total=stats["total"],
        processed=stats["processed"],
        failed=stats["failed"],
        queue_remaining=stats["queue_remaining"],
        started_at=stats["started_at"].isoformat() if stats["started_at"] else None,
        completed_at=stats["completed_at"].isoformat()
        if stats["completed_at"]
        else None,
    )


@router.get("/dataset/stats", response_model=DatasetStatsResponse)
@limiter.limit("60/minute")
async def get_dataset_statistics(
    request: Request,
    user: CurrentUser,
) -> DatasetStatsResponse:
    """
    Get statistics about the email dataset.

    Returns total count and distribution by category.
    """
    dataset = get_dataset()
    stats = get_dataset_stats()

    return DatasetStatsResponse(
        total=len(dataset),
        categories=stats,
    )
