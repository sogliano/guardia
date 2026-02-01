"""Quarantine API endpoints: list, detail, release, keep, delete."""

from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession, RequireAnalyst
from app.core.exceptions import NotFoundError
from app.core.rate_limit import limiter
from app.schemas.case import CaseList, CaseResponse
from app.schemas.quarantine import QuarantineEmailDetailResponse
from app.services.quarantine_service import QuarantineService

router = APIRouter()


@router.get("", response_model=CaseList)
@limiter.limit("60/minute")
async def list_quarantined(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    sender: str | None = Query(None),
):
    """List quarantined cases with pagination."""
    svc = QuarantineService(db)
    result = await svc.list_quarantined(
        page=page, size=size, date_from=date_from, date_to=date_to, sender=sender,
    )
    return result


@router.get(
    "/{case_id}/email", response_model=QuarantineEmailDetailResponse
)
@limiter.limit("100/minute")
async def get_quarantine_email_detail(request: Request, case_id: UUID, db: DbSession, user: CurrentUser):
    """Get full email detail for a quarantined case."""
    svc = QuarantineService(db)
    detail = await svc.get_email_detail(case_id)
    if not detail:
        raise NotFoundError("Quarantined case or email not found")
    return detail


@router.post("/{case_id}/release", response_model=CaseResponse)
@limiter.limit("5/minute")
async def release_quarantined(
    request: Request,
    case_id: UUID,
    db: DbSession,
    user: RequireAnalyst,
    reason: str | None = None,
):
    """Release a quarantined email (forward to destination)."""
    svc = QuarantineService(db)
    case = await svc.release(case_id, user.id, reason)
    if not case:
        raise NotFoundError("Quarantined case not found or release failed")
    await db.commit()
    return case


@router.post("/{case_id}/keep", response_model=CaseResponse)
@limiter.limit("5/minute")
async def keep_quarantined(
    request: Request,
    case_id: UUID,
    db: DbSession,
    user: RequireAnalyst,
    reason: str | None = None,
):
    """Keep email quarantined (confirm block)."""
    svc = QuarantineService(db)
    case = await svc.keep(case_id, user.id, reason)
    if not case:
        raise NotFoundError("Quarantined case not found")
    await db.commit()
    return case


@router.post("/{case_id}/delete", response_model=CaseResponse)
@limiter.limit("3/minute")
async def delete_quarantined(
    request: Request,
    case_id: UUID,
    db: DbSession,
    user: RequireAnalyst,
    reason: str | None = None,
):
    """Delete quarantined email permanently."""
    svc = QuarantineService(db)
    case = await svc.delete_quarantined(case_id, user.id, reason)
    if not case:
        raise NotFoundError("Quarantined case not found")
    await db.commit()
    return case
