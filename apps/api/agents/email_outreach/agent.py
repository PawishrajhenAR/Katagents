from agents.base import AgentContext, StepResult
from agents.email_outreach.steps.approval import run_approval_gate
from agents.email_outreach.steps.follow_up import run_follow_up_scheduler
from agents.email_outreach.steps.generate import run_email_generator
from agents.email_outreach.steps.lead_manager import run_lead_manager
from agents.email_outreach.steps.research import run_research
from agents.email_outreach.steps.send import run_sender
from agents.registry import register_agent


@register_agent(
    "email_outreach",
    display_name="Email Outreach Agent",
    description="Research prospects, generate personalized emails, manage approvals, send, and follow up.",
    version="1.0.0",
    required_integrations=["resend"],
)
class EmailOutreachAgent:
    agent_type = "email_outreach"
    version = "1.0.0"
    display_name = "Email Outreach Agent"
    description = "Research prospects, generate personalized emails, manage approvals, send, and follow up."
    required_integrations = ["resend"]

    STEPS = [
        "lead_manager",
        "research",
        "generate",
        "approval",
        "send",
        "follow_up",
    ]

    STEP_HANDLERS = {
        "lead_manager": run_lead_manager,
        "research": run_research,
        "generate": run_email_generator,
        "approval": run_approval_gate,
        "send": run_sender,
        "follow_up": run_follow_up_scheduler,
    }

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "tone": {"type": "string", "default": "professional"},
                "max_follow_ups": {"type": "integer", "default": 2},
                "follow_up_delay_days": {"type": "integer", "default": 7},
                "require_approval": {"type": "boolean", "default": True},
            },
        }

    def get_steps(self) -> list[str]:
        return self.STEPS

    async def execute_step(self, ctx: AgentContext, step_name: str) -> StepResult:
        handler = self.STEP_HANDLERS.get(step_name)
        if not handler:
            return StepResult(success=False, error=f"Unknown step: {step_name}")
        return await handler(ctx)

    async def on_run_start(self, ctx: AgentContext) -> None:
        await ctx.services.analytics.track(
            org_id=ctx.org_id,
            event_name="agent_run.started",
            campaign_id=ctx.campaign_id,
            run_id=ctx.run_id,
            properties={"agent_type": self.agent_type},
        )

    async def on_run_complete(self, ctx: AgentContext) -> None:
        await ctx.services.analytics.track(
            org_id=ctx.org_id,
            event_name="agent_run.completed",
            campaign_id=ctx.campaign_id,
            run_id=ctx.run_id,
            properties={"agent_type": self.agent_type},
        )
