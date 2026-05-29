


## PROBLEM 1: The Evidence Dossier Is Built on Sand

### What's Wrong Now

Your pipeline has two evidence paths: a direct-map fast path (when evidence is pre-supplied) and an LLM parallel build (4 concurrent calls). Both paths share a critical flaw: **the LLM is asked to generate evidence about influencers using only its parametric knowledge or user-supplied text — there is no verification against external reality.**

### Why This Matters in Real Animal Advocacy Scenarios

**Real case:** The MrBeast animal rescue video controversy. MrBeast released "I Saved 1,000 Animals From Dying" — which looks like perfect alignment on the surface. But FOUR PAWS criticized the same creator for featuring elephants painting and cheetahs racing against cars, calling it "bizarre and unnatural." The same person scores 9/10 on values alignment if your LLM only knows the rescue video, and 3/10 if it knows the FOUR PAWS criticism.

**Real case:** The Heigl Foundation / Working Dogs of Nevada disaster. For years, actress Katherine Heigl's animal rescue foundation partnered with Working Dogs of Nevada — which was then raided by police, with 50+ dogs seized and two arrests on felony animal cruelty charges. Any LLM scoring Heigl's foundation before the raid would have given maximum alignment scores. The evidence dossier had no mechanism to surface the risk.

**Real case:** Austin Pets Alive! controversy. The executive director posted a video that triggered massive community backlash from shelter workers and fosters. Their influencer-style apology made things worse. An LLM scoring APA! as an outreach partner before this would have missed the brewing community resentment.

### Specific Improvements

**1A. Add an Evidence Verification Stage Between Collection and Scoring**

```python
# NEW STAGE: Evidence Verification
# After build_evidence_dossier_parallel() returns, 
# BEFORE score_all_dimensions()

class EvidenceVerifier:
    """Cross-references LLM-generated evidence claims against 
    searchable sources. Marks each evidence item as:
    - VERIFIED: Found corroborating source
    - UNVERIFIED: No source found (not necessarily false)
    - CONTRADICTED: Found contradicting information
    - FABRICATED: Claim appears to be LLM hallucination
    """
    
    async def verify_dossier(
        self, 
        dossier: EvidenceDossier,
        influencer_name: str,
        influencer_handle: str
    ) -> VerifiedEvidenceDossier:
        
        # For each evidence claim in the dossier:
        # 1. Extract the factual assertion
        # 2. Search for corroboration (web search API)
        # 3. Classify verification status
        # 4. Attach source URLs
        
        verification_results = []
        for claim in dossier.all_claims():
            search_query = f"{influencer_name} {claim.key_assertion}"
            search_results = await self.search_api.search(search_query)
            
            verification = await self.llm_verify(
                claim=claim,
                search_results=search_results,
                system_prompt=VERIFICATION_PROMPT
            )
            verification_results.append(verification)
        
        # Compute dossier-level confidence
        verified_ratio = count(VERIFIED) / total_claims
        contradicted_count = count(CONTRADICTED)
        
        return VerifiedEvidenceDossier(
            original=dossier,
            verifications=verification_results,
            overall_confidence=self._compute_confidence(
                verified_ratio, contradicted_count
            ),
            # CRITICAL: Flag if >30% of claims are unverified
            low_confidence_warning=verified_ratio < 0.3
        )
```

**Why:** The HALLUHARD benchmark found that **even frontier LLMs hallucinate 30–60% of the time** on factual claims about real-world entities. Your evidence dossier, built entirely by LLM calls, will contain fabricated evidence — specific quotes the person never said, events that never happened, partnerships that don't exist. Scoring on top of hallucinated evidence produces confidently wrong scores.

**1B. Add Temporal Decay to Evidence**

```python
class TemporalEvidenceWeight:
    """Evidence from 5 years ago is less predictive of 
    current alignment than evidence from last month."""
    
    DECAY_FACTORS = {
        "last_30_days": 1.0,
        "last_6_months": 0.85,
        "last_1_year": 0.70,
        "last_3_years": 0.50,
        "older_than_3_years": 0.30,
        "undated": 0.40,  # Penalty for unknown recency
    }
```

**Why:** People change. An influencer who posted pro-animal content in 2020 may have completely pivoted. The WIRES Australia case shows this vividly — an organization went from $100M in bushfire donations and celebrity endorsements (Obama, Ellen) to internal civil war, losing 1,000 members, and being called "the right money at the right time in the wrong hands." Static evidence snapshots miss trajectory.

---

## PROBLEM 2: Scoring Dimensions Miss Critical Real-World Signals

### What's Wrong Now

Your 7 dimensions (D0–D6) focus on alignment, values, audience, credibility, reachability, risk, and campaign fit. You're missing the two signals that real-world influencer vetting has identified as **the most predictive of partnership failure**.

### Improvements

**2A. Add D7: Audience Authenticity (Weight: 0.10, taken from D1 and D3)**

Research from SociaVault Labs (100,000 accounts analyzed) found that **37.2% of influencer followers show signs of being fake or inauthentic** — with Instagram at 41.8% and the macro tier (100K–500K, your most likely recommendation range) at a staggering 48.3% fraud rate.

For an animal advocacy org, recommending an influencer with 48% fake followers means **the org's outreach message reaches half the expected audience**, and if discovered, damages the org's credibility ("they can't even vet their own partners").

