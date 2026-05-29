import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campaign import Campaign
from app.models.discovery_run import DiscoveryRun


def create_campaign(db: Session, payload: dict) -> Campaign:
    campaign = Campaign(id=str(uuid.uuid4()), **payload, status="draft")
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def get_campaign(db: Session, campaign_id: str) -> Campaign | None:
    return db.scalar(select(Campaign).where(Campaign.id == campaign_id))


def list_campaigns(db: Session) -> list[Campaign]:
    campaigns = list(db.scalars(select(Campaign).order_by(Campaign.created_at.desc())).all())
    for campaign in campaigns:
        campaign._runs = list(
            db.scalars(
                select(DiscoveryRun)
                .where(DiscoveryRun.campaign_id == campaign.id)
                .order_by(DiscoveryRun.id.desc())
                .limit(5)
            ).all()
        )
    return campaigns


def get_campaign_with_runs(db: Session, campaign_id: str) -> Campaign | None:
    campaign = get_campaign(db, campaign_id)
    if campaign:
        campaign._runs = list(
            db.scalars(
                select(DiscoveryRun)
                .where(DiscoveryRun.campaign_id == campaign_id)
                .order_by(DiscoveryRun.id.desc())
            ).all()
        )
    return campaign
