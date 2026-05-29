
────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/api/app/services/draft_generation.py:94-95

  Add defensive access for LLM response parsing.

  Direct dictionary/list access on
  response["choices"][0]["message"]["content"] will raise KeyError or
  IndexError if the LLM API returns a malformed or unexpected response
  (e.g., empty choices array, missing message field, rate limit response).



  🛡️ Proposed fix: Add defensive access

  -            content = response["choices"][0]["message"]["content"]
  -            draft_data = safe_json_loads(content)
  +            try:
  +                content = response["choices"][0]["message"]["content"]
  +            except (KeyError, IndexError, TypeError) as e:
  +                raise ValueError(f"Malformed LLM response: {e}") from e
  +            draft_data = safe_json_loads(content)
  +            if not isinstance(draft_data, dict):
  +                draft_data = {}


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/api/app/services/draft_generation.py:99-111

  Remove redundant attribute assignment loop.

  Lines 99-108 already assign values from draft_data with sensible
  defaults via .get(). The loop at lines 109-111 then overwrites these
  same attributes, making the earlier .get() defaults ineffective if the
  key exists in draft_data.



  🔧 Proposed fix: Remove the redundant loop

       draft = OutreachDraft(
           id=str(uuid.uuid4()),
           influencer_id=influencer.id,
           subject_line=draft_data.get("subject_line", "Let's collaborate"),
           message_body=draft_data.get("message_body", ""),
           framing_angles=draft_data.get("framing_angles", []),
           messaging_tips=draft_data.get("messaging_tips", []),
           status="draft",
           is_edited=False,
       )
  -    for key in ("subject_line", "message_body", "framing_angles", "messaging_tips", "status"):
  -        if key in draft_data:
  -            setattr(draft, key, draft_data[key])
  
       db.add(draft)


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/api/app/api/routes/discovery.py:577-635

  GET endpoint has side effects: spawns background tasks and mutates DB
  state.

  get_discovery_status updates the discovery run and spawns background
  scoring tasks (lines 617-620), violating REST semantics for GET requests.
  GET should be idempotent and safe. Consider moving state-changing logic to
  a separate POST endpoint or a dedicated polling mechanism.


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → n8nworkflow.json:457-478

  Reddit API tools missing User-Agent header configuration.

  The Reddit User Overview, User Posts, User Comments, Reddit Post, and
  Reddit Search tools have sendHeaders: true with `specifyHeaders:
  "model"`, but no actual headers are defined in the parameters. Reddit's
  public JSON endpoints require a descriptive User-Agent header to avoid
  rate limiting or blocking.

  Add a User-Agent header to ensure reliable Reddit API access:



  Example header configuration to add

  "headerParameters": {
    "parameters": [
      {
        "name": "User-Agent",
        "value": "n8n-research-agent/1.0"
      }
    ]
  }


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → n8nworkflow.json:951-963

  Respond to Webhook node may error on non-webhook trigger paths.

  The workflow has three entry points (Chat Trigger, Execute Workflow
  Trigger, Webhook Trigger), but all paths merge into Respond to Webhook.
  When triggered via chat or another workflow, there's no webhook context,
  which may cause this node to fail or behave unexpectedly.

  Consider adding conditional branching before Respond to Webhook to skip
  it when the trigger is not a webhook, or verify that n8n gracefully
  handles this scenario.




  Also applies to: 1370-1380


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → n8nworkflow.json:648-661

  Silent truncation in recovery path may cause incomplete responses.

  The Fix Empty Response node truncates intermediateSteps to 500KB without
  indicating to the LLM that data was truncated. If the agent gathered
  extensive research data, the recovery prompt may receive incomplete
  context, potentially producing an incomplete report.

  Consider adding a truncation indicator to the prompt (e.g.,
  "[TRUNCATED]") when data exceeds the limit so the LLM knows to
  acknowledge potential gaps.


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/api/app/api/routes/discovery.py:391-409

  Fire-and-forget asyncio.create_task may lose tasks.

  Tasks created without storing a reference can be garbage-collected before
  completion. Store references or use asyncio.TaskGroup (Python 3.11+) to
  ensure tasks complete.



  🛡️ Minimal fix to hold task reference

  +    _background_tasks: set = set()  # module-level set
  +
       if passed:
           campaign_context = {"campaign_id": campaign_id, "goal": getattr(campaign, 'campaign_goal', '')}
  -        asyncio.create_task(_score_candidates_background(campaign_id, run.id, passed, campaign_context))
  +        task = asyncio.create_task(_score_candidates_background(campaign_id, run.id, passed, campaign_context))
  +        _background_tasks.add(task)
  +        task.add_done_callback(_background_tasks.discard)


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/api/app/services/scoring/evidence_parallel.py:27-55

  asyncio.gather without return_exceptions=True will fail the entire
  batch if one task errors.

  If any single LLM call fails, the entire gather raises and returns an
  empty EvidenceDossier, losing partial results from successful tasks.
  Consider using return_exceptions=True and filtering out exceptions from
  results.



  🛡️ Proposed fix to handle partial failures

  -    results = dict(
  -        await asyncio.gather(
  -            *[_run_task(key, task) for key, task in EVIDENCE_TASKS.items()]
  -        )
  -    )
  +    raw_results = await asyncio.gather(
  +        *[_run_task(key, task) for key, task in EVIDENCE_TASKS.items()],
  +        return_exceptions=True,
  +    )
  +    results = {k: v for k, v in raw_results if not isinstance(v, Exception)}


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/api/app/api/routes/discovery.py:288-356

  Session leak risk in _trigger_n8n_background.

  Line 329 creates a session directly via get_session_maker()() but the
  finally block only closes on success paths. If an exception occurs in
  update_discovery_run at line 351, the session is still closed, but if
  exception handling itself fails, the close may not happen. Use a context
  manager for safer cleanup.



  🛡️ Proposed fix using context manager

  -    db = get_session_maker()()
  -    try:
  +    sm = get_session_maker()
  +    with sm() as db:
           run = create_discovery_run(db, campaign_id)
           # ... rest of try block ...
  -    except Exception as exc:
  -        try:
  -            update_discovery_run(db, run, {"status": "failed", "error": f"n8n trigger failed: {exc}"})
  -        except Exception:
  -            pass
  -    finally:
  -        db.close()
  +        except Exception as exc:
  +            try:
  +                update_discovery_run(db, run, {"status": "failed", "error": f"n8n trigger failed: {exc}"})
  +            except Exception:
  +                pass


