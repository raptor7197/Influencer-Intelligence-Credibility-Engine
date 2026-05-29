# Influencer Intelligence & Credibility Engine Plan

## Objectives
- Build an open-source standalone web app that helps animal advocacy orgs discover, evaluate, and activate aligned influencers.
- Use existing n8n workflow for raw discovery; implement native evidence + scoring + outreach support.
- Preserve human review: AI never auto-initiates outreach.

## Confirmed Decisions
- Repo: monorepo using Turborepo.
- Frontend: React + Vite + TypeScript.
- Backend: Python + FastAPI.
- Discovery: n8n cloud-hosted workflow triggered via webhook.
- Scoring: auto-trigger after discovery completes.
- Async pipeline: discovery and scoring are asynchronous with status polling.
- Candidate cap: max 20 candidates per discovery run.
- Persistence: campaigns are stored; not session-based.

## Scaffold Layout
```
/apps/api
  pyproject.toml
  .env.example
  app/
    api/
    core/
    db/
    integrations/
    models/
    services/
    tasks/
  tests/

/packages/db
  schema/
  migrations/
  sql/

/integrations/n8n
  README.md
  contracts/
  workflow/
```

## Architecture Overview
```
User -> Web App (React/Vite)
     -> API (FastAPI)
        -> n8n Webhook (Stage 1 discovery)
        -> Evidence + Scoring Service (Stages 2-4)What were the possible approaches you had, which one did you choose and how is it the most optimal?
        -> Postgres DB (campaigns, influencers, evidence, drafts)
```

## Ranking Engine Pipeline (Async)
```
USER INPUT
(org, goal, audience, geo, language, categories, exclusions)
                      |
                      v
STAGE 1: RAW DISCOVERY (async)
- API triggers n8n webhook
- n8n returns 10-20 raw candidates
                      |
                      v
STAGE 2: EVIDENCE COLLECTION (async, per candidate)
- 4 parallel LLM calls per candidate
  1) Content & Values Analysis
  2) Public Record Scan
  3) Audience Profile Inference
  4) Risk & Controversy Check
- Output: Evidence Dossier (JSON)
                      |
                      v
STAGE 3: ANALYTIC RUBRIC SCORING (async, per candidate)
- 6 parallel LLM calls per candidate
  D1 Values Alignment (w: +0.30)
  D2 Audience Relevance (w: +0.20)
  D3 Credibility & Trust (w: +0.20)
  D4 Reachability (w: +0.10)
  D5 Risk & Controversy (w: -0.15)
  D6 Campaign Fit (w: +0.15)
- Each returns score + rationale + evidence + confidence
                      |
                      v
STAGE 4: COMPOSITE SCORE (deterministic)
score = sum(w_i * s_i/10) / sum(positive weights)
clamped to [0, 1]
                      |
                      v
STAGE 5: HUMAN REVIEW
- Approve / Reject / Maybe
- Outreach draft generation, fully editable
```

## Data Model
### campaigns
- id
- org_name
- outreach_person
- campaign_goal
- target_audience (optional)
- geo_focus (optional)
- language
- categories (optional)
- exclusions (optional)
- status
- created_at

### discovery_runs
- id
- campaign_id
- n8n_run_id
- status (queued/running/complete/failed)
- result_count
- triggered_at

### influencers
- id
- campaign_id
- discovery_run_id
- name
- handle
- platforms
- estimated_reach
- location
- bio
- audience_category
- composite_score
- status (pending/approved/rejected/maybe)
- evidence_json
- created_at

### dimension_scores
- id
- influencer_id
- dimension
- score
- rationale
- evidence[]
- confidence
- uncertainty

### outreach_drafts
- id
- influencer_id
- subject_line
- message_body
- is_edited
- status
- created_at

