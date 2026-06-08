from pydantic import BaseModel, Field


class AnalyticsOverview(BaseModel):
    total_campaigns: int = 0
    active_campaigns: int = 0
    total_leads: int = 0
    emails_sent: int = 0
    emails_delivered: int = 0
    replies_received: int = 0
    reply_rate: float = 0.0
    pending_approvals: int = 0


class CampaignAnalytics(BaseModel):
    campaign_id: str
    leads_total: int = 0
    researched: int = 0
    drafts_pending: int = 0
    drafts_approved: int = 0
    emails_sent: int = 0
    replies: int = 0
    classifications: dict = Field(default_factory=dict)
