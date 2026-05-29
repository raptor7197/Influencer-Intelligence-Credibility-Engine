# Backend Scaffold

FastAPI service for campaign management, discovery orchestration, evidence collection, scoring, and outreach draft generation.

## Planned Structure
- `app/api` - route modules
- `app/core` - settings and shared backend config
- `app/db` - database session and repository wiring
- `app/integrations` - external service clients
- `app/models` - request/response and domain models
- `app/services` - business logic
- `app/tasks` - async orchestration jobs
- `tests` - backend tests

## Notes
- No runtime implementation is included yet.
- This scaffold is aligned to the async discovery and scoring flow.



POST /api/campaigns (create)
{
  "id": "c5f266f1-a9f6-44cc-9ff2-7c0d1a351b51",
  "org_name": "Animal Advocacy Alliance",
  "outreach_person": "Kris",
  "campaign_goal": "Promote plant-based eating to health-conscious millennials",
  "target_audience": "Health-conscious millennials",
  "geo_focus": "US",
  "language": "en",
  "categories": ["health", "fitness", "food"],
  "exclusions": ["politics"],
  "status": "draft"
}
GET /api/campaigns (list)
Array of the same CampaignResponse objects above.
GET /api/campaigns/{id} (detail with runs)
Same as above plus discovery_runs[]:
{
  "discovery_runs": [
    {
      "id": "run-uuid",
      "campaign_id": "campaign-uuid",
      "status": "completed",
      "n8n_run_id": null,
      "result_count": 5
    }
  ]
}
GET /api/campaigns/{id}/influencers (list)
Array of influencer cards. Each card the frontend renders:
{
  "id": "cbd6e41f-...",
  "campaign_id": "c5f266f1-...",
  "discovery_run_id": "a788ac3a-...",
  "name": "Grace Wellness",
  "handle": "@gracewellness",
  "platforms": ["instagram", "youtube"],
  "estimated_reach": 15000,
  "location": "US",
  "bio": "Plant-based nutrition advocate helping people transition to vegan diets",
  "audience_category": "health",
  "composite_score": 0.72,
  "status": "pending",
  "recommended_channel": "instagram",
  "dimension_scores": [
    {
      "id": "16f430f7-...",
      "dimension": "D0_ANIMAL_WELFARE_ALIGNMENT",
      "score": 9.0,
      "rationale": "Consistently promotes plant-based diet with evidence-based nutritional guidance...",
      "evidence": ["Advocates for plant-based nutrition"],
      "confidence": "high",
      "uncertainty": null
    },
    { "...same shape for D1 through D6..." }
  ],
  "outreach_draft": {
    "id": "3813a697-...",
    "subject_line": "Collaborate to inspire plant-based living",
    "message_body": "Hi Grace, I love your practical approach to vegan nutrition...",
    "framing_angles": [
      "Highlight their existing interest in plant-based nutrition",
      "Emphasize shared audience values of health and sustainability",
      "Position as a natural extension of their current content"
    ],
    "messaging_tips": [
      "Reference their specific content about budget-friendly vegan meals",
      "Suggest reaching out via Instagram for best response",
      "Keep initial message light and focused on shared values"
    ],
    "is_edited": false,
    "status": "draft"
  }
}
Frontend usage: This is the main card view. Show: name, handle, platforms, location, composite_score (show as badge), recommended_channel (show as icon), dimension scores could be a small radar or bar chart. Status drives UI color.
GET /api/campaigns/{id}/influencers/{id} (detail)
Same as list but adds evidence_json:
{
  "...same fields as list, plus...",
  "evidence_json": {
    "content_values": [
      "Advocates for plant-based nutrition in YouTube videos",
      "Shares vegan recipes weekly on Instagram",
      "Promotes cruelty-free lifestyle products"
    ],
    "public_record": [
      "Featured in Plant-Based News (2025)",
      "Spoke at Vegan Health Summit 2025"
    ],
    "audience_profile": [
      "80% followers aged 22-35",
      "High engagement rate on Instagram (4.5%)"
    ],
    "risk_controversy": [
      "No known controversies",
      "Occasionally posts about fast food alternatives"
    ],
    "sources": [
      "https://instagram.com/gracewellness",
      "https://youtube.com/gracewellness"
    ]
  }
}
Frontend usage: This is the drill-down / explainability panel. Show:
- evidence_json.content_values → "Why this influencer?" section
- evidence_json.risk_controversy → "Risks & concerns" section
- evidence_json.audience_profile → "Audience overview"
- Each dimension_score's rationale + uncertainty → per-dimension explanation
POST /api/campaigns/{id}/influencers/{id}/draft (generate)
{
  "id": "3813a697-...",
  "subject_line": "Collaborate to inspire plant-based living",
  "message_body": "Hi Grace, I love your practical approach to vegan nutrition...",
  "framing_angles": [
    "Highlight their existing interest in plant-based nutrition",
    "Emphasize shared audience values of health and sustainability",
    "Position as a natural extension of their current content"
  ],
  "messaging_tips": [
    "Reference their specific content about budget-friendly vegan meals",
    "Suggest reaching out via Instagram for best response",
    "Keep initial message light and focused on shared values"
  ],
  "is_edited": false,
  "status": "draft"
}
Frontend usage: Show the draft editor:
- subject_line → editable text input
- message_body → editable textarea
- framing_angles → show as suggestion pills/tips on the side
- messaging_tips → show as contextual guidance below the editor
PATCH /api/campaigns/{id}/influencers/{id}/draft (edit)
{
  "id": "3813a697-...",
  "subject_line": "Custom subject after human review",
  "message_body": "Hi Grace, we love your content...",
  "framing_angles": ["..."],
  "messaging_tips": ["..."],
  "is_edited": true,
  "status": "draft"
}
Request body: {"subject_line": "...", "message_body": "..."} (omit fields you don't want to change)
PATCH /api/campaigns/{id}/influencers/{id}/status
// Request body: {"status": "approved"}
// Response:
{
  "id": "cbd6e41f-...",
  "status": "approved"
}
Valid statuses: pending, approved, rejected, maybe
POST /api/campaigns/{id}/discover (trigger n8n)
{
  "id": "run-uuid",
  "campaign_id": "campaign-uuid",
  "status": "queued",
  "n8n_run_id": null,
  "result_count": null
}
Dimension Reference (7 dimensions)
Key	Label
D0_ANIMAL_WELFARE_ALIGNMENT	Animal Welfare Alignment
D1_VALUES_ALIGNMENT	Values Alignment
D2_AUDIENCE_RELEVANCE	Audience Relevance
D3_CREDIBILITY_TRUST	Credibility & Trust
D4_REACHABILITY	Reachability
D5_RISK_CONTROVERSY	Risk & Controversy
D6_CAMPAIGN_FIT	Campaign Fit
Influencer statuses: pending → approved / rejected / maybe
