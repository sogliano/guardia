from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Email(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "emails"

    message_id: Mapped[str] = mapped_column(String(998), unique=True, nullable=False, index=True)
    sender_email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    sender_name: Mapped[str | None] = mapped_column(String(255))
    reply_to: Mapped[str | None] = mapped_column(String(320))
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False)
    recipients_cc: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    subject: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    urls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    auth_results: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    case: Mapped["Case"] = relationship(back_populates="email")

    __table_args__ = (
        Index("ix_emails_sender_received", "sender_email", received_at.desc()),
    )
