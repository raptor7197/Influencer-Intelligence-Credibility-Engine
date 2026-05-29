import asyncio

from app.core.settings import Settings
from app.services.llm import build_openrouter_client
from app.services.scoring.prompts import EVIDENCE_SYSTEM_PROMPT
from app.services.scoring.json_guard import safe_json_loads
from app.services.scoring.types import EvidenceDossier


EVIDENCE_TASKS = {
    "content_values": "Analyze content and values alignment evidence with sources.",
    "public_record": "Scan public record for relevant signals and sources.",
    "audience_profile": "Infer audience profile with evidence and sources.",
    "risk_controversy": "Identify risk or controversy evidence with sources.",
}


def _build_prompt(task: str, campaign_context: dict, influencer_context: dict) -> str:
    return (
        f"Campaign context: {campaign_context}\n"
        f"Influencer context: {influencer_context}\n"
        f"Task: {task}\n"
        "Return JSON: {\"evidence\": [..], \"sources\": [..]}"
    )


async def build_evidence_dossier_parallel(
    campaign_context: dict,
    influencer_context: dict,
) -> EvidenceDossier:
    settings = Settings()
    if settings.llm_mode != "openrouter":
        return EvidenceDossier()
    client = build_openrouter_client()
    async def _run_task(key: str, task: str) -> tuple[str, dict]:
        response = await client.chat(
            model=settings.openrouter_model_evidence,
            messages=[
                {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _build_prompt(task, campaign_context, influencer_context),
                },
            ],
            temperature=0.1,
            max_tokens=settings.openrouter_max_tokens_evidence,
        )
        content = response["choices"][0]["message"]["content"]
        return key, safe_json_loads(content)

    raw_results = await asyncio.gather(
        *[_run_task(key, task) for key, task in EVIDENCE_TASKS.items()],
        return_exceptions=True,
    )
    results = {k: v for k, v in raw_results if not isinstance(v, Exception)}

    seen = set()
    sources = []
    for key in ["content_values", "public_record", "audience_profile", "risk_controversy"]:
        for s in results.get(key, {}).get("sources", []):
            s_str = str(s)
            if s_str not in seen:
                seen.add(s_str)
                sources.append(s)
    return EvidenceDossier(
        content_values=results.get("content_values", {}).get("evidence", []),
        public_record=results.get("public_record", {}).get("evidence", []),
        audience_profile=results.get("audience_profile", {}).get("evidence", []),
        risk_controversy=results.get("risk_controversy", {}).get("evidence", []),
        sources=sources,
    )
