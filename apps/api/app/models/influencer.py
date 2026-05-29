import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.dimension_score import DimensionScore
    from app.models.outreach_draft import OutreachDraft


class Influencer(Base):
    __tablename__ = "influencers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    discovery_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_runs.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platforms: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    estimated_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", server_default=text("'pending'"))
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommended_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    knocked_out: Mapped[bool] = mapped_column(default=False)
    knockout_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_profile: Mapped[str | None] = mapped_column(String(32), nullable=True)

    dimension_scores: Mapped[list["DimensionScore"]] = relationship(
        back_populates="influencer", cascade="all, delete-orphan"
    )
    outreach_draft: Mapped["OutreachDraft"] = relationship(
        back_populates="influencer", uselist=False, cascade="all, delete-orphan"
    )
