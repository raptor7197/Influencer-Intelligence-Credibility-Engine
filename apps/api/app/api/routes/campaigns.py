import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.campaigns import CampaignCreate, CampaignDetailResponse, CampaignResponse
from app.api.schemas.discovery import DiscoveryRunResponse
from app.db.session import get_db, get_session_maker
from app.services.audit import log_action
from app.services.campaigns import create_campaign, get_campaign, get_campaign_with_runs, list_campaigns
from app.services.discovery_runs import create_discovery_run
from app.services.event_bus import event_bus

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


_background_tasks: set = set()


async def _run_discovery_background(campaign_id: str, run_id: str) -> None:
    from app.models.campaign import Campaign
    from app.models.discovery_run import DiscoveryRun
    from sqlalchemy import select

    from app.api.routes.discovery import run_auto_discovery

    sm = get_session_maker()
    with sm() as db:
        campaign = db.scalar(select(Campaign).where(Campaign.id == campaign_id))
        run = db.scalar(select(DiscoveryRun).where(DiscoveryRun.id == run_id))
        if not campaign or not run:
            return
        await run_auto_discovery(db, run, campaign, campaign_id)


@router.post("", response_model=CampaignResponse)
async def create_campaign_endpoint(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
) -> CampaignResponse:
    campaign = create_campaign(db, payload.model_dump())
    log_action(db, "campaign.created", "campaign", campaign.id, {"org_name": campaign.org_name})

    run = create_discovery_run(db, campaign.id)

    await event_bus.publish("campaign.created", {"campaign_id": campaign.id, "org_name": campaign.org_name})

    t = asyncio.create_task(_run_discovery_background(campaign.id, run.id))
    _background_tasks.add(t)
    t.add_done_callback(_background_tasks.discard)

    return CampaignResponse(
        id=campaign.id,
        org_name=campaign.org_name,
        outreach_person=campaign.outreach_person,
        campaign_goal=campaign.campaign_goal,
        target_audience=campaign.target_audience,
        geo_focus=campaign.geo_focus,
        language=campaign.language,
        categories=campaign.categories,
        exclusions=campaign.exclusions,
        status=campaign.status,
        created_at=campaign.created_at,
    )


@router.get("", response_model=list[CampaignResponse])
def list_campaigns_endpoint(
    db: Session = Depends(get_db),
) -> list[CampaignResponse]:
    campaigns = list_campaigns(db)
    return [
        CampaignResponse(
            id=c.id,
            org_name=c.org_name,
            outreach_person=c.outreach_person,
            campaign_goal=c.campaign_goal,
            target_audience=c.target_audience,
            geo_focus=c.geo_focus,
            language=c.language,
            categories=c.categories,
            exclusions=c.exclusions,
            status=c.status,
            created_at=c.created_at,
            discovery_runs=[
                DiscoveryRunResponse(
                    id=r.id,
                    campaign_id=r.campaign_id,
                    status=r.status,
                    n8n_run_id=r.n8n_run_id,
                    result_count=r.result_count,
                    raw_input=r.raw_input,
                    raw_output=r.raw_output,
                    error=r.error,
                    created_at=r.created_at,
                )
                for r in (getattr(c, "_runs", []) or [])
            ],
        )
        for c in campaigns
    ]


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
def get_campaign_endpoint(
    campaign_id: str,
    db: Session = Depends(get_db),
) -> CampaignDetailResponse:
    campaign = get_campaign_with_runs(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="campaign not found")
    runs = getattr(campaign, "_runs", [])
    return CampaignDetailResponse(
        id=campaign.id,
        org_name=campaign.org_name,
        outreach_person=campaign.outreach_person,
        campaign_goal=campaign.campaign_goal,
        target_audience=campaign.target_audience,
        geo_focus=campaign.geo_focus,
        language=campaign.language,
        categories=campaign.categories,
        exclusions=campaign.exclusions,
        status=campaign.status,
        created_at=campaign.created_at,
        discovery_runs=[
            DiscoveryRunResponse(
                id=r.id,
                campaign_id=r.campaign_id,
                status=r.status,
                n8n_run_id=r.n8n_run_id,
                result_count=r.result_count,
                raw_input=r.raw_input,
                raw_output=r.raw_output,
                error=r.error,
                created_at=r.created_at,
            )
            for r in runs
        ],
    )
