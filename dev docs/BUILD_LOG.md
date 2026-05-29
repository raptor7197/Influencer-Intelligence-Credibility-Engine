# Build Log — Influencer Intelligence & Credibility Engine

This document captures every step, decision, and file change made during the build, in the order they occurred.

---

## Step 1: Initial Plan & Scope

**Prompt:** "draft a plan for making this app the backend and the front end"

**Decisions:**
- Monorepo with Turborepo
- Frontend: React + Vite + TypeScript
- Backend: Python + FastAPI
- Discovery: existing n8n cloud-hosted workflow triggered via webhook
- Scoring: auto-trigger after discovery completes
- Async pipeline: discovery and scoring are asynchronous with status polling
- Candidate cap: max 20 candidates per run
- Persistence: campaigns stored in PostgreSQL (not session-based)
- Keep n8n for Stage 1 discovery; build native scoring on top
- Human review required before outreach

**Pipeline Designed:**
```
STAGE 1: Raw Discovery (n8n webhook → 10-20 candidates)
STAGE 2: Evidence Collection (4 parallel LLM calls per candidate)
STAGE 3: Analytic Rubric Scoring (6 parallel LLM calls per candidate)
STAGE 4: Composite Score (deterministic weighted sum)
STAGE 5: Human Review (approve/reject/maybe + outreach draft)
```

**Files created:**
- `plan.md` — full project plan with architecture, data model, API contract, phases

---

## Step 2: Monorepo Scaffolding

**Prompt:** "proceed to scaffold the structure and the base setup ... start with the backend then the db and then the n8n integration"

**Actions:**
- Created root `package.json` (Turborepo + pnpm workspaces)
- Created `pnpm-workspace.yaml`
- Created `turbo.json`

**Directory structure created:**
```
/apps/api/
  app/
    api/         → route modules
    core/        → settings
    db/          → session, base, migrations
    integrations/ → external clients
    models/      → SQLAlchemy ORM models
    services/    → business logic
    tasks/       → async jobs
  tests/
/packages/db/
  schema/
  migrations/
  sql/
/integrations/n8n/
  contracts/
  workflow/
```

**Files created:**
- `package.json`, `pnpm-workspace.yaml`, `turbo.json`
- `apps/api/README.md`, `apps/api/pyproject.toml`
- `apps/api/.env.example`
- Empty `__init__.py` files for all Python packages
- `packages/db/README.md`
- `packages/db/schema/.gitkeep`, `packages/db/migrations/.gitkeep`
- `integrations/n8n/README.md`
- `integrations/n8n/contracts/discovery-request.example.json`
- `integrations/n8n/contracts/discovery-response.example.json`
- `integrations/n8n/contracts/scoring-job.example.json`

---

## Step 3: Backend Base Setup + DB Schema

**Prompt:** "proceed with this"

**Actions:**
- Created FastAPI app entry point at `apps/api/app/main.py`
- Created `apps/api/app/core/settings.py` with Settings (env-based config)
- Created `apps/api/app/db/session.py` with SQLAlchemy engine + sessionmaker + `get_db` dependency
- Created `apps/api/app/db/base.py` with DeclarativeBase
- Created `apps/api/app/api/router.py` as root APIRouter

**SQLAlchemy Models (in `apps/api/app/models/`):**
- `Campaign` — `campaigns` table (org_name, goal, audience, geo, language, etc.)
- `DiscoveryRun` — `discovery_runs` table (campaign_id, n8n_run_id, status, result_count)
- `Influencer` — `influencers` table (handle, platforms, reach, composite_score, status, evidence_json)
- `DimensionScore` — `dimension_scores` table (influencer_id, dimension, score, rationale, evidence, confidence, uncertainty)
- `OutreachDraft` — `outreach_drafts` table (subject_line, message_body, is_edited)
- Exported all in `apps/api/app/models/__init__.py`

**Alembic:**
- `apps/api/app/db/alembic.ini` — config file
- `apps/api/app/db/migrations/env.py` — env script importing Base.metadata
- `apps/api/app/db/migrations/README.md`

**API Schemas & Routes:**
- `apps/api/app/api/schemas/campaigns.py` — CampaignCreate + CampaignResponse
- `apps/api/app/api/schemas/discovery.py` — DiscoveryRunResponse
- `apps/api/app/api/schemas/influencers.py` — InfluencerResponse
- `apps/api/app/api/routes/campaigns.py` — POST /campaigns (placeholder)
- `apps/api/app/api/routes/discovery.py` — POST .../discover, GET .../runs/{run_id} (placeholder)
- `apps/api/app/api/routes/influencers.py` — GET .../influencers (placeholder)

