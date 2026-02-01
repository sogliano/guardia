"""Monitoring page response schemas."""

from datetime import datetime

from pydantic import BaseModel


class MonitoringKPI(BaseModel):
    total_calls: int
    avg_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    estimated_cost: float
    error_count: int
    error_rate: float
    prev_total_calls: int


class TokenTrendPoint(BaseModel):
    date: str
    prompt_tokens: int
    completion_tokens: int


class LatencyBucket(BaseModel):
    range: str
    count: int


class ScoreAgreement(BaseModel):
    agree_pct: float
    minor_diff_pct: float
    major_divergence_pct: float
    total: int


class CostBreakdownPoint(BaseModel):
    date: str
    model: str
    cost: float


class RecentLLMAnalysis(BaseModel):
    time: datetime
    case_number: int | None = None
    sender: str | None = None
    llm_score: float | None = None
    final_score: float | None = None
    tokens: int | None = None
    latency_ms: int | None = None
    status: str
    model: str | None = None
    threat_category: str | None = None
    explanation_summary: str | None = None

    model_config = {"from_attributes": True}


class MonitoringResponse(BaseModel):
    kpi: MonitoringKPI
    token_trend: list[TokenTrendPoint] = []
    latency_distribution: list[LatencyBucket] = []
    score_agreement: ScoreAgreement
    cost_breakdown: list[CostBreakdownPoint] = []
    recent_analyses: list[RecentLLMAnalysis] = []


# ML Monitoring Schemas
class MLMonitoringKPI(BaseModel):
    total_calls: int
    avg_latency_ms: float
    p95_latency_ms: float
    avg_confidence: float
    error_count: int
    error_rate: float
    prev_total_calls: int


class ScoreDistributionBucket(BaseModel):
    range: str
    count: int


class ConfidenceAccuracyPoint(BaseModel):
    confidence: float
    accuracy: float


class LatencyTrendPoint(BaseModel):
    date: str
    avg_latency_ms: float


class RecentMLAnalysis(BaseModel):
    time: datetime
    case_number: int | None = None
    sender: str | None = None
    ml_score: float | None = None
    final_score: float | None = None
    confidence: float | None = None
    latency_ms: int | None = None
    status: str

    model_config = {"from_attributes": True}


class MLMonitoringResponse(BaseModel):
    kpi: MLMonitoringKPI
    score_distribution: list[ScoreDistributionBucket] = []
    confidence_accuracy: list[ConfidenceAccuracyPoint] = []
    latency_trend: list[LatencyTrendPoint] = []
    score_agreement: ScoreAgreement
    recent_analyses: list[RecentMLAnalysis] = []


# Heuristics Monitoring Schemas
class HeuristicsMonitoringKPI(BaseModel):
    total_runs: int
    avg_latency_ms: float
    p95_latency_ms: float
    high_score_rate: float
    zero_score_rate: float
    prev_total_runs: int


class TopRulePoint(BaseModel):
    rule_name: str
    count: int


class RecentHeuristicsAnalysis(BaseModel):
    time: datetime
    case_number: int | None = None
    sender: str | None = None
    heuristic_score: float | None = None
    final_score: float | None = None
    triggered_rules: list[str] = []
    latency_ms: int | None = None

    model_config = {"from_attributes": True}


class HeuristicsMonitoringResponse(BaseModel):
    kpi: HeuristicsMonitoringKPI
    top_triggered_rules: list[TopRulePoint] = []
    score_distribution: list[ScoreDistributionBucket] = []
    score_agreement: ScoreAgreement
    recent_analyses: list[RecentHeuristicsAnalysis] = []


# Score Analysis Schemas
class ScoreMetrics(BaseModel):
    agreement_rate: float
    avg_std_dev: float
    correlation_heur_ml: float
    correlation_heur_llm: float
    correlation_ml_llm: float
    total_cases_analyzed: int


class CaseScoreBreakdown(BaseModel):
    case_number: int
    email_sender: str
    email_received_at: datetime
    heuristic_score: float | None
    ml_score: float | None
    llm_score: float | None
    final_score: float
    std_dev: float
    agreement_level: str

    model_config = {"from_attributes": True}


class ScoreAnalysisResponse(BaseModel):
    metrics: ScoreMetrics | None
    cases: list[CaseScoreBreakdown]
