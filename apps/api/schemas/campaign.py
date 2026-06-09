import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str
    agent_type: str = "email_outreach"
    config_json: dict = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    config_json: dict | None = None


class CampaignOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    agent_type: str
    status: str
    config_json: dict
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    lead_count: int = 0
    pending_drafts: int = 0

    model_config = {"from_attributes": True}


class LeadCreate(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    title: str | None = None
    source: str | None = "manual"


class LeadUpdate(BaseModel):
    status: str | None = None


class LeadOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    company: str | None
    title: str | None
    source: str | None
    status: str
    metadata_json: dict
    campaign_status: str | None = None

    model_config = {"from_attributes": True}


class LeadImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str] = Field(default_factory=list)
    import_id: uuid.UUID
