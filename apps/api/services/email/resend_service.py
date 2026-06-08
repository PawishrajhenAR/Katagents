import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.email import Email, EmailStatus


class EmailService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_email(
        self,
        *,
        to_email: str,
        subject: str,
        body: str,
        campaign_id: uuid.UUID,
        lead_id: uuid.UUID,
        org_id: uuid.UUID,
        draft_id: uuid.UUID | None = None,
    ) -> Email:
        email_record = Email(
            draft_id=draft_id,
            lead_id=lead_id,
            campaign_id=campaign_id,
            org_id=org_id,
            subject=subject,
            body=body,
            to_email=to_email,
            status=EmailStatus.QUEUED.value,
        )
        self.db.add(email_record)
        await self.db.flush()

        if settings.resend_api_key:
            try:
                import resend

                resend.api_key = settings.resend_api_key
                result = resend.Emails.send({
                    "from": settings.resend_from_email,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                })
                email_record.resend_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
                email_record.status = EmailStatus.SENT.value
                email_record.sent_at = datetime.now(UTC)
            except Exception as e:
                email_record.status = EmailStatus.FAILED.value
                email_record.body = f"{body}\n\n[Send error: {e}]"
        else:
            email_record.resend_id = f"mock-{email_record.id}"
            email_record.status = EmailStatus.SENT.value
            email_record.sent_at = datetime.now(UTC)

        return email_record
