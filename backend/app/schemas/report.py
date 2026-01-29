from datetime import datetime

from pydantic import BaseModel


class ReportFilter(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    risk_level: str | None = None
    verdict: str | None = None
    threat_category: str | None = None
    status: str | None = None


class ReportExport(BaseModel):
    format: str = "csv"  # csv | pdf
    filters: ReportFilter = ReportFilter()