**Persistence Services:**
- `apps/api/app/services/campaigns.py` — create_campaign (UUID + commit)
- `apps/api/app/services/discovery_runs.py` — create_discovery_run, update_discovery_run, get_discovery_run
- `apps/api/app/services/influencers.py` — create_influencer, list_influencers_by_run

**n8n Client:**
- `apps/api/app/integrations/n8n/client.py` — N8nClient (trigger_discovery via httpx POST)
- `apps/api/app/integrations/n8n/status.py` — N8nStatusClient (get_run_status via httpx GET)
- `apps/api/app/services/n8n.py` — build_n8n_client / build_n8n_status_client factories

**dependencies added to pyproject.toml:**
- fastapi, uvicorn, pydantic-settings, httpx, sqlalchemy, psycopg[binary], alembic

---

## Step 4: Scoring Pipeline Skeleton

**Prompt:** "the scoring pipeline is the most imp thing so do it carefully"

**Actions:**
Created the scoring engine under `apps/api/app/services/scoring/`:

- **`types.py`** — EvidenceDossier + DimensionResult Pydantic models
- **`rubric.py`** — DIMENSIONS dict (6 dimensions with weights + scale anchors)
  - D1: Values Alignment (30%)
  - D2: Audience Relevance (20%)
  - D3: Credibility & Trust (20%)
  - D4: Reachability (10%)
  - D5: Risk & Controversy (-15%)
  - D6: Campaign Fit (15%)
- **`composite.py`** — compute_composite_score (weighted sum normalized to [0,1])
- **`evidence.py`** — build_evidence_dossier (raw to typed)
- **`scorer.py`** — score_dimension + score_all_dimensions (stub returning 5.0)
- **`pipeline.py`** — ScoringPipeline orchestrator
- Exported ScoringPipeline in `apps/api/app/services/__init__.py`

---

## Step 5: Wire Discovery + Normalize Candidates

**Prompt:** "continue"

**Actions:**
- `apps/api/app/services/normalization.py` — normalize_candidates (cap at 20, extract key fields)
- `apps/api/app/services/scoring/runner.py` — run_scoring_pipeline (orchestrates pipeline, builds DimensionScore objects)
- `apps/api/app/services/scoring/persist.py` — persist_scoring (saves composite + evidence + dimension scores to DB)
- Updated `apps/api/app/api/routes/discovery.py`:
  - POST trigger: creates run → triggers n8n → stores run_id
  - GET status: polls n8n → on completion → normalizes candidates → persists influencers → runs scoring per candidate → persists scores

---

## Step 6: LLM Evidence + Scoring Integration

**Prompt:** "continue"

**Actions:**
- Added `LLM_MODE`, model names, max_tokens to `apps/api/app/core/settings.py`
- Added env vars to `apps/api/.env.example`
- Created `apps/api/app/integrations/openrouter/client.py` — OpenRouterClient with `chat` method
- Created `apps/api/app/services/llm.py` — build_openrouter_client factory
- Created `apps/api/app/services/scoring/prompts.py` — system + user prompt templates for evidence and scoring
- Updated `apps/api/app/services/scoring/evidence.py` — added `build_evidence_dossier_llm` (single LLM call)
- Updated `apps/api/app/services/scoring/scorer.py` — when `LLM_MODE=openrouter`, calls OpenRouter for each dimension
- Updated `apps/api/app/services/scoring/pipeline.py` — falls through to LLM evidence if dossier empty

---

## Step 7: Token Limits + Parallel Evidence Collection

**Prompt:** "make sure the LLM tokens are limited so 4 parallel LLM calls would eat up the tokens"

**Actions:**
- Added `openrouter_max_tokens_evidence: int = 600` and `openrouter_max_tokens_scoring: int = 600` to settings
- Updated `OpenRouterClient.chat` to accept `max_tokens` param
- Applied `max_tokens` to all evidence and scoring LLM calls
- Created `apps/api/app/services/scoring/evidence_parallel.py`:
  - Runs 4 evidence tasks concurrently via `asyncio.gather`
  - Each task gets a separate prompt with max_tokens cap
- Created `apps/api/app/services/scoring/json_guard.py`:
  - `safe_json_loads` — tries standard parse, falls back to extracting JSON block, returns `{}` on failure
