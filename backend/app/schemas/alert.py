from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Alert Rules ──────────────────────────────────────────────

class AlertRuleCreate(BaseModel):
    name: str
    description: str | None = None
    severity: str  # info | warning | critical
    conditions: dict = {}
    channels: list[str] = []  # ["email", "slack"]
    is_active: bool = True


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    severity: str | None = None
    conditions: dict | None = None
    channels: list[str] | None = None
    is_active: bool | None = None


class AlertRuleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    severity: str
    conditions: dict
    channels: list[str]
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Alert Events ─────────────────────────────────────────────

class AlertEventResponse(BaseModel):
    id: UUID
    alert_rule_id: UUID
    case_id: UUID | None
    severity: str
    channel: str
    delivery_status: str
    trigger_info: dict
    delivered_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertEventList(BaseModel):
    items: list[AlertEventResponse]
    total: int
    page: int
    size: int
