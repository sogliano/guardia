from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    clerk_id: str
    email: str
    full_name: str
    role: str = "analyst"


class UserResponse(BaseModel):
    id: UUID
    clerk_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
