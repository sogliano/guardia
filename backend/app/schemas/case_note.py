from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CaseNoteCreate(BaseModel):
    content: str


class CaseNoteResponse(BaseModel):
    id: UUID
    case_id: UUID
    author_id: UUID
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
