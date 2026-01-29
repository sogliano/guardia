from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, model_validator


class CaseNoteCreate(BaseModel):
    content: str


class CaseNoteUpdate(BaseModel):
    content: str


class CaseNoteResponse(BaseModel):
    id: UUID
    case_id: UUID
    author_id: UUID
    author_name: str | None = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def extract_author_name(cls, data):  # type: ignore[no-untyped-def]
        if hasattr(data, "author") and data.author is not None:
            data.__dict__["author_name"] = data.author.full_name
        return data
