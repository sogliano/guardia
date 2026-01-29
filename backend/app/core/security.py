import jwt
from jwt.exceptions import PyJWTError

from app.config import settings


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT using the PEM public key (RS256).
    Returns the decoded payload dict on success, raises PyJWTError on failure.
    """
    payload = jwt.decode(
        token,
        key=settings.clerk_pem_public_key,
        algorithms=["RS256"],
        options={
            "verify_exp": True,
            "verify_nbf": True,
            "verify_aud": False,
        },
    )
    return payload
