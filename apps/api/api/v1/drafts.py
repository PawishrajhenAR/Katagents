import asyncio
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import log_audit
from database import get_db
from dependencies import AuthContext, get_auth_context, require_role
from jobs.tasks import enqueue_agent_run
from models.agent import AgentRun, AgentRunStatus
from models.campaign import Campaign, Lead
from models.email import ApprovalDecision, ApprovalItem, EmailDraft
from models.user import OrgRole
from schemas.email import BulkApproveRequest, DraftOut, DraftRejectRequest, DraftUpdate

router = APIRouter(tags=["drafts"])


async def _maybe_resume_run_after_approval(db: AsyncSession, run: AgentRun) -> str | None:
    """When all drafts for a paused run are approved, queue continuation from the send step."""
    if run.status != AgentRunStatus.WAITING_APPROVAL.value:
        return None

    pending_count = await db.scalar(
        select(func.count())
        .select_from(EmailDraft)
        .where(
            EmailDraft.agent_run_id == run.id,
            EmailDraft.status == "pending",
        )
    )
    if pending_count:
        return None

    ctx_json = dict(run.context_json or {})
    ctx_json["from_step"] = "send"
    run.context_json = ctx_json
    run.status = AgentRunStatus.QUEUED.value
    return str(run.id)


async def _get_campaign(db: AsyncSession, campaign_id: uuid.UUID, org_id: uuid.UUID) -> Campaign:
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.org_id == org_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


def _draft_to_out(draft: EmailDraft, lead: Lead | None = None) -> DraftOut:
    out = DraftOut.model_validate(draft)
    if lead:
        out.lead_email = lead.email
        out.lead_name = " ".join(filter(None, [lead.first_name, lead.last_name])) or None
    return out


