import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

case_number_seq = Sequence("case_number_seq")


class Case(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cases"

    case_number: Mapped[int] = mapped_column(
        Integer,
        case_number_seq,
        server_default=case_number_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    final_score: Mapped[float | None] = mapped_column(Float)
    risk_level: Mapped[str | None] = mapped_column(String(20), index=True)
    verdict: Mapped[str | None] = mapped_column(String(20), index=True)
    threat_category: Mapped[str | None] = mapped_column(String(30))
    pipeline_duration_ms: Mapped[int | None] = mapped_column(Integer)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    email: Mapped["Email"] = relationship(back_populates="case")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="case")
    quarantine_actions: Mapped[list["QuarantineActionRecord"]] = relationship(
        back_populates="case"
    )
    fp_reviews: Mapped[list["FPReview"]] = relationship(back_populates="case")
    notes: Mapped[list["CaseNote"]] = relationship(back_populates="case")
    resolver: Mapped["User | None"] = relationship()

    __table_args__ = (
        Index("ix_cases_verdict_created", "verdict", "created_at"),
        CheckConstraint(
            "final_score IS NULL OR (final_score >= 0.0 AND final_score <= 1.0)",
            name="ck_cases_final_score_range",
        ),
    )