```python
# rubric.py — add new dimension

D7_AUDIENCE_AUTHENTICITY = DimensionRubric(
    name="Audience Authenticity",
    weight=0.10,
    description=(
        "Based on available signals, how authentic and genuine "
        "does this influencer's audience engagement appear? "
        "Consider: engagement rate relative to follower tier, "
        "comment quality patterns, follower growth patterns, "
        "audience-content geographic/demographic alignment."
    ),
    scale_anchors={
        1: "Strong indicators of purchased followers or engagement "
           "(suspicious growth spikes, generic bot-like comments, "
           "engagement rate far outside expected range for tier)",
        3: "Some concerning signals but inconclusive",
        5: "Average — no strong signals either way, typical for tier",
        7: "Positive signals — organic growth pattern, quality comments, "
           "audience demographics match content niche",
        9: "Strongly authentic — consistent organic growth, high-quality "
           "engagement, audience deeply engaged with content themes",
    },
    # Include tier-specific engagement benchmarks in prompt
    context_injection=ENGAGEMENT_RATE_BENCHMARKS,
)
```

And include these benchmarks from real data in the scoring prompt:

```python
ENGAGEMENT_RATE_BENCHMARKS = """
Expected engagement rate ranges by follower tier (Instagram):
- Nano (1K-10K): 3.0%-12.0%
- Micro (10K-50K): 1.5%-6.0%
- Mid (50K-100K): 1.0%-4.0%
- Macro (100K-500K): 0.5%-2.5%
- Mega (500K+): 0.3%-1.5%

Red flags for fake engagement:
- Engagement rate >2x the tier maximum (suspiciously high)
- Engagement rate <0.5x the tier minimum (fake followers diluting)
- Comment-to-like ratio below 0.5% (bots produce likes not comments)
- Generic/emoji-only comments >40% of total comments

Fraud rates by niche (from 2026 SociaVault study, 100K accounts):
- Food & Cooking: 30.6% (relatively clean)
- Education/How-to: 28.8%
- Fitness & Health: 40.8%
- Travel & Lifestyle: 44.6%
- Beauty & Cosmetics: 52.1% (highest fraud)
"""
```

**Rebalance weights to accommodate:**

| Dimension | Current Weight | New Weight | Change |
|-----------|---------------|------------|--------|
| D0 Animal Welfare Alignment | 0.15 | 0.15 | — |
| D1 Values Alignment | 0.25 | 0.20 | -0.05 |
| D2 Audience Relevance | 0.20 | 0.18 | -0.02 |
| D3 Credibility & Trust | 0.20 | 0.17 | -0.03 |
| D4 Reachability | 0.10 | 0.08 | -0.02 |
| D5 Risk & Controversy | -0.15 | -0.15 | — |
| D6 Campaign Fit | 0.15 | 0.12 | -0.03 |
| **D7 Audience Authenticity** | **—** | **0.10** | **NEW** |
| **Positive sum** | **1.05** | **1.00** | |

**2B. Add D8: Controversy Velocity (Weight: -0.05, second penalty dimension)**

The existing D5 (Risk & Controversy) captures **static risk** — what has happened. But the most dangerous influencers for nonprofit partnerships are the ones who **attract controversy frequently**, even if each individual controversy seems minor.

```python
D8_CONTROVERSY_VELOCITY = DimensionRubric(
    name="Controversy Velocity",
    weight=-0.05,  # Second penalty dimension
    description=(
        "How frequently does this person attract public controversy, "
        "backlash, or negative attention — regardless of severity? "
        "A person who has one major controversy in 10 years is less "
        "risky than someone with minor controversies every quarter."
    ),
    scale_anchors={
        1: "No known controversies in recent years; stable public presence",
        3: "One notable controversy in last 2 years, handled well",
        5: "Occasional minor controversies (1-2 per year), some poorly handled",
        7: "Frequent controversy (quarterly+), pattern of polarizing behavior",
        9: "Constant controversy magnet; associating with them guarantees "
           "your org will be drawn into public disputes",
    },
)
```

**Why:** The Carrot Cottage Rabbit Rescue case is a perfect example. A tiny animal charity in South Wales got dragged into a months-long online harassment campaign by activists simply because the charity *followed the wrong account on X*. For an animal advocacy org, partnering with someone who attracts controversy (even unrelated) creates surface area for the org to get dragged into disputes that damage their mission.

**Adjust composite formula denominator to only sum positive weights:**

```python
# composite.py update
positive_weights = sum(w for w in weights if w > 0)  
# Now: 0.15+0.20+0.18+0.17+0.08+0.12+0.10 = 1.00
# Penalty weights: -0.15 (D5) + -0.05 (D8) = -0.20
# These subtract from numerator but don't appear in denominator
```

---

## PROBLEM 3: LLM Scoring Bias Is Unmitigated

### What's Wrong Now

You fire 7 (soon 9) concurrent LLM calls with fixed rubric prompts and take the scores at face value. Research on LLM-as-a-Judge reveals **multiple systematic biases** that will silently corrupt your scores.

### Specific Biases Affecting Your Pipeline

**Positional Bias in Rubric Scoring:** Research published at EACL 2026 and multiple 2025–2026 papers demonstrates that when LLMs are given a rubric with score options listed in order (1 through 10), they exhibit **systematic position preference** — favoring scores at the beginning or end of the rubric list. Since your rubric always presents anchors in ascending order (1, 3, 5, 7, 9), you likely have a slight bias toward middle or endpoint scores.

**Overconfidence:** Research from AAAI 2026 identifies the "Overconfidence Phenomenon" where LLM judges' predicted confidence *significantly overstates actual correctness*. Your pipeline trusts the LLM's reported `confidence` field — but this is systematically inflated.

**Score ID Bias:** The literal score numbers matter. LLMs may prefer "7" over "6" for reasons unrelated to the rubric content — simply because 7 is a more "natural" or common number in training data.

### Specific Improvements

**3A. Implement Balanced Permutation Scoring**

