import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery_run import DiscoveryRun


def create_discovery_run(db: Session, campaign_id: str) -> DiscoveryRun:
    run = DiscoveryRun(id=str(uuid.uuid4()), campaign_id=campaign_id, status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_discovery_run(db: Session, run_id: str, campaign_id: str) -> DiscoveryRun | None:
    statement = select(DiscoveryRun).where(
        DiscoveryRun.id == run_id,
        DiscoveryRun.campaign_id == campaign_id,
    )
    return db.scalar(statement)


def update_discovery_run(db: Session, run: DiscoveryRun, updates: dict) -> DiscoveryRun:
    allowed_fields = {"status", "n8n_run_id", "result_count", "raw_input", "raw_output", "error"}
    for key, value in updates.items():
        if key not in allowed_fields:
            raise ValueError(f"Cannot update field: {key}")
        setattr(run, key, value)
    db.commit()
    db.refresh(run)
    return run
