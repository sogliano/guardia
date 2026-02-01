"""Case service: list, detail, resolve, and manage investigation cases."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import CaseStatus
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.case_note import CaseNote
from app.models.email import Email
from app.models.user import User


class CaseService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_cases(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
        risk_level: str | None = None,
        verdict: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        search: str | None = None,
        sender: str | None = None,
    ) -> dict:
        """List cases with filters and pagination."""
        query = select(Case).options(
            selectinload(Case.email),
        )
        joined = False

        if status:
            query = query.where(Case.status == status)
        if risk_level:
            query = query.where(Case.risk_level == risk_level)
        if verdict:
            query = query.where(Case.verdict == verdict)
        if date_from:
            query = query.where(Case.created_at >= date_from)
        if date_to:
            query = query.where(Case.created_at <= date_to)
        if sender:
            safe_s = sender.replace("%", "\\%").replace("_", "\\_")
            if not joined:
                query = query.join(Case.email)
                joined = True
            query = query.where(Email.sender_email.ilike(f"%{safe_s}%"))
        if search:
            safe = search.replace("%", "\\%").replace("_", "\\_")
            if not joined:
                query = query.join(Case.email)
                joined = True
            query = query.where(
                Email.subject.ilike(f"%{safe}%")
                | Email.sender_email.ilike(f"%{safe}%")
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        offset = (page - 1) * size
        query = query.order_by(Case.created_at.desc()).offset(offset).limit(size)
        result = await self.db.execute(query)
        cases = result.scalars().all()

        # Fetch only needed analyses (latest per case/stage) in one targeted query
        case_ids = [case.id for case in cases]
        analyses_map: dict[UUID, dict[str, float | None]] = {}

        if case_ids:
            analyses_stmt = (
                select(Analysis)
                .where(Analysis.case_id.in_(case_ids))
                .order_by(Analysis.created_at.desc())
            )
            analyses_result = await self.db.execute(analyses_stmt)
            all_analyses = analyses_result.scalars().all()

            # Build map: {case_id: {stage: score}}
            for analysis in all_analyses:
                if analysis.case_id not in analyses_map:
                    analyses_map[analysis.case_id] = {}
                if analysis.stage not in analyses_map[analysis.case_id]:
                    # Only store first (latest) analysis per stage
                    analyses_map[analysis.case_id][analysis.stage] = analysis.score

        items = []
        for case in cases:
            stage_scores = analyses_map.get(case.id, {})
            # Ensure all stages are present with None as default
            stage_scores = {
                "heuristic": stage_scores.get("heuristic"),
                "ml": stage_scores.get("ml"),
                "llm": stage_scores.get("llm"),
            }

            item = {
                "id": case.id,
                "case_number": case.case_number,
                "email_id": case.email_id,
                "status": case.status,
                "final_score": case.final_score,
                "risk_level": case.risk_level,
                "verdict": case.verdict,
                "threat_category": case.threat_category,
                "pipeline_duration_ms": case.pipeline_duration_ms,
                "resolved_by": case.resolved_by,
                "resolved_at": case.resolved_at,
                "created_at": case.created_at,
                "updated_at": case.updated_at,
                "email_subject": case.email.subject if case.email else None,
                "email_sender": case.email.sender_email if case.email else None,
                "email_received_at": (
                    case.email.received_at if case.email else None
                ),
                "heuristic_score": stage_scores["heuristic"],
                "ml_score": stage_scores["ml"],
                "llm_score": stage_scores["llm"],
            }
            items.append(item)

        return {"items": items, "total": total, "page": page, "size": size}

    async def get_case(self, case_id: UUID) -> Case | None:
        """Get case by ID."""
        stmt = select(Case).where(Case.id == case_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_case_detail(self, case_id: UUID) -> Case | None:
        """Get case with all related data (analyses, evidences, notes)."""
        stmt = (
            select(Case)
            .where(Case.id == case_id)
            .options(
                selectinload(Case.email),
                selectinload(Case.analyses).selectinload(Analysis.evidences),
                selectinload(Case.notes).selectinload(CaseNote.author),
                selectinload(Case.quarantine_actions),
                selectinload(Case.fp_reviews),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def resolve_case(
        self, case_id: UUID, verdict: str, user_id: UUID
    ) -> Case | None:
        """Resolve a case with a final verdict."""
        stmt = select(Case).where(Case.id == case_id).with_for_update()
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        if not case:
            return None

        case.status = CaseStatus.RESOLVED
        case.verdict = verdict
        case.resolved_by = user_id
        case.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        return case

    async def add_note(
        self, case_id: UUID, author_id: UUID, content: str
    ) -> CaseNote:
        """Add a note to a case."""
        note = CaseNote(
            case_id=case_id,
            author_id=author_id,
            content=content,
        )
        self.db.add(note)
        await self.db.flush()
        return note

    async def update_note(
        self, note_id: UUID, author_id: UUID, content: str
    ) -> CaseNote | None:
        """Update a note's content (only by original author)."""
        stmt = select(CaseNote).where(CaseNote.id == note_id)
        result = await self.db.execute(stmt)
        note = result.scalar_one_or_none()
        if not note or note.author_id != author_id:
            return None
        note.content = content
        await self.db.flush()
        return note

    async def get_analyses(self, case_id: UUID) -> list[Analysis]:
        """Get all analyses for a case with their evidences."""
        stmt = (
            select(Analysis)
            .where(Analysis.case_id == case_id)
            .options(selectinload(Analysis.evidences))
            .order_by(Analysis.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
