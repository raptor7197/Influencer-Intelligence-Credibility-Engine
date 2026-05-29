import re

from app.services.scoring.rubric import DIMENSIONS
from app.services.scoring.types import CompositeResult, DimensionResult, KnockoutResult, ScoreProfile


SPONSORSHIP_RED_FLAGS = [
    "dairy", "meat", "beef", "chicken", "pork", "leather", "fur", "wool",
    "kfc", "mcdonald", "burger king", "wendy", "domino", "pizza hut",
    "nestle", "coca-cola", "pepsi", "starbucks",
]


def has_sponsorship_conflict(evidence: list[str]) -> bool:
    if not evidence:
        return False
    text = " ".join(evidence).lower()
    for flag in SPONSORSHIP_RED_FLAGS:
        if re.search(rf'\b{re.escape(flag)}\b', text):
            return True
    return False


DEAL_BREAKER_CONFLICT_SCORE = 0.3


def check_knockouts(results: list[DimensionResult], dossier_evidence: list[str] | None = None) -> KnockoutResult:
    scores = {r.dimension: r.score for r in results}
    d0 = scores.get("D0_ANIMAL_WELFARE_ALIGNMENT", 5)
    d5 = scores.get("D5_RISK_CONTROVERSY", 1)
    d7 = scores.get("D7_AUDIENCE_AUTHENTICITY", 5)

    if d0 <= 2:
        return KnockoutResult(knocked_out=True, reason="Influencer shows active opposition to animal welfare", rule="D0 ≤ 2")
    if d5 >= 9:
        return KnockoutResult(knocked_out=True, reason="Extreme reputational risk — association would damage org credibility", rule="D5 ≥ 9")
    if d5 >= 7:
        if dossier_evidence and has_sponsorship_conflict(dossier_evidence):
            return KnockoutResult(knocked_out=True, reason="Active sponsorship conflict detected from conflicting industry", rule="D5 ≥ 7 + sponsorship conflict")
    if d7 <= 2:
        return KnockoutResult(knocked_out=True, reason="Strong indicators of inauthentic audience — real reach is likely a fraction of reported numbers", rule="D7 ≤ 2")

    return KnockoutResult()


def classify_profile(results: list[DimensionResult]) -> ScoreProfile:
    scores = {r.dimension: r.score for r in results}
    d1 = scores.get("D1_VALUES_ALIGNMENT", 5)
    d3 = scores.get("D3_CREDIBILITY_TRUST", 5)
    d4 = scores.get("D4_REACHABILITY", 5)
    d5 = scores.get("D5_RISK_CONTROVERSY", 1)
    d6 = scores.get("D6_CAMPAIGN_FIT", 5)

    all_scores = [s.score for s in results if DIMENSIONS.get(s.dimension, {}).get("weight", 0) > 0]

    if all(s >= 6 for s in all_scores) and (max(all_scores) - min(all_scores)) <= 3:
        return ScoreProfile(
            label="strong_all_round",
            description="Consistently strong across all dimensions",
            recommendation="Strong candidate. Proceed with standard outreach.",
        )
    if d1 >= 7 and d5 >= 6:
        return ScoreProfile(
            label="high_alignment_high_risk",
            description="Strong values alignment but significant risk factors",
            recommendation="High potential but high risk. Requires careful manual review of risk factors before outreach.",
        )
    if d1 >= 7 and d3 >= 7 and d4 <= 4:
        return ScoreProfile(
            label="hidden_gem",
            description="Strong alignment and credibility but lower reach",
            recommendation="Small but mighty. Consider for niche campaigns or grassroots partnerships.",
        )
    if d4 >= 7 and (d1 <= 4 or d3 <= 4):
        return ScoreProfile(
            label="reach_over_substance",
            description="High reach but low alignment or credibility",
            recommendation="Looks good on paper but lacks genuine alignment. Partnership risks appearing inauthentic.",
        )
    return ScoreProfile(
        label="mixed_profile",
        description="Mixed signals across dimensions — manual review recommended",
        recommendation="Review dimension scores directly to assess suitability.",
    )


def compute_composite_score(results: list[DimensionResult]) -> float:
    total_weight = 0.0
    weighted_sum = 0.0
    for result in results:
        dimension = DIMENSIONS.get(result.dimension)
        if not dimension:
            continue
        weight = dimension["weight"]
        if weight > 0:
            total_weight += weight
        weighted_sum += weight * (result.score / 10.0)
    if total_weight == 0:
        return 0.0
    score = weighted_sum / total_weight
    return max(0.0, min(1.0, score))


def compute_composite_with_knockouts(results: list[DimensionResult], dossier_evidence: list[str] | None = None) -> CompositeResult:
    knockout = check_knockouts(results, dossier_evidence)
    if knockout.knocked_out:
        return CompositeResult(
            score=0.0,
            knocked_out=True,
            knockout_reason=knockout.reason,
            knockout_rule=knockout.rule,
        )
    score = compute_composite_score(results)
    profile = classify_profile(results)
    return CompositeResult(score=score, profile=profile)
