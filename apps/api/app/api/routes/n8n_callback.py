from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.audit import log_action
from app.services.discovery_runs import get_discovery_run, update_discovery_run
from app.services.influencers import create_influencer
from app.services.normalization import normalize_candidates
from app.services.scoring.persist import persist_scoring
from app.services.scoring.runner import run_scoring_pipeline

router = APIRouter(prefix="/n8n", tags=["n8n"])


@router.post("/callback/{run_id}")
async def n8n_discovery_callback(
    run_id: str,
    body: dict,
    db: Session = Depends(get_db),
) -> dict:
    from app.models.discovery_run import DiscoveryRun
    from sqlalchemy import select

    from app.services.scoring.profile_verify import verify_candidate

    stmt = select(DiscoveryRun).where(DiscoveryRun.id == run_id)
    run = db.scalar(stmt)
    if not run:
        raise HTTPException(status_code=404, detail="discovery run not found")

    raw_candidates = body.get("candidates", [])
    status = body.get("status", "completed")
    n8n_run_id = body.get("run_id")

    normalized = normalize_candidates(raw_candidates, cap=20)

    run = update_discovery_run(
        db,
        run,
        {
            "status": status,
            "result_count": len(normalized),
            "n8n_run_id": n8n_run_id or run.n8n_run_id,
        },
    )

    verified_normalized = []
    for candidate in normalized:
        ref = await verify_candidate(candidate)
        if ref.get("evidence_json", {}).get("verification_confidence", "unverified") != "unverified":
            verified_normalized.append(ref)
        else:
            log_action(db, "candidate.eliminated", "discovery_run", run.id,
                       {"reason": "profile_not_found", "name": candidate.get("name")})

    normalized = verified_normalized
    run = update_discovery_run(db, run, {"result_count": len(normalized)})

    for candidate in normalized:
        clean = {k: v for k, v in candidate.items() if k not in ("profile_verified", "profile_urls", "verification_confidence")}
        influencer = create_influencer(
            db,
            {
                "campaign_id": run.campaign_id,
                "discovery_run_id": run.id,
                **clean,
            },
        )
        composite_result, evidence_json, dimension_scores = await run_scoring_pipeline(
            db,
            campaign_context={"campaign_id": run.campaign_id},
            influencer_context={"id": influencer.id},
            raw_evidence=candidate.get("evidence_json") or {},
        )
        persist_scoring(
            db,
            influencer,
            composite_result.score,
            dimension_scores,
            evidence_json,
            composite_result=composite_result,
        )
        log_action(
            db,
            "influencer.scored",
            "influencer",
            influencer.id,
            {"composite_score": composite_result.score, "dimensions": len(dimension_scores)},
        )

    log_action(
        db,
        "discovery.completed",
        "discovery_run",
        run.id,
        {"influencers_created": len(normalized)},
    )

    return {"status": "ok", "influencers_created": len(normalized)}
