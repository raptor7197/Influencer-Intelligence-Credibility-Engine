import json
import uuid

from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.models.influencer import Influencer
from app.models.outreach_draft import OutreachDraft
from app.services.scoring.json_guard import safe_json_loads

SYSTEM_PROMPT = """
You are an outreach specialist. Write a short, personalized outreach message for an influencer.
Keep it concise (max 3 sentences for the body). Reference their actual content or values.

You MUST output ONLY valid JSON with these exact keys:
{
  "subject_line": "string (max 10 words)",
  "message_body": "string (max 3 sentences)",
  "framing_angles": ["string", "string", "string"],
  "messaging_tips": ["string", "string", "string"]
}

DO NOT include markdown, backticks, or any text outside the JSON object.
Return ONLY the JSON object, nothing else.
"""

USER_PROMPT_TEMPLATE = """
Organization: {org_name}
Outreach person: {outreach_person}
Campaign goal: {campaign_goal}
Target audience: {target_audience}

Influencer: {name}
Handle: {handle}
Bio: {bio}
Platforms: {platforms}
Recommended channel: {recommended_channel}

Their content / values alignment:
{evidence_content}

Past behavior / public record:
{public_record}

Write a short, warm outreach message suggesting a collaboration.
Reference something specific from their content or values to show personalization.
Recommend reaching out via {recommended_channel}.
Also suggest 2-3 framing angles and 2-3 messaging tips tailored to this influencer.

Return ONLY valid JSON with keys: subject_line, message_body, framing_angles, messaging_tips.
"""


def format_evidence_list(items: list[str] | None) -> str:
    if not items:
        return "Not available"
    return "\n".join(f"- {item}" for item in items)


async def generate_outreach_draft(
    db: Session,
    influencer: Influencer,
    tone: str = "professional",
) -> OutreachDraft:
    from app.models.campaign import Campaign
    from sqlalchemy import select

    settings = Settings()
    campaign = db.scalar(select(Campaign).where(Campaign.id == influencer.campaign_id))

    evidence = influencer.evidence_json or {}
    content_values = format_evidence_list(evidence.get("content_values"))
    public_record = format_evidence_list(evidence.get("public_record"))

    user_prompt = USER_PROMPT_TEMPLATE.format(
        org_name=campaign.org_name if campaign else "Unknown",
        outreach_person=campaign.outreach_person if campaign else "Unknown",
        campaign_goal=campaign.campaign_goal if campaign else "Unknown",
        target_audience=campaign.target_audience or "General",
        name=influencer.name,
        handle=influencer.handle or "N/A",
        bio=influencer.bio or "N/A",
        platforms=", ".join(influencer.platforms) if influencer.platforms else "N/A",
        recommended_channel=influencer.recommended_channel or "email",
        evidence_content=content_values,
        public_record=public_record,
    )

    draft_data = None
    if settings.llm_mode == "stub":
        draft_data = _stub_draft(influencer, tone)
    else:
        draft_data = await _llm_draft(influencer, user_prompt)

    if not draft_data or not draft_data.get("message_body", "").strip():
        draft_data = _stub_draft(influencer, tone)

    draft = OutreachDraft(
        id=str(uuid.uuid4()),
        influencer_id=influencer.id,
        subject_line=draft_data.get("subject_line", "Let's collaborate"),
        message_body=draft_data.get("message_body", ""),
        framing_angles=draft_data.get("framing_angles", []),
        messaging_tips=draft_data.get("messaging_tips", []),
        status=draft_data.get("status", "draft"),
        is_edited=False,
    )

    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


async def _llm_draft(influencer: Influencer, user_prompt: str) -> dict | None:
    from app.services.llm import build_openrouter_client
    settings = Settings()
    client = build_openrouter_client()
    try:
        response = await client.chat(
            model=settings.openrouter_model_scoring,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )
        content = response["choices"][0]["message"]["content"]
        parsed = safe_json_loads(content)
        if isinstance(parsed, dict) and parsed.get("message_body", "").strip():
            return parsed
    except Exception:
        pass
    finally:
        try:
            await client.close()
        except Exception:
            pass
    return None


def _stub_draft(influencer: Influencer, tone: str = "professional") -> dict:
    name = influencer.name.split()[0] if influencer.name else "there"
    channel = influencer.recommended_channel or "social media"
    bio = influencer.bio or "advocacy"
    return {
        "subject_line": "Collaboration opportunity",
        "message_body": f"Hi {name}, I've been following your work and love your content on {channel}. Your values around {bio} really align with our campaign. Would you be open to a conversation about collaborating?",
        "framing_angles": [
            f"Highlight their existing interest in {bio}",
            "Emphasize shared audience values",
            "Position as a natural extension of their content",
        ],
        "messaging_tips": [
            f"Reference their specific content about {bio}",
            f"Suggest reaching out via {channel} for best response",
            "Keep initial message light and exploratory",
        ],
        "status": "draft",
    }
