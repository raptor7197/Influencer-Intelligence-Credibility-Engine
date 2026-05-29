from sqlalchemy.orm import Session

import uuid

from app.models.dimension_score import DimensionScore
from app.services.scoring.pipeline import ScoringPipeline
from app.services.scoring.types import CompositeResult


async def run_scoring_pipeline(
    db: Session,
    campaign_context: dict,
    influencer_context: dict,
    raw_evidence: dict,
) -> tuple[CompositeResult, dict, list[DimensionScore]]:
    if "id" not in influencer_context:
        raise ValueError("influencer_context must contain 'id' key")
    pipeline = ScoringPipeline()
    composite_result, dossier, dimension_results = await pipeline.run(
        campaign_context=campaign_context,
        influencer_context=influencer_context,
        raw_evidence=raw_evidence,
    )

    dimension_scores = []
    for result in dimension_results:
        dimension_scores.append(
            DimensionScore(
                id=str(uuid.uuid4()),
                influencer_id=influencer_context["id"],
                dimension=result.dimension,
                score=result.score,
                rationale=result.rationale,
                evidence=result.evidence,
                confidence=result.confidence,
                uncertainty=result.uncertainty,
            )
        )

    influencer_context["composite_score"] = composite_result.score
    influencer_context["evidence_json"] = dossier.model_dump()
    influencer_context["knocked_out"] = composite_result.knocked_out
    if composite_result.profile:
        influencer_context["score_profile"] = composite_result.profile.label

    return composite_result, dossier.model_dump(), dimension_scores
