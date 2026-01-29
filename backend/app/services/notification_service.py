"""Notification service: create, list, and manage user notifications."""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_notifications(
        self,
        user_id: UUID,
        is_read: bool | None = None,
        page: int = 1,
        size: int = 50,
    ) -> dict:
        """List notifications for a user with optional read filter."""
        query = select(Notification).where(Notification.user_id == user_id)

        if is_read is not None:
            query = query.where(Notification.is_read == is_read)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Unread count (always)
        unread_count = (
            await self.db.execute(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            )
        ).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "unread_count": unread_count,
        }

    async def mark_read(self, notification_id: UUID) -> bool:
        """Mark a single notification as read."""
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0  # type: ignore[return-value]

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount  # type: ignore[return-value]

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        severity: str,
        title: str,
        message: str | None = None,
        reference_id: UUID | None = None,
        reference_type: str | None = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            severity=severity,
            title=title,
            message=message,
            reference_id=reference_id,
            reference_type=reference_type,
            is_read=False,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread notification count for a user."""
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        return result.scalar() or 0
