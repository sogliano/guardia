"""Email service: ingest, list, and retrieve emails."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.email import Email
from app.schemas.email import EmailIngest


class EmailService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ingest(self, data: EmailIngest) -> Email:
        """Create a new email record. Returns existing if message_id is duplicated."""
        email = Email(
            message_id=data.message_id,
            sender_email=data.sender_email,
            sender_name=data.sender_name,
            reply_to=data.reply_to,
            recipient_email=data.recipient_email,
            recipients_cc=data.recipients_cc,
            subject=data.subject,
            body_text=data.body_text,
            body_html=data.body_html,
            headers=data.headers,
            urls=data.urls,
            attachments=data.attachments,
            auth_results=data.auth_results,
            received_at=data.received_at,
        )
        self.db.add(email)
        try:
            await self.db.flush()
            return email
        except IntegrityError:
            await self.db.rollback()
            stmt = select(Email).where(Email.message_id == data.message_id)
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing
            raise

    async def list_emails(
        self,
        page: int = 1,
        size: int = 50,
        sender: str | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        risk_level: str | None = None,
    ) -> dict:
        """List emails with pagination and optional filters."""
        query = select(Email).options(selectinload(Email.case))

        if sender:
            safe = sender.replace("%", "\\%").replace("_", "\\_")
            query = query.where(Email.sender_email.ilike(f"%{safe}%"))
        if search:
            safe = search.replace("%", "\\%").replace("_", "\\_")
            query = query.where(
                Email.subject.ilike(f"%{safe}%")
                | Email.sender_email.ilike(f"%{safe}%")
            )
        if date_from:
            query = query.where(Email.received_at >= date_from)
        if date_to:
            query = query.where(Email.received_at <= date_to)
        if risk_level:
            query = query.join(Email.case).where(
                Case.risk_level == risk_level
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(Email.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        emails = result.scalars().all()

        items = []
        for email in emails:
            items.append({
                "id": email.id,
                "message_id": email.message_id,
                "sender_email": email.sender_email,
                "sender_name": email.sender_name,
                "reply_to": email.reply_to,
                "recipient_email": email.recipient_email,
                "recipients_cc": email.recipients_cc,
                "subject": email.subject,
                "body_text": email.body_text,
                "headers": email.headers,
                "urls": email.urls,
                "attachments": email.attachments,
                "auth_results": email.auth_results,
                "received_at": email.received_at,
                "ingested_at": email.ingested_at,
                "created_at": email.created_at,
                "risk_level": email.case.risk_level if email.case else None,
                "verdict": email.case.verdict if email.case else None,
                "final_score": email.case.final_score if email.case else None,
            })

        return {"items": items, "total": total, "page": page, "size": size}

    async def get_email(self, email_id: UUID) -> Email | None:
        """Get a single email by ID."""
        stmt = select(Email).where(Email.id == email_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
