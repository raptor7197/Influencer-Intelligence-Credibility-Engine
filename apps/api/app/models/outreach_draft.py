import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.sql import text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.influencer import Influencer


class OutreachDraft(Base):
    __tablename__ = "outreach_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    influencer_id: Mapped[str] = mapped_column(String(36), ForeignKey("influencers.id"), index=True)
    subject_line: Mapped[str] = mapped_column(String(255))
    message_body: Mapped[str] = mapped_column(Text)
    framing_angles: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    messaging_tips: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(32), server_default=text("'draft'"))

    influencer: Mapped["Influencer"] = relationship(back_populates="outreach_draft")
