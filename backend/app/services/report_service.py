"""Report service: generate CSV and PDF exports of case data."""

import csv
import io
from datetime import datetime, timezone

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
        """Generate a minimal valid PDF report of cases.

        Uses raw PDF 1.4 syntax to avoid external dependencies.
        """
        cases = await self._query_cases(filters)

        text_lines: list[str] = []
        text_lines.append("Guard-IA Case Report")
        text_lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        text_lines.append(f"Total Cases: {len(cases)}")
        text_lines.append("=" * 60)

        for case in cases:
            email = case.email
            text_lines.append("")
            text_lines.append(f"Case: {case.id}")
            text_lines.append(f"  Date: {case.created_at}")
            text_lines.append(f"  From: {email.sender_email if email else 'N/A'}")
            text_lines.append(f"  Subject: {email.subject if email else 'N/A'}")
            text_lines.append(f"  Score: {case.final_score}")
            text_lines.append(f"  Verdict: {case.verdict}")
            text_lines.append(f"  Risk: {case.risk_level}")
            text_lines.append(f"  Category: {case.threat_category}")

        return self._build_pdf(text_lines)

    @staticmethod
    def _build_pdf(lines: list[str]) -> bytes:
        """Build a minimal valid PDF 1.4 document from text lines."""
        font_size = 10
        leading = 14
        margin_left = 50
        margin_top = 750
        page_height = 842
        page_width = 595

        # Split lines into pages
        max_lines_per_page = (margin_top - 50) // leading
        pages: list[list[str]] = []
        for i in range(0, len(lines), max_lines_per_page):
            pages.append(lines[i:i + max_lines_per_page])

        if not pages:
            pages = [[""]]

        buf = io.BytesIO()
        offsets: list[int] = []
        obj_count = 0

        def write(data: str) -> None:
            buf.write(data.encode("latin-1", errors="replace"))

        def new_obj() -> int:
            nonlocal obj_count
            obj_count += 1
            offsets.append(buf.tell())
            write(f"{obj_count} 0 obj\n")
            return obj_count

        write("%PDF-1.4\n")

        # 1: Catalog
        cat_id = new_obj()
        write(f"<< /Type /Catalog /Pages {cat_id + 1} 0 R >>\nendobj\n")

        # 2: Pages
        pages_id = new_obj()
        first_page_id = pages_id + 2  # after font
        page_refs = " ".join(f"{first_page_id + i * 2} 0 R" for i in range(len(pages)))
        write(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(pages)} >>\nendobj\n")

        # 3: Font
        font_id = new_obj()
        write("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n")

        # Pages + streams
        for page_lines in pages:
            # Build stream content
            stream_lines = [f"BT /F1 {font_size} Tf"]
            y = margin_top
            for line in page_lines:
                safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                stream_lines.append(f"{margin_left} {y} Td ({safe}) Tj")
                y -= leading
            stream_lines.append("ET")
            stream = "\n".join(stream_lines)

            # Stream object
            stream_id = new_obj()
            write(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream\nendobj\n")

            # Page object
            page_id = new_obj()
            write(
                f"<< /Type /Page /Parent {pages_id} 0 R "
                f"/MediaBox [0 0 {page_width} {page_height}] "
                f"/Contents {stream_id} 0 R "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>\n"
                f"endobj\n"
            )

        # xref
        xref_offset = buf.tell()
        write(f"xref\n0 {obj_count + 1}\n")
        write("0000000000 65535 f \n")
        for off in offsets:
            write(f"{off:010d} 00000 n \n")

        write(f"trailer\n<< /Size {obj_count + 1} /Root {cat_id} 0 R >>\n")
        write(f"startxref\n{xref_offset}\n%%EOF\n")

        return buf.getvalue()

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