────────────────────────────────────────────────────────────────────────
  critical [potential_issue]
  → apps/api/app/api/routes/n8n_callback.py:45-77

  asyncio.run() inside a FastAPI endpoint will fail with RuntimeError.

  asyncio.run() cannot be called when an event loop is already running.
  FastAPI runs endpoints within an async event loop, so this will raise
  RuntimeError: This event loop is already running. Either make the
  endpoint async and await the coroutines directly, or use
  asyncio.get_event_loop().run_until_complete() (though making it async is
  preferred).



  🐛 Proposed fix: convert to async endpoint

   @router.post("/callback/{run_id}")
  -def n8n_discovery_callback(
  +async def n8n_discovery_callback(
       run_id: str,
       body: dict,
       db: Session = Depends(get_db),
   ) -> dict:
       # ... existing code ...
  
  -    import asyncio
  -
       from app.services.scoring.profile_verify import verify_candidate
       verified_normalized = []
       for candidate in normalized:
  -        ref = asyncio.run(verify_candidate(candidate))
  +        ref = await verify_candidate(candidate)
           if ref.get("evidence_json", {}).get("verification_confidence", "unverified") != "unverified":
               verified_normalized.append(ref)
           # ...
  
       for candidate in normalized:
           # ...
  -        composite_result, evidence_json, dimension_scores = asyncio.run(
  -            run_scoring_pipeline(
  +        composite_result, evidence_json, dimension_scores = await run_scoring_pipeline(
                   db,
                   campaign_context={"campaign_id": run.campaign_id},
                   influencer_context={"id": influencer.id},
                   raw_evidence=candidate.get("evidence_json") or {},
               )
  -        )


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/api/README.md:15-17

  Documentation contradicts actual implementation.

  Lines 16-17 state "No runtime implementation is included yet" but the PR
  stack context shows extensive implementation across 8 cohorts including
  core settings (apps/api/app/core/settings.py), database layer
  (apps/api/app/db/), ORM models (apps/api/app/models/), API routers
  (apps/api/app/api/routes/), services (apps/api/app/services/), scoring
  pipeline (apps/api/app/services/scoring/), and tests (apps/api/tests/).

  This README should document the actual implemented backend, not describe
  it as planned/future work.





  📝 Suggested fix

   ## Notes
  -- No runtime implementation is included yet.
  -- This scaffold is aligned to the async discovery and scoring flow.
  +- This backend implements async discovery orchestration, evidence collection, multi-dimensional scoring, and outreach draft generation.
  +- See the implementation in `app/` and tests in `tests/`.


────────────────────────────────────────────────────────────────────────
  critical [potential_issue]
  → apps/api/app/integrations/openrouter/client.py:27-37

  Fix malformed dataclass field declaration.

  Line 37 declares _client outside __post_init__, which is invalid
  syntax for dataclass fields. This should be declared with field() in the
  class body.



  🐛 Proposed fix

   @dataclass
   class OpenRouterClient:
       api_key: str
       fallback_model: str = "google/gemini-2.5-flash-preview"
       rate_per_second: int = 5
       base_url: str = "https://openrouter.ai/api/v1"
       _bucket: TokenBucket = field(init=False)
  +    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)
  
       def __post_init__(self) -> None:
           self._bucket = TokenBucket(self.rate_per_second)
  -    _client: httpx.AsyncClient | None = None


────────────────────────────────────────────────────────────────────────
  major [refactor_suggestion]
  → apps/api/app/api/routes/influencers.py:97-106

  Use typed request model instead of generic dict.

  The endpoint accepts a generic dict and manually validates the status
  field. This bypasses Pydantic validation and reduces type safety.



  ♻️ Proposed refactor

  Add a request schema in apps/api/app/api/schemas/influencers.py:

  class InfluencerStatusUpdate(BaseModel):
      status: Literal["pending", "approved", "rejected", "maybe"]

  Then update the endpoint:

  +from typing import Literal
  +from app.api.schemas.influencers import InfluencerStatusUpdate
  +
   @router.patch("/{campaign_id}/influencers/{influencer_id}/status")
   def update_influencer_status_endpoint(
       campaign_id: str,
       influencer_id: str,
  -    body: dict,
  +    body: InfluencerStatusUpdate,
       db: Session = Depends(get_db),
   ) -> dict:
  -    status = body.get("status")
  -    if status not in ("pending", "approved", "rejected", "maybe"):
  -        raise HTTPException(status_code=422, detail="invalid status")
  -    influencer = update_influencer_status(db, influencer_id, status)
  +    influencer = update_influencer_status(db, influencer_id, body.status)


────────────────────────────────────────────────────────────────────────
  major [refactor_suggestion]
  → apps/api/app/integrations/n8n/client.py:6-10

  Fix mutable default in dataclass.

  The _client field uses a mutable default (None) without wrapping it in
  field(). While None itself is immutable, the pattern is inconsistent
  with dataclass best practices and could cause issues if the default is
  later changed to a mutable type.



  ♻️ Proposed fix

  +from dataclasses import dataclass, field
  +
   @dataclass
   class N8nClient:
       webhook_url: str
       api_key: str | None = None
  -    _client: httpx.AsyncClient | None = None
  +    _client: httpx.AsyncClient | None = field(default=None, init=False, repr=False)


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/frontend/src/features/influencers/InfluencerDetail.tsx:344-349

  Add error handling for clipboard write operation.

  The navigator.clipboard.writeText call is not awaited and lacks error
  handling. If the clipboard write fails (due to permissions or browser
  support), the success toast will still display, misleading the user.




  🛡️ Proposed fix with proper async handling

                       <button 
  -                      onClick={() => {
  -                        navigator.clipboard.writeText(influencer.outreach_draft?.message_body || '');
  -                        showToast('Copied! Marking as approved...', 'success');
  -                        handleUpdateStatus('approved');
  +                      onClick={async () => {
  +                        try {
  +                          await navigator.clipboard.writeText(influencer.outreach_draft?.message_body || '');
  +                          showToast('Copied! Marking as approved...', 'success');
  +                          handleUpdateStatus('approved');
  +                        } catch (err) {
  +                          showToast('Failed to copy to clipboard', 'error');
  +                        }
                         }}
                         className="w-full sketch-button"
                       >


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/api/app/integrations/openrouter/client.py:72-92

  Prevent infinite retry loops.

  The fallback logic retries with fallback_model but doesn't track whether
  it's already the fallback attempt. If fallback_model itself fails with a
  5xx or network error, this will recurse indefinitely.



  🛡️ Proposed fix

  Add a parameter to track retry state:

       async def chat(
           self,
           model: str,
           messages: list[dict],
           temperature: float = 0.2,
           max_tokens: int | None = None,
  +        _is_retry: bool = False,
       ) -> dict:
           try:
               return await self._post(model, messages, temperature, max_tokens)
           except httpx.HTTPStatusError as exc:
  -            if exc.response.status_code >= 500 and self.fallback_model:
  +            if exc.response.status_code >= 500 and self.fallback_model and not _is_retry:
                   return await self._post(
                       self.fallback_model, messages, temperature, max_tokens
                   )
               raise
           except httpx.RequestError:
  -            if self.fallback_model:
  +            if self.fallback_model and not _is_retry:
                   return await self._post(
                       self.fallback_model, messages, temperature, max_tokens
                   )
               raise

  Or better, call chat recursively with the flag:

  -            if exc.response.status_code >= 500 and self.fallback_model:
  -                return await self._post(
  -                    self.fallback_model, messages, temperature, max_tokens
  -                )
  +            if exc.response.status_code >= 500 and self.fallback_model and not _is_retry:
  +                return await self.chat(
  +                    self.fallback_model, messages, temperature, max_tokens, _is_retry=True
  +                )


────────────────────────────────────────────────────────────────────────
  critical [potential_issue]
  → apps/api/app/integrations/openrouter/client.py:14-24

  Critical: Rate limiting is broken - asyncio.sleep must be awaited.

  Line 21 calls asyncio.sleep(sleep_for) without await, so the coroutine
  is created but never executed. This means the rate limiter never actually
  sleeps, defeating the entire purpose of the TokenBucket.



  🐛 Proposed fix

  The acquire method must be async and must await the sleep:

  -    def acquire(self) -> None:
  +    async def acquire(self) -> None:
           now = monotonic()
           elapsed = now - self.last_refill
           self.tokens = min(float(self.rate), self.tokens + elapsed * self.rate)
           self.last_refill = now
           if self.tokens < 1:
               sleep_for = (1 - self.tokens) / self.rate
  -            asyncio.sleep(sleep_for)
  +            await asyncio.sleep(sleep_for)
               self.tokens = 0.0
           else:
               self.tokens -= 1.0

  And update the caller on line 51:

  -        self._bucket.acquire()
  +        await self._bucket.acquire()


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/api/app/api/routes/events.py:15-19

  Ensure payload is properly serialized.

  The payload from event_bus is directly interpolated into the SSE
  message. If the event bus returns non-string payloads (e.g., dicts), this
  will fail. Consider explicitly serializing to JSON.



  🛡️ Proposed fix

  +import json
  +
   async def generate():
       try:
           while True:
               payload = await queue.get()
  -            yield f"data: {payload}\n\n"
  +            if isinstance(payload, str):
  +                yield f"data: {payload}\n\n"
  +            else:
  +                yield f"data: {json.dumps(payload)}\n\n"
       except asyncio.CancelledError:
           await event_bus.unsubscribe(queue)


────────────────────────────────────────────────────────────────────────
  critical [potential_issue]
  → apps/api/app/services/scoring/evidence.py:43-66

  Add error handling for malformed OpenRouter responses.

  Unlike score_dimension in scorer.py (lines 61-99),
  build_evidence_dossier_llm lacks error handling for:
  - Malformed response structure (line 64 could raise KeyError,
  IndexError, or TypeError)
  - Non-dict JSON payloads from safe_json_loads (line 65)

  This will cause unhandled exceptions and crash the scoring pipeline when
  the LLM returns unexpected responses.




  🐛 Proposed fix matching scorer.py error handling

   async def build_evidence_dossier_llm(
       campaign_context: dict,
       influencer_context: dict,
   ) -> EvidenceDossier:
       settings = Settings()
       if settings.llm_mode != "openrouter":
           return EvidenceDossier()
       client = build_openrouter_client()
       user_prompt = EVIDENCE_USER_PROMPT_TEMPLATE.format(
           campaign_context=campaign_context,
           influencer_context=influencer_context,
       )
  -    response = await client.chat(
  -        model=settings.openrouter_model_evidence,
  -        messages=[
  -            {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
  -            {"role": "user", "content": user_prompt},
  -        ],
  -        temperature=0.1,
  -        max_tokens=settings.openrouter_max_tokens_evidence,
  -    )
  -    content = response["choices"][0]["message"]["content"]
  -    payload = safe_json_loads(content)
  -    return build_evidence_dossier(payload)
  +    try:
  +        response = await client.chat(
  +            model=settings.openrouter_model_evidence,
  +            messages=[
  +                {"role": "system", "content": EVIDENCE_SYSTEM_PROMPT},
  +                {"role": "user", "content": user_prompt},
  +            ],
  +            temperature=0.1,
  +            max_tokens=settings.openrouter_max_tokens_evidence,
  +        )
  +    except Exception:
  +        return EvidenceDossier()
  +    
  +    try:
  +        content = response["choices"][0]["message"]["content"]
  +    except (KeyError, IndexError, TypeError):
  +        return EvidenceDossier()
  +    
  +    payload = safe_json_loads(content)
  +    if not isinstance(payload, dict):
  +        return EvidenceDossier()
  +    
  +    return build_evidence_dossier(payload)


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/api/app/services/scoring/composite.py:12-19

  Substring matching in sponsorship conflict detection may produce false
  positives.

  The current implementation uses case-insensitive substring matching (line
  17). This could incorrectly flag phrases like "secondary" (contains
  "dairy") or "beat" (contains "meat").




  🔍 Proposed fix using word boundaries

  +import re
  +
   def has_sponsorship_conflict(evidence: list[str]) -> bool:
       if not evidence:
           return False
       text = " ".join(evidence).lower()
       for flag in SPONSORSHIP_RED_FLAGS:
  -        if flag in text:
  +        if re.search(rf'\b{re.escape(flag)}\b', text):
               return True
       return False


────────────────────────────────────────────────────────────────────────
  critical [potential_issue]
  → apps/frontend/src/features/campaigns/CampaignDetail.tsx:64

  Critical: Clean up progressTimerRef timeout on component unmount.

  The timeout stored in progressTimerRef.current is not cleared when the
  component unmounts, which will cause the callback to execute on an
  unmounted component, potentially causing memory leaks and state update
  warnings.




  🐛 Proposed fix

     const progressTimerRef = useRef<ReturnType<typeof setTimeout>>();
  +
  +  useEffect(() => {
  +    return () => {
  +      if (progressTimerRef.current) {
  +        clearTimeout(progressTimerRef.current);
  +      }
  +    };
  +  }, []);
  
     useSse((event) => {
       if (event.type === 'discovery.progress') {
         const d = event.data as Record<string, unknown>;
         setProgress({
           campaign_id: d.campaign_id as string,
           run_id: d.run_id as string,
           current: d.current as number,
           total: d.total as number,
           candidate_name: d.candidate_name as string | undefined,
           comment: d.comment as string | undefined,
         });
       }
       if (event.type === 'discovery.completed') {
         const d = event.data as Record<string, unknown>;
         const totalNum = progress?.total ?? (d.result_count as number) || 1;
         setProgress({
           campaign_id: d.campaign_id as string,
           run_id: d.run_id as string,
           current: totalNum,
           total: totalNum,
           candidate_name: undefined,
           comment: d.status === 'failed' ? 'Scoring failed' : 'All done — all candidates scored',
         });
         if (progressTimerRef.current) clearTimeout(progressTimerRef.current);
         progressTimerRef.current = setTimeout(() => {
           setProgress(null);
           fetchCampaign();
         }, 5000);
       }
       if (event.type === 'campaign.created') {
         setProgress(null);
         fetchCampaign();
       }
     });

  Also applies to: 89-93


────────────────────────────────────────────────────────────────────────
  critical [potential_issue]
  → apps/api/.env:1-18

  CRITICAL SECURITY ISSUE: Remove .env file from version control
  immediately.

  This .env file contains actual API keys (Lines 8, 10) and should never
  be committed to version control. The exposed keys include:
  - SERPER_API_KEY (Line 8)
  - OPENROUTER_API_KEY (Line 10)

  Immediate actions required:
  1. Remove this file from the repository
  2. Add .env to .gitignore if not already present
  3. Revoke and regenerate all exposed API keys
  4. Use .env.example with placeholder values for documentation




  🔒 Steps to remediate

  1. Remove the file from git:

  git rm --cached apps/api/.env

  2. Ensure .gitignore contains:

  .env
  *.env
  !.env.example

  3. Immediately revoke these API keys from their respective providers:
  - Serper API Dashboard
  - OpenRouter API Dashboard

  4. Keep only .env.example in version control with placeholder values:

  # apps/api/.env.example
  SERPER_API_KEY=your_serper_api_key_here
  OPENROUTER_API_KEY=your_openrouter_api_key_here


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/api/app/api/routes/campaigns.py:25-26

  Avoid blocking HTTP response with potentially long-running discovery.

  The run_auto_discovery call is awaited during campaign creation, which
  blocks the HTTP response until discovery completes. If discovery is a
  long-running operation (LLM calls, external APIs, scoring), this will
  cause request timeouts and poor user experience.

  Consider using FastAPI's BackgroundTasks to run discovery asynchronously
  after returning the response.




  🚀 Proposed fix using BackgroundTasks

  -from fastapi import APIRouter, Depends, HTTPException
  +from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
   from sqlalchemy.orm import Session
  
   from app.api.schemas.campaigns import CampaignCreate, CampaignDetailResponse, CampaignResponse
   from app.api.schemas.discovery import DiscoveryRunResponse
   from app.db.session import get_db
   from app.services.audit import log_action
   from app.services.campaigns import create_campaign, get_campaign, get_campaign_with_runs, list_campaigns
   from app.services.discovery_runs import create_discovery_run
   from app.services.event_bus import event_bus
   from app.api.routes.discovery import run_auto_discovery
  
  
   router = APIRouter(prefix="/campaigns", tags=["campaigns"])
  
  
   @router.post("", response_model=CampaignResponse)
   async def create_campaign_endpoint(
       payload: CampaignCreate,
       db: Session = Depends(get_db),
  +    background_tasks: BackgroundTasks = BackgroundTasks(),
   ) -> CampaignResponse:
       campaign = create_campaign(db, payload.model_dump())
       log_action(db, "campaign.created", "campaign", campaign.id, {"org_name": campaign.org_name})
  
       run = create_discovery_run(db, campaign.id)
  -    await run_auto_discovery(db, run, campaign, campaign.id)
  +    background_tasks.add_task(run_auto_discovery, db, run, campaign, campaign.id)
  
       await event_bus.publish("campaign.created", {"campaign_id": campaign.id, "org_name": campaign.org_name})
       return CampaignResponse(
           id=campaign.id,
           org_name=campaign.org_name,
           outreach_person=campaign.outreach_person,
           campaign_goal=campaign.campaign_goal,
           target_audience=campaign.target_audience,
           geo_focus=campaign.geo_focus,
           language=campaign.language,
           categories=campaign.categories,
           exclusions=campaign.exclusions,
           status=campaign.status,
       )


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/frontend/src/features/campaigns/CampaignList.tsx:117-147

  Replace hard-coded scores with real data.

  The "Recent Discoveries" sidebar displays hard-coded scores (`92 - index *
  4`) rather than actual metrics. This presents misleading information to
  users.


────────────────────────────────────────────────────────────────────────
  minor [potential_issue]
  → apps/frontend/src/App.tsx:92-98

  Clarify button text logic.

  The button text switches between "Start Campaign" (when a campaign is
  selected) and "New Campaign" (otherwise). Since this button always
  navigates to the campaign creation form, the text "Start Campaign" when a
  campaign is already selected might be confusing to users.


────────────────────────────────────────────────────────────────────────
  major [refactor_suggestion]
  → apps/frontend/src/features/campaigns/DiscoveryRuns.tsx:190-199

  Duplicate status color mapping.

  The statusColor function here duplicates the map defined in the
  RunDetail component (lines 13-19). Consolidate into a single shared
  constant at the file level.



  ♻️ Proposed consolidation

  +const STATUS_COLOR_MAP: Record<string, string> = {
  +  completed: 'tag-yellow',
  +  failed: 'bg-[var(--red-soft)] text-[var(--ink)]',
  +  queued: 'bg-white',
  +  running: 'bg-[var(--olive)]',
  +  processing: 'bg-[var(--olive)]',
  +};
  +
   const RunDetail: React.FC<{ run: DiscoveryRun }> = ({ run }) => {
     const [open, setOpen] = useState(false);
  -  const statusColor: Record<string, string> = { ... };
  -  const sc = statusColor[run.status] || 'bg-white';
  +  const sc = STATUS_COLOR_MAP[run.status] || 'bg-white';
     // ...
   };
  
   // Later in the file, remove the statusColor function and use:
  -              <span className={`tag uppercase ${statusColor(selectedRun.status)}`}>{selectedRun.status}</span>
  +              <span className={`tag uppercase ${STATUS_COLOR_MAP[selectedRun.status] || 'bg-white'}`}>{selectedRun.status}</span>


────────────────────────────────────────────────────────────────────────
  major [potential_issue]
  → apps/frontend/src/features/discovery/DiscoveryStatus.tsx:17-33

  Initialization guard doesn't reset on campaignId change.

  The initialized.current flag prevents the effect from running more than
  once, but it's not reset when campaignId changes. This means switching
  campaigns won't trigger a new discovery run.



  🐛 Proposed fix

     useEffect(() => {
  -    if (initialized.current) return;
  -    initialized.current = true;
  +    initialized.current = true;
  
       const startDiscovery = async () => {
         try {

  Or reset the ref when campaignId changes:

  +  useEffect(() => {
  +    initialized.current = false;
  +  }, [campaignId]);
  +
     useEffect(() => {
       if (initialized.current) return;