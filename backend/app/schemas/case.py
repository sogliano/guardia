from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.analysis import AnalysisWithEvidencesResponse
from app.schemas.case_note import CaseNoteResponse


class CaseResponse(BaseModel):
    id: UUID
    case_number: int
    email_id: UUID
    status: str
    final_score: float | None
    risk_level: str | None
    verdict: str | None
    threat_category: str | None
    pipeline_duration_ms: int | None
    resolved_by: UUID | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseListItemResponse(CaseResponse):
    email_subject: str | None = None
    email_sender: str | None = None
    email_received_at: datetime | None = None
    heuristic_score: float | None = None
    ml_score: float | None = None
    llm_score: float | None = None


class CaseList(BaseModel):
    items: list[CaseListItemResponse]
    total: int
    page: int
    size: int


class CaseResolve(BaseModel):
    verdict: str


class CaseEmailInfo(BaseModel):
    sender_email: str
    sender_name: str | None = None
    recipient_email: str
    recipients_cc: list = []
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    headers: dict = {}
    urls: list = []
    attachments: list = []
    auth_results: dict = {}
    received_at: datetime | None = None

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseResponse):
    email: CaseEmailInfo | None = None
    analyses: list[AnalysisWithEvidencesResponse] = []
    notes: list[CaseNoteResponse] = []
