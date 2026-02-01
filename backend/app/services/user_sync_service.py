import httpx
import structlog
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
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://api.clerk.com/v1/users/{clerk_id}",
                headers={
                    "Authorization": f"Bearer {settings.clerk_secret_key}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            clerk_user = response.json()
        except Exception as exc:
            logger.error("Failed to fetch Clerk user", clerk_id=clerk_id, error=str(exc))
            raise UnauthorizedError("Unable to verify user identity")

    if not clerk_user:
        raise UnauthorizedError("User not found in Clerk")

    # Extract primary email
    email = None
    email_addresses = clerk_user.get("email_addresses", [])
    primary_email_id = clerk_user.get("primary_email_address_id")

    if email_addresses:
        primary = next(
            (e for e in email_addresses if e.get("id") == primary_email_id),
            email_addresses[0],
        )
        email = primary.get("email_address")

    if not email:
        raise UnauthorizedError("Clerk user has no email address")

    # Build full name
    first_name = clerk_user.get("first_name", "")
    last_name = clerk_user.get("last_name", "")
    full_name = " ".join(part for part in [first_name, last_name] if part) or email.split("@")[0]

    # Create local user record
    user = User(
        clerk_id=clerk_id,
        email=email,
        full_name=full_name,
        role="analyst",
        is_active=True,
    )
    db.add(user)

    try:
        await db.commit()
        await db.refresh(user)
        logger.info("Created local user from Clerk", clerk_id=clerk_id, email=email)
        return user
    except Exception as e:
        # Race condition: another request created the user already
        await db.rollback()
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.clerk_id == clerk_id))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            logger.info("User already created by concurrent request", clerk_id=clerk_id)
            return existing_user
        raise
