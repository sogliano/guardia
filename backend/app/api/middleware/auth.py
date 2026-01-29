from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=True)


async def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract the Bearer token from the Authorization header."""
    return credentials.credentials
