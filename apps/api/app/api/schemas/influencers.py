from typing import Literal

from pydantic import BaseModel, ConfigDict


class DimensionScoreResponse(BaseModel):
    id: str
    dimension: str
    score: float
    rationale: str
    evidence: list[str] | None = None
    confidence: str | None = None
    uncertainty: str | None = None


class OutreachDraftResponse(BaseModel):
    id: str
    subject_line: str
    message_body: str
    framing_angles: list[str] | None = None
    messaging_tips: list[str] | None = None
    is_edited: bool
    status: str


class InfluencerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    discovery_run_id: str
    name: str
    handle: str | None
    platforms: list[str] | None
    estimated_reach: int | None
    location: str | None
    bio: str | None
    audience_category: str | None
    composite_score: float | None
    status: str
    recommended_channel: str | None = None
    knocked_out: bool = False
    knockout_reason: str | None = None
    score_profile: str | None = None
    evidence_json: dict | None = None
    dimension_scores: list[DimensionScoreResponse] | None = None
    outreach_draft: OutreachDraftResponse | None = None


class InfluencerDetailResponse(InfluencerResponse):
    pass


class InfluencerStatusUpdate(BaseModel):
    status: Literal["pending", "approved", "rejected", "maybe"]


class OutreachDraftGenerate(BaseModel):
    tone: str = "professional"


class OutreachDraftUpdate(BaseModel):
    subject_line: str | None = None
    message_body: str | None = None
    status: str | None = None
