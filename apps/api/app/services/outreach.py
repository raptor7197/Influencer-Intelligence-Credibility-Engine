from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.outreach_draft import OutreachDraft


def get_outreach_draft(db: Session, draft_id: str) -> OutreachDraft | None:
    statement = select(OutreachDraft).where(OutreachDraft.id == draft_id)
    return db.scalars(statement).one_or_none()


def update_outreach_draft(
    db: Session,
    draft_id: str,
    payload: dict,
) -> OutreachDraft | None:
    IMMUTABLE_FIELDS = {"id", "influencer_id", "created_at"}
    draft = get_outreach_draft(db, draft_id)
    if draft:
        for key, value in payload.items():
            if hasattr(draft, key) and key not in IMMUTABLE_FIELDS:
                setattr(draft, key, value)
        draft.is_edited = True
        db.commit()
        db.refresh(draft)
    return draft
