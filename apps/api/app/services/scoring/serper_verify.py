import httpx

from app.core.settings import Settings

SERPER_URL = "https://google.serper.dev/search"


async def serper_search(query: str, num: int = 5) -> list[dict]:
    settings = Settings()
    if not settings.serper_api_key:
        return []
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(
                SERPER_URL,
                json={"q": query, "num": num},
                headers={"X-API-KEY": settings.serper_api_key},
            )
            if resp.status_code != 200:
                return []
            return resp.json().get("organic", [])
        except Exception:
            return []


async def verify_with_serper(
    name: str,
    handle: str | None,
    platforms: list[str] | None,
) -> dict:
    if not name or not handle:
        return {"verified": False, "confidence": "unverified", "found_urls": [], "reason": "no handle to verify"}

    handle_clean = handle.lower().lstrip("@")

    display = name[:80]
    query = f'"{display}" {handle_clean}'

    results = await serper_search(query)
    if not results:
        return {"verified": False, "confidence": "unverified", "found_urls": [], "reason": "no search results returned"}

    name_lower = name.lower()
    found_urls: list[str] = []
    name_matched = False
    handle_matched = False

    for r in results:
        link = (r.get("link") or "").lower()
        title = (r.get("title") or "").lower()
        snippet = (r.get("snippet") or "").lower()
        all_text = f"{title} {snippet}"

        if handle_clean and (handle_clean in link or handle_clean in all_text):
            handle_matched = True
            url = r["link"]
            if url not in found_urls:
                found_urls.append(url)

        if name_lower and (name_lower in title or name_lower in snippet):
            name_matched = True

    if handle_matched and name_matched:
        return {"verified": True, "confidence": "confirmed", "found_urls": found_urls, "reason": ""}
    if handle_matched or name_matched:
        return {"verified": True, "confidence": "uncertain", "found_urls": found_urls,
                "reason": f"{'handle' if handle_matched else 'name'} matched but not both"}
    return {"verified": False, "confidence": "unverified", "found_urls": [],
            "reason": "no search results match this person's name or handle"}
