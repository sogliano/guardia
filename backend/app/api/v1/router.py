from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    auth,
    cases,
    dashboard,
    emails,
    monitoring,
    notifications,
    policies,
    quarantine,
    reports,
    settings,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(quarantine.router, prefix="/quarantine", tags=["quarantine"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
