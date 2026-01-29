import structlog
from clerk_backend_api import Clerk
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.models.user import User

logger = structlog.get_logger()


async def sync_clerk_user(db: AsyncSession, clerk_id: str) -> User:
    """
    Fetch user info from Clerk Backend API and create a local User record.
    Called during JIT provisioning when a Clerk user first accesses the API.
    """
    try:
        with Clerk(bearer_auth=settings.clerk_secret_key) as clerk:
            clerk_user = clerk.users.get(user_id=clerk_id)
    except Exception as exc:
        logger.error("Failed to fetch Clerk user", clerk_id=clerk_id, error=str(exc))
        raise UnauthorizedError("Unable to verify user identity")

    if clerk_user is None:
        raise UnauthorizedError("User not found in Clerk")

    # Extract primary email
    email = None
    if clerk_user.email_addresses:
        primary = next(
            (e for e in clerk_user.email_addresses if e.id == clerk_user.primary_email_address_id),
            clerk_user.email_addresses[0],
        )
        email = primary.email_address

    if not email:
        raise UnauthorizedError("Clerk user has no email address")

    # Build full name
    full_name = " ".join(
        part for part in [clerk_user.first_name, clerk_user.last_name] if part
    ) or email.split("@")[0]

    # Create local user record
    user = User(
        clerk_id=clerk_id,
        email=email,
        full_name=full_name,
        role="analyst",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("Created local user from Clerk", clerk_id=clerk_id, email=email)
    return user
