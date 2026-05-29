import httpx

PLATFORM_URLS: dict[str, str] = {
    "instagram": "https://instagram.com/{}",
    "youtube": "https://youtube.com/@{}",
    "tiktok": "https://tiktok.com/@{}",
    "twitter": "https://x.com/{}",
    "facebook": "https://facebook.com/{}",
    "threads": "https://threads.net/@{}",
}


def _clean_handle(raw: str) -> str:
    raw = raw.strip().removeprefix("@").removeprefix("https://").removeprefix("http://")
    for prefix in ("instagram.com/", "x.com/", "twitter.com/", "facebook.com/",
                    "youtube.com/@", "youtube.com/", "tiktok.com/@", "tiktok.com/",
                    "threads.net/@", "threads.net/"):
        if raw.startswith(prefix):
            raw = raw.removeprefix(prefix)
            raw = raw.split("/")[0]
            break
    return raw.strip()


def build_profile_urls(handle: str | None, platforms: list[str] | None) -> list[str]:
    if not handle:
        return []
    cleaned = _clean_handle(handle)
    if not cleaned:
        return []
    platform_list = platforms or list(PLATFORM_URLS.keys())
    urls: list[str] = []
    for p in platform_list:
        tmpl = PLATFORM_URLS.get(p.lower())
        if tmpl and tmpl.format(cleaned) not in urls:
            urls.append(tmpl.format(cleaned))
    return urls


async def verify_profile_urls(urls: list[str]) -> list[str]:
    if not urls:
        return []
    live: list[str] = []
    async with httpx.AsyncClient(timeout=5) as client:
        for url in urls:
            try:
                resp = await client.head(url, follow_redirects=True)
                if resp.status_code < 400:
                    live.append(url)
            except Exception:
                pass
    return live


async def verify_candidate(candidate: dict) -> dict:
    handle = candidate.get("handle")
    platforms = candidate.get("platforms")
    urls = build_profile_urls(handle, platforms)
    live_urls = await verify_profile_urls(urls)

    evidence = candidate.get("evidence_json")
    if not isinstance(evidence, dict):
        evidence = {}
        candidate["evidence_json"] = evidence
    existing_sources = evidence.get("sources")
    if not isinstance(existing_sources, list):
        existing_sources = []
        evidence["sources"] = existing_sources

    for u in live_urls:
        if u not in existing_sources:
            existing_sources.append(u)

    from app.services.scoring.serper_verify import verify_with_serper
    name = candidate.get("name", "")
    serper_result = await verify_with_serper(name, handle, platforms)

    candidate["profile_verified"] = serper_result["verified"]
    candidate["profile_urls"] = live_urls
    evidence["verification_confidence"] = serper_result["confidence"]

    for url in serper_result.get("found_urls", []):
        if url not in existing_sources:
            existing_sources.append(url)

    return candidate
