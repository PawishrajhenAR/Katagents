import time
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base import AgentContext, StepResult
from agents.registry import get_agent_class
from models.agent import AgentLog, AgentRun, AgentRunStatus, AgentStep
from models.campaign import Campaign
from models.user import Organization
from services.shared import SharedServices


class AgentLogger:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, run_id: uuid.UUID, level: str, message: str, metadata: dict | None = None) -> None:
        self.db.add(
            AgentLog(
                run_id=run_id,
                level=level,
                message=message,
                metadata_json=metadata or {},
            )
        )


class AgentExecutionEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = AgentLogger(db)

    async def execute_run(self, run_id: uuid.UUID) -> None:
        result = await self.db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            return

        if run.status in (AgentRunStatus.CANCELLED.value, AgentRunStatus.COMPLETED.value):
            return

        campaign_result = await self.db.execute(select(Campaign).where(Campaign.id == run.campaign_id))
        campaign = campaign_result.scalar_one()
        org_result = await self.db.execute(select(Organization).where(Organization.id == run.org_id))
        org = org_result.scalar_one()

        agent_cls = get_agent_class(run.agent_type)
        agent = agent_cls()
        services = SharedServices(self.db, org_settings=org.settings_json or {})
        services.logger = self.logger

        ctx = AgentContext(
            run_id=run.id,
            org_id=run.org_id,
            campaign_id=run.campaign_id,
            user_id=run.triggered_by,
            config={**(campaign.config_json or {}), **(run.context_json or {})},
            memory=run.context_json or {},
            services=services,
            db=self.db,
        )

        run.status = AgentRunStatus.RUNNING.value
        run.started_at = run.started_at or datetime.now(UTC)
        from_step = (run.context_json or {}).get("from_step")
        resuming = bool(from_step)
        if not resuming:
            await self.logger.log(run.id, "info", f"Starting agent run for {run.agent_type}")
            await agent.on_run_start(ctx)
        else:
            await self.logger.log(run.id, "info", f"Resuming agent run from step: {from_step}")

        steps = agent.get_steps()
        start_idx = steps.index(from_step) if from_step and from_step in steps else 0

        for step_name in steps[start_idx:]:
            if run.status == AgentRunStatus.CANCELLED.value:
                break

            run.current_step = step_name
            step_row = AgentStep(run_id=run.id, step_name=step_name, status="running")
            self.db.add(step_row)
            await self.db.flush()

            start = time.monotonic()
            try:
                step_result: StepResult = await agent.execute_step(ctx, step_name)
                step_row.duration_ms = int((time.monotonic() - start) * 1000)
                step_row.output_json = step_result.output

                if not step_result.success:
                    step_row.status = "failed"
                    step_row.error = step_result.error
                    run.status = AgentRunStatus.FAILED.value
                    run.error = step_result.error
                    await self.logger.log(run.id, "error", f"Step {step_name} failed: {step_result.error}")
                    break

                step_row.status = "completed"
                ctx.memory.update(step_result.output)
                run.context_json = ctx.memory
                await self.logger.log(run.id, "info", f"Completed step: {step_name}")

                if step_result.pause:
                    run.status = AgentRunStatus.WAITING_APPROVAL.value
                    await self.logger.log(
                        run.id, "info", f"Paused at {step_name}: {step_result.pause_reason or 'approval required'}"
                    )
                    break

            except Exception as e:
                step_row.status = "failed"
                step_row.error = str(e)
                step_row.duration_ms = int((time.monotonic() - start) * 1000)
                run.status = AgentRunStatus.FAILED.value
                run.error = str(e)
                await self.logger.log(run.id, "error", f"Step {step_name} exception: {e}")
                break

        if run.status == AgentRunStatus.RUNNING.value:
            run.status = AgentRunStatus.COMPLETED.value
            run.completed_at = datetime.now(UTC)
            await agent.on_run_complete(ctx)
            await self.logger.log(run.id, "info", "Agent run completed")

        await self.db.commit()
