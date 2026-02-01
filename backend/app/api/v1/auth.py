from fastapi import APIRouter, Request

from app.api.deps import CurrentUser
from app.core.rate_limit import limiter
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
@limiter.limit("300/minute")
async def get_me(request: Request, user: CurrentUser):
    """Return the currently authenticated user's profile."""
    return user
