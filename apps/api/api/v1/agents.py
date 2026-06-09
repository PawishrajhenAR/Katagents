import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.registry import list_agents
from database import get_db
from dependencies import AuthContext, get_auth_context, require_role
from jobs.tasks import enqueue_agent_run
from models.agent import AgentLog, AgentRun, AgentRunStatus, AgentStep
from models.campaign import Campaign
from models.user import OrgRole
from schemas.agent import AgentLogOut, AgentMetadata, AgentRunCreate, AgentRunDetail, AgentRunOut, AgentStepOut

router = APIRouter(tags=["agents"])


@router.get("/agents", response_model=list[AgentMetadata])
async def get_registered_agents():
    return [
        AgentMetadata(
            agent_type=a.agent_type,
            display_name=a.display_name,
            description=a.description,
            version=a.version,
            required_integrations=a.required_integrations,
        )
        for a in list_agents()
    ]


async def _get_run(db: AsyncSession, run_id: uuid.UUID, org_id: uuid.UUID) -> AgentRun:
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == run_id, AgentRun.org_id == org_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.post("/campaigns/{campaign_id}/runs", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
async def start_run(
    campaign_id: uuid.UUID,
    body: AgentRunCreate,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.org_id == ctx.org_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    run = AgentRun(
        campaign_id=campaign_id,
        org_id=ctx.org_id,
        agent_type=campaign.agent_type,
        status=AgentRunStatus.QUEUED.value,
        context_json={"step_mode": body.step_mode, "from_step": body.from_step},
        triggered_by=ctx.user.id,
    )
    db.add(run)
    await db.flush()
    await db.commit()
    asyncio.create_task(enqueue_agent_run(str(run.id)))
    return AgentRunOut.model_validate(run)


@router.get("/campaigns/{campaign_id}/runs", response_model=dict)
async def list_runs(
    campaign_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.campaign_id == campaign_id, AgentRun.org_id == ctx.org_id)
        .order_by(AgentRun.created_at.desc())
    )
    runs = result.scalars().all()
    return {"data": [AgentRunOut.model_validate(r) for r in runs]}


@router.get("/runs/{run_id}", response_model=AgentRunDetail)
async def get_run(
    run_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    run = await _get_run(db, run_id, ctx.org_id)
    steps_result = await db.execute(
        select(AgentStep).where(AgentStep.run_id == run_id).order_by(AgentStep.created_at)
    )
    steps = steps_result.scalars().all()
    detail = AgentRunDetail.model_validate(run)
    detail.steps = [AgentStepOut.model_validate(s) for s in steps]
    return detail


@router.get("/runs/{run_id}/logs", response_model=dict)
async def get_run_logs(
    run_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await _get_run(db, run_id, ctx.org_id)
    result = await db.execute(
        select(AgentLog)
        .where(AgentLog.run_id == run_id)
        .order_by(AgentLog.created_at)
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    logs = result.scalars().all()
    return {"data": [AgentLogOut.model_validate(l) for l in logs]}


@router.post("/runs/{run_id}/pause", response_model=AgentRunOut)
async def pause_run(
    run_id: uuid.UUID,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    run = await _get_run(db, run_id, ctx.org_id)
    if run.status not in (AgentRunStatus.RUNNING.value, AgentRunStatus.QUEUED.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pause run")
    run.status = AgentRunStatus.PAUSED.value
    return AgentRunOut.model_validate(run)


@router.post("/runs/{run_id}/resume", response_model=AgentRunOut)
async def resume_run(
    run_id: uuid.UUID,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    run = await _get_run(db, run_id, ctx.org_id)
    if run.status not in (
        AgentRunStatus.PAUSED.value,
        AgentRunStatus.WAITING_APPROVAL.value,
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot resume run")

    ctx_json = dict(run.context_json or {})
    if run.status == AgentRunStatus.WAITING_APPROVAL.value:
        ctx_json["from_step"] = "send"
    run.context_json = ctx_json
    run.status = AgentRunStatus.QUEUED.value
    await db.commit()
    asyncio.create_task(enqueue_agent_run(str(run.id)))
    return AgentRunOut.model_validate(run)


@router.post("/runs/{run_id}/cancel", response_model=AgentRunOut)
async def cancel_run(
    run_id: uuid.UUID,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    run = await _get_run(db, run_id, ctx.org_id)
    run.status = AgentRunStatus.CANCELLED.value
    return AgentRunOut.model_validate(run)
