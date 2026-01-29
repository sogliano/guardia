"""Dashboard service: aggregate statistics for the dashboard view."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import CaseStatus
from app.models.alert_event import AlertEvent
from app.models.analysis import Analysis
from app.models.case import Case
from app.models.email import Email


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_stats(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        sender: str | None = None,
    ) -> dict:
        """Build complete dashboard statistics with optional filters."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Determine trend range
        if date_from:
            trend_since = datetime.fromisoformat(date_from)
        else:
            trend_since = now - timedelta(days=30)

        # Build set of email IDs matching sender filter (if any)
        sender_email_ids = None
        if sender:
            safe = sender.replace("%", "\\%").replace("_", "\\_")
            id_q = select(Email.id).where(Email.sender_email.ilike(f"%{safe}%"))
            result = await self.db.execute(id_q)
            sender_email_ids = [r[0] for r in result.all()]
            if not sender_email_ids:
                return self._empty_stats()

        def _apply_case_filters(q):  # type: ignore[no-untyped-def]
            if date_from:
                q = q.where(Case.created_at >= date_from)
            if date_to:
                q = q.where(Case.created_at <= date_to)
            if sender_email_ids is not None:
                q = q.where(Case.email_id.in_(sender_email_ids))
            return q

        def _apply_email_filters(q):  # type: ignore[no-untyped-def]
            if date_from:
                q = q.where(Email.created_at >= date_from)
            if date_to:
                q = q.where(Email.created_at <= date_to)
            if sender_email_ids is not None:
                q = q.where(Email.id.in_(sender_email_ids))
            return q

        # Total emails
        eq = select(func.count()).select_from(Email)
        eq = _apply_email_filters(eq)
        total_emails = (await self.db.execute(eq)).scalar() or 0

        # Emails today
        et = select(func.count()).select_from(Email).where(Email.created_at >= today_start)
        et = _apply_email_filters(et)
        emails_today = (await self.db.execute(et)).scalar() or 0

        # Cases by verdict
        vq = select(Case.verdict, func.count()).where(Case.verdict.isnot(None)).group_by(
            Case.verdict
        )
        vq = _apply_case_filters(vq)
        verdict_counts = await self.db.execute(vq)
        by_verdict = {row[0]: row[1] for row in verdict_counts.all()}

        # Pending cases
        pq = (
            select(func.count())
            .select_from(Case)
            .where(
                Case.status.in_([
                    CaseStatus.PENDING, CaseStatus.ANALYZING, CaseStatus.QUARANTINED,
                ])
            )
        )
        pq = _apply_case_filters(pq)
        pending_cases = (await self.db.execute(pq)).scalar() or 0

        # Total cases
        tcq = select(func.count()).select_from(Case)
        tcq = _apply_case_filters(tcq)
        total_cases = (await self.db.execute(tcq)).scalar() or 0

        # Average score
        aq = select(func.avg(Case.final_score)).where(Case.final_score.isnot(None))
        aq = _apply_case_filters(aq)
        avg_score = (await self.db.execute(aq)).scalar() or 0.0

        # Risk distribution
        rq = (
            select(Case.risk_level, func.count())
            .where(Case.risk_level.isnot(None))
            .group_by(Case.risk_level)
        )
        rq = _apply_case_filters(rq)
        risk_counts = await self.db.execute(rq)
        risk_distribution = [
            {"label": row[0], "value": row[1]} for row in risk_counts.all()
        ]

        # Daily trend
        daily_trend = await self._get_daily_trend(
            trend_since, sender_email_ids=sender_email_ids, date_to=date_to,
        )

        # Threat categories
        tq = (
            select(Case.threat_category, func.count())
            .where(Case.threat_category.isnot(None))
            .group_by(Case.threat_category)
        )
        tq = _apply_case_filters(tq)
        threat_counts = await self.db.execute(tq)
        threat_categories = [
            {"category": row[0], "count": row[1]} for row in threat_counts.all()
        ]

        pipeline_health = await self._get_pipeline_health()
        recent_cases = await self._get_recent_critical_cases(
            sender_email_ids=sender_email_ids, date_from=date_from, date_to=date_to,
        )
        active_alerts = await self._get_active_alerts()
        top_senders = await self._get_top_senders(date_from=date_from, date_to=date_to)
        verdict_trend = await self._get_verdict_trend(
            trend_since, sender_email_ids=sender_email_ids, date_to=date_to,
        )
        score_distribution = await self._get_score_distribution(
            sender_email_ids=sender_email_ids, date_from=date_from, date_to=date_to,
        )

        return {
            "stats": {
                "total_emails": total_emails,
                "emails_today": emails_today,
                "total_cases": total_cases,
                "pending_cases": pending_cases,
                "avg_score": round(float(avg_score), 4),
                "by_verdict": by_verdict,
            },
            "risk_distribution": risk_distribution,
            "daily_trend": daily_trend,
            "threat_categories": threat_categories,
            "pipeline_health": pipeline_health,
            "recent_cases": recent_cases,
            "active_alerts": active_alerts,
            "top_senders": top_senders,
            "verdict_trend": verdict_trend,
            "score_distribution": score_distribution,
        }

    def _empty_stats(self) -> dict:
        """Return empty dashboard when filters match nothing."""
        return {
            "stats": {
                "total_emails": 0, "emails_today": 0, "total_cases": 0,
                "pending_cases": 0, "avg_score": 0.0, "by_verdict": {},
            },
            "risk_distribution": [],
            "daily_trend": [],
            "threat_categories": [],
            "pipeline_health": None,
            "recent_cases": [],
            "active_alerts": [],
            "top_senders": [],
            "verdict_trend": [],
            "score_distribution": [],
        }

    async def _get_daily_trend(
        self,
        since: datetime,
        sender_email_ids: list | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Get daily email count."""
        q = (
            select(
                func.date(Case.created_at).label("date"),
                func.count().label("count"),
            )
            .where(Case.created_at >= since)
        )
        if date_to:
            q = q.where(Case.created_at <= date_to)
        if sender_email_ids is not None:
            q = q.where(Case.email_id.in_(sender_email_ids))
        q = q.group_by(func.date(Case.created_at)).order_by(func.date(Case.created_at))
        result = await self.db.execute(q)
        return [
            {"label": str(row.date), "value": row.count} for row in result.all()
        ]

    async def _get_pipeline_health(self) -> dict | None:
        """Get pipeline performance metrics."""
        result = await self.db.execute(
            select(
                func.avg(Case.pipeline_duration_ms).label("avg_ms"),
                func.count().label("total"),
            )
            .where(Case.pipeline_duration_ms.isnot(None))
        )
        row = result.first()
        if not row or not row.avg_ms:
            return None

        # p95 duration
        p95_result = await self.db.execute(
            select(
                func.percentile_cont(0.95).within_group(Case.pipeline_duration_ms)
            ).where(Case.pipeline_duration_ms.isnot(None))
        )
        p95_val = p95_result.scalar() or 0.0

        stage_result = await self.db.execute(
            select(
                Analysis.stage,
                func.avg(Analysis.execution_time_ms).label("avg_ms"),
            )
            .where(Analysis.execution_time_ms.isnot(None))
            .group_by(Analysis.stage)
        )
        stage_avg = {r.stage: round(float(r.avg_ms), 1) for r in stage_result.all()}

        analyzed = (
            await self.db.execute(
                select(func.count())
                .select_from(Case)
                .where(Case.status.in_([
                    CaseStatus.ANALYZED, CaseStatus.RESOLVED, CaseStatus.QUARANTINED,
                ]))
            )
        ).scalar() or 0

        total = (
            await self.db.execute(select(func.count()).select_from(Case))
        ).scalar() or 1

        return {
            "avg_duration_ms": round(float(row.avg_ms), 1),
            "p95_duration_ms": round(float(p95_val), 1),
            "success_rate": round(analyzed / max(total, 1), 4),
            "stage_avg_ms": stage_avg,
        }

    async def _get_recent_critical_cases(
        self,
        limit: int = 10,
        sender_email_ids: list | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Get the most recent cases with high risk scores."""
        q = (
            select(Case)
            .options(selectinload(Case.email))
            .where(Case.final_score.isnot(None))
        )
        if date_from:
            q = q.where(Case.created_at >= date_from)
        if date_to:
            q = q.where(Case.created_at <= date_to)
        if sender_email_ids is not None:
            q = q.where(Case.email_id.in_(sender_email_ids))
        q = q.order_by(Case.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        cases = result.scalars().all()
        return [
            {
                "id": str(c.id),
                "subject": c.email.subject if c.email else None,
                "sender": c.email.sender_email if c.email else "unknown",
                "score": c.final_score,
                "verdict": c.verdict,
                "created_at": c.created_at.isoformat(),
            }
            for c in cases
        ]

    async def _get_active_alerts(self, limit: int = 10) -> list[dict]:
        """Get the most recent alert events with their rule names."""
        result = await self.db.execute(
            select(AlertEvent)
            .options(selectinload(AlertEvent.alert_rule))
            .order_by(AlertEvent.created_at.desc())
            .limit(limit)
        )
        events = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "rule_name": e.alert_rule.name if e.alert_rule else "Unknown Rule",
                "severity": e.severity,
                "message": str(e.trigger_info.get("message", "Alert triggered")),
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]

    async def _get_verdict_trend(
        self,
        since: datetime,
        sender_email_ids: list | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Get daily verdict counts for stacked area chart."""
        q = (
            select(
                func.date(Case.created_at).label("date"),
                Case.verdict,
                func.count().label("count"),
            )
            .where(Case.created_at >= since)
            .where(Case.verdict.isnot(None))
        )
        if date_to:
            q = q.where(Case.created_at <= date_to)
        if sender_email_ids is not None:
            q = q.where(Case.email_id.in_(sender_email_ids))
        q = q.group_by(func.date(Case.created_at), Case.verdict).order_by(
            func.date(Case.created_at)
        )
        result = await self.db.execute(q)
        rows = result.all()

        # Pivot into per-date records
        by_date: dict[str, dict[str, int]] = {}
        for row in rows:
            d = str(row.date)
            if d not in by_date:
                by_date[d] = {"allow": 0, "warn": 0, "quarantine": 0, "block": 0}
            verdict = row.verdict
            if verdict in ("allowed",):
                by_date[d]["allow"] += row.count
            elif verdict in ("warned",):
                by_date[d]["warn"] += row.count
            elif verdict in ("quarantined",):
                by_date[d]["quarantine"] += row.count
            elif verdict in ("blocked",):
                by_date[d]["block"] += row.count

        return [
            {"date": d, **counts} for d, counts in sorted(by_date.items())
        ]

    async def _get_score_distribution(
        self,
        sender_email_ids: list | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Get score distribution in 10 buckets (0.0-0.1, ..., 0.9-1.0)."""
        q = (
            select(
                func.width_bucket(Case.final_score, 0.0, 1.0, 10).label("bucket"),
                func.count().label("count"),
            )
            .where(Case.final_score.isnot(None))
        )
        if date_from:
            q = q.where(Case.created_at >= date_from)
        if date_to:
            q = q.where(Case.created_at <= date_to)
        if sender_email_ids is not None:
            q = q.where(Case.email_id.in_(sender_email_ids))
        q = q.group_by("bucket").order_by("bucket")
        result = await self.db.execute(q)

        # Build all 10 buckets
        bucket_counts = {i: 0 for i in range(1, 11)}
        for row in result.all():
            b = row.bucket
            if 1 <= b <= 10:
                bucket_counts[b] = row.count

        labels = [
            f"{(i - 1) / 10:.1f}-{i / 10:.1f}" for i in range(1, 11)
        ]
        return [
            {"range": labels[i], "count": bucket_counts[i + 1]}
            for i in range(10)
        ]

    async def _get_top_senders(
        self,
        limit: int = 10,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict]:
        """Get top senders by email count with avg score."""
        q = (
            select(
                Email.sender_email,
                func.count().label("email_count"),
                func.avg(Case.final_score).label("avg_score"),
            )
            .join(Case, Case.email_id == Email.id)
        )
        if date_from:
            q = q.where(Case.created_at >= date_from)
        if date_to:
            q = q.where(Case.created_at <= date_to)
        q = (
            q.group_by(Email.sender_email)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        return [
            {
                "sender": row.sender_email,
                "count": row.email_count,
                "avg_score": round(float(row.avg_score or 0), 4),
            }
            for row in result.all()
        ]
