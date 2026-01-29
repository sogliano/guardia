"""Alert API endpoints: CRUD for alert rules and list alert events."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.alert import (
    AlertEventList,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
)
from app.services.alert_service import AlertService

router = APIRouter()

# ── Alert Rules ───────────────────────────────────────────────


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(
    db: DbSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List alert rules with pagination."""
    svc = AlertService(db)
    result = await svc.list_rules(page=page, size=size)
    return result["items"]


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_rule(
    body: AlertRuleCreate, db: DbSession, user: CurrentUser
):
    """Create a new alert rule."""
    svc = AlertService(db)
    rule = await svc.create_rule(
        name=body.name,
        description=body.description,
        severity=body.severity,
        conditions=body.conditions,
        channels=body.channels,
        created_by=user.id,
    )
    await db.commit()
    return rule


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_rule(rule_id: UUID, db: DbSession):
    """Get a single alert rule."""
    svc = AlertService(db)
    rule = await svc.get_rule(rule_id)
    if not rule:
        raise NotFoundError("Alert rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: UUID, body: AlertRuleUpdate, db: DbSession
):
    """Update an alert rule."""
    svc = AlertService(db)
    rule = await svc.update_rule(
        rule_id,
        name=body.name,
        description=body.description,
        severity=body.severity,
        conditions=body.conditions,
        channels=body.channels,
        is_active=body.is_active,
    )
    if not rule:
        raise NotFoundError("Alert rule not found")
    await db.commit()
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: UUID, db: DbSession):
    """Delete an alert rule."""
    svc = AlertService(db)
    deleted = await svc.delete_rule(rule_id)
    if not deleted:
        raise NotFoundError("Alert rule not found")
    await db.commit()


# ── Alert Events ──────────────────────────────────────────────


@router.get("/events", response_model=AlertEventList)
async def list_events(
    db: DbSession,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List alert events with pagination."""
    svc = AlertService(db)
    result = await svc.list_events(page=page, size=size)
    return result
