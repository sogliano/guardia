"""Pipeline data models: results passed between pipeline stages.

These dataclasses carry data through the pipeline without
depending on SQLAlchemy or Pydantic. DB persistence is handled
by the orchestrator after each stage completes.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class EvidenceItem:
    """A single detection signal found during analysis."""

    type: str  # EvidenceType value
    severity: str  # Severity value
    description: str
    raw_data: dict = field(default_factory=dict)


@dataclass
class HeuristicResult:
    """Output of the heuristic analysis engine (Layer 1)."""

    score: float = 0.0
    domain_score: float = 0.0
    url_score: float = 0.0
    keyword_score: float = 0.0
    auth_score: float = 0.0
    evidences: list[EvidenceItem] = field(default_factory=list)
    execution_time_ms: int = 0


@dataclass
class MLResult:
    """Output of the ML classifier (Layer 2)."""

    score: float = 0.0
    confidence: float = 0.0
    model_available: bool = False
    model_version: str = ""
    evidences: list[EvidenceItem] = field(default_factory=list)
    execution_time_ms: int = 0
    # XAI fields: token-level explanations
    top_tokens: list[tuple[str, float]] = field(default_factory=list)
    xai_available: bool = False


@dataclass
class LLMResult:
    """Output of the LLM analyst (Layer 3): score + explanation."""

    score: float = 0.0
    confidence: float = 0.0
    explanation: str = ""
    provider: str = ""  # "openai"
    model_used: str = ""
    tokens_used: int = 0
    execution_time_ms: int = 0


@dataclass
class PipelineResult:
    """Aggregate result of the full pipeline run."""

    case_id: UUID | None = None
    final_score: float = 0.0
    risk_level: str = ""  # RiskLevel value
    verdict: str = ""  # Verdict value
    threat_category: str = ""  # ThreatCategory value
    heuristic: HeuristicResult = field(default_factory=HeuristicResult)
    ml: MLResult = field(default_factory=MLResult)
    llm: LLMResult = field(default_factory=LLMResult)
    pipeline_duration_ms: int = 0