@router.get("/campaigns/{campaign_id}/drafts", response_model=dict)
async def list_drafts(
    campaign_id: uuid.UUID,
    status_filter: str | None = None,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    await _get_campaign(db, campaign_id, ctx.org_id)
    query = (
        select(EmailDraft, Lead)
        .join(Lead, Lead.id == EmailDraft.lead_id)
        .where(EmailDraft.campaign_id == campaign_id)
    )
    if status_filter:
        query = query.where(EmailDraft.status == status_filter)
    result = await db.execute(query.order_by(EmailDraft.created_at.desc()))
    data = [_draft_to_out(draft, lead) for draft, lead in result.all()]
    return {"data": data}


@router.get("/drafts/{draft_id}", response_model=DraftOut)
async def get_draft(
    draft_id: uuid.UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailDraft, Campaign)
        .join(Campaign, Campaign.id == EmailDraft.campaign_id)
        .where(EmailDraft.id == draft_id, Campaign.org_id == ctx.org_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    draft, _ = row
    lead_result = await db.execute(select(Lead).where(Lead.id == draft.lead_id))
    lead = lead_result.scalar_one_or_none()
    return _draft_to_out(draft, lead)


@router.patch("/drafts/{draft_id}", response_model=DraftOut)
async def update_draft(
    draft_id: uuid.UUID,
    body: DraftUpdate,
    ctx: AuthContext = Depends(require_role(OrgRole.REVIEWER.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailDraft, Campaign)
        .join(Campaign, Campaign.id == EmailDraft.campaign_id)
        .where(EmailDraft.id == draft_id, Campaign.org_id == ctx.org_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    draft, _ = row
    if body.subject is not None:
        draft.subject = body.subject
    if body.body is not None:
        draft.body = body.body
    draft.version += 1
    lead_result = await db.execute(select(Lead).where(Lead.id == draft.lead_id))
    lead = lead_result.scalar_one_or_none()
    return _draft_to_out(draft, lead)


@router.post("/drafts/{draft_id}/approve", response_model=DraftOut)
async def approve_draft(
    draft_id: uuid.UUID,
    ctx: AuthContext = Depends(require_role(OrgRole.REVIEWER.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailDraft, Campaign)
        .join(Campaign, Campaign.id == EmailDraft.campaign_id)
        .where(EmailDraft.id == draft_id, Campaign.org_id == ctx.org_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    draft, campaign = row
    draft.status = "approved"

    approval_result = await db.execute(
        select(ApprovalItem).where(ApprovalItem.draft_id == draft_id)
    )
    approval = approval_result.scalar_one_or_none()
    if approval:
        approval.decision = ApprovalDecision.APPROVED.value
        approval.decided_at = datetime.now(UTC)
        approval.decided_by = ctx.user.id
    else:
        db.add(
            ApprovalItem(
                draft_id=draft_id,
                decision=ApprovalDecision.APPROVED.value,
                decided_at=datetime.now(UTC),
                decided_by=ctx.user.id,
            )
        )

    run_to_resume: str | None = None
    if draft.agent_run_id:
        run_result = await db.execute(select(AgentRun).where(AgentRun.id == draft.agent_run_id))
        run = run_result.scalar_one_or_none()
        if run:
            await db.flush()
            run_to_resume = await _maybe_resume_run_after_approval(db, run)

    await log_audit(
        db, org_id=ctx.org_id, user_id=ctx.user.id, action="draft.approve",
        resource_type="email_draft", resource_id=str(draft_id),
    )

    await db.commit()
    if run_to_resume:
        asyncio.create_task(enqueue_agent_run(run_to_resume))

    lead_result = await db.execute(select(Lead).where(Lead.id == draft.lead_id))
    lead = lead_result.scalar_one_or_none()
    return _draft_to_out(draft, lead)


@router.post("/drafts/{draft_id}/reject", response_model=DraftOut)
async def reject_draft(
    draft_id: uuid.UUID,
    body: DraftRejectRequest,
    ctx: AuthContext = Depends(require_role(OrgRole.REVIEWER.value)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailDraft, Campaign)
        .join(Campaign, Campaign.id == EmailDraft.campaign_id)
        .where(EmailDraft.id == draft_id, Campaign.org_id == ctx.org_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    draft, _ = row
    draft.status = "rejected"
    db.add(
        ApprovalItem(
            draft_id=draft_id,
            decision=ApprovalDecision.REJECTED.value,
            decided_at=datetime.now(UTC),
            decided_by=ctx.user.id,
            notes=body.reason,
        )
    )
    lead_result = await db.execute(select(Lead).where(Lead.id == draft.lead_id))
    lead = lead_result.scalar_one_or_none()
    return _draft_to_out(draft, lead)


@router.post("/campaigns/{campaign_id}/drafts/bulk-approve", response_model=dict)
async def bulk_approve(
    campaign_id: uuid.UUID,
    body: BulkApproveRequest,
    ctx: AuthContext = Depends(require_role(OrgRole.REVIEWER.value)),
    db: AsyncSession = Depends(get_db),
):
    await _get_campaign(db, campaign_id, ctx.org_id)
    if not body.draft_ids:
        return {"approved": 0}

    result = await db.execute(
        update(EmailDraft)
        .where(
            EmailDraft.id.in_(body.draft_ids),
            EmailDraft.campaign_id == campaign_id,
            EmailDraft.status == "pending",
        )
        .values(status="approved")
        .returning(EmailDraft.id, EmailDraft.agent_run_id)
    )
    rows = result.all()
    approved = len(rows)

    run_ids = {row.agent_run_id for row in rows if row.agent_run_id}
    runs_to_resume: list[str] = []
    for run_id in run_ids:
        run_result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = run_result.scalar_one_or_none()
        if run:
            resumed = await _maybe_resume_run_after_approval(db, run)
            if resumed:
                runs_to_resume.append(resumed)

    await db.commit()
    for run_id in runs_to_resume:
        asyncio.create_task(enqueue_agent_run(run_id))

    return {"approved": approved}
