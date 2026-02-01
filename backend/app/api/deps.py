from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends
from jwt.exceptions import PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_bearer_token
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import verify_clerk_token
from app.db.session import get_db
from app.models.user import User
from app.services.user_sync_service import sync_clerk_user

logger = structlog.get_logger()

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: str = Depends(get_bearer_token),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Verify the Clerk JWT and return the local User record.
    If no local record exists, create one via JIT provisioning.
    """
    try:
        payload = verify_clerk_token(token)
    except PyJWTError as e:
        logger.error("Token verification failed", error=str(e))
        raise UnauthorizedError("Invalid or expired token")

    clerk_id: str | None = payload.get("sub")
    if not clerk_id:
        raise UnauthorizedError("Token missing subject claim")

    result = await db.execute(
        select(User).where(User.clerk_id == clerk_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        logger.info("User not found locally, attempting JIT provisioning", clerk_id=clerk_id)
        try:
            user = await sync_clerk_user(db, clerk_id)
            logger.info("User created successfully via JIT", clerk_id=clerk_id, email=user.email)
        except Exception as e:
            logger.error("JIT provisioning failed", clerk_id=clerk_id, error=str(e), error_type=type(e).__name__)
            raise

    if not user.is_active:
        raise ForbiddenError("User account is deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_id(
    user: User = Depends(get_current_user),
) -> UUID:
    """Convenience dependency that returns just the user's UUID."""
    return user.id


def require_role(*allowed_roles: str):
    """Factory that returns a dependency enforcing the user has one of the allowed roles."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            required = ", ".join(allowed_roles)
            raise ForbiddenError(f"Role '{user.role}' not authorized. Required: {required}")
        return user

    return _check


RequireAdmin = Annotated[User, Depends(require_role("administrator"))]
RequireAnalyst = Annotated[User, Depends(require_role("administrator", "analyst"))]
RequireAuditor = Annotated[User, Depends(require_role("administrator", "analyst", "auditor"))]
