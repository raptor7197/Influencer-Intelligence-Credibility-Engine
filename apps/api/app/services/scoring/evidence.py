import httpx

from app.core.settings import Settings
from app.services.llm import build_openrouter_client
from app.services.scoring.json_guard import safe_json_loads
from app.services.scoring.prompts import EVIDENCE_SYSTEM_PROMPT, EVIDENCE_USER_PROMPT_TEMPLATE
from app.services.scoring.types import EvidenceDossier


async def verify_source_urls(urls: list[str]) -> list[str]:
    if not urls:
        return []
    live = []
    async with httpx.AsyncClient(timeout=5) as client:
        for url in urls:
            if not url.startswith(("http://", "https://")):
                continue
            try:
                resp = await client.head(url, follow_redirects=True)
                if resp.status_code < 400:
                    live.append(url)
            except Exception:
                pass
    return live


async def verify_dossier_sources(dossier: EvidenceDossier) -> EvidenceDossier:
    live_sources = await verify_source_urls(dossier.sources)
    dossier.sources = live_sources
    return dossier


def build_evidence_dossier(raw_inputs: dict) -> EvidenceDossier:
    return EvidenceDossier(
        content_values=raw_inputs.get("content_values", []),
        public_record=raw_inputs.get("public_record", []),
        audience_profile=raw_inputs.get("audience_profile", []),
        risk_controversy=raw_inputs.get("risk_controversy", []),
        sources=raw_inputs.get("sources", []),
    )


async def build_evidence_dossier_llm(
    campaign_context: dict,
    influencer_context: dict,
) -> EvidenceDossier:
    settings = Settings()
    if settings.llm_mode != "openrouter":
        return EvidenceDossier()
    client = build_openrouter_client()
    user_prompt = EVIDENCE_USER_PROMPT_TEMPLATE.format(
        campaign_context=campaign_context,
        influencer_context=influencer_context,
    )
    try:
        response = await client.chat(
            model=settings.openrouter_model_evidence,
            messages=[
                {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=settings.openrouter_max_tokens_evidence,
        )
    except Exception:
        return EvidenceDossier()

    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return EvidenceDossier()

    payload = safe_json_loads(content)
    if not isinstance(payload, dict):
        return EvidenceDossier()
    return build_evidence_dossier(payload)
