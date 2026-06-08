import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from jobs.follow_up_jobs import enqueue_classify_reply
from models.campaign import CampaignLead, LeadStatus
from models.email import Email, EmailEvent, EmailReply, Unsubscribe

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_resend_signature(payload: bytes, signature: str | None) -> bool:
    if not settings.resend_webhook_secret:
        return True
    if not signature:
        return False
    expected = hmac.new(
        settings.resend_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/resend")
async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("svix-signature") or request.headers.get("x-resend-signature")
    if not verify_resend_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = json.loads(body)
    event_type = payload.get("type", "")
    data = payload.get("data", {})
    email_id = data.get("email_id") or data.get("emailId")

    if event_type == "email.received":
        await _handle_inbound_reply(db, data)
    elif email_id and event_type in ("email.delivered", "email.bounced", "email.opened"):
        await _handle_email_event(db, email_id, event_type, data)

    return {"ok": True}


async def _handle_email_event(db: AsyncSession, resend_id: str, event_type: str, data: dict) -> None:
    result = await db.execute(select(Email).where(Email.resend_id == resend_id))
    email = result.scalar_one_or_none()
    if not email:
        return

    status_map = {
        "email.delivered": "delivered",
        "email.bounced": "bounced",
        "email.opened": "delivered",
    }
    if event_type in status_map:
        email.status = status_map[event_type]

    db.add(
        EmailEvent(
            email_id=email.id,
            event_type=event_type.replace("email.", ""),
            payload_json=data,
        )
    )


async def _handle_inbound_reply(db: AsyncSession, data: dict) -> None:
    in_reply_to = data.get("in_reply_to") or data.get("message_id")
    from_address = data.get("from", "")
    body_text = data.get("text") or data.get("html") or ""
    event_id = data.get("email_id") or data.get("id") or str(uuid.uuid4())

    existing = await db.execute(
        select(EmailReply).where(EmailReply.resend_event_id == event_id)
    )
    if existing.scalar_one_or_none():
        return

    email = None
    if in_reply_to:
        result = await db.execute(select(Email).where(Email.resend_id == in_reply_to))
        email = result.scalar_one_or_none()

    if not email:
        to_list = data.get("to", [])
        subject = data.get("subject", "")
        result = await db.execute(
            select(Email).where(Email.to_email == from_address).order_by(Email.sent_at.desc()).limit(1)
        )
        email = result.scalar_one_or_none()

    if not email:
        return

    reply = EmailReply(
        email_id=email.id,
        from_address=from_address,
        body_text=body_text[:10000],
        received_at=datetime.now(UTC),
        resend_event_id=event_id,
    )
    db.add(reply)
    await db.flush()

    cl_result = await db.execute(
        select(CampaignLead).where(
            CampaignLead.campaign_id == email.campaign_id,
            CampaignLead.lead_id == email.lead_id,
        )
    )
    cl = cl_result.scalar_one_or_none()
    if cl:
        cl.status = LeadStatus.REPLIED.value

    await enqueue_classify_reply(str(reply.id))

    if "unsubscribe" in body_text.lower():
        unsub_check = await db.execute(
            select(Unsubscribe).where(
                Unsubscribe.org_id == email.org_id,
                Unsubscribe.email == from_address.lower(),
            )
        )
        if not unsub_check.scalar_one_or_none():
            db.add(Unsubscribe(org_id=email.org_id, email=from_address.lower(), reason="reply"))
