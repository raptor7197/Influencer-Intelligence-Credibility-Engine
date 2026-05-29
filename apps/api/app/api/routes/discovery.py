import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.discovery import DiscoverRequest, DiscoveryRunResponse
from app.db.session import get_db
from app.models.discovery_run import DiscoveryRun
from app.services.audit import log_action
from app.services.discovery_runs import create_discovery_run, get_discovery_run, update_discovery_run
from app.services.event_bus import event_bus
from app.services.influencers import create_influencer
from app.services.normalization import normalize_candidates
from app.services.scoring.persist import persist_scoring
from app.services.scoring.runner import run_scoring_pipeline
from app.services.llm import build_openrouter_client
from app.services.n8n import build_n8n_client, build_n8n_status_client


async def _score_influencers_background(
    campaign_id: str,
    run_id: str,
    scoring_tasks: list[dict],
    campaign_context: dict,
) -> None:
    from app.db.session import get_session_maker
    from app.services.influencers import get_influencer

    sm = get_session_maker()
    with sm() as db:
        run = get_discovery_run(db, run_id, campaign_id)
        if not run:
            return
        try:
            total = len(scoring_tasks)
            for idx, task in enumerate(scoring_tasks):
                current = idx + 1
                candidate = task["candidate"]
                influencer = get_influencer(db, task["influencer_id"])
                if not influencer:
                    continue
                comment = f"scoring {candidate.get('name', 'unknown')}"
                await event_bus.publish("discovery.progress", {
                    "campaign_id": campaign_id,
                    "run_id": run.id,
                    "current": current,
                    "total": total,
                    "candidate_name": candidate.get("name", "unknown"),
                    "comment": comment,
                })
                composite_result, evidence_json, dimension_scores = await run_scoring_pipeline(
                    db,
                    campaign_context=campaign_context,
                    influencer_context={
                        "id": influencer.id,
                        "name": candidate.get("name"),
                        "handle": candidate.get("handle"),
                        "bio": candidate.get("bio"),
                        "location": candidate.get("location"),
                        "platforms": candidate.get("platforms"),
                        "audience_category": candidate.get("audience_category"),
                    },
                    raw_evidence=task["evidence"],
                )
                persist_scoring(
                    db,
                    influencer,
                    composite_result.score,
                    dimension_scores,
                    evidence_json,
                    composite_result=composite_result,
                )
                log_action(db, "influencer.scored", "influencer", influencer.id,
                           {"composite_score": composite_result.score, "dimensions": len(dimension_scores)})
                if dimension_scores:
                    first = dimension_scores[0]
                    detail = first.rationale[:120]
                    await event_bus.publish("discovery.progress", {
                        "campaign_id": campaign_id,
                        "run_id": run.id,
                        "current": current,
                        "total": total,
                        "candidate_name": candidate.get("name", "unknown"),
                        "comment": f"score {composite_result.score:.1f} — {detail}",
                    })
            update_discovery_run(db, run, {"status": "completed", "result_count": total})
            await event_bus.publish("discovery.completed", {
                "campaign_id": campaign_id,
                "run_id": run.id,
                "status": "completed",
                "result_count": len(scoring_tasks),
            })
        except Exception as exc:
            update_discovery_run(db, run, {"status": "failed", "error": str(exc)})
            await event_bus.publish("discovery.completed", {
                "campaign_id": campaign_id,
                "run_id": run.id,
                "status": "failed",
                "result_count": 0,
            })


