from app.core.settings import Settings
from app.services.llm import build_openrouter_client
from app.services.scoring.composite import compute_composite_with_knockouts
from app.services.scoring.evidence import build_evidence_dossier, verify_dossier_sources
from app.services.scoring.evidence_parallel import build_evidence_dossier_parallel
from app.services.scoring.json_guard import safe_json_loads
from app.services.scoring.scorer import score_all_dimensions
from app.services.scoring.types import CompositeResult, DimensionResult, EvidenceDossier


async def _risk_audit(
    dimension_results: list[DimensionResult],
    dossier: EvidenceDossier,
    campaign_context: dict,
    influencer_context: dict,
) -> float:
    settings = Settings()
    if settings.llm_mode != "openrouter":
        return 0.0
    client = build_openrouter_client()
    dossier_summary = "\n".join(dossier.risk_controversy[:5]) if dossier.risk_controversy else "No specific risk evidence."
    scores = {r.dimension: r.score for r in dimension_results}
    current_d5 = scores.get("D5_RISK_CONTROVERSY", 5)
    current_d8 = scores.get("D8_CONTROVERSY_VELOCITY", 1)
    prompt = (
        f"Campaign: {campaign_context}\n"
        f"Influencer: {influencer_context.get('name', '')} @{influencer_context.get('handle', '')}\n"
        f"Risk evidence:\n{dossier_summary}\n"
        f"Current D5 (Risk) score: {current_d5}/10\n"
        f"Current D8 (Controversy Velocity) score: {current_d8}/10\n"
        "Review all available evidence. If the current risk scores miss any red flags, "
        "return a higher score. Be conservative — false negatives on risk are dangerous.\n"
        "Return JSON: {\"d5_score\": float 1-10, \"d8_score\": float 1-10, \"reasoning\": str}"
    )
    try:
        response = await client.chat(
            model=settings.openrouter_model_scoring,
            messages=[
                {"role": "system", "content": "You are a conservative risk auditor. Output JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        content = response["choices"][0]["message"]["content"]
        payload = safe_json_loads(content)
        audited_d5 = payload.get("d5_score", current_d5)
        audited_d8 = payload.get("d8_score", current_d8)
        d5 = max(current_d5, audited_d5)
        for r in dimension_results:
            if r.dimension == "D5_RISK_CONTROVERSY":
                r.score = max(r.score, audited_d5)
            if r.dimension == "D8_CONTROVERSY_VELOCITY":
                r.score = max(r.score, audited_d8)
        return d5
    except Exception:
        return current_d5


class ScoringPipeline:
    async def run(
        self,
        campaign_context: dict,
        influencer_context: dict,
        raw_evidence: dict,
    ) -> tuple[CompositeResult, EvidenceDossier, list[DimensionResult]]:
        dossier = build_evidence_dossier(raw_evidence)
        if dossier.content_values or dossier.public_record or dossier.audience_profile or dossier.risk_controversy:
            pass
        else:
            parallel = await build_evidence_dossier_parallel(campaign_context, influencer_context)
            dossier.content_values = dossier.content_values or parallel.content_values
            dossier.public_record = dossier.public_record or parallel.public_record
            dossier.audience_profile = dossier.audience_profile or parallel.audience_profile
            dossier.risk_controversy = dossier.risk_controversy or parallel.risk_controversy
            dossier.sources = dossier.sources or parallel.sources
        dossier = await verify_dossier_sources(dossier)
        dimension_results = await score_all_dimensions(
            campaign_context=campaign_context,
            influencer_context=influencer_context,
            dossier=dossier,
        )
        await _risk_audit(dimension_results, dossier, campaign_context, influencer_context)
        all_evidence = (
            dossier.content_values
            + dossier.public_record
            + dossier.audience_profile
            + dossier.risk_controversy
        )
        composite_result = compute_composite_with_knockouts(dimension_results, all_evidence)
        return composite_result, dossier, dimension_results
