import signal
import sys
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.api.middleware.logging import LoggingMiddleware
from app.api.v1.router import api_router
from app.config import settings
from app.core.constants import GUARD_IA_VERSION
from app.core.exceptions import PipelineError
from app.core.rate_limit import limiter
from app.db.session import async_session_factory, engine

logger = structlog.get_logger()


def _setup_signal_handlers():
    """Setup graceful shutdown on SIGTERM/SIGINT to close DB connections."""
    def handle_shutdown(signum, frame):
        logger.info("shutdown_signal_received", signal=signum)
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)


_SENSITIVE_KEYS = {"app_secret_key", "database_url", "clerk_secret_key",
                    "clerk_pem_public_key", "openai_api_key", "slack_webhook_url",
                    "gateway_internal_token", "google_relay_password",
                    "google_service_account_json"}


def _log_config() -> None:
    """Log loaded config keys at startup (values redacted for sensitive keys)."""
    config_data = {}
    for key in settings.model_fields:
        value = getattr(settings, key)
        if key in _SENSITIVE_KEYS:
            config_data[key] = "***" if value else "(empty)"
        else:
            config_data[key] = str(value)
    logger.info("config_loaded", **config_data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _setup_signal_handlers()
    _log_config()
    logger.info("startup", env=settings.app_env, debug=settings.app_debug)
    yield
    await engine.dispose()
    logger.info("shutdown", message="database connections closed")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Guard-IA",
        description="Corporate email fraud detection middleware",
        version=GUARD_IA_VERSION,
        lifespan=lifespan,
        redirect_slashes=False,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Exception handlers
    @app.exception_handler(PipelineError)
    async def pipeline_error_handler(request: Request, exc: PipelineError) -> JSONResponse:
        logger.error("pipeline_error", stage=exc.stage, detail=exc.message)
        return JSONResponse(
            status_code=502,
            content={"detail": f"Pipeline error at {exc.stage}: {exc.message}"},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc), type=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Middleware (order: last added = first executed)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Request-ID",
        ],
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        db_ok = False
        try:
            async with async_session_factory() as session:
                await session.execute(text("SELECT 1"))
                db_ok = True
        except Exception:
            pass
        status = "ok" if db_ok else "degraded"
        return {"status": status, "version": GUARD_IA_VERSION, "database": db_ok}

    return app


app = create_app()
