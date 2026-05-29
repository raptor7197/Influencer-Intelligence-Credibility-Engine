from fastapi import APIRouter

from app.api.routes.campaigns import router as campaigns_router
from app.api.routes.discovery import router as discovery_router
from app.api.routes.events import router as events_router
from app.api.routes.influencers import router as influencers_router
from app.api.routes.n8n_callback import router as n8n_callback_router


router = APIRouter()
router.include_router(campaigns_router)
router.include_router(discovery_router)
router.include_router(influencers_router)
router.include_router(n8n_callback_router)
router.include_router(events_router)
