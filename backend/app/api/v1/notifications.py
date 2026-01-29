"""Notification API endpoints: list, mark read, unread count."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.notification import NotificationList
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationList)
async def list_notifications(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_read: bool | None = None,
):
    """List notifications for the current user."""
    svc = NotificationService(db)
    result = await svc.list_notifications(
        user_id=user.id, is_read=is_read, page=page, size=size
    )
    return result


@router.put("/{notification_id}/read", response_model=dict)
async def mark_notification_read(notification_id: UUID, db: DbSession):
    """Mark a single notification as read."""
    svc = NotificationService(db)
    success = await svc.mark_read(notification_id)
    if not success:
        raise NotFoundError("Notification not found")
    await db.commit()
    return {"ok": True}


@router.post("/mark-all-read", response_model=dict)
async def mark_all_read(db: DbSession, user: CurrentUser):
    """Mark all notifications as read for the current user."""
    svc = NotificationService(db)
    count = await svc.mark_all_read(user.id)
    await db.commit()
    return {"updated": count}


@router.get("/unread-count", response_model=dict)
async def get_unread_count(db: DbSession, user: CurrentUser):
    """Get unread notification count for the current user."""
    svc = NotificationService(db)
    count = await svc.get_unread_count(user.id)
    return {"unread_count": count}
