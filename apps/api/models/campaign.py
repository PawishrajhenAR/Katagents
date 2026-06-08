import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, new_uuid


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, default="email_outreach")
    status: Mapped[str] = mapped_column(String(50), default=CampaignStatus.DRAFT.value)
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LeadStatus(str, enum.Enum):
    IMPORTED = "imported"
    READY = "ready"
    RESEARCHED = "researched"
    DRAFT_PENDING = "draft_pending"
    APPROVED = "approved"
    SENT = "sent"
    REPLIED = "replied"
    FOLLOW_UP_SCHEDULED = "follow_up_scheduled"
    CONVERTED = "converted"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    SKIPPED = "skipped"


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("org_id", "email", name="uq_org_lead_email"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default=LeadStatus.IMPORTED.value)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class CampaignLead(Base, TimestampMixin):
    __tablename__ = "campaign_leads"
    __table_args__ = (UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_lead"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), index=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default=LeadStatus.IMPORTED.value)
    priority: Mapped[int] = mapped_column(default=0)


class LeadImport(Base, TimestampMixin):
    __tablename__ = "lead_imports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    row_count: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
