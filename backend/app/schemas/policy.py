from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Policy Entries (Whitelist / Blacklist) ────────────────────

class PolicyEntryCreate(BaseModel):
    list_type: str  # whitelist | blacklist
    entry_type: str  # domain | email | ip
    value: str
    is_active: bool = True


class PolicyEntryUpdate(BaseModel):
    is_active: bool | None = None


class PolicyEntryResponse(BaseModel):
    id: UUID
    list_type: str
    entry_type: str
    value: str
    is_active: bool
    added_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PolicyEntryList(BaseModel):
    items: list[PolicyEntryResponse]
    total: int
    page: int
    size: int


# ── Custom Rules ─────────────────────────────────────────────

class CustomRuleCreate(BaseModel):
    name: str
    description: str | None = None
    conditions: dict = {}
    action: str  # warn | quarantine | block
    is_active: bool = True


class CustomRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    conditions: dict | None = None
    action: str | None = None
    is_active: bool | None = None


class CustomRuleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    conditions: dict
    action: str
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
