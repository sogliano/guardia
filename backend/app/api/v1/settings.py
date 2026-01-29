"""Settings API endpoints: get and update application settings."""

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.models.setting import Setting
from app.schemas.setting import SettingResponse, SettingUpdate

router = APIRouter()


@router.get("", response_model=list[SettingResponse])
async def get_settings(db: DbSession):
    """Get all application settings."""
    result = await db.execute(select(Setting).order_by(Setting.key))
    settings = result.scalars().all()
    return settings


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(key: str, db: DbSession):
    """Get a single setting by key."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise NotFoundError(f"Setting '{key}' not found")
    return setting


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str, body: SettingUpdate, db: DbSession, user: CurrentUser
):
    """Update a setting value. Creates the setting if it doesn't exist."""
    result = await db.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()

    if setting:
        setting.value = body.value
        setting.updated_by = user.id
    else:
        setting = Setting(key=key, value=body.value, updated_by=user.id)
        db.add(setting)

    await db.flush()
    await db.commit()
    return setting
