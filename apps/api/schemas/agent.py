import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AgentMetadata(BaseModel):
    agent_type: str
    display_name: str
    description: str
    version: str
    required_integrations: list[str] = Field(default_factory=list)


class AgentRunCreate(BaseModel):
    step_mode: str = "full"
    from_step: str | None = None


class AgentRunOut(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    org_id: uuid.UUID
    agent_type: str
    status: str
    current_step: str | None
    context_json: dict
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentStepOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    step_name: str
    status: str
    input_json: dict
    output_json: dict
    attempt: int
    duration_ms: int | None
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentLogOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    level: str
    message: str
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentRunDetail(AgentRunOut):
    steps: list[AgentStepOut] = Field(default_factory=list)
