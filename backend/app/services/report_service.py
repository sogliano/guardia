"""Report service: generate CSV and PDF exports of case data."""

import csv
import io
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.email import Email


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_csv(self, filters: dict) -> bytes:
        """Generate CSV report of cases matching filters.

        Filters:
          - date_from, date_to: ISO date strings
          - verdict: filter by verdict
          - risk_level: filter by risk level
          - threat_category: filter by threat category
        """
        cases = await self._query_cases(filters)

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Case ID",
            "Created At",
            "Sender",
            "Recipient",
            "Subject",
            "Score",
            "Risk Level",
            "Verdict",
            "Threat Category",
            "Pipeline Duration (ms)",
            "Status",
        ])

        # Rows
        for case in cases:
            email = case.email
            writer.writerow([
                str(case.id),
                case.created_at.isoformat() if case.created_at else "",
                email.sender_email if email else "",
                email.recipient_email if email else "",
                email.subject if email else "",
                f"{case.final_score:.4f}" if case.final_score is not None else "",
                case.risk_level or "",
                case.verdict or "",
                case.threat_category or "",
                case.pipeline_duration_ms or "",
                case.status,
            ])

        return output.getvalue().encode("utf-8")

    async def generate_pdf(self, filters: dict) -> bytes:
        """Generate PDF report of cases.

        Uses basic HTML-to-PDF approach. Falls back to CSV-like text if
        reportlab/weasyprint not available.
        """
        cases = await self._query_cases(filters)

        # Simple text-based PDF fallback
        lines: list[str] = []
        lines.append("Guard-IA Case Report")
        lines.append(f"Generated: {datetime.utcnow().isoformat()}")
        lines.append(f"Total Cases: {len(cases)}")
        lines.append("=" * 60)

        for case in cases:
            email = case.email
            lines.append(f"\nCase: {case.id}")
            lines.append(f"  Date: {case.created_at}")
            lines.append(f"  From: {email.sender_email if email else 'N/A'}")
            lines.append(f"  Subject: {email.subject if email else 'N/A'}")
            lines.append(f"  Score: {case.final_score}")
            lines.append(f"  Verdict: {case.verdict}")
            lines.append(f"  Risk: {case.risk_level}")
            lines.append(f"  Category: {case.threat_category}")

        return "\n".join(lines).encode("utf-8")

    async def _query_cases(self, filters: dict) -> list[Case]:
        """Query cases with filters, eager-loading email."""
        query = select(Case).options(selectinload(Case.email))

        if filters.get("date_from"):
            query = query.where(Case.created_at >= filters["date_from"])
        if filters.get("date_to"):
            query = query.where(Case.created_at <= filters["date_to"])
        if filters.get("verdict"):
            query = query.where(Case.verdict == filters["verdict"])
        if filters.get("risk_level"):
            query = query.where(Case.risk_level == filters["risk_level"])
        if filters.get("threat_category"):
            query = query.where(Case.threat_category == filters["threat_category"])

        query = query.order_by(Case.created_at.desc()).limit(10000)
        result = await self.db.execute(query)
        return list(result.scalars().all())
