"""Email API endpoints: ingest, list, get."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.core.rate_limit import limiter
from app.schemas.email import EmailIngest, EmailList, EmailResponse
from app.services.email_service import EmailService
from app.services.pipeline.orchestrator import PipelineOrchestrator

logger = structlog.get_logger()

router = APIRouter()


@router.post("/ingest", response_model=EmailResponse, status_code=201)
@limiter.limit("100/minute")
async def ingest_email(request: Request, body: EmailIngest, db: DbSession, user: CurrentUser):
    """Ingest a new email into the system."""
    svc = EmailService(db)
    email = await svc.ingest(body)
    await db.commit()
    
    # Trigger analysis pipeline
    try:
        orchestrator = PipelineOrchestrator(db)
        await orchestrator.analyze(email.id)
        await db.commit()
    except Exception as e:
        logger.error("ingest_pipeline_failed", error=str(e), email_id=str(email.id))

    return email


@router.get("", response_model=EmailList)
@limiter.limit("300/minute")
async def list_emails(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    sender: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    risk_level: str | None = None,
):
    """List emails with pagination and optional filters."""
    svc = EmailService(db)
    result = await svc.list_emails(
        page=page,
        size=size,
        sender=sender,
        search=search,
        date_from=date_from,
        date_to=date_to,
        risk_level=risk_level,
    )
    return result


@router.get("/{email_id}", response_model=EmailResponse)
@limiter.limit("500/minute")
async def get_email(request: Request, email_id: UUID, db: DbSession, user: CurrentUser):
    """Get a single email by ID."""
    svc = EmailService(db)
    email = await svc.get_email(email_id)
    if not email:
        raise NotFoundError("Email not found")
    return email
