"""Policy service: CRUD for whitelist/blacklist entries and custom rules."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_rule import CustomRule
from app.models.policy_entry import PolicyEntry


class PolicyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Policy Entries (Whitelist / Blacklist) ---

    async def list_entries(
        self,
        list_type: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> dict:
        """List policy entries with optional filter by list_type."""
        query = select(PolicyEntry)
        if list_type:
            query = query.where(PolicyEntry.list_type == list_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(PolicyEntry.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total, "page": page, "size": size}

    async def create_entry(
        self,
        list_type: str,
        entry_type: str,
        value: str,
        is_active: bool = True,
        added_by: UUID | None = None,
    ) -> PolicyEntry:
        """Create a new policy entry."""
        entry = PolicyEntry(
            list_type=list_type,
            entry_type=entry_type,
            value=value.lower().strip(),
            is_active=is_active,
            added_by=added_by,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_entry(self, entry_id: UUID) -> PolicyEntry | None:
        """Get a single policy entry by ID."""
        stmt = select(PolicyEntry).where(PolicyEntry.id == entry_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_entry(
        self, entry_id: UUID, is_active: bool | None = None, value: str | None = None
    ) -> PolicyEntry | None:
        """Update a policy entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            return None
        if is_active is not None:
            entry.is_active = is_active
        if value is not None:
            entry.value = value.lower().strip()
        await self.db.flush()
        return entry

    async def delete_entry(self, entry_id: UUID) -> bool:
        """Delete a policy entry."""
        entry = await self.get_entry(entry_id)
        if not entry:
            return False
        await self.db.delete(entry)
        await self.db.flush()
        return True

    async def get_blacklisted_domains(self) -> list[str]:
        """Get all active blacklisted domain values."""
        stmt = select(PolicyEntry.value).where(
            PolicyEntry.list_type == "blacklist",
            PolicyEntry.entry_type == "domain",
            PolicyEntry.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        return [r[0] for r in result.all()]

    async def get_whitelisted_domains(self) -> list[str]:
        """Get all active whitelisted domain values."""
        stmt = select(PolicyEntry.value).where(
            PolicyEntry.list_type == "whitelist",
            PolicyEntry.entry_type == "domain",
            PolicyEntry.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        return [r[0] for r in result.all()]

    # --- Custom Rules ---

    async def list_custom_rules(self, page: int = 1, size: int = 50) -> dict:
        """List custom rules with pagination."""
        query = select(CustomRule)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(CustomRule.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total, "page": page, "size": size}

    async def create_custom_rule(
        self,
        name: str,
        description: str | None,
        conditions: dict,
        action: str,
        is_active: bool = True,
        created_by: UUID | None = None,
    ) -> CustomRule:
        """Create a new custom rule."""
        rule = CustomRule(
            name=name,
            description=description,
            conditions=conditions,
            action=action,
            is_active=is_active,
            created_by=created_by,
        )
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def get_custom_rule(self, rule_id: UUID) -> CustomRule | None:
        stmt = select(CustomRule).where(CustomRule.id == rule_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_custom_rule(
        self,
        rule_id: UUID,
        name: str | None = None,
        description: str | None = None,
        conditions: dict | None = None,
        action: str | None = None,
        is_active: bool | None = None,
    ) -> CustomRule | None:
        """Update a custom rule."""
        rule = await self.get_custom_rule(rule_id)
        if not rule:
            return None
        if name is not None:
            rule.name = name
        if description is not None:
            rule.description = description
        if conditions is not None:
            rule.conditions = conditions
        if action is not None:
            rule.action = action
        if is_active is not None:
            rule.is_active = is_active
        await self.db.flush()
        return rule

    async def delete_custom_rule(self, rule_id: UUID) -> bool:
        rule = await self.get_custom_rule(rule_id)
        if not rule:
            return False
        await self.db.delete(rule)
        await self.db.flush()
        return True
