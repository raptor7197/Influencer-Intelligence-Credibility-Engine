from pydantic import BaseModel, Field

from app.api.schemas.discovery import DiscoveryRunResponse


class CampaignCreate(BaseModel):
    org_name: str = Field(..., max_length=255)
    outreach_person: str = Field(..., max_length=255)
    campaign_goal: str = Field(..., max_length=2000)
    target_audience: str | None = None
    geo_focus: str | None = None
    language: str = Field(..., max_length=64)
    categories: list[str] | None = None
    exclusions: list[str] | None = None


class CampaignResponse(BaseModel):
    id: str
    org_name: str
    outreach_person: str
    campaign_goal: str
    target_audience: str | None
    geo_focus: str | None
    language: str
    categories: list[str] | None
    exclusions: list[str] | None
    status: str
    created_at: str | None = None
    discovery_runs: list[DiscoveryRunResponse] = []


class CampaignDetailResponse(CampaignResponse):
    pass
