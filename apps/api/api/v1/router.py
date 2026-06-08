from fastapi import APIRouter

from api.v1 import agents, analytics, auth, campaigns, drafts, emails, leads, organizations
from api.v1.webhooks import resend

router = APIRouter(prefix="/v1")
router.include_router(auth.router)
router.include_router(organizations.router)
router.include_router(campaigns.router)
router.include_router(leads.router)
router.include_router(agents.router)
router.include_router(drafts.router)
router.include_router(emails.router)
router.include_router(analytics.router)
router.include_router(resend.router)
