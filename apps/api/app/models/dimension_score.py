import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.influencer import Influencer


class DimensionScore(Base):
    __tablename__ = "dimension_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    influencer_id: Mapped[str] = mapped_column(String(36), ForeignKey("influencers.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(64))
    score: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text)
    evidence: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    uncertainty: Mapped[str | None] = mapped_column(Text, nullable=True)

    influencer: Mapped["Influencer"] = relationship(back_populates="dimension_scores")
