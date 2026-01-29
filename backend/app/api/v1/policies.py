"""Policy API endpoints: CRUD for policy entries and custom rules."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.policy import (
    CustomRuleCreate,
    CustomRuleResponse,
    CustomRuleUpdate,
    PolicyEntryCreate,
    PolicyEntryList,
    PolicyEntryResponse,
    PolicyEntryUpdate,
)
from app.services.policy_service import PolicyService

router = APIRouter()

# ── Policy Entries ────────────────────────────────────────────


@router.get("/entries", response_model=PolicyEntryList)
async def list_entries(
    db: DbSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    list_type: str | None = None,
):
    """List policy entries with optional filter by list_type."""
    svc = PolicyService(db)
    result = await svc.list_entries(page=page, size=size, list_type=list_type)
    return result


@router.post("/entries", response_model=PolicyEntryResponse, status_code=201)
async def create_entry(
    body: PolicyEntryCreate, db: DbSession, user: CurrentUser
):
    """Create a new policy entry (whitelist/blacklist)."""
    svc = PolicyService(db)
    entry = await svc.create_entry(
        list_type=body.list_type,
        entry_type=body.entry_type,
        value=body.value,
        is_active=body.is_active,
        added_by=user.id,
    )
    await db.commit()
    return entry


@router.get("/entries/{entry_id}", response_model=PolicyEntryResponse)
async def get_entry(entry_id: UUID, db: DbSession):
    """Get a single policy entry."""
    svc = PolicyService(db)
    entry = await svc.get_entry(entry_id)
    if not entry:
        raise NotFoundError("Policy entry not found")
    return entry


@router.put("/entries/{entry_id}", response_model=PolicyEntryResponse)
async def update_entry(
    entry_id: UUID, body: PolicyEntryUpdate, db: DbSession
):
    """Update a policy entry."""
    svc = PolicyService(db)
    entry = await svc.update_entry(entry_id, is_active=body.is_active)
    if not entry:
        raise NotFoundError("Policy entry not found")
    await db.commit()
    return entry


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(entry_id: UUID, db: DbSession):
    """Delete a policy entry."""
    svc = PolicyService(db)
    deleted = await svc.delete_entry(entry_id)
    if not deleted:
        raise NotFoundError("Policy entry not found")
    await db.commit()


# ── Custom Rules ──────────────────────────────────────────────


@router.get("/rules", response_model=list[CustomRuleResponse])
async def list_custom_rules(db: DbSession):
    """List all custom rules."""
    svc = PolicyService(db)
    result = await svc.list_custom_rules()
    return result["items"]


@router.post("/rules", response_model=CustomRuleResponse, status_code=201)
async def create_custom_rule(
    body: CustomRuleCreate, db: DbSession, user: CurrentUser
):
    """Create a new custom rule."""
    svc = PolicyService(db)
    rule = await svc.create_custom_rule(
        name=body.name,
        description=body.description,
        conditions=body.conditions,
        action=body.action,
        is_active=body.is_active,
        created_by=user.id,
    )
    await db.commit()
    return rule


@router.get("/rules/{rule_id}", response_model=CustomRuleResponse)
async def get_custom_rule(rule_id: UUID, db: DbSession):
    """Get a single custom rule."""
    svc = PolicyService(db)
    rule = await svc.get_custom_rule(rule_id)
    if not rule:
        raise NotFoundError("Custom rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=CustomRuleResponse)
async def update_custom_rule(
    rule_id: UUID, body: CustomRuleUpdate, db: DbSession
):
    """Update a custom rule."""
    svc = PolicyService(db)
    rule = await svc.update_custom_rule(
        rule_id,
        name=body.name,
        description=body.description,
        conditions=body.conditions,
        action=body.action,
        is_active=body.is_active,
    )
    if not rule:
        raise NotFoundError("Custom rule not found")
    await db.commit()
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_custom_rule(rule_id: UUID, db: DbSession):
    """Delete a custom rule."""
    svc = PolicyService(db)
    deleted = await svc.delete_custom_rule(rule_id)
    if not deleted:
        raise NotFoundError("Custom rule not found")
    await db.commit()
