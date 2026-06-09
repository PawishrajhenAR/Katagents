import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import log_audit
from database import get_db
from dependencies import AuthContext, require_role
from models.campaign import Campaign, CampaignLead, CampaignStatus, Lead, LeadImport, LeadStatus
from models.email import Unsubscribe
from models.user import OrgRole
from schemas.campaign import LeadCreate, LeadImportResult, LeadOut, LeadUpdate

router = APIRouter(tags=["leads"])


async def _get_campaign(db: AsyncSession, campaign_id: uuid.UUID, org_id: uuid.UUID) -> Campaign:
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.org_id == org_id,
            Campaign.deleted_at.is_(None),
        )
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


@router.get("/campaigns/{campaign_id}/leads", response_model=dict)
async def list_leads(
    campaign_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
    ctx: AuthContext = Depends(require_role(OrgRole.VIEWER.value)),
    db: AsyncSession = Depends(get_db),
):
    await _get_campaign(db, campaign_id, ctx.org_id)
    base_query = (
        select(Lead, CampaignLead)
        .join(CampaignLead, CampaignLead.lead_id == Lead.id)
        .where(CampaignLead.campaign_id == campaign_id, Lead.org_id == ctx.org_id)
    )
    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
    result = await db.execute(
        base_query.offset((page - 1) * per_page).limit(per_page)
    )
    rows = result.all()
    data = []
    for lead, cl in rows:
        out = LeadOut.model_validate(lead)
        out.campaign_status = cl.status
        data.append(out)
    return {"data": data, "meta": {"page": page, "per_page": per_page, "total": total or 0}}