```python
# scorer.py — major upgrade

class CalibratedDimensionScorer:
    """Scores each dimension using balanced rubric permutation
    to mitigate position bias. Runs 2-3 scoring calls per dimension
    with permuted rubric orderings and aggregates."""
    
    async def score_dimension_calibrated(
        self,
        dimension: DimensionRubric,
        evidence: VerifiedEvidenceDossier,
        campaign_context: CampaignContext,
        influencer_context: InfluencerContext,
    ) -> CalibratedDimensionResult:
        
        # Generate 3 rubric orderings by rotating anchor positions
        orderings = [
            # Original: 1, 3, 5, 7, 9 (ascending)
            dimension.scale_anchors,
            # Reversed: 9, 7, 5, 3, 1 (descending)  
            dict(reversed(dimension.scale_anchors.items())),
            # Shuffled: 5, 1, 9, 3, 7 (random)
            self._shuffle_anchors(dimension.scale_anchors),
        ]
        
        scores = []
        for ordering in orderings:
            result = await self._score_with_ordering(
                dimension, ordering, evidence,
                campaign_context, influencer_context
            )
            scores.append(result)
        
        # Aggregate: median score (robust to outliers)
        final_score = statistics.median([s.score for s in scores])
        
        # Measure scoring variance as a reliability signal
        score_variance = statistics.variance([s.score for s in scores])
        
        # If variance > 2.0, the dimension score is unreliable
        reliability = "high" if score_variance < 1.0 else \
                     "medium" if score_variance < 2.0 else "low"
        
        return CalibratedDimensionResult(
            score=final_score,
            # Use rationale from the run closest to the median
            rationale=self._best_rationale(scores, final_score),
            evidence=self._merge_evidence(scores),
            confidence=reliability,  # Replace LLM self-reported confidence
            uncertainty=self._merge_uncertainties(scores),
            raw_scores=scores,  # Store all runs for transparency
            score_variance=score_variance,
        )
```

**Cost impact:** This triples your dimension-scoring LLM calls (7→21 per influencer, or 9→27 with new dimensions). At ~$0.01/call with Grok/Gemini Flash, that's ~$0.27 per influencer vs ~$0.09 before. For 15 influencers: $4.05 vs $1.35. Still cheap. Reliability matters more.

**3B. Replace LLM Self-Reported Confidence with Computed Confidence**

```python
# confidence.py — NEW FILE

class ConfidenceComputer:
    """Computes confidence from observable signals rather than
    trusting the LLM's self-reported confidence level."""
    
    def compute_dimension_confidence(
        self,
        calibrated_result: CalibratedDimensionResult,
        evidence_verification: VerificationResult,
    ) -> ComputedConfidence:
        
        signals = {
            # 1. Score stability across rubric permutations
            "score_stability": 1.0 - min(
                calibrated_result.score_variance / 4.0, 1.0
            ),
            
            # 2. Evidence verification ratio
            "evidence_grounding": evidence_verification.verified_ratio,
            
            # 3. Evidence volume (more evidence = more confidence)
            "evidence_volume": min(
                len(evidence_verification.verified_claims) / 5.0, 1.0
            ),
            
            # 4. Rationale consistency across runs
            "rationale_consistency": self._compute_rationale_similarity(
                calibrated_result.raw_scores
            ),
            
            # 5. No contradicted evidence used
            "no_contradictions": 1.0 if 
                evidence_verification.contradicted_count == 0 
                else 0.3,
        }
        
        # Weighted confidence score
        weights = {
            "score_stability": 0.30,
            "evidence_grounding": 0.25,
            "evidence_volume": 0.20,
            "rationale_consistency": 0.15,
            "no_contradictions": 0.10,
        }
        
        computed = sum(
            signals[k] * weights[k] for k in signals
        )
        
        level = "high" if computed > 0.7 else \
                "medium" if computed > 0.4 else "low"
        
        return ComputedConfidence(
            level=level,
            score=computed,
            breakdown=signals,
        )
```

**Why:** The Overconfidence paper showed LLMs routinely report "high confidence" when they're wrong. By deriving confidence from *observable behavioral signals* (score stability, evidence verification, rationale consistency), you get a much more reliable signal for the user.

---

## PROBLEM 4: The Composite Score Hides Important Information

### What's Wrong Now

Your composite formula produces a single 0–1 score. But a score of 0.65 can mean very different things:

- **Profile A:** Scores 7 on everything. Boring but safe. (Flat 0.65)
- **Profile B:** Scores 9 on values alignment, 9 on campaign fit, but 2 on credibility and 8 on risk. Exciting but dangerous. (Spiky 0.65)

An animal advocacy org needs to know the *shape* of the score, not just the number.

### Improvements

**4A. Add Score Profile Classification**

```python
# composite.py — add after compute_composite_score()

class ScoreProfileClassifier:
    """Classifies the scoring pattern to help users 
    quickly understand what KIND of candidate this is."""
    
    PROFILES = {
        "strong_all_round": {
            "description": "Consistently strong across all dimensions",
            "condition": lambda scores: all(s >= 6 for s in scores.values())
                        and max(scores.values()) - min(scores.values()) <= 3,
            "recommendation": "Strong candidate. Proceed with standard outreach.",
            "emoji": "🟢",
        },
        "high_alignment_high_risk": {
            "description": "Strong values alignment but significant risk factors",
            "condition": lambda scores: scores["values_alignment"] >= 7
                        and scores["risk_controversy"] >= 6,
            "recommendation": "⚠️ High potential but high risk. Requires "
                            "careful manual review of risk factors before outreach.",
            "emoji": "🟡",
        },
        "hidden_gem": {
            "description": "Strong alignment and credibility, lower reach",
            "condition": lambda scores: scores["values_alignment"] >= 7
                        and scores["credibility_trust"] >= 7
                        and scores["reachability"] <= 4,
            "recommendation": "Small but mighty. Consider for niche campaigns "
                            "or grassroots partnerships.",
            "emoji": "💎",
        },
        "reach_over_substance": {
            "description": "High reach but low alignment or credibility",
            "condition": lambda scores: scores["reachability"] >= 7
                        and (scores["values_alignment"] <= 4 
                             or scores["credibility_trust"] <= 4),
            "recommendation": "🔴 Looks good on paper but lacks genuine alignment. "
                            "Partnership risks appearing inauthentic.",
            "emoji": "🔴",
        },
        "low_confidence": {
            "description": "Insufficient data to evaluate reliably",
            "condition": lambda scores, conf: conf.level == "low",
            "recommendation": "⚠️ Not enough information to evaluate. "
                            "Consider manual research before deciding.",
            "emoji": "❓",
        },
    }
```

