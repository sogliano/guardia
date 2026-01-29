from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FPReviewCreate(BaseModel):
    decision: str  # confirmed_fp | kept_flagged
    notes: str | None = None


class FPReviewResponse(BaseModel):
    id: UUID
    case_id: UUID
    decision: str
    reviewer_id: UUID
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
