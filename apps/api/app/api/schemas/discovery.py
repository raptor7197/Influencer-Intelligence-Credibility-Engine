from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileInput(BaseModel):
    name: str = Field(..., max_length=255)
    handle: str | None = None
    platforms: list[str] | None = None
    estimated_reach: int | None = None
    location: str | None = None
    bio: str | None = None
    audience_category: str | None = None
    evidence: str | None = None


class DiscoverRequest(BaseModel):
    profiles: list[ProfileInput] | None = None


class DiscoveryRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: str
    status: str
    n8n_run_id: str | None = None
    result_count: int | None = None
    raw_input: str | None = None
    raw_output: str | None = None
    error: str | None = None
    created_at: datetime | None = None
