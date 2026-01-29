from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.evidence import EvidenceResponse


class AnalysisResponse(BaseModel):
    id: UUID
    case_id: UUID
    stage: str
    score: float | None
    confidence: float | None
    explanation: str | None
    metadata: dict = Field(validation_alias="metadata_")
    execution_time_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class AnalysisWithEvidencesResponse(AnalysisResponse):
    evidences: list[EvidenceResponse] = []
