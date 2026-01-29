from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EmailIngest(BaseModel):
    message_id: str
    sender_email: str
    sender_name: str | None = None
    reply_to: str | None = None
    recipient_email: str
    recipients_cc: list[str] = []
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    headers: dict = {}
    urls: list = []
    attachments: list = []
    auth_results: dict = {}
    received_at: datetime | None = None


class EmailResponse(BaseModel):
    id: UUID
    message_id: str
    sender_email: str
    sender_name: str | None
    reply_to: str | None
    recipient_email: str
    recipients_cc: list[str]
    subject: str | None
    body_text: str | None
    headers: dict
    urls: list
    attachments: list
    auth_results: dict
    received_at: datetime | None
    ingested_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailListItemResponse(EmailResponse):
    risk_level: str | None = None
    verdict: str | None = None
    final_score: float | None = None


class EmailList(BaseModel):
    items: list[EmailListItemResponse]
    total: int
    page: int
    size: int
