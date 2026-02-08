import jwt

from app.config import settings


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT using the PEM public key (RS256).
    Returns the decoded payload dict on success, raises PyJWTError on failure.

    In local/development mode, issuer verification is skipped.
    In production/staging, issuer is verified if clerk_issuer_url is configured.
    Audience verification is always disabled (Clerk doesn't send aud by default).
    """
    options = {
        "verify_exp": True,
        "verify_nbf": True,
        "verify_aud": False,  # Clerk doesn't send aud claim by default
    }

    kwargs: dict = {}
    is_local = settings.app_env in ("local", "development")

    if not is_local and settings.clerk_issuer_url:
        options["verify_iss"] = True
        kwargs["issuer"] = settings.clerk_issuer_url
    else:
        options["verify_iss"] = False

    return jwt.decode(
        token,
        key=settings.clerk_pem_public_key,
        algorithms=["RS256"],
        options=options,
        **kwargs,
    )
