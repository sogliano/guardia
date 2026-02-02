from fastapi import APIRouter

from app.api.v1 import (
    auth,
    cases,
    dashboard,
    emails,
    ingestion,
    monitoring,
    quarantine,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(quarantine.router, prefix="/quarantine", tags=["quarantine"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(ingestion.router)