**4B. Add Knockout Rules (Hard Disqualifiers)**

Some scores should **immediately disqualify** a candidate regardless of composite score. Inspired by CreatorScore's knockout factor system:

```python
# composite.py — add knockout checks

KNOCKOUT_RULES = [
    {
        "name": "Active animal harm",
        "condition": lambda d: d["animal_welfare_alignment"].score <= 2,
        "reason": "Influencer shows active opposition to animal welfare",
    },
    {
        "name": "Severe reputational risk",
        "condition": lambda d: d["risk_controversy"].score >= 9,
        "reason": "Extreme reputational risk would damage org by association",
    },
    {
        "name": "Audience fraud",
        "condition": lambda d: d.get("audience_authenticity", {}).get("score", 5) <= 2,
        "reason": "Strong indicators of fake followers/engagement. "
                 "Real reach likely a fraction of reported numbers.",
    },
    {
        "name": "Evidence vacuum",
        "condition": lambda d, conf: conf.overall_confidence.score < 0.2,
        "reason": "Almost no verifiable information found about this person. "
                 "Cannot reliably assess alignment or risk.",
    },
]

def compute_composite_with_knockouts(
    dimension_scores: dict,
    confidence: ComputedConfidence,
) -> CompositeResult:
    
    # Check knockouts first
    for rule in KNOCKOUT_RULES:
        if rule["condition"](dimension_scores, confidence):
            return CompositeResult(
                score=0.0,
                knocked_out=True,
                knockout_reason=rule["reason"],
                knockout_name=rule["name"],
                dimension_scores=dimension_scores,
            )
    
    # Otherwise compute normally
    composite = _weighted_sum(dimension_scores)
    profile = ScoreProfileClassifier.classify(dimension_scores, confidence)
    
    return CompositeResult(
        score=composite,
        knocked_out=False,
        profile=profile,
        dimension_scores=dimension_scores,
    )
```

---

## PROBLEM 5: The Recommended Channel Logic Is Naive

### What's Wrong Now

```python
compute_recommended_channel()  # picks highest-priority platform from list
# Priority: Instagram > YouTube > TikTok > Twitter > LinkedIn > Facebook...
```

This is a static priority list that ignores the campaign context, the influencer's actual engagement patterns per platform, and the audience you're trying to reach.

### Why This Matters

For animal advocacy specifically, **the platform choice dramatically affects reception.** A factory farming exposé works on YouTube (long-form, documentary audiences) but is wrong for TikTok (entertainment-first, algorithmic discovery). A partnership announcement works on Instagram (visual, story-driven) but not LinkedIn (professional, feels tone-deaf for emotional causes).

### Improvement

```python
# channel.py — complete rewrite

class RecommendedChannelComputer:
    
    PLATFORM_CAUSE_FIT = {
        # Platform: { campaign_type: fit_score }
        "Instagram": {
            "awareness": 0.9,
            "fundraising": 0.7,
            "policy_advocacy": 0.3,
            "community_building": 0.8,
            "expose_investigation": 0.4,
        },
        "YouTube": {
            "awareness": 0.8,
            "fundraising": 0.5,
            "policy_advocacy": 0.6,
            "community_building": 0.5,
            "expose_investigation": 0.9,
        },
        "TikTok": {
            "awareness": 0.95,
            "fundraising": 0.4,
            "policy_advocacy": 0.2,
            "community_building": 0.7,
            "expose_investigation": 0.3,
        },
        "LinkedIn": {
            "awareness": 0.4,
            "fundraising": 0.3,
            "policy_advocacy": 0.8,
            "community_building": 0.3,
            "expose_investigation": 0.5,
        },
        "Twitter": {
            "awareness": 0.7,
            "fundraising": 0.3,
            "policy_advocacy": 0.9,
            "community_building": 0.6,
            "expose_investigation": 0.7,
        },
    }
    
    def compute(
        self,
        influencer_platforms: list[str],
        campaign_type: str,
        influencer_primary_platform: str | None,
        audience_match_signals: dict,
    ) -> ChannelRecommendation:
        
        candidates = []
        for platform in influencer_platforms:
            cause_fit = self.PLATFORM_CAUSE_FIT.get(
                platform, {}
            ).get(campaign_type, 0.5)
            
            # Bonus if this is the influencer's primary/strongest platform
            primary_bonus = 0.2 if platform == influencer_primary_platform else 0.0
            
            # Bonus if audience signals suggest this platform has 
            # the best audience match
            audience_fit = audience_match_signals.get(platform, 0.5)
            
            total = (cause_fit * 0.4) + (audience_fit * 0.35) + \
                    (primary_bonus * 0.25)
            
            candidates.append(ChannelCandidate(
                platform=platform,
                score=total,
                reasoning=f"Cause fit: {cause_fit:.0%}, "
                         f"Audience fit: {audience_fit:.0%}, "
                         f"Primary platform: {'Yes' if primary_bonus else 'No'}",
            ))
        
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        return ChannelRecommendation(
            primary=candidates[0],
            alternatives=candidates[1:3],
            rationale=self._generate_rationale(candidates[0], campaign_type),
        )
```

---

## PROBLEM 6: No Feedback Loop or Calibration Mechanism

### What's Wrong Now

Every scoring run is independent. You never learn from past results. If a user approves an influencer that the system scored at 0.45, or rejects one scored at 0.85, that signal is lost.

### Improvement: Store User Decisions as Calibration Data

