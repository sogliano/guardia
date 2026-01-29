"""Email API endpoints: ingest, list, get."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.core.exceptions import NotFoundError
from app.schemas.email import EmailIngest, EmailList, EmailResponse
from app.services.email_service import EmailService

router = APIRouter()


@router.post("/ingest", response_model=EmailResponse, status_code=201)
async def ingest_email(body: EmailIngest, db: DbSession):
    """Ingest a new email into the system."""
    svc = EmailService(db)
    email = await svc.ingest(body)
    await db.commit()
    return email


@router.get("", response_model=EmailList)
async def list_emails(
    db: DbSession,
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
async def get_email(email_id: UUID, db: DbSession):
    """Get a single email by ID."""
    svc = EmailService(db)
    email = await svc.get_email(email_id)
    if not email:
        raise NotFoundError("Email not found")
    return email
