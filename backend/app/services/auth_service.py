from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_clerk_id(self, clerk_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.clerk_id == clerk_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
