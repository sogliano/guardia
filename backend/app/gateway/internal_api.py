"""Internal HTTP API for quarantine operations (runs on the VM alongside SMTP).

Cloud Run calls these endpoints to release/delete quarantined emails whose .eml
files live on the VM's local disk.
"""

from uuid import UUID

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.gateway.relay import RelayClient
from app.gateway.storage import EmailStorage

logger = structlog.get_logger()


class ReleaseRequest(BaseModel):
    sender: str
    recipients: list[str]


def _verify_token(x_gateway_token: str = Header(...)) -> str:
    """Validate the shared secret token."""
    if not settings.gateway_internal_token:
        raise HTTPException(status_code=503, detail="Token not configured")
    if x_gateway_token != settings.gateway_internal_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return x_gateway_token


def create_internal_app() -> FastAPI:
    """Factory for the internal quarantine API."""
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/internal/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.post("/internal/quarantine/{case_id}/release")
    async def release_email(
        case_id: UUID,
        body: ReleaseRequest,
        _token: str = Depends(_verify_token),
    ) -> JSONResponse:
        """Retrieve .eml from disk, forward via relay, then delete."""
        storage = EmailStorage()
        relay = RelayClient()

        raw_data = await storage.retrieve(str(case_id))
        if not raw_data:
            logger.warning("internal_api_eml_not_found", case_id=str(case_id))
            raise HTTPException(status_code=404, detail="Email file not found")

        forwarded = await relay.deferred_forward(
            raw_data=raw_data,
            sender=body.sender,
            recipients=body.recipients,
            case_id=str(case_id),
        )

        if not forwarded:
            logger.error("internal_api_forward_failed", case_id=str(case_id))
            raise HTTPException(status_code=502, detail="SMTP relay failed")

        await storage.delete(str(case_id))
        logger.info(
            "internal_api_email_released",
            case_id=str(case_id),
            sender=body.sender,
            recipients=body.recipients,
        )
        return JSONResponse({"status": "released"})

    @app.post("/internal/quarantine/{case_id}/delete")
    async def delete_email(
        case_id: UUID,
        _token: str = Depends(_verify_token),
    ) -> JSONResponse:
        """Delete .eml from disk storage."""
        storage = EmailStorage()

        deleted = await storage.delete(str(case_id))
        if not deleted:
            logger.warning("internal_api_eml_not_found_for_delete", case_id=str(case_id))
            raise HTTPException(status_code=404, detail="Email file not found")

        logger.info("internal_api_email_deleted", case_id=str(case_id))
        return JSONResponse({"status": "deleted"})

    return app
