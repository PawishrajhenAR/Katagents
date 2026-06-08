from sqlalchemy.ext.asyncio import AsyncSession

from services.analytics.analytics_service import AnalyticsService
from services.approval.approval_service import ApprovalService
from services.email.resend_service import EmailService
from services.llm.provider import LLMService
from services.research.research_service import ResearchService
from services.scheduler.scheduler_service import SchedulerService


class SharedServices:
    def __init__(self, db: AsyncSession, org_settings: dict | None = None):
        self.db = db
        self.org_settings = org_settings or {}
        self.llm = LLMService()
        self.email = EmailService(db)
        self.research = ResearchService(self.llm)
        self.scheduler = SchedulerService()
        self.approval = ApprovalService(db)
        self.analytics = AnalyticsService(db)
        self.logger = None
