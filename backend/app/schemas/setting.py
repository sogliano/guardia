from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SettingUpdate(BaseModel):
    value: dict | str | int | float | bool | list


class SettingResponse(BaseModel):
    id: UUID
    key: str
    value: dict | str | int | float | bool | list
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