- Wired `json_guard` into evidence.py and scorer.py
- Updated `scorer.py` — safe defaults for missing keys
- Updated `apps/api/app/services/scoring/pipeline.py` — replaced single-call LLM evidence with parallel version

---

## Step 8: Async End-to-End Pipeline + Grok + Fallback + Rate Limiting

**Prompt:** "convert the scoring pipeline async from end to end and add a fallback model also change the models from gemini to grok and add a rate limiting"

**Actions:**

### Model Changes
- `apps/api/app/core/settings.py`:
  - Changed defaults: `openrouter_model_evidence=xai/grok-2-latest`, `openrouter_model_scoring=xai/grok-2-latest`
  - Added `openrouter_fallback_model=google/gemini-2.5-flash-preview`
  - Added `openrouter_rate_per_second=5`

### Rate Limiter
- `apps/api/app/integrations/openrouter/client.py`:
  - Added `TokenBucket` class (token-bucket rate limiter)
  - Added fallback model logic: on 5xx or network errors, retries with fallback model
  - Combined `chat` and `chat_async` into single async `chat` method
  - Uses shared `httpx.AsyncClient` (created once, reused)
  - Added `close()` method for cleanup

### Factory Update
- `apps/api/app/services/llm.py`:
  - Passes `fallback_model` and `rate_per_second` to `OpenRouterClient`

### Async Conversion
- `apps/api/app/services/scoring/scorer.py`:
  - `score_dimension` → `async def`
  - `score_all_dimensions` → `async def` with `asyncio.gather` (6 parallel calls)
- `apps/api/app/services/scoring/evidence.py`:
  - `build_evidence_dossier_llm` → `async def`
- `apps/api/app/services/scoring/evidence_parallel.py`:
  - Changed `client.chat_async` → `client.chat` (now the async method)
- `apps/api/app/services/scoring/pipeline.py`:
  - `run()` → `async def`
  - Removed `asyncio.run()` wrapper
  - `await` for evidence + scoring calls
- `apps/api/app/services/scoring/runner.py`:
  - `run_scoring_pipeline` → `async def`
- `apps/api/app/api/routes/discovery.py`:
  - `get_discovery_status` → `async def`
  - `await run_scoring_pipeline(...)`

**Environment example updated:**
- `apps/api/.env.example` — new defaults and added fallback model + rate limit

---

## Step 9: Build Log Creation

**Prompt:** "everything in this thread everything that has been said I need it in a step by step and prompt wise md file"

**Actions:**
- Created this file: `BUILD_LOG.md`

---

## Current File Tree (Scaffold)