async def _score_candidates_background(
    campaign_id: str,
    run_id: str,
    candidates: list[dict],
    campaign_context: dict,
) -> None:
    from app.db.session import get_session_maker

    sm = get_session_maker()
    with sm() as db:
        run = get_discovery_run(db, run_id, campaign_id)
        if not run:
            return
        try:
            total = len(candidates)
            for idx, candidate in enumerate(candidates):
                current = idx + 1
                name = candidate.get("name", "unknown")
                await event_bus.publish("discovery.progress", {
                    "campaign_id": campaign_id,
                    "run_id": run.id,
                    "current": current,
                    "total": total,
                    "candidate_name": name,
                    "comment": f"scoring {name}",
                })
                clean = {k: v for k, v in candidate.items() if k not in ("profile_verified", "profile_urls", "verification_confidence")}
                influencer = create_influencer(db, {"campaign_id": campaign_id, "discovery_run_id": run.id, **clean})
                composite_result, evidence_json, dimension_scores = await run_scoring_pipeline(
                    db,
                    campaign_context=campaign_context,
                    influencer_context={
                        "id": influencer.id, "name": candidate.get("name"),
                        "handle": candidate.get("handle"), "bio": candidate.get("bio"),
                        "location": candidate.get("location"),
                    },
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
                log_action(db, "influencer.scored", "influencer", influencer.id,
                           {"composite_score": composite_result.score, "dimensions": len(dimension_scores)})
                if dimension_scores:
                    first = dimension_scores[0]
                    detail = first.rationale[:120]
                    await event_bus.publish("discovery.progress", {
                        "campaign_id": campaign_id,
                        "run_id": run.id,
                        "current": current,
                        "total": total,
                        "candidate_name": name,
                        "comment": f"score {composite_result.score:.1f} — {detail}",
                    })
            update_discovery_run(db, run, {"status": "completed", "result_count": total})
            await event_bus.publish("discovery.completed", {
                "campaign_id": campaign_id,
                "run_id": run.id,
                "status": "completed",
                "result_count": len(candidates),
            })
        except Exception as exc:
            update_discovery_run(db, run, {"status": "failed", "error": str(exc)})
            await event_bus.publish("discovery.completed", {
                "campaign_id": campaign_id,
                "run_id": run.id,
                "status": "failed",
                "result_count": 0,
            })


def _parse_n8n_output(raw_data: dict) -> dict:
    output_str = raw_data.get("output", "{}")
    try:
        return json.loads(output_str) if isinstance(output_str, str) else output_str
    except (json.JSONDecodeError, TypeError):
        return {}


def _n8n_output_to_evidence(n8n_output: dict) -> dict:
    pw = n8n_output.get("profileSummary", {})
    aae = n8n_output.get("animalAbuseEvidence", {})
    raw_citations = n8n_output.get("citations", [])
    sources = []
    for c in raw_citations:
        if isinstance(c, str):
            sources.append(c)
        elif isinstance(c, dict):
            url = c.get("url") or c.get("link") or c.get("source")
            if url:
                sources.append(url)
    return {
        "content_values": n8n_output.get("contentThemes", []) + n8n_output.get("advantages", []),
        "public_record": aae.get("verifiedIncidents", []),
        "audience_profile": [
            f"Name: {pw.get('name', 'N/A')}",
            f"Bio: {pw.get('bio', 'N/A')}",
            f"Followers: {pw.get('followers', {})}",
            f"Account: {pw.get('accountCreated', 'N/A')}",
        ],
        "risk_controversy": n8n_output.get("negativeAspects", [])
            + n8n_output.get("disadvantages", [])
            + ([aae.get("conclusion", "")] if aae.get("conclusion") else []),
        "sources": sources,
    }


async def _batch_discover_candidates(
    db: Session,
    run: DiscoveryRun,
    campaign: object,
) -> list[dict]:
    from app.core.settings import Settings
    settings = Settings()
    if settings.llm_mode != "openrouter":
        return []

    client = build_openrouter_client()
    geo = getattr(campaign, 'geo_focus', '') or ''
    cats = getattr(campaign, 'categories', '') or ''
    goal = getattr(campaign, 'campaign_goal', '') or ''

    def _strip_markdown(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        return text.strip()

    def _ensure_dict(item):
        if isinstance(item, dict):
            return item
        if isinstance(item, str):
            return {"name": item, "handle": item}
        return {"name": str(item)}

    cats_str = ", ".join(cats) if isinstance(cats, list) else (cats or "")
    topic = cats_str.split(",")[0].strip() if cats_str else goal[:100]

    prompt = (
        f"Topic: {topic}\nRegion: {geo}\n"
        "List 20+ relevant social media figures. "
        "Return JSON array [{name,handle,platforms,estimated_reach,bio,location,audience_category,evidence}]"
    )
    run = update_discovery_run(db, run, {"raw_input": prompt})

    raw = ""
    candidates: list = []
    for attempt in range(2):
        try:
            p = prompt if attempt == 0 else f"List 20 Indian social media figures. JSON array [name,handle,platforms,bio,evidence]."
            response = await client.chat(
                model=settings.openrouter_model_evidence,
                messages=[{"role": "system", "content": "Output JSON only."}, {"role": "user", "content": p}],
                temperature=0.3, max_tokens=6000,
            )
            raw = response["choices"][0]["message"]["content"]
            run = update_discovery_run(db, run, {"raw_output": raw[:10000]})
            cleaned = _strip_markdown(raw)
            if not cleaned:
                continue
            data = json.loads(cleaned)
            if isinstance(data, dict):
                data = data.get("candidates") or data.get("profiles") or [data]
            if isinstance(data, list):
                candidates = [_ensure_dict(d) for d in data if d]
                break
        except Exception:
            continue

    if not candidates:
        run = update_discovery_run(db, run, {"error": "LLM discovery failed after 2 attempts"})
        return []

    normalized = normalize_candidates(candidates, cap=20)
    return normalized


def _n8n_output_to_candidates(n8n_output: dict) -> list[dict]:
    ps = n8n_output.get("profileSummary") or {}
    name = ps.get("name", "") if isinstance(ps, dict) else ""
    if not name:
        return []
    handles = ps.get("handles", []) if isinstance(ps, dict) else []
    platforms = ps.get("platforms", []) if isinstance(ps, dict) else []
    followers = ps.get("followers", {}) if isinstance(ps, dict) else {}
    bio = ps.get("bio", "") if isinstance(ps, dict) else ""
    handle = handles[0] if handles else ""
    def _parse_num(v: object) -> int | None:
        try:
            s = str(v).replace(",", "").strip()
            return int(s) if s.isdigit() else None
        except (ValueError, TypeError):
            return None
    reach = max((n for n in (_parse_num(v) for v in followers.values()) if n is not None), default=None)
    evidence = _n8n_output_to_evidence(n8n_output)
    return [
        {
            "name": name,
            "handle": handle,
            "platforms": platforms,
            "estimated_reach": reach,
            "bio": bio,
            "evidence_json": evidence,
        }
    ]


async def _trigger_n8n_background(
    campaign_data: dict,
    campaign_id: str,
) -> None:
    from app.core.settings import Settings
    from app.db.session import get_session_maker

    settings = Settings()
    if not settings.n8n_webhook_url:
        return

    sm = get_session_maker()
    with sm() as db:
        try:
            run = create_discovery_run(db, campaign_id)
            n8n_client = build_n8n_client()
            geo = campaign_data.get("geo_focus", "") or ""
            cats = campaign_data.get("categories", "") or ""
            goal = campaign_data.get("campaign_goal", "") or ""

            chat_input = (
                f"Campaign: {campaign_data.get('org_name', 'N/A')}\n"
                f"Goal: {goal}\n"
                f"Location/Area: {geo or 'Not specified'}\n"
                f"Categories: {cats or 'Any'}\n"
                f"Exclusions: {campaign_data.get('exclusions', 'None')}\n"
                "Discover and analyze social media figures aligned with this campaign."
            )
            n8n_response = await n8n_client.trigger_discovery({"chatInput": chat_input})
            n8n_run_id = n8n_response.get("run_id") or n8n_response.get("execution_id")
            if n8n_run_id:
                update_discovery_run(db, run, {"n8n_run_id": n8n_run_id})
        except Exception as exc:
            try:
                update_discovery_run(db, run, {"status": "failed", "error": f"n8n trigger failed: {exc}"})
            except Exception:
                pass


router = APIRouter(prefix="/campaigns", tags=["discovery"])

_background_tasks: set = set()


async def run_auto_discovery(
    db: Session,
    run: object,
    campaign: object,
    campaign_id: str,
) -> DiscoveryRunResponse:
    candidates_data = await _batch_discover_candidates(db, run, campaign)

    from app.services.scoring.phase0 import phase0_filter
    passed, eliminated = phase0_filter(candidates_data)
    if eliminated:
        for el in eliminated:
            log_action(db, "candidate.eliminated", "discovery_run", run.id, el)

    from app.services.scoring.profile_verify import verify_candidate
    verified_passed = []
    for candidate in passed:
        candidate = await verify_candidate(candidate)
        confidence = candidate.get("evidence_json", {}).get("verification_confidence", "unverified")
        if confidence == "unverified":
            eliminated.append({"name": candidate.get("name"), "reason": "profile_not_found",
                               "detail": "No matching social media profiles found"})
            log_action(db, "candidate.eliminated", "discovery_run", run.id,
                       {"reason": "profile_not_found", "name": candidate.get("name"), "confidence": confidence})
        else:
            verified_passed.append(candidate)

    passed = verified_passed
    run = update_discovery_run(db, run, {"status": "processing", "result_count": len(passed)})

    if passed:
        campaign_context = {"campaign_id": campaign_id, "goal": getattr(campaign, 'campaign_goal', '')}
        t = asyncio.create_task(_score_candidates_background(campaign_id, run.id, passed, campaign_context))
        _background_tasks.add(t)
        t.add_done_callback(_background_tasks.discard)

    await event_bus.publish("discovery.completed", {
        "campaign_id": campaign_id,
        "run_id": run.id,
        "status": "processing",
        "result_count": run.result_count or 0,
    })

    campaign_data = {
        "org_name": getattr(campaign, "org_name", ""),
        "campaign_goal": getattr(campaign, "campaign_goal", ""),
        "geo_focus": getattr(campaign, "geo_focus", ""),
        "categories": getattr(campaign, "categories", ""),
        "exclusions": getattr(campaign, "exclusions", ""),
    }
    t2 = asyncio.create_task(_trigger_n8n_background(campaign_data, campaign_id))
    _background_tasks.add(t2)
    t2.add_done_callback(_background_tasks.discard)

    return DiscoveryRunResponse(
        id=run.id,
        campaign_id=run.campaign_id,
        status="processing",
        n8n_run_id=run.n8n_run_id,
        result_count=run.result_count,
        raw_input=run.raw_input,
        raw_output=run.raw_output,
        error=run.error,
        created_at=run.created_at,
    )


@router.post("/{campaign_id}/discover", response_model=DiscoveryRunResponse)
async def trigger_discovery(
    campaign_id: str,
    body: DiscoverRequest | None = None,
    db: Session = Depends(get_db),
) -> DiscoveryRunResponse:
    from app.models.campaign import Campaign
    from sqlalchemy import select

    run = create_discovery_run(db, campaign_id)
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    campaign = db.scalar(stmt)

    if body and body.profiles:
        return await _process_direct_profiles(db, run, campaign_id, body.profiles)

    return await run_auto_discovery(db, run, campaign, campaign_id)


async def _process_direct_profiles(
    db: Session,
    run: DiscoveryRun,
    campaign_id: str,
    profiles: list,
) -> DiscoveryRunResponse:
    from app.models.campaign import Campaign
    from sqlalchemy import select

    stmt = select(Campaign).where(Campaign.id == campaign_id)
    campaign = db.scalar(stmt)

    raw_candidates = [p.model_dump() for p in profiles]
    normalized = normalize_candidates(raw_candidates, cap=20)

    run = update_discovery_run(db, run, {
        "raw_input": json.dumps(raw_candidates),
        "result_count": len(normalized),
    })

    profile_details = "\n".join(
        f"{i+1}. Name: {p.get('name', '')}\n   Handle: {p.get('handle', '')}\n   Platforms: {', '.join(p.get('platforms', []) or [])}"
        for i, p in enumerate(raw_candidates)
    )
    geo = campaign.geo_focus if campaign else ''
    cats = campaign.categories if campaign else ''
    exclusions = campaign.exclusions if campaign else ''
    scope = f" in {geo}" if geo else ""
    focus_areas = f"Focus on evidence of: alignment with {cats or 'the campaign goal'}, controversies, risks, credibility, reach, and audience demographics."

    chat_input = (
        f"Campaign: {campaign.org_name if campaign else 'N/A'}\n"
        f"Goal: {campaign.campaign_goal if campaign else 'N/A'}\n"
        f"Location/Area: {geo or 'Not specified'}\n"
        f"Categories: {cats or 'Any'}\n"
        f"Exclusions: {exclusions or 'None'}\n"
        f"\n"
        f"Research these public figures{scope} for alignment with the campaign goal:\n\n"
        f"{profile_details}\n\n"
        "For each figure, analyze publicly available information including social media posts, "
        "news articles, and public statements. "
        f"{focus_areas}"
    )
    n8n_client = build_n8n_client()
    try:
        n8n_response = await n8n_client.trigger_discovery({"chatInput": chat_input})
        n8n_output = _parse_n8n_output(n8n_response)
        scraped_evidence = _n8n_output_to_evidence(n8n_output)
    except Exception:
        scraped_evidence = {}

    run = update_discovery_run(db, run, {"status": "completed"})

    from app.services.scoring.profile_verify import verify_candidate
    verified_normalized = []
    for candidate in normalized:
        candidate = await verify_candidate(candidate)
        conf = candidate.get("evidence_json", {}).get("verification_confidence", "unverified")
        if conf != "unverified":
            verified_normalized.append(candidate)
        else:
            log_action(db, "candidate.eliminated", "discovery_run", run.id,
                       {"reason": "profile_not_found", "name": candidate.get("name")})

    normalized = verified_normalized
    run = update_discovery_run(db, run, {"result_count": len(normalized), "status": "processing"})

    if normalized:
        scoring_tasks = []
        for idx, candidate in enumerate(normalized):
            clean = {k: v for k, v in candidate.items() if k not in ("profile_verified", "profile_urls", "verification_confidence")}
            influencer = create_influencer(
                db,
                {
                    "campaign_id": campaign_id,
                    "discovery_run_id": run.id,
                    **clean,
                },
            )
            candidate_evidence_raw = candidate.get("evidence_json") or {}
            if isinstance(candidate_evidence_raw, str):
                try:
                    candidate_evidence = json.loads(candidate_evidence_raw)
                except (json.JSONDecodeError, TypeError):
                    candidate_evidence = {}
            elif isinstance(candidate_evidence_raw, dict):
                candidate_evidence = candidate_evidence_raw
            else:
                candidate_evidence = {}
            if idx < len(raw_candidates) and raw_candidates[idx].get("evidence"):
                text_evidence = raw_candidates[idx]["evidence"]
                candidate_evidence.setdefault("content_values", []).append(text_evidence)
            for key in ["content_values", "public_record", "audience_profile", "risk_controversy"]:
                scraped_items = scraped_evidence.get(key, [])
                existing = candidate_evidence.get(key, [])
                if isinstance(existing, list):
                    candidate_evidence[key] = existing + scraped_items
                else:
                    candidate_evidence[key] = scraped_items
            existing_sources = candidate_evidence.get("sources", [])
            if isinstance(existing_sources, list):
                candidate_evidence["sources"] = existing_sources + scraped_evidence.get("sources", [])
            else:
                candidate_evidence["sources"] = scraped_evidence.get("sources", [])

            scoring_tasks.append({
                "influencer_id": influencer.id,
                "candidate": candidate,
                "evidence": candidate_evidence,
            })

        campaign_context = {"campaign_id": campaign_id, "goal": getattr(campaign, 'campaign_goal', '')}
        t3 = asyncio.create_task(_score_influencers_background(
            campaign_id, run.id, scoring_tasks, campaign_context
        ))
        _background_tasks.add(t3)
        t3.add_done_callback(_background_tasks.discard)
    await event_bus.publish("discovery.completed", {
        "campaign_id": run.campaign_id,
        "run_id": run.id,
        "status": run.status,
        "result_count": run.result_count or 0,
    })
    return DiscoveryRunResponse(
        id=run.id,
        campaign_id=run.campaign_id,
        status=run.status,
        n8n_run_id=run.n8n_run_id,
        result_count=run.result_count,
        raw_input=run.raw_input,
        raw_output=run.raw_output,
        error=run.error,
        created_at=run.created_at,
    )


@router.get("/{campaign_id}/runs/{run_id}", response_model=DiscoveryRunResponse)
async def get_discovery_status(
    campaign_id: str,
    run_id: str,
    db: Session = Depends(get_db),
) -> DiscoveryRunResponse:
    run = get_discovery_run(db, run_id, campaign_id)
    if not run:
        raise HTTPException(status_code=404, detail="discovery run not found")
    if run.status in ("completed", "failed"):
        return DiscoveryRunResponse(
            id=run.id,
            campaign_id=campaign_id,
            status=run.status,
            n8n_run_id=run.n8n_run_id,
            result_count=run.result_count,
            raw_input=run.raw_input,
            raw_output=run.raw_output,
            error=run.error,
            created_at=run.created_at,
        )
    status = run.status
    if run.n8n_run_id:
        status_client = build_n8n_status_client()
        if status_client:
            try:
                result = await status_client.get_run_status(run.n8n_run_id)
                status = result.get("status", run.status)
                if status == "completed" and run.result_count is None:
                    raw_candidates = result.get("candidates", [])
                    normalized = normalize_candidates(raw_candidates, cap=20)
                    from app.services.scoring.profile_verify import verify_candidate
                    verified = []
                    for candidate in normalized:
                        candidate = await verify_candidate(candidate)
                        conf = candidate.get("evidence_json", {}).get("verification_confidence", "unverified")
                        if conf != "unverified":
                            verified.append(candidate)
                    normalized = verified
                    if normalized:
                        run = update_discovery_run(db, run, {"status": "processing", "result_count": len(normalized)})
                        t4 = asyncio.create_task(_score_candidates_background(
                            campaign_id, run.id, normalized, {"campaign_id": campaign_id}
                        ))
                        _background_tasks.add(t4)
                        t4.add_done_callback(_background_tasks.discard)
                    else:
                        run = update_discovery_run(db, run, {"status": "completed", "result_count": 0})
            except Exception:
                pass
    return DiscoveryRunResponse(
        id=run.id,
        campaign_id=campaign_id,
        status=status,
        n8n_run_id=run.n8n_run_id,
        result_count=run.result_count,
        raw_input=run.raw_input,
        raw_output=run.raw_output,
        error=run.error,
        created_at=run.created_at,
    )
