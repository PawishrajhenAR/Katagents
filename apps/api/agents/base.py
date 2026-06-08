from dataclasses import dataclass, field
from typing import Any, Protocol
import uuid


@dataclass
class StepResult:
    success: bool
    output: dict = field(default_factory=dict)
    pause: bool = False
    pause_reason: str | None = None
    error: str | None = None


@dataclass
class AgentContext:
    run_id: uuid.UUID
    org_id: uuid.UUID
    campaign_id: uuid.UUID
    user_id: uuid.UUID | None
    config: dict
    memory: dict
    services: Any
    db: Any

    def log(self, level: str, message: str, **metadata: Any) -> None:
        if hasattr(self.services, "logger"):
            self.services.logger.log(self.run_id, level, message, metadata)


class BaseAgent(Protocol):
    agent_type: str
    version: str
    display_name: str
    description: str
    required_integrations: list[str]

    def get_config_schema(self) -> dict: ...
    def get_steps(self) -> list[str]: ...
    async def execute_step(self, ctx: AgentContext, step_name: str) -> StepResult: ...
    async def on_run_start(self, ctx: AgentContext) -> None: ...
    async def on_run_complete(self, ctx: AgentContext) -> None: ...