```
/home/krxsna/dev/iice/
├── plan.md                          # Full project plan & build progress
├── BUILD_LOG.md                     # This file — step-by-step log
├── readme.md                        # Original project discovery docs
├── n8nworkflow.json                 # Existing n8n workflow
├── package.json                     # Root Turborepo config
├── pnpm-workspace.yaml              # pnpm workspace definition
├── turbo.json                       # Turborepo pipeline config
├── ps.txt                           # Empty placeholder
│
├── apps/api/
│   ├── README.md
│   ├── pyproject.toml               # Python deps (FastAPI, SQLAlchemy, httpx, etc.)
│   ├── .env.example                 # All config env vars
│   ├── app/
│   │   ├── main.py                  # FastAPI entry, router mount
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py            # Aggregates all sub-routers
│   │   │   ├── routes/
│   │   │   │   ├── campaigns.py     # POST /campaigns
│   │   │   │   ├── discovery.py     # POST .../discover, GET .../runs/{id}
│   │   │   │   └── influencers.py   # GET .../influencers
│   │   │   └── schemas/
│   │   │       ├── campaigns.py     # CampaignCreate, CampaignResponse
│   │   │       ├── discovery.py     # DiscoveryRunResponse
│   │   │       └── influencers.py   # InfluencerResponse
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── settings.py          # Pydantic Settings (all env vars)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   │   ├── session.py           # engine + sessionmaker + get_db
│   │   │   ├── alembic.ini          # Alembic config
│   │   │   └── migrations/
│   │   │       ├── env.py           # Alembic env (imports all models)
│   │   │       └── README.md
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── n8n/
│   │   │   │   ├── client.py        # N8nClient (httpx POST trigger)
│   │   │   │   └── status.py        # N8nStatusClient (httpx GET status)
│   │   │   └── openrouter/
│   │   │       └── client.py        # OpenRouterClient (async, rate-limited, fallback)
│   │   ├── models/
│   │   │   ├── __init__.py          # Exports all models
│   │   │   ├── campaign.py
│   │   │   ├── discovery_run.py
│   │   │   ├── influencer.py
│   │   │   ├── dimension_score.py
│   │   │   └── outreach_draft.py
│   │   ├── services/
│   │   │   ├── __init__.py          # Exports ScoringPipeline
│   │   │   ├── campaigns.py         # create_campaign
│   │   │   ├── discovery_runs.py    # create/get/update discovery_run
│   │   │   ├── influencers.py       # create_influencer, list_influencers_by_run
│   │   │   ├── llm.py              # build_openrouter_client factory
│   │   │   ├── n8n.py              # build_n8n_client / build_n8n_status_client
│   │   │   ├── normalization.py     # normalize_candidates (cap 20)
│   │   │   └── scoring/
│   │   │       ├── __init__.py
│   │   │       ├── types.py         # EvidenceDossier, DimensionResult
│   │   │       ├── rubric.py        # 6 dimensions with weights
│   │   │       ├── composite.py     # compute_composite_score
│   │   │       ├── evidence.py      # build_evidence_dossier (sync), build_evidence_dossier_llm (async)
│   │   │       ├── evidence_parallel.py  # 4 parallel LLM evidence calls
│   │   │       ├── scorer.py        # async per-dimension + batch scorer
│   │   │       ├── pipeline.py      # async ScoringPipeline orchestrator
│   │   │       ├── runner.py        # async run_scoring_pipeline (orchestrates scoring + builds DimensionScore objs)
│   │   │       ├── persist.py       # persist_scoring (saves to DB)
│   │   │       ├── prompts.py       # System/user prompt templates
│   │   │       └── json_guard.py    # safe_json_loads with fallback
│   │   └── tasks/
│   │       └── __init__.py
│   └── tests/
│       └── __init__.py
│
├── packages/db/
│   ├── README.md
│   ├── schema/
│   │   └── schema.sql               # Placeholder SQL
│   ├── migrations/
│   │   └── .gitkeep
│   └── sql/
│       └── .gitkeep
│
└── integrations/n8n/
    ├── README.md
    ├── contracts/
    │   ├── discovery-request.example.json
    │   ├── discovery-response.example.json
    │   ├── discovery-status.example.json
    │   └── scoring-job.example.json
    └── workflow/
        └── .gitkeep
```

---

## Key Configuration Options

### Environment Variables (`apps/api/.env.example`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `N8N_WEBHOOK_URL` | — | n8n discovery webhook URL |
| `N8N_BASE_URL` | — | n8n API base URL for status polling |
| `N8N_API_KEY` | — | n8n API auth key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `LLM_MODE` | `stub` | `stub` or `openrouter` |
| `OPENROUTER_MODEL_EVIDENCE` | `xai/grok-2-latest` | Model for evidence collection |
| `OPENROUTER_MODEL_SCORING` | `xai/grok-2-latest` | Model for rubric scoring |
| `OPENROUTER_FALLBACK_MODEL` | `google/gemini-2.5-flash-preview` | Fallback model on primary failure |
| `OPENROUTER_MAX_TOKENS_EVIDENCE` | `600` | Max tokens per evidence call |
| `OPENROUTER_MAX_TOKENS_SCORING` | `600` | Max tokens per scoring call |
| `OPENROUTER_RATE_PER_SECOND` | `5` | Max LLM requests per second |

### Scoring Rubric Weights

| Dimension | Weight |
|---|---|
| D1: Values Alignment | +30% |
| D2: Audience Relevance | +20% |
| D3: Credibility & Trust | +20% |
| D4: Reachability | +10% |
| D5: Risk & Controversy | -15% |
| D6: Campaign Fit | +15% |

Formula: `score = Σ(wᵢ × sᵢ/10) / Σ(positive weights)`, clamped to [0, 1]

---

## Known Next Steps (Unimplemented)

- Frontend app shell (React + Vite)
- Influencer review endpoints (approve/reject/maybe, outreach draft generation)
- Discovery dashboard and scoring visualization UI
- Outreach editor UI
- Side-by-side influencer comparison
- Error handling + retry for n8n failures
- Audit logging
- Rate limiting for API (not just LLM)
- Alembic migration to create initial tables
- `uvicorn` run configuration
- Async cleanup (`client.close()` lifecycle)
