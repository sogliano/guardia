from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    severity: str
    title: str
    message: str | None
    is_read: bool
    reference_id: UUID | None
    reference_type: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
