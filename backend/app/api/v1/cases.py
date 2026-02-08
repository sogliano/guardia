"""Case API endpoints: list, detail, resolve, notes, analyses, fp-review."""

from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSession, RequireAnalyst
from app.core.exceptions import NotFoundError
from app.core.rate_limit import limiter
from app.models.case import Case
from app.schemas.analysis import AnalysisWithEvidencesResponse
from app.schemas.case import CaseDetailResponse, CaseList, CaseResolve, CaseResponse
from app.schemas.case_note import CaseNoteCreate, CaseNoteResponse, CaseNoteUpdate
from app.schemas.fp_review import FPReviewCreate, FPReviewResponse
from app.services.case_service import CaseService

router = APIRouter()


async def _resolve_case_id(case_id_str: str, db: AsyncSession) -> UUID:
    """Parse case_id as case_number (int) or UUID."""
    try:
        num = int(case_id_str)
        stmt = select(Case.id).where(Case.case_number == num)
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise NotFoundError("Case not found")
        return row
    except ValueError:
        return UUID(case_id_str)


@router.get("", response_model=CaseList)
@limiter.limit("60/minute")
async def list_cases(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    risk_level: str | None = None,
    verdict: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search: str | None = None,
    sender: str | None = None,
):
    """List cases with filters and pagination."""
    svc = CaseService(db)
    result = await svc.list_cases(
        page=page,
        size=size,
        status=status,
        risk_level=risk_level,
        verdict=verdict,
        date_from=date_from,
        date_to=date_to,
        search=search,
        sender=sender,
    )
    return result


@router.get("/{case_id}", response_model=CaseResponse)
@limiter.limit("100/minute")
async def get_case(request: Request, case_id: str, db: DbSession, user: CurrentUser):
    """Get a single case."""
    resolved_id = await _resolve_case_id(case_id, db)
    svc = CaseService(db)
    case = await svc.get_case(resolved_id)
    if not case:
        raise NotFoundError("Case not found")
    return case


@router.get("/{case_id}/detail", response_model=CaseDetailResponse)
@limiter.limit("100/minute")
async def get_case_detail(request: Request, case_id: str, db: DbSession, user: CurrentUser):
    """Get case with all related data (email, analyses, evidences, notes, fp reviews)."""
    resolved_id = await _resolve_case_id(case_id, db)
    svc = CaseService(db)
    case = await svc.get_case_detail(resolved_id)
    if not case:
        raise NotFoundError("Case not found")
    return case


@router.post("/{case_id}/resolve", response_model=CaseResponse)
@limiter.limit("10/minute")
async def resolve_case(
    request: Request, case_id: str, body: CaseResolve, db: DbSession, user: RequireAnalyst
):
    """Resolve a case with a final verdict."""
    resolved_id = await _resolve_case_id(case_id, db)
    svc = CaseService(db)
    case = await svc.resolve_case(resolved_id, body.verdict, user.id)
    if not case:
        raise NotFoundError("Case not found")
    await db.commit()
    return case


@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=201)
@limiter.limit("30/minute")
async def add_note(
    request: Request, case_id: str, body: CaseNoteCreate, db: DbSession, user: CurrentUser
):
    """Add an investigation note to a case."""
    resolved_id = await _resolve_case_id(case_id, db)
    svc = CaseService(db)
    # Verify case exists
    case = await svc.get_case(resolved_id)
    if not case:
        raise NotFoundError("Case not found")
    note = await svc.add_note(resolved_id, user.id, body.content)
    await db.commit()
    return note


@router.patch("/{case_id}/notes/{note_id}", response_model=CaseNoteResponse)
@limiter.limit("20/minute")
async def update_note(
    request: Request,
    case_id: str,
    note_id: UUID,
    body: CaseNoteUpdate,
    db: DbSession,
    user: CurrentUser,
):
    """Update a note's content (only by original author)."""
    await _resolve_case_id(case_id, db)
    svc = CaseService(db)
    note = await svc.update_note(note_id, user.id, body.content)
    if not note:
        raise NotFoundError("Note not found or not authorized")
    await db.commit()
    return note


@router.get("/{case_id}/analyses", response_model=list[AnalysisWithEvidencesResponse])
@limiter.limit("100/minute")
async def get_analyses(request: Request, case_id: str, db: DbSession, user: CurrentUser):
    """Get pipeline analyses for a case with their evidences."""
    resolved_id = await _resolve_case_id(case_id, db)
    svc = CaseService(db)
    analyses = await svc.get_analyses(resolved_id)
    return analyses


@router.post(
    "/{case_id}/fp-review", response_model=FPReviewResponse, status_code=201
)
@limiter.limit("5/minute")
async def create_fp_review(
    request: Request, case_id: str, body: FPReviewCreate, db: DbSession, user: RequireAnalyst
):
    """Submit a false positive review for a case."""
    resolved_id = await _resolve_case_id(case_id, db)
    case_svc = CaseService(db)
    case = await case_svc.get_case(resolved_id)
    if not case:
        raise NotFoundError("Case not found")
    review = await case_svc.create_fp_review(
        case_id=resolved_id,
        reviewer_id=user.id,
        decision=body.decision,
        notes=body.notes,
    )
    await db.commit()
    return review
