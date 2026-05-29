from collections.abc import Iterable

from app.services.channel import compute_recommended_channel


def _parse_reach(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip().upper()
    if not s:
        return None
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    suffix = s[-1]
    try:
        if suffix in multipliers:
            num = float(s[:-1].rstrip("."))
            return int(num * multipliers[suffix])
        return int(float(s.replace(",", "")))
    except (ValueError, TypeError):
        return None


def normalize_candidates(raw_candidates: Iterable[dict], cap: int = 20) -> list[dict]:
    normalized = []
    for candidate in raw_candidates:
        if len(normalized) >= cap:
            break
        platforms = candidate.get("platforms")
        normalized.append(
            {
                "name": candidate.get("name", ""),
                "handle": candidate.get("handle"),
                "platforms": platforms,
                "estimated_reach": _parse_reach(candidate.get("estimated_reach")),
                "location": candidate.get("location"),
                "bio": candidate.get("bio"),
                "audience_category": candidate.get("audience_category"),
                "evidence_json": {"content_values": [candidate["evidence"]]} if isinstance(candidate.get("evidence"), str) else (candidate.get("evidence") or {}),
                "recommended_channel": compute_recommended_channel(platforms),
            }
        )
    return normalized