```python
# persist.py — add to persistence

async def persist_user_decision(
    influencer_id: str,
    decision: Literal["approved", "rejected", "maybe"],
    user_notes: str | None,
    composite_score: float,
    dimension_scores: dict,
):
    """Store the user's actual decision alongside the system's scores.
    Over time, this creates a calibration dataset that reveals:
    - Systematic over/under-scoring on specific dimensions
    - Score thresholds where users actually approve/reject
    - Dimensions that most predict user approval
    """
    await db.execute(
        """
        INSERT INTO scoring_calibration_log 
        (influencer_id, decision, user_notes, composite_score,
         dimension_scores_json, created_at)
        VALUES ($1, $2, $3, $4, $5, NOW())
        """,
        influencer_id, decision, user_notes,
        composite_score, json.dumps(dimension_scores)
    )

# Periodically analyze:
async def compute_calibration_report():
    """Generate a report showing how well scores predict user decisions."""
    rows = await db.fetch("""
        SELECT decision, composite_score, dimension_scores_json
        FROM scoring_calibration_log
        ORDER BY created_at DESC LIMIT 500
    """)
    
    approved = [r for r in rows if r["decision"] == "approved"]
    rejected = [r for r in rows if r["decision"] == "rejected"]
    
    return CalibrationReport(
        avg_approved_score=mean([r["composite_score"] for r in approved]),
        avg_rejected_score=mean([r["composite_score"] for r in rejected]),
        # Which dimensions best separate approved from rejected?
        discriminative_dimensions=compute_discriminative_power(
            approved, rejected
        ),
        # Is the system systematically over or under-scoring?
        calibration_bias=mean([r["composite_score"] for r in approved]) - 0.5,
    )
```

This doesn't change scores retroactively, but over time it tells you: *"Users approve influencers when D0 > 6 and D5 < 4, regardless of composite score — maybe D0 and D5 should be weighted higher."*

---

## PROBLEM 7: Model Fallback Strategy Is Too Crude

### What's Wrong Now

You use `x-ai/grok-4.20` for evidence and scoring, with `google/gemini-2.5-flash-preview` as fallback on HTTP 500+. But different models have different scoring biases, and switching models mid-pipeline without accounting for this introduces systematic score shifts.

### Improvement

```python
# openrouter_client.py — smarter fallback

class ModelFallbackStrategy:
    """When primary model fails, use the same fallback for ALL 
    remaining calls in the current influencer's scoring run.
    Don't mix models within a single influencer's evaluation."""
    
    PRIMARY = "x-ai/grok-4.20"
    FALLBACK = "google/gemini-2.5-flash-preview"
    
    def __init__(self):
        self._influencer_model_lock: dict[str, str] = {}
    
    def get_model_for_influencer(self, influencer_id: str) -> str:
        """Once a fallback is triggered for an influencer,
        ALL remaining calls for that influencer use the fallback."""
        return self._influencer_model_lock.get(
            influencer_id, self.PRIMARY
        )
    
    def record_failure(self, influencer_id: str):
        """Lock this influencer to fallback model."""
        self._influencer_model_lock[influencer_id] = self.FALLBACK
    
    # Also: tag the scoring results with which model was used
    # so the UI can show "⚠ Scored with fallback model" 
```

**Why:** If influencer A is scored with Grok for 5 dimensions and Gemini Flash for 2 (due to transient failures), those two dimensions will have subtly different scoring calibration. It's better to commit to one model per influencer.

---

## PROBLEM 8: No Scoring Provenance / Audit Trail

### What's Wrong Now

You persist composite_score, evidence_json, and 7 DimensionScore rows. But you don't store:
- Which model was used
- The exact prompts sent
- Raw LLM response text
- Evidence verification results
- Whether knockout rules were triggered
- Score variance from calibrated scoring

### Improvement

```python
# persist.py — add scoring_audit_log table

class ScoringAuditLog:
    """Full provenance for every scoring run. Required for:
    1. Debugging why a specific influencer was scored a certain way
    2. Reproducing scores if models change
    3. Organizational accountability (who ran what, when)
    4. Legal/reputational protection (can show due diligence)"""
    
    schema = """
    CREATE TABLE scoring_audit_log (
        id UUID PRIMARY KEY,
        influencer_id UUID REFERENCES influencers(id),
        campaign_id UUID REFERENCES campaigns(id),
        
        -- Pipeline metadata
        pipeline_version TEXT NOT NULL,
        primary_model TEXT NOT NULL,
        fallback_model TEXT,
        model_actually_used TEXT NOT NULL,
        
        -- Evidence phase
        evidence_source TEXT,  -- 'direct' | 'llm_parallel'
        evidence_verification_results JSONB,
        evidence_confidence_score FLOAT,
        
        -- Scoring phase
        dimension_raw_scores JSONB,  -- All permutation scores
        dimension_final_scores JSONB,
        score_variances JSONB,
        
        -- Composite phase
        composite_score FLOAT,
        knocked_out BOOLEAN,
        knockout_reason TEXT,
        score_profile TEXT,
        
        -- Full audit
        full_prompts_sent JSONB,
        full_responses_received JSONB,
        
        -- Metadata
        duration_ms INTEGER,
        total_llm_calls INTEGER,
        total_tokens_used INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """
```

---

## Updated Pipeline Diagram

