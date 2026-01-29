from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_emails_analyzed: int
    emails_today: int
    blocked_count: int
    quarantined_count: int
    warned_count: int
    allowed_count: int
    avg_score: float
    pending_cases: int


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ThreatCategoryCount(BaseModel):
    category: str
    count: int


class PipelineHealthStats(BaseModel):
    avg_duration_ms: float
    p95_duration_ms: float
    success_rate: float
    stage_avg_ms: dict[str, float]


class RecentCaseItem(BaseModel):
    id: str
    subject: str | None
    sender: str
    score: float | None
    verdict: str | None
    created_at: datetime


class ActiveAlertItem(BaseModel):
    id: str
    rule_name: str
    severity: str
    message: str
    created_at: datetime


class TopSenderItem(BaseModel):
    sender: str
    count: int
    avg_score: float


class VerdictTrendPoint(BaseModel):
    date: str
    allow: int = 0
    warn: int = 0
    quarantine: int = 0
    block: int = 0


class ScoreBucket(BaseModel):
    range: str
    count: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    risk_distribution: list[ChartDataPoint]
    daily_trend: list[ChartDataPoint]
    threat_categories: list[ThreatCategoryCount]
    pipeline_health: PipelineHealthStats | None = None
    recent_cases: list[RecentCaseItem]
    active_alerts: list[ActiveAlertItem]
    top_senders: list[TopSenderItem] = []
    verdict_trend: list[VerdictTrendPoint] = []
    score_distribution: list[ScoreBucket] = []
