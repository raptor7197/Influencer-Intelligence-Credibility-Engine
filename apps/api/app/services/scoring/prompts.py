EVIDENCE_SYSTEM_PROMPT = """
You are an expert research agent. Provide evidence-only findings with citations.
Output must be valid JSON and contain only evidence lists and sources.
"""

EVIDENCE_USER_PROMPT_TEMPLATE = """
Campaign context:
{campaign_context}

Influencer context:
{influencer_context}

Task: Return a JSON object with keys:
- content_values: list of evidence statements with source URLs
- public_record: list of evidence statements with source URLs
- audience_profile: list of evidence statements with source URLs
- risk_controversy: list of evidence statements with source URLs
- sources: list of source URLs
"""

SCORING_SYSTEM_PROMPT = """
You are an evaluator. Use only the provided evidence dossier.
Return JSON with score (1-10), rationale, evidence[], confidence, uncertainty.
Do not infer beyond evidence.
"""

SCORING_USER_PROMPT_TEMPLATE = """
Campaign context:
{campaign_context}

Influencer context:
{influencer_context}

Dimension:
{dimension_key}

Rubric:
{rubric}

Evidence dossier:
{dossier}
"""