```
Raw evidence (dict)
    │
    ▼
build_evidence_dossier()
    │ empty? ──► build_evidence_dossier_parallel() (4 LLM calls)
    ▼
┌────────────────────────────────┐
│  NEW: verify_evidence_dossier()│  ◄── Web search API calls
│  Cross-reference claims against│      per evidence claim
│  external sources              │
│  Output: VerifiedEvidenceDossier│
│  with per-claim verification   │
│  status + overall confidence   │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│  NEW: check_knockout_rules()   │
│  Hard disqualifiers:           │
│  - Active animal harm          │
│  - Extreme risk                │
│  - Evidence vacuum             │
│  ──► If knocked out: STOP,     │
│      persist with score=0      │
└───────────────┬────────────────┘
                │ (not knocked out)
                ▼
┌────────────────────────────────┐
│  UPGRADED: score_all_dimensions│
│  9 dimensions (D0-D8)         │
│  × 3 rubric permutations each │
│  = 27 parallel LLM calls       │
│                                │
│  Per dimension:                │
│  - 3 scores (ascending,        │
│    descending, shuffled rubric)│
│  - Median score selected       │
│  - Variance computed           │
│  - Rationale from best-match   │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│  NEW: compute_confidence()     │
│  From observable signals:      │
│  - Score stability (variance)  │
│  - Evidence verification ratio │
│  - Evidence volume             │
│  - Rationale consistency       │
│  - No contradictions           │
│  NOT from LLM self-report      │
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│  UPGRADED: compute_composite() │
│  Weighted sum (same formula)   │
│  + Score profile classification│
│  + Channel recommendation      │
│    (campaign-aware, not static)│
└───────────────┬────────────────┘
                │
                ▼
┌────────────────────────────────┐
│  UPGRADED: persist_scoring()   │
│  → influencer row (composite,  │
│    evidence, channel, profile) │
│  → 9 dimension_score rows      │
│  → scoring_audit_log row       │
│    (full provenance)           │
│  → COMMIT                      │
└────────────────────────────────┘
```

---

## Summary: Priority-Ordered Implementation Roadmap

| Priority | Improvement | Impact | Effort | Reason |
|----------|-----------|--------|--------|--------|
| **P0** | Evidence verification stage | 🔴 Critical | Medium | Without this, you're scoring on hallucinated evidence. All downstream scores are unreliable. |
| **P0** | Knockout rules | 🔴 Critical | Low | Prevents catastrophic recommendations (active animal harm, extreme risk). 30 minutes to implement. |
| **P1** | Balanced permutation scoring | 🟠 High | Medium | Proven to improve LLM-as-a-Judge reliability. Doubles cost but doubles trust. |
| **P1** | Computed confidence (replace self-reported) | 🟠 High | Medium | Users need to know when to trust scores. Self-reported confidence is proven unreliable. |
| **P1** | Audience authenticity dimension (D7) | 🟠 High | Low | 37-48% of influencer audiences are fake. Can't recommend influencers without assessing this. |
| **P2** | Score profile classification | 🟡 Medium | Low | Transforms a number into actionable insight. Small effort, big UX impact. |
| **P2** | Campaign-aware channel recommendation | 🟡 Medium | Low | Current static priority list gives wrong answers for many campaign types. |
| **P2** | Scoring audit log | 🟡 Medium | Low | Required for organizational accountability and debugging. |
| **P2** | Controversy velocity dimension (D8) | 🟡 Medium | Low | Adds nuance to risk assessment. |
| **P3** | Model fallback consistency | 🟢 Lower | Low | Edge case but easy fix. |
| **P3** | Calibration feedback loop | 🟢 Lower | Medium | Long-term improvement. Needs user decisions data first. |



-------------------------------------------------------------------------------------------------------------------------------------------------------into
Part 2 

# Improving Your Influencer Scoring Pipeline for Animal Advocacy Outreach

Your current pipeline is solid architecturally, but for the *specific use case* of identifying credible, authentic influencers for animal advocacy outreach, there are significant gaps in **evidence quality, scoring robustness, authenticity verification, and human-in-the-loop trust**. Let me walk through real-world failure modes and concrete improvements.

---

## 1. The Core Problems With Your Current Pipeline (Real-World Failure Modes)

Before fixing things, let's name what actually goes wrong in production:

### Failure Mode A: "The Performative Vegan"
An influencer posts a single Veganuary photo in 2021. Your Grok-4 evidence call surfaces it, D0 (Animal Welfare Alignment) scores 7/10, composite looks great. In reality, they've posted steakhouse content 40 times since. **Your pipeline has no temporal weighting or contradiction detection.**

### Failure Mode B: "The Lookalike Audience Trap"
A fitness influencer with 2M followers scores high on D2 (Audience Relevance) because "health-conscious audience." But 60% of their followers are bots or low-engagement ghost accounts purchased in 2019. **You have no audience authenticity check.**

### Failure Mode C: "The Hidden Sponsor"
An influencer aligns perfectly on paper — plant-based recipes, sustainability content. Your pipeline misses that they have an active dairy industry sponsorship deal from 6 months ago. **D5 (Risk) is too dependent on what the LLM "remembers" rather than structured sponsorship/affiliation evidence.**

### Failure Mode D: "The LLM Hallucination Cascade"
Grok-4.20 invents a quote ("X said factory farming is barbaric in a 2023 podcast") with a plausible-looking but fake URL. The dimension scorer cites it as evidence. The campaign manager reaches out citing the quote. Reputational disaster. **You have no source verification layer.**

### Failure Mode E: "The Single-Snapshot Score"
You score once and persist. Six months later the influencer has a controversy, but the DB still shows composite 0.82. **No re-scoring cadence, no decay, no change detection.**

---

## 2. Concrete Improvements (Prioritized)

### 🔴 Priority 1: Add a Source Verification Layer (Between Phase 1 and Phase 2)

Right now your LLM returns `evidence + source URLs` and you trust them. Add a **deterministic verification step**:

```
Phase 1.5 — Evidence Verification
├── For each source URL in dossier:
│   ├── HEAD request → confirm 200 OK
│   ├── Fetch + extract text (trafilatura/readability)
│   ├── Semantic match: does the page actually contain the claim?
│   │   └── Small cheap LLM call (gemini-flash) returns {verified: bool, confidence}
│   └── Tag evidence: verified | unverified | dead_link | contradicted
└── Drop or downweight unverified evidence before Phase 2
```

