import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DraftOut(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    lead_id: uuid.UUID
    agent_run_id: uuid.UUID | None
    subject: str
    body: str
    status: str
    version: int
    created_at: datetime
    lead_email: str | None = None
    lead_name: str | None = None

    model_config = {"from_attributes": True}


class DraftUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None


class DraftRejectRequest(BaseModel):
    reason: str | None = None


class BulkApproveRequest(BaseModel):
    draft_ids: list[uuid.UUID]


class EmailOut(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    lead_id: uuid.UUID
    subject: str
    to_email: str
    status: str
    sent_at: datetime | None

    model_config = {"from_attributes": True}


class ReplyOut(BaseModel):
    id: uuid.UUID
    email_id: uuid.UUID
    from_address: str
    body_text: str
    received_at: datetime
    classification: str | None
    classification_json: dict

    model_config = {"from_attributes": True}


class ReplyClassificationUpdate(BaseModel):
    classification: str
