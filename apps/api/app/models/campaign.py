from datetime import datetime, timezone

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.db.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_name: Mapped[str] = mapped_column(String(255))
    outreach_person: Mapped[str] = mapped_column(String(255))
    campaign_goal: Mapped[str] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    geo_focus: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(64))
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    exclusions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[str] = mapped_column(String(32), default=lambda: datetime.now(timezone.utc).isoformat(), server_default=text("CURRENT_TIMESTAMP"))