**Why this matters:** Eliminates ~80% of hallucinated quotes. Animal advocacy outreach lives or dies on credibility — citing a fake quote to a celebrity's PR team ends the relationship.

Add a new field to `DimensionResult`: `verified_evidence_ratio` (0.0–1.0). If <0.5, flag the score as `low_confidence` regardless of LLM-reported confidence.

---

### 🔴 Priority 2: Temporal Weighting & Behavioral Consistency

Add a **recency-weighted evidence model**. Not all evidence is equal:

| Evidence Age | Weight Multiplier |
|---|---|
| < 6 months | 1.0 |
| 6–18 months | 0.7 |
| 18–36 months | 0.4 |
| > 36 months | 0.2 |
| Contradicted by newer evidence | 0.0 + risk flag |

Add a new sub-process in evidence building:

```python
# evidence_consistency.py
def detect_contradictions(dossier: EvidenceDossier) -> List[Contradiction]:
    # LLM call: "Given these timestamped evidence items, 
    # identify pairs that contradict each other.
    # Output: [{item_a, item_b, contradiction_type, severity}]"
```

This directly catches **Failure Mode A** (performative vegan). The pipeline shouldn't reward a 4-year-old Veganuary post equally with last week's grilled salmon promo.

---

### 🟠 Priority 3: Replace D2 (Audience Relevance) With a Structured Audience Authenticity Module

Right now D2 is one LLM call. For animal advocacy you need to know:

1. **Audience size validity** — engagement-to-follower ratio benchmarked against platform/niche norms
2. **Audience overlap with relevant communities** (plant-based, animal welfare, environmental, health & wellness)
3. **Bot/inauthentic follower estimation** — integrate with HypeAuditor, Modash, or compute proxy from engagement variance
4. **Geographic match** to campaign target region

Convert D2 from a single LLM score to a **composite of structured signals + LLM interpretation**:

```
D2_score = 0.3 * engagement_authenticity 
         + 0.3 * niche_overlap_score 
         + 0.2 * geographic_fit 
         + 0.2 * llm_qualitative_score
```

This addresses **Failure Mode B** and makes D2 the most defensible dimension to your human reviewers — they can drill into the components.

---

### 🟠 Priority 4: Split D5 (Risk & Controversy) Into Sub-Dimensions

A single risk score is too coarse for advocacy work. Different risks have different mitigations:

| Sub-Dimension | Examples | Weight |
|---|---|---|
| D5a — Sponsorship Conflicts | Active dairy/meat/leather brand deals | -0.05 |
| D5b — Personal Conduct Controversy | Harassment, legal issues | -0.05 |
| D5c — Ideological Risk | Adjacent to extremist communities | -0.03 |
| D5d — Inconsistency Risk | Public flip-flops on values | -0.02 |

Each gets its own evidence query and scorer. Persistence stores them separately so a campaign manager can say "I'm fine with D5d but not D5a." This directly fixes **Failure Mode C**.

Add a **deal-breaker flag**: if any sub-dimension exceeds a threshold (e.g., active meat industry sponsorship), the composite is capped at 0.3 regardless of other scores. Hard floor logic, not soft weighting.

---

### 🟡 Priority 5: Model Routing & Ensemble for High-Stakes Dimensions

Grok-4.20 for everything is risky. Use a **tiered router**:

| Task | Primary | Cross-Check |
|---|---|---|
| Evidence gathering (content_values, public_record) | Grok-4 (web access) | — |
| Audience profile | Perplexity sonar-large (real-time web) | — |
| D0, D1 scoring (values alignment) | Claude Sonnet 4.5 (nuance) | Gemini 2.5 Pro on disagreements |
| D3 (Credibility) | GPT-4o or Claude (calibrated) | — |
| D5 (Risk) | Claude (refuses to fabricate) + Grok (web) | **Always run both, take max risk score** |
| Cheap verification tasks | Gemini Flash | — |

For D5 specifically, **ensemble with max()** — you want the *more pessimistic* risk reading, not an average. False negatives on risk are catastrophic; false positives just mean you skip a candidate.

---

### 🟡 Priority 6: Add Phase 0 — Candidate Pre-Filtering

Before spending 11+ LLM calls per candidate, run a cheap gate:

```
Phase 0 — Eligibility Gate (1 small LLM call + structured checks)
├── Follower threshold met for campaign tier? 
├── Platform present in campaign's target platforms?
├── Last public activity within 90 days? (not dormant)
├── Account verified or has verifiable web presence?
└── Not on global block-list (previously rejected, hostile to advocacy)
   → If any fail: short-circuit, status=ineligible, skip Phases 1–3
```

This saves cost and dramatically speeds up batch discovery runs. At 5 req/s rate limit, gating out 40% of candidates upfront is a huge throughput win.

---

### 🟡 Priority 7: Confidence-Aware Composite Score

Your current composite is `Σ(weight_i * score_i/10) / Σ(positive_weights)`. Add **confidence weighting**:

```python
composite_raw = Σ(w_i * (score_i/10)) / Σ(positive_weights_i)
confidence_avg = Σ(w_i * confidence_i) / Σ(|w_i|)
verified_ratio = avg(verified_evidence_ratio across dimensions)

composite_final = composite_raw * confidence_avg * verified_ratio
```

