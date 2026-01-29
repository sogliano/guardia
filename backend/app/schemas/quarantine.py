from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class QuarantineActionCreate(BaseModel):
    action: str  # released | kept | deleted
    reason: str | None = None


class QuarantineActionResponse(BaseModel):
    id: UUID
    case_id: UUID
    action: str
    reason: str | None
    performed_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class QuarantineEmailDetailResponse(BaseModel):
    case_id: str
    subject: str | None
    sender_email: str
    sender_name: str | None
    recipient_email: str
    reply_to: str | None
    received_at: datetime | None
    message_id: str
    auth_results: dict
    body_preview: str | None
    urls: list
    attachments: list
    risk_level: str | None
    final_score: float | None
    threat_category: str | None
    ai_explanation: str | None
