import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.email import ApprovalDecision, ApprovalItem, EmailDraft


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_approval_item(self, draft: EmailDraft, assigned_to: uuid.UUID | None = None) -> ApprovalItem:
        item = ApprovalItem(
            draft_id=draft.id,
            assigned_to=assigned_to,
            decision=ApprovalDecision.PENDING.value,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def count_pending_drafts(self, campaign_id: uuid.UUID, agent_run_id: uuid.UUID) -> int:
        from sqlalchemy import func, select

        result = await self.db.scalar(
            select(func.count()).select_from(EmailDraft).where(
                EmailDraft.campaign_id == campaign_id,
                EmailDraft.agent_run_id == agent_run_id,
                EmailDraft.status == "pending",
            )
        )
        return result or 0
