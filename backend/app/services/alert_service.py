"""Alert service: CRUD for alert rules, evaluate and fire alert events."""

from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AlertDeliveryStatus
from app.models.alert_event import AlertEvent
from app.models.alert_rule import AlertRule
from app.models.case import Case

logger = structlog.get_logger()


class AlertService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Alert Rules ---

    async def list_rules(self, page: int = 1, size: int = 50) -> dict:
        """List alert rules with pagination."""
        query = select(AlertRule)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(AlertRule.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total, "page": page, "size": size}

    async def create_rule(
        self,
        name: str,
        description: str | None,
        severity: str,
        conditions: dict,
        channels: list[str],
        created_by: UUID | None = None,
    ) -> AlertRule:
        """Create a new alert rule."""
        rule = AlertRule(
            name=name,
            description=description,
            severity=severity,
            conditions=conditions,
            channels=channels,
            is_active=True,
            created_by=created_by,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def get_rule(self, rule_id: UUID) -> AlertRule | None:
        stmt = select(AlertRule).where(AlertRule.id == rule_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_rule(
        self,
        rule_id: UUID,
        name: str | None = None,
        description: str | None = None,
        severity: str | None = None,
        conditions: dict | None = None,
        channels: list[str] | None = None,
        is_active: bool | None = None,
    ) -> AlertRule | None:
        """Update an alert rule."""
        rule = await self.get_rule(rule_id)
        if not rule:
            return None
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if severity is not None:
            rule.severity = severity
        if conditions is not None:
            rule.conditions = conditions
        if channels is not None:
            rule.channels = channels
        if is_active is not None:
            rule.is_active = is_active
        await self.db.flush()
        return rule

    async def delete_rule(self, rule_id: UUID) -> bool:
        rule = await self.get_rule(rule_id)
        if not rule:
            return False
        await self.db.delete(rule)
        await self.db.flush()
        return True

    # --- Alert Events ---

    async def list_events(self, page: int = 1, size: int = 50) -> dict:
        """List alert events with pagination."""
        query = select(AlertEvent)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(AlertEvent.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total, "page": page, "size": size}

    async def evaluate_and_fire(self, case: Case) -> list[AlertEvent]:
        """Evaluate all active alert rules against a case and fire matching alerts."""
        stmt = select(AlertRule).where(AlertRule.is_active.is_(True))
        result = await self.db.execute(stmt)
        rules = result.scalars().all()

        fired: list[AlertEvent] = []
        for rule in rules:
            if self._matches(rule, case):
                for channel in rule.channels:
                    event = AlertEvent(
                        alert_rule_id=rule.id,
                        case_id=case.id,
                        severity=rule.severity,
                        channel=channel,
                        delivery_status=AlertDeliveryStatus.PENDING,
                        trigger_info={
                            "case_id": str(case.id),
                            "verdict": case.verdict,
                            "risk_level": case.risk_level,
                            "final_score": case.final_score,
                            "rule_name": rule.name,
                        },
                    )
                    self.db.add(event)
                    fired.append(event)

        if fired:
            await self.db.flush()
            logger.info(
                "alerts_fired",
                case_id=str(case.id),
                count=len(fired),
            )

        return fired

    def _matches(self, rule: AlertRule, case: Case) -> bool:
        """Check if a case matches an alert rule's conditions."""
        conditions = rule.conditions or {}

        # Check minimum score
        min_score = conditions.get("min_score")
        if min_score is not None and case.final_score is not None:
            if case.final_score < min_score:
                return False

        # Check verdict match
        verdicts = conditions.get("verdicts")
        if verdicts and case.verdict not in verdicts:
            return False

        # Check risk level match
        risk_levels = conditions.get("risk_levels")
        if risk_levels and case.risk_level not in risk_levels:
            return False

        # Check threat category match
        categories = conditions.get("threat_categories")
        if categories and case.threat_category not in categories:
            return False

        return True
