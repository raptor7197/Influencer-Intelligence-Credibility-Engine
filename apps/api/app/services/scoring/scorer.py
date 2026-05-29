import asyncio

import httpx

from app.core.settings import Settings
from app.services.llm import build_openrouter_client
from app.services.scoring.json_guard import safe_json_loads
from app.services.scoring.prompts import SCORING_SYSTEM_PROMPT, SCORING_USER_PROMPT_TEMPLATE
from app.services.scoring.rubric import DIMENSIONS
from app.services.scoring.types import DimensionResult, EvidenceDossier


async def score_dimension(
    dimension_key: str,
    campaign_context: dict,
    influencer_context: dict,
    dossier: EvidenceDossier,
) -> DimensionResult:
    settings = Settings()
    if dimension_key not in DIMENSIONS:
        return DimensionResult(
            dimension=dimension_key,
            score=5.0,
            rationale=f"Invalid dimension_key: {dimension_key}",
            evidence=[],
            confidence="low",
            uncertainty="Unknown dimension",
        )
    dimension = DIMENSIONS[dimension_key]
    if settings.llm_mode != "openrouter":
        rationale = (
            f"Scoring placeholder for {dimension['label']}. "
            "LLM scoring disabled."
        )
        return DimensionResult(
            dimension=dimension_key,
            score=5.0,
            rationale=rationale,
            evidence=[],
            confidence="low",
            uncertainty="LLM scoring disabled",
        )
    client = build_openrouter_client()
    user_prompt = SCORING_USER_PROMPT_TEMPLATE.format(
        campaign_context=campaign_context,
        influencer_context=influencer_context,
        dimension_key=dimension_key,
        rubric=dimension,
        dossier=dossier.model_dump(),
    )
    try:
        response = await client.chat(
            model=settings.openrouter_model_scoring,
            messages=[
                {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=settings.openrouter_max_tokens_scoring,
        )
    except httpx.HTTPStatusError as exc:
        return DimensionResult(
            dimension=dimension_key,
            score=5.0,
            rationale=f"OpenRouter returned {exc.response.status_code}",
            evidence=[],
            confidence="low",
            uncertainty=f"API HTTP error: {exc.response.status_code}",
        )
    except Exception as exc:
        return DimensionResult(
            dimension=dimension_key,
            score=5.0,
            rationale=f"API call failed: {type(exc).__name__}",
            evidence=[],
            confidence="low",
            uncertainty=f"OpenRouter API error: {type(exc).__name__}",
        )
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        return DimensionResult(
            dimension=dimension_key,
            score=5.0,
            rationale=f"Invalid API response structure: {exc}",
            evidence=[],
            confidence="low",
            uncertainty="Malformed OpenRouter response",
        )
    payload = safe_json_loads(content)
    if not isinstance(payload, dict):
        return DimensionResult(
            dimension=dimension_key,
            score=5.0,
            rationale="LLM returned invalid JSON",
            evidence=[],
            confidence="low",
            uncertainty="JSON parsing failed",
        )
    confidence_raw = payload.get("confidence")
    uncertainty_raw = payload.get("uncertainty")
    return DimensionResult(
        dimension=dimension_key,
        score=payload.get("score", 5.0),
        rationale=payload.get("rationale", ""),
        evidence=payload.get("evidence", []),
        confidence=str(confidence_raw) if confidence_raw is not None else None,
        uncertainty=str(uncertainty_raw) if uncertainty_raw is not None else None,
    )


async def score_all_dimensions(
    campaign_context: dict,
    influencer_context: dict,
    dossier: EvidenceDossier,
) -> list[DimensionResult]:
    results = await asyncio.gather(
        *[
            score_dimension(key, campaign_context, influencer_context, dossier)
            for key in DIMENSIONS
        ]
    )
    return list(results)
