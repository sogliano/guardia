from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    type: str
    severity: str
    description: str
    raw_data: dict
    created_at: datetime

    model_config = {"from_attributes": True}