Also persist three numbers instead of one:
- `composite_raw` (the LLM's view)
- `composite_adjusted` (confidence-weighted)
- `composite_floor` / `composite_ceiling` (uncertainty bounds)

Surface the **range** in the UI: "0.62–0.78 (medium confidence)" instead of "0.71". This is essential for the "human makes final call" model in your spec.

---

### 🟢 Priority 8: Persistent Evidence Lineage & Re-Scoring

Current persistence overwrites. Change to versioned:

```sql
-- New tables
evidence_dossier_versions (id, influencer_id, dossier_json, created_at, pipeline_version)
score_versions (id, influencer_id, dimension, score, evidence_refs[], created_at)
score_changes (influencer_id, dimension, old, new, delta, reason, detected_at)
```

Schedule **re-scoring triggers**:
- Time-based: every 90 days for "active" candidates, 180 days for "shortlisted"
- Event-based: when n8n detects new public activity, a news mention, or a sponsorship change
- Manual: campaign manager hits "Re-evaluate"

When composite shifts by > 0.15 between versions, send an alert. This fixes **Failure Mode E** and gives your users an audit trail — critical for organizations that need to justify outreach choices to boards or donors.

---

### 🟢 Priority 9: Authenticity Signals Specific to Animal Advocacy

Add a new bucket to `EvidenceDossier`: `authenticity_signals`. Look for things that distinguish performative from genuine alignment:

- **Longitudinal consistency**: Same values expressed across 2+ years
- **Costly signaling**: Turned down brand deals for ethical reasons (mentioned publicly)
- **Connections**: Engages with established advocacy figures, orgs, sanctuaries
- **Lifestyle integration**: Cooking, pets, daily life vs. only "campaign moments"
- **Educational content**: Explains *why*, not just *what*
- **Crisis behavior**: How they responded to public animal welfare incidents

Build a dedicated `authenticity_score` (0–1) that gates D0 and D1. An influencer with D0=9 but authenticity=0.3 should be flagged as "high-reach, low-genuineness — outreach risk."

---

### 🟢 Priority 10: Structured Outreach Recommendations Tied to Evidence

Your spec mentions "AI-generated outreach recommendations" but the pipeline doesn't produce them. Add Phase 4:

```
Phase 4 — Engagement Strategy Synthesis
├── Input: full dossier + all dimension scores + campaign context
├── Output structured JSON:
│   ├── recommended_approach: "warm intro" | "cold DM" | "agent outreach" | "press"
│   ├── recommended_channel: (your existing logic, but evidence-informed)
│   ├── opening_hooks: [3 specific topics from their content to reference]
│   ├── values_bridge: how campaign aligns with their stated values (with citations)
│   ├── topics_to_avoid: things their audience reacts negatively to
│   ├── ideal_ask: content collab | one-time post | event | quiet endorsement
│   ├── timing_signals: upcoming relevant moments (launches, anniversaries)
│   └── do_not_use_phrases: jargon their audience rejects (e.g. avoid "vegan" if they brand as "plant-based")
└── Every recommendation must cite specific evidence IDs from the dossier
```

This makes the pipeline output **directly actionable** for the outreach strategist persona, instead of leaving them to interpret a composite score.

---

## 3. Revised Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 0 — Eligibility Gate (cheap, ~1s)                        │
│   structured checks + 1 small LLM call → short-circuit if fail  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1 — Evidence Dossier (parallel, 5 buckets now)           │
│   content_values | public_record | audience_profile             │
│   risk_controversy | authenticity_signals                       │
│   + temporal metadata on every evidence item                    │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1.5 — Verification & Consistency                         │
│   ├── URL liveness + content match                              │
│   ├── Temporal weighting                                        │
│   ├── Contradiction detection                                   │
│   └── verified_evidence_ratio tagged per bucket                 │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2 — Dimension Scoring (parallel, 10 dimensions now)      │
│   D0, D1, D2 (structured composite), D3, D4,                    │
│   D5a, D5b, D5c, D5d (risk sub-dims), D6                        │
│   + authenticity_score gate on D0/D1                            │
│   + model routing per dimension                                 │
│   + ensemble (max risk) for D5                                  │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3 — Composite + Confidence Bounds                        │
│   composite_raw, composite_adjusted, ceiling, floor             │
│   + deal-breaker flags (hard caps)                              │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4 — Outreach Strategy Synthesis                          │
│   approach, channel, hooks, bridges, asks, timing, avoidances   │
│   every recommendation cites evidence IDs                       │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Persistence (versioned)                                        │
│   dossier_versions, score_versions, change_log, alerts          │
└─────────────────────────────────────────────────────────────────┘
                              ▼
                  Re-scoring scheduler (90/180d + event-triggered)
```

---

## 4. Quick Wins You Can Ship This Week

If the full redesign is too big, do these five first — each is independently valuable:

1. **Add URL liveness check** in a post-evidence step. Drop evidence with dead links. (2-day effort, eliminates worst hallucinations.)
2. **Ensemble D5 with max()** across Grok + Claude. (1-day effort, biggest risk reduction.)
3. **Add deal-breaker hard caps** on composite for active conflicting sponsorships. (1-day effort, prevents catastrophic outreach.)
4. **Persist confidence bounds** alongside composite and surface range in UI. (2-day effort, sets correct expectations for human reviewers.)
5. **Version evidence dossiers** instead of overwriting. (1-day effort, enables future re-scoring and audit trails.)

---

## 5. Metrics to Track Whether It's Actually Working

You can't improve what you don't measure. Add these:

- **Outreach acceptance rate** by composite score bucket (does 0.8+ actually convert better than 0.6?)
- **Post-outreach reputational incidents** per 100 contacts (are you catching the risks?)
- **Evidence verification pass rate** per LLM model (which models hallucinate most?)
- **Score stability**: composite delta between v1 and v2 of same influencer (high churn = pipeline noise)
- **Human override rate**: how often do reviewers reject pipeline recommendations, and on which dimensions? Feed this back into prompt tuning.

---

The throughline of all these changes is the same: **your users are making real outreach decisions that affect real relationships and real organizational reputations.** The pipeline should optimize for *defensibility and authenticity* over raw throughput. Every score should be traceable to verified evidence, every recommendation should cite its sources, and every risk signal should be conservative by default.

Want me to draft the schema changes, the Phase 1.5 verification code, or the revised rubric.py with sub-dimensions next?
