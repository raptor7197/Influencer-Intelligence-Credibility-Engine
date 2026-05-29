import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.influencer import Influencer


def create_influencer(db: Session, payload: dict) -> Influencer:
    influencer = Influencer(id=str(uuid.uuid4()), **payload)
    db.add(influencer)
    db.commit()
    db.refresh(influencer)
    return influencer


def list_influencers_by_campaign(
    db: Session,
    campaign_id: str,
) -> list[Influencer]:
    statement = (
        select(Influencer)
        .where(Influencer.campaign_id == campaign_id)
        .options(
            joinedload(Influencer.dimension_scores),
            joinedload(Influencer.outreach_draft),
        )
        .order_by(Influencer.composite_score.desc().nullslast())
    )
    return list(db.scalars(statement).unique().all())


def get_influencer(db: Session, influencer_id: str) -> Influencer | None:
    statement = (
        select(Influencer)
        .where(Influencer.id == influencer_id)
        .options(
            joinedload(Influencer.dimension_scores),
            joinedload(Influencer.outreach_draft),
        )
    )
    return db.scalars(statement).unique().one_or_none()


def update_influencer_status(
    db: Session,
    influencer_id: str,
    status: str,
) -> Influencer | None:
    influencer = get_influencer(db, influencer_id)
    if influencer:
        influencer.status = status
        db.commit()
        db.refresh(influencer)
    return influencer
