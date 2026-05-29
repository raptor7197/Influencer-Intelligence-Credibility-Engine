from app.services.scoring.types import CompositeResult


ELIGIBILITY_RULES = [
    {
        "name": "missing_name",
        "check": lambda c: bool(c.get("name", "").strip()),
        "reason": "Candidate has no name",
    },
    {
        "name": "no_platforms",
        "check": lambda c: bool(c.get("platforms")),
        "reason": "Candidate has no known social media platforms",
    },
    {
        "name": "dormant_account",
        "check": lambda c: not (c.get("bio") or "").strip().startswith("[deactivated"),
        "reason": "Account appears deactivated or dormant",
    },
    {
        "name": "hostile_keywords",
        "check": lambda c: not any(
            kw in (c.get("bio") or "").lower()
            for kw in ["i hate animals", "animal cruelty", "pro-slaughter", "anti-vegan", "troll", "hate"]
        ),
        "reason": "Bio contains hostility indicators",
    },
]


def check_eligibility(candidate: dict) -> tuple[bool, str | None]:
    for rule in ELIGIBILITY_RULES:
        if not rule["check"](candidate):
            return False, rule["reason"]
    return True, None


def phase0_filter(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    passed = []
    eliminated = []
    for c in candidates:
        eligible, reason = check_eligibility(c)
        if eligible:
            passed.append(c)
        else:
            eliminated.append({"candidate": c, "reason": reason})
    return passed, eliminated