## API Contract (Draft)
- POST /api/campaigns
- GET /api/campaigns/:id
- POST /api/campaigns/:id/discover
- GET /api/campaigns/:id/runs/:runId
- GET /api/campaigns/:id/influencers
- GET /api/influencers/:id
- PATCH /api/influencers/:id
- POST /api/influencers/:id/outreach
- PATCH /api/outreach/:id

## Async Workflow & Status
- Discovery run is created immediately with status=queued.
- API triggers n8n webhook and stores n8n_run_id.
- Backend polls n8n run status; on completion:
  - Normalize candidate list (cap at 20)
  - Enqueue evidence collection + scoring per candidate
- Scoring completion updates influencer records and composite score.
- Frontend polls discovery run and influencers list for progress.

## Business Rules
- No auto-outreach. Human approval is required.
- Scoring prioritizes credibility and audience trust over reach alone.
- Every score must include rationale + evidence + uncertainty.
- Users must be able to edit outreach drafts.

## Security & Controls (Medium Tier)
- Secure API key handling
- Rate limiting
- Audit logs for recommendation generation
- Human approval requirement before outreach
- AI-generated content disclosures
- Secure storage of organizational data/preferences

## UI/UX Components
- Campaign setup flow
- Influencer discovery dashboard
- Search/filter interface
- Credibility scoring visualizations
- Values alignment indicators
- Evidence/reasoning panels
- Outreach message editor
- Side-by-side influencer comparison

## Implementation Phases
### Phase 1: Foundation
- Turborepo bootstrap
- FastAPI service with DB setup
- React + Vite app shell
- Campaign CRUD

### Phase 2: Discovery Integration
- n8n webhook trigger
- discovery_runs tracking
- Async polling + candidate normalization

### Phase 3: Evidence + Scoring Engine
- Evidence dossier service (4 calls)
- Rubric scoring service (6 calls)
- Composite score calculation

### Phase 4: Review + Outreach
- Influencer list + scoring breakdown UI
- Approve/Reject/Maybe workflow
- Outreach draft generation + editor

### Phase 5: Polish
- Error handling + retries
- Progress states
- Audit logging
- Export/copy outreach drafts

## Build Progress
- Backend base app + settings + router scaffolded.
- SQLAlchemy models scaffolded for core entities.
- Alembic config placeholder added.
- API schemas and placeholder endpoints for campaign creation and discovery runs added.
- n8n client + status adapter scaffolded.
- Discovery endpoint now triggers n8n and stores run metadata.
- Scoring pipeline skeleton added (evidence dossier, rubric map, composite calculator).
- n8n completion path now normalizes candidates (cap 20) and runs scoring pipeline.
- LLM-backed evidence + scoring hooks added (OpenRouter client and prompts).
- Token caps added for evidence/scoring calls; evidence collection now uses 4-task LLM pass.
- Evidence collection now runs in parallel with JSON guardrails.
- Scoring pipeline converted to async end-to-end (10 concurrent LLM calls: 4 evidence + 6 rubric).
- Default model changed to Grok (xai/grok-2-latest) with Gemini fallback.
- Token-bucket rate limiter added to OpenRouter client (rate configurable).
- Fallback model logic: retries on 5xx or network errors.
- Auto table creation on startup (lifespan event).
- SQLite support in session.py for dev/test environments.
- 10 unit/integration tests passing + 4 smoke tests passing.
- Test suite covers: campaign CRUD, scoring pipeline, normalization, composite calc, evidence, JSON guard, rubrics, types.
- n8n webhook URL configured: https://openpaws-iice.app.n8n.cloud/webhook-test/trigger-agent
- Payload format: n8n Chat Trigger expects `{"chatInput": "..."}` with campaign context as prompt.

## Configurations to Record
- n8n webhook URL and credential handling
- LLM provider keys and model fallback
- Candidate cap = 20
- Async polling interval and timeout strategy
- Composite score formula and weights
## Build Mode Notes
- Backend base app and config are now scaffolded.
- Database placeholder schema added for core tables.
- n8n contracts include request, response, and status examples.
