"""Report API endpoints: export CSV/PDF."""

import io

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import DbSession
from app.schemas.report import ReportExport
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/export")
async def export_report(body: ReportExport, db: DbSession):
    """Generate and download a report in CSV or PDF format."""
    svc = ReportService(db)
    filters = body.filters.model_dump(exclude_none=True)

    if body.format == "pdf":
        data = await svc.generate_pdf(filters)
        return StreamingResponse(
            io.BytesIO(data),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=guardia-report.pdf"},
        )

    # Default: CSV
    data = await svc.generate_csv(filters)
    return StreamingResponse(
        io.BytesIO(data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=guardia-report.csv"},
    )
