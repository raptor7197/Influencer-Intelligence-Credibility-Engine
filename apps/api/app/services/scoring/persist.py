from sqlalchemy.orm import Session

from app.models.dimension_score import DimensionScore
from app.models.influencer import Influencer
from app.services.channel import compute_recommended_channel
from app.services.scoring.types import CompositeResult


def persist_scoring(
    db: Session,
    influencer: Influencer,
    composite_score: float,
    dimension_scores: list[DimensionScore],
    evidence_json: dict,
    composite_result: CompositeResult | None = None,
) -> Influencer:
    influencer.composite_score = composite_score
    influencer.evidence_json = evidence_json
    influencer.recommended_channel = compute_recommended_channel(influencer.platforms)
    if composite_result:
        influencer.knocked_out = composite_result.knocked_out
        influencer.knockout_reason = composite_result.knockout_reason
        influencer.score_profile = composite_result.profile.label if composite_result.profile else None
    db.add(influencer)
    for score in dimension_scores:
        db.add(score)
    try:
        db.commit()
        db.refresh(influencer)
    except Exception:
        db.rollback()
        raise
    return influencer
