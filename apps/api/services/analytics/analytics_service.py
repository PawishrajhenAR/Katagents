import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.analytics import AnalyticsEvent


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def track(
        self,
        *,
        org_id: uuid.UUID,
        event_name: str,
        campaign_id: uuid.UUID | None = None,
        run_id: uuid.UUID | None = None,
        properties: dict | None = None,
    ) -> None:
        self.db.add(
            AnalyticsEvent(
                org_id=org_id,
                event_name=event_name,
                campaign_id=campaign_id,
                run_id=run_id,
                properties_json=properties or {},
            )
        )
