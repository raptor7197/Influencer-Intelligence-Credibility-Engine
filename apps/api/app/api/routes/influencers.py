from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.influencers import (
    DimensionScoreResponse,
    InfluencerDetailResponse,
    InfluencerResponse,
    InfluencerStatusUpdate,
    OutreachDraftGenerate,
    OutreachDraftResponse,
    OutreachDraftUpdate,
)
from app.db.session import get_db
from app.services.audit import log_action
from app.services.influencers import get_influencer, list_influencers_by_campaign, update_influencer_status
from app.services.outreach import update_outreach_draft


def _influencer_to_response(i) -> InfluencerResponse:
    return InfluencerResponse(
        id=i.id,
        campaign_id=i.campaign_id,
        discovery_run_id=i.discovery_run_id,
        name=i.name,
        handle=i.handle,
        platforms=i.platforms,
        estimated_reach=i.estimated_reach,
        location=i.location,
        bio=i.bio,
        audience_category=i.audience_category,
        composite_score=i.composite_score,
        status=i.status,
        recommended_channel=i.recommended_channel,
        evidence_json=getattr(i, 'evidence_json', None),
        knocked_out=getattr(i, 'knocked_out', False),
        knockout_reason=getattr(i, 'knockout_reason', None),
        score_profile=getattr(i, 'score_profile', None),
        dimension_scores=(
            [
                DimensionScoreResponse(
                    id=d.id,
                    dimension=d.dimension,
                    score=d.score,
                    rationale=d.rationale,
                    evidence=d.evidence,
                    confidence=d.confidence,
                    uncertainty=d.uncertainty,
                )
                for d in i.dimension_scores
            ]
            if i.dimension_scores
            else None
        ),
        outreach_draft=(
            OutreachDraftResponse(
                id=i.outreach_draft.id,
                subject_line=i.outreach_draft.subject_line,
                message_body=i.outreach_draft.message_body,
                framing_angles=i.outreach_draft.framing_angles,
                messaging_tips=i.outreach_draft.messaging_tips,
                is_edited=i.outreach_draft.is_edited,
                status=i.outreach_draft.status,
            )
            if i.outreach_draft
            else None
        ),
    )


router = APIRouter(prefix="/campaigns", tags=["influencers"])


@router.get("/{campaign_id}/influencers", response_model=list[InfluencerResponse])
def list_influencers(
    campaign_id: str,
    db: Session = Depends(get_db),
) -> list[InfluencerResponse]:
    influencers = list_influencers_by_campaign(db, campaign_id)
    return [_influencer_to_response(i) for i in influencers]


@router.get("/{campaign_id}/influencers/{influencer_id}", response_model=InfluencerDetailResponse)
def get_influencer_detail(
    campaign_id: str,
    influencer_id: str,
    db: Session = Depends(get_db),
) -> InfluencerDetailResponse:
    influencer = get_influencer(db, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="influencer not found")
    base = _influencer_to_response(influencer)
    return InfluencerDetailResponse(
        **base.model_dump(exclude={"evidence_json"}),
        evidence_json=influencer.evidence_json,
    )


@router.patch("/{campaign_id}/influencers/{influencer_id}/status")
def update_influencer_status_endpoint(
    campaign_id: str,
    influencer_id: str,
    body: InfluencerStatusUpdate,
    db: Session = Depends(get_db),
) -> dict:
    influencer = update_influencer_status(db, influencer_id, body.status)
    if not influencer:
        raise HTTPException(status_code=404, detail="influencer not found")
    log_action(db, "influencer.status_changed", "influencer", influencer.id, {"status": body.status})
    return {"id": influencer.id, "status": influencer.status}


@router.post("/{campaign_id}/influencers/{influencer_id}/draft", response_model=OutreachDraftResponse)
async def generate_draft(
    campaign_id: str,
    influencer_id: str,
    regenerate: bool = False,
    body: OutreachDraftGenerate = OutreachDraftGenerate(),
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    from app.services.draft_generation import generate_outreach_draft

    influencer = get_influencer(db, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="influencer not found")

    if regenerate and influencer.outreach_draft:
        db.delete(influencer.outreach_draft)
        db.flush()
        influencer.outreach_draft = None

    if not influencer.outreach_draft:
        draft = await generate_outreach_draft(db, influencer, tone=body.tone)
        log_action(db, "draft.generated", "outreach_draft", draft.id, {"influencer_id": influencer.id})
    else:
        draft = influencer.outreach_draft

    return OutreachDraftResponse(
        id=draft.id,
        subject_line=draft.subject_line,
        message_body=draft.message_body,
        framing_angles=draft.framing_angles,
        messaging_tips=draft.messaging_tips,
        is_edited=draft.is_edited,
        status=draft.status,
    )


@router.patch("/{campaign_id}/influencers/{influencer_id}/draft", response_model=OutreachDraftResponse)
def update_draft(
    campaign_id: str,
    influencer_id: str,
    body: OutreachDraftUpdate,
    db: Session = Depends(get_db),
) -> OutreachDraftResponse:
    from app.services.influencers import get_influencer

    influencer = get_influencer(db, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="influencer not found")
    if not influencer.outreach_draft:
        raise HTTPException(status_code=404, detail="no draft exists, generate one first")
    draft = update_outreach_draft(
        db,
        influencer.outreach_draft.id,
        body.model_dump(exclude_none=True),
    )
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    log_action(db, "draft.edited", "outreach_draft", draft.id, {"influencer_id": influencer.id})
    return OutreachDraftResponse(
        id=draft.id,
        subject_line=draft.subject_line,
        message_body=draft.message_body,
        framing_angles=draft.framing_angles,
        messaging_tips=draft.messaging_tips,
        is_edited=draft.is_edited,
        status=draft.status,
    )
