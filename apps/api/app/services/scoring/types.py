from pydantic import BaseModel, Field


class EvidenceDossier(BaseModel):
    content_values: list[str] = Field(default_factory=list)
    public_record: list[str] = Field(default_factory=list)
    audience_profile: list[str] = Field(default_factory=list)
    risk_controversy: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class DimensionResult(BaseModel):
    dimension: str
    score: float
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    confidence: str | None = None
    uncertainty: str | None = None


class KnockoutResult(BaseModel):
    knocked_out: bool = False
    reason: str | None = None
    rule: str | None = None


class ScoreProfile(BaseModel):
    label: str
    description: str
    recommendation: str


class CompositeResult(BaseModel):
    score: float
    knocked_out: bool = False
    knockout_reason: str | None = None
    knockout_rule: str | None = None
    profile: ScoreProfile | None = None