@router.post("/campaigns/{campaign_id}/leads", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def add_lead(
    campaign_id: uuid.UUID,
    body: LeadCreate,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign(db, campaign_id, ctx.org_id)
    email = body.email.lower().strip()

    unsub = await db.execute(
        select(Unsubscribe).where(Unsubscribe.org_id == ctx.org_id, Unsubscribe.email == email)
    )
    if unsub.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is unsubscribed")

    existing = await db.execute(
        select(Lead).where(Lead.org_id == ctx.org_id, Lead.email == email)
    )
    lead = existing.scalar_one_or_none()
    if not lead:
        lead = Lead(
            org_id=ctx.org_id,
            email=email,
            first_name=body.first_name,
            last_name=body.last_name,
            company=body.company,
            title=body.title,
            source=body.source,
            status=LeadStatus.IMPORTED.value,
        )
        db.add(lead)
        await db.flush()

    cl_check = await db.execute(
        select(CampaignLead).where(
            CampaignLead.campaign_id == campaign_id,
            CampaignLead.lead_id == lead.id,
        )
    )
    if not cl_check.scalar_one_or_none():
        db.add(CampaignLead(campaign_id=campaign_id, lead_id=lead.id, status=LeadStatus.READY.value))

    out = LeadOut.model_validate(lead)
    out.campaign_status = LeadStatus.READY.value
    return out


@router.post("/campaigns/{campaign_id}/leads/import", response_model=LeadImportResult)
async def import_leads_csv(
    campaign_id: uuid.UUID,
    file: UploadFile = File(...),
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    campaign = await _get_campaign(db, campaign_id, ctx.org_id)
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    import_record = LeadImport(campaign_id=campaign_id, status="processing")
    db.add(import_record)
    await db.flush()

    unsub_result = await db.execute(
        select(Unsubscribe.email).where(Unsubscribe.org_id == ctx.org_id)
    )
    unsubscribed = set(unsub_result.scalars().all())

    existing_leads_result = await db.execute(select(Lead).where(Lead.org_id == ctx.org_id))
    leads_by_email = {lead.email: lead for lead in existing_leads_result.scalars().all()}

    existing_cl_result = await db.execute(
        select(CampaignLead.lead_id).where(CampaignLead.campaign_id == campaign_id)
    )
    campaign_lead_ids = set(existing_cl_result.scalars().all())

    imported = 0
    skipped = 0
    errors: list[str] = []

    for i, row in enumerate(reader, start=2):
        email = (row.get("email") or row.get("Email") or "").lower().strip()
        if not email or "@" not in email:
            skipped += 1
            errors.append(f"Row {i}: invalid email")
            continue

        if email in unsubscribed:
            skipped += 1
            continue

        lead = leads_by_email.get(email)
        if not lead:
            lead = Lead(
                org_id=ctx.org_id,
                email=email,
                first_name=row.get("first_name") or row.get("firstName") or row.get("First Name"),
                last_name=row.get("last_name") or row.get("lastName") or row.get("Last Name"),
                company=row.get("company") or row.get("Company"),
                title=row.get("title") or row.get("Title"),
                source="csv",
                status=LeadStatus.IMPORTED.value,
            )
            db.add(lead)
            await db.flush()
            leads_by_email[email] = lead

        if lead.id in campaign_lead_ids:
            skipped += 1
            continue

        db.add(CampaignLead(campaign_id=campaign_id, lead_id=lead.id, status=LeadStatus.READY.value))
        campaign_lead_ids.add(lead.id)
        imported += 1

    import_record.row_count = imported
    import_record.status = "completed"
    if campaign.status == CampaignStatus.DRAFT.value:
        campaign.status = CampaignStatus.ACTIVE.value

    return LeadImportResult(imported=imported, skipped=skipped, errors=errors[:20], import_id=import_record.id)


async def _get_campaign_lead(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    lead_id: uuid.UUID,
    org_id: uuid.UUID,
) -> tuple[Lead, CampaignLead]:
    result = await db.execute(
        select(Lead, CampaignLead)
        .join(CampaignLead, CampaignLead.lead_id == Lead.id)
        .where(
            CampaignLead.campaign_id == campaign_id,
            Lead.id == lead_id,
            Lead.org_id == org_id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return row


@router.patch("/campaigns/{campaign_id}/leads/{lead_id}", response_model=LeadOut)
async def update_campaign_lead(
    campaign_id: uuid.UUID,
    lead_id: uuid.UUID,
    body: LeadUpdate,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    await _get_campaign(db, campaign_id, ctx.org_id)
    lead, cl = await _get_campaign_lead(db, campaign_id, lead_id, ctx.org_id)

    if body.status:
        allowed = {
            LeadStatus.READY.value,
            LeadStatus.SKIPPED.value,
            LeadStatus.IMPORTED.value,
        }
        if body.status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status must be one of: {', '.join(sorted(allowed))}",
            )
        cl.status = body.status
        if body.status in (LeadStatus.READY.value, LeadStatus.SKIPPED.value):
            lead.status = body.status

        await log_audit(
            db,
            org_id=ctx.org_id,
            user_id=ctx.user.id,
            action="lead.exclude" if body.status == LeadStatus.SKIPPED.value else "lead.update",
            resource_type="lead",
            resource_id=str(lead_id),
        )

    out = LeadOut.model_validate(lead)
    out.campaign_status = cl.status
    return out


@router.delete("/campaigns/{campaign_id}/leads/{lead_id}")
async def remove_campaign_lead(
    campaign_id: uuid.UUID,
    lead_id: uuid.UUID,
    ctx: AuthContext = Depends(require_role(OrgRole.MANAGER.value)),
    db: AsyncSession = Depends(get_db),
):
    await _get_campaign(db, campaign_id, ctx.org_id)
    lead, cl = await _get_campaign_lead(db, campaign_id, lead_id, ctx.org_id)

    await db.delete(cl)
    await log_audit(
        db,
        org_id=ctx.org_id,
        user_id=ctx.user.id,
        action="lead.remove",
        resource_type="lead",
        resource_id=str(lead_id),
    )
    return {"ok": True, "email": lead.email}
