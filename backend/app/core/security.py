import jwt

from app.config import settings


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT using the PEM public key (RS256).
    Returns the decoded payload dict on success, raises PyJWTError on failure.

    NOTE: In development (local/development), audience verification is disabled
    because Clerk tokens may not include the 'aud' claim.
    In production/staging, audience verification is enabled for security.
    """
    # Disable audience verification for local development only
    is_local = settings.app_env in ("local", "development")

    if is_local:
        # Development: skip audience verification
        payload = jwt.decode(
            token,
            key=settings.clerk_pem_public_key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                "verify_nbf": True,
                "verify_aud": False,  # Disabled for local dev
            },
        )
    else:
        # Production/Staging: verify audience
        payload = jwt.decode(
            token,
            key=settings.clerk_pem_public_key,
            algorithms=["RS256"],
            audience=settings.clerk_publishable_key,
            options={
                "verify_exp": True,
                "verify_nbf": True,
                "verify_aud": True,  # Enabled for production
            },
        )

    return payload
