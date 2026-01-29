import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PolicyEntry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "policy_entries"

    list_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # Relationships
    creator: Mapped["User | None"] = relationship()

    __table_args__ = (
        UniqueConstraint("list_type", "entry_type", "value", name="uq_policy_entries_list_value"),
    )
