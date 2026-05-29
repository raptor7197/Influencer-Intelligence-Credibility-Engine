import React from 'react';

export const Docs: React.FC = () => {
  return (
    <div className="space-y-12 max-w-4xl">
      <div className="solid-rule pt-8">
        <h2 className="text-5xl md:text-6xl font-black tracking-tight">how the Scoring algo  Works</h2>
        <p className="text-xl text-[var(--muted)] mt-3">
          Every influencer candidate is evaluated through a multi-stage pipeline that combines LLM-driven evidence gathering, eight-dimensional scoring, knockout checks, and a risk audit ensemble.
        </p>
      </div>

      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Phase 0: Eligibility Gate</h3>
        <p>Before any scoring happens, each candidate runs through four quick disqualification checks based on bio and metadata. Any candidate that fails a check is eliminated immediately with a reason.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-2 border-[var(--line)]">
            <thead>
              <tr className="bg-[var(--yellow)]">
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Rule</th>
                <th className="p-2 font-black text-left">Eliminates when</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">missing_name</td>
                <td className="p-2">Candidate has no name field.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">no_platforms</td>
                <td className="p-2">Candidate has no known social media platforms.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">dormant_account</td>
                <td className="p-2">Bio starts with "[deactivated" indicating a dormant account.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">hostile_keywords</td>
                <td className="p-2">Bio contains hostility phrases like "i hate animals", "pro-slaughter", "anti-vegan", or "troll".</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-[var(--muted)]">Only candidates that pass all four rules proceed to evidence gathering and scoring.</p>
      </section>

      {/* Profile Verification */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Profile Verification</h3>
        <p>Each eligible candidate's identity is cross-checked against real social media platforms and web search results. This step eliminates hallucinated profiles (common in LLM-generated candidate lists).</p>
        <ol className="list-decimal list-inside space-y-2 font-medium">
          <li>Build profile URLs from the candidate's handle for each known platform (Instagram, YouTube, TikTok, X, Facebook, Threads).</li>
          <li>Send HTTP HEAD requests to verify which profile URLs actually resolve (status below 400).</li>
          <li>Run a Serper (Google Search API) query for the candidate's name and handle to find additional real-world references.</li>
          <li>Assign a <span className="font-bold">verification confidence</span> level: <span className="tag">confirmed</span> (name and handle both match in search results), <span className="tag">uncertain</span> (only one matches), or <span className="tag">unverified</span> (neither matches).</li>
        </ol>
        <p className="text-sm text-[var(--muted)]">Discovered URLs are added to the evidence dossier sources for downstream scoring. This step eliminates 70%+ of hallucinated profiles.</p>
      </section>

      {/* Evidence Gathering */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Evidence Gathering</h3>
        <p>The pipeline first tries to use pre-existing evidence (from n8n scraping or manual input). If none is available, it launches four parallel LLM calls, each focused on a different evidence category.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-2 border-[var(--line)]">
            <thead>
              <tr className="bg-[var(--yellow)]">
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Category</th>
                <th className="p-2 font-black text-left">What it collects</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">content_values</td>
                <td className="p-2">Content themes, values alignment signals, vegan/animal advocacy messaging.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">public_record</td>
                <td className="p-2">Past campaigns, charitable work, interviews, organizational affiliations.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">audience_profile</td>
                <td className="p-2">Inferred audience demographics, engagement patterns, follower authenticity signals.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">risk_controversy</td>
                <td className="p-2">Past controversies, toxic associations, negative press, sponsorship conflicts.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p>Each LLM call returns <span className="font-bold">evidence statements with source URLs</span>. After gathering, every source URL is HEAD-verified -- dead links are stripped from the dossier. The full evidence dossier is then provided to every downstream scoring call.</p>
      </section>

      {/* Dimensions */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Eight Scoring Dimensions</h3>
        <p>Seven of these dimensions are scored by individual LLM calls. Each receives the full evidence dossier plus a dimension-specific rubric. The LLM returns a score from 1 to 10, a rationale, evidence citations, confidence level, and optional uncertainty notes.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-2 border-[var(--line)]">
            <thead>
              <tr className="bg-[var(--yellow)]">
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Dim</th>
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Name</th>
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Weight</th>
                <th className="p-2 font-black text-left">Scale (1 to 10)</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D0</td>
                <td className="p-2 border-r border-[var(--line)]">Animal Welfare Alignment</td>
                <td className="p-2 border-r border-[var(--line)]">+0.15</td>
                <td className="p-2">Actively opposes welfare ... strong authentic advocacy</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D1</td>
                <td className="p-2 border-r border-[var(--line)]">Values Alignment</td>
                <td className="p-2 border-r border-[var(--line)]">+0.20</td>
                <td className="p-2">Actively opposes positions ... active consistent advocacy</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D2</td>
                <td className="p-2 border-r border-[var(--line)]">Audience Relevance</td>
                <td className="p-2 border-r border-[var(--line)]">+0.18</td>
                <td className="p-2">Complete mismatch ... ideal demographic match</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D3</td>
                <td className="p-2 border-r border-[var(--line)]">Credibility and Trust</td>
                <td className="p-2 border-r border-[var(--line)]">+0.17</td>
                <td className="p-2">Known for inauthenticity or scandals ... widely regarded as highly credible</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D4</td>
                <td className="p-2 border-r border-[var(--line)]">Reachability</td>
                <td className="p-2 border-r border-[var(--line)]">+0.08</td>
                <td className="p-2">No realistic access ... actively seeks nonprofit partnerships</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D5</td>
                <td className="p-2 border-r border-[var(--line)]">Risk and Controversy</td>
                <td className="p-2 border-r border-[var(--line)]">-0.15</td>
                <td className="p-2">No known risks ... serious controversy or toxic association</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D6</td>
                <td className="p-2 border-r border-[var(--line)]">Campaign Fit</td>
                <td className="p-2 border-r border-[var(--line)]">+0.12</td>
                <td className="p-2">No natural connection ... obvious fit</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D8</td>
                <td className="p-2 border-r border-[var(--line)]">Controversy Velocity</td>
                <td className="p-2 border-r border-[var(--line)]">-0.05</td>
                <td className="p-2">No recent controversies ... constant controversy magnet</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="sketch-panel-soft p-3 text-sm">
          <span className="font-bold">Weight polarity:</span> Positive weights (D0-D4, D6) contribute positively to the composite score. Negative weights (D5, D8) are penalties -- higher scores in these dimensions <span className="font-bold">reduce</span> the final composite. D7 is not currently scored.
        </div>
      </section>

      {/* Composite Score */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Composite Score Calculation</h3>
        <p>The composite score is a weighted average of normalized dimension scores. Only positive-weight dimension weights are included in the denominator, meaning D5 and D8 can only subtract from the total, not inflate the denominator.</p>
        <div className="sketch-panel-soft p-4 space-y-2 text-sm">
          <p className="font-bold text-base">Formula:</p>
          <p className="font-type">composite = ( Sum of weight_i x (score_i / 10) ) / (Sum of positive weights)</p>
          <p className="font-type">positive weight sum = 0.15 + 0.20 + 0.18 + 0.17 + 0.08 + 0.12 = <span className="font-bold">0.90</span></p>
          <p>The result is clamped to the range [0.0, 1.0].</p>
        </div>
        <div className="sketch-panel-soft p-4 space-y-2 text-sm">
          <p className="font-bold text-base">Example:</p>
          <p>An influencer scores 8/10 on every positive dimension and 2/10 on both risk dimensions (D5 and D8).</p>
          <p className="font-type">weighted_sum = 0.15x0.8 + 0.20x0.8 + 0.18x0.8 + 0.17x0.8 + 0.08x0.8 + (-0.15)x0.2 + 0.12x0.8 + (-0.05)x0.2</p>
          <p className="font-type">weighted_sum = 0.68</p>
          <p className="font-type">composite = 0.68 / 0.90 = 0.756</p>
          <p>The frontend displays this as a percentage: <span className="font-bold">76</span>.</p>
        </div>
      </section>

      {/* Knockout Rules */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Knockout Rules</h3>
        <p>After scoring, the system checks four knockout conditions in order. The first matching rule eliminates the candidate with a composite score of 0.0 and no profile classification.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-2 border-[var(--line)]">
            <thead>
              <tr className="bg-[var(--yellow)]">
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Condition</th>
                <th className="p-2 font-black text-left">Effect and Reason</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D0 (Animal Welfare) less than or equal to 2</td>
                <td className="p-2">Candidate shows active opposition to animal welfare.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D5 (Risk) greater than or equal to 9</td>
                <td className="p-2">Extreme reputational risk. Not safe to approach.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D5 at least 7 AND sponsorship conflict detected</td>
                <td className="p-2">Active sponsorship conflict. Evidence contains red-flag brands (dairy, meat, KFC, McDonald's, Nestle, etc.) matched via word-boundary regex.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">D7 (Audience Authenticity) less than or equal to 2</td>
                <td className="p-2">Strong indicators of inauthentic audience. (Note: D7 is not currently scored, so this rule is inactive.)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Risk Audit */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Risk Audit Ensemble</h3>
        <p>After the initial 7 dimension scores are computed, a separate LLM call re-evaluates D5 (Risk) and D8 (Controversy Velocity) with a deliberately conservative mandate. The prompt instructs the auditor to be strict: "if the current risk scores miss any red flags, return a higher score. False negatives on risk are dangerous."</p>
        <p>The final score for each risk dimension is <span className="font-bold">max(original, audited)</span>. Scores can only increase -- never decrease -- ensuring the system is biased toward caution on reputation risk.</p>
        <p className="text-sm text-[var(--muted)]">If the audit call fails (network error, parsing error), the original scores are preserved unchanged.</p>
      </section>

      {/* Score Profiles */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Score Profiles</h3>
        <p>Every non-knocked-out candidate receives a profile classification and a human-readable recommendation. Profiles are evaluated in priority order -- the first match wins.</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-2 border-[var(--line)]">
            <thead>
              <tr className="bg-[var(--yellow)]">
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Profile</th>
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Condition</th>
                <th className="p-2 font-black text-left">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">strong_all_round</td>
                <td className="p-2 border-r border-[var(--line)]">All positive dimensions at least 6 and range across them at most 3.</td>
                <td className="p-2">Strong candidate. Proceed with standard outreach.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">high_alignment_high_risk</td>
                <td className="p-2 border-r border-[var(--line)]">D1 at least 7 and D5 at least 6.</td>
                <td className="p-2">High potential but high risk. Requires careful manual review.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">hidden_gem</td>
                <td className="p-2 border-r border-[var(--line)]">D1 at least 7 and D3 at least 7 and D4 at most 4.</td>
                <td className="p-2">Small but mighty. Consider for niche campaigns or grassroots partnerships.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">reach_over_substance</td>
                <td className="p-2 border-r border-[var(--line)]">D4 at least 7 and (D1 at most 4 or D3 at most 4).</td>
                <td className="p-2">Looks good on paper but lacks genuine alignment. Partnership risks appearing inauthentic.</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">mixed_profile</td>
                <td className="p-2 border-r border-[var(--line)]">Fallthrough when no other profile matches.</td>
                <td className="p-2">Review dimension scores directly to assess suitability.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Pipeline Summary */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">End-to-End Flow</h3>
        <div className="space-y-3 text-sm">
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">1.</span>
            <div><span className="font-bold">Phase 0:</span> Filter raw candidates by name, platforms, bio health, and hostile keywords.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">2.</span>
            <div><span className="font-bold">Profile Verification:</span> HEAD-verify social URLs, cross-reference via Serper search. Eliminate hallucinated profiles.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">3.</span>
            <div><span className="font-bold">Evidence Dossier:</span> Build from pre-existing data or 4 parallel LLM calls. Verify source URLs are live.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">4.</span>
            <div><span className="font-bold">Scoring:</span> 7 parallel LLM calls producing dimension scores (1-10) with rationale and evidence citations.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">5.</span>
            <div><span className="font-bold">Risk Audit:</span> Conservative LLM re-evaluates D5 and D8. Scores can only increase.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">6.</span>
            <div><span className="font-bold">Knockouts:</span> Check 4 rules. First match produces score 0.0 and no profile.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">7.</span>
            <div><span className="font-bold">Composite:</span> Weighted average (denominator = 0.90). Clamped to [0.0, 1.0].</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">8.</span>
            <div><span className="font-bold">Profile Classification:</span> Assign one of 5 profiles with a human-readable recommendation.</div>
          </div>
          <div className="flex items-start gap-3">
            <span className="font-black text-lg shrink-0 w-8">9.</span>
            <div><span className="font-bold">Persistence:</span> Write composite score, evidence JSON, knockout status, score profile, and individual dimension scores to the database.</div>
          </div>
        </div>
      </section>

      {/* Per-Candidate Cost */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">LLM Call Cost Per Candidate</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-2 border-[var(--line)]">
            <thead>
              <tr className="bg-[var(--yellow)]">
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Stage</th>
                <th className="p-2 font-black text-left border-r border-[var(--line)]">Calls</th>
                <th className="p-2 font-black text-left">Max Tokens Each</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">Evidence (parallel)</td>
                <td className="p-2 border-r border-[var(--line)]">4</td>
                <td className="p-2">2000</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">Dimension scoring</td>
                <td className="p-2 border-r border-[var(--line)]">7</td>
                <td className="p-2">512</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">Risk audit</td>
                <td className="p-2 border-r border-[var(--line)]">1</td>
                <td className="p-2">512</td>
              </tr>
              <tr className="border-t border-[var(--line)]">
                <td className="p-2 font-bold border-r border-[var(--line)]">Total</td>
                <td className="p-2 font-black border-r border-[var(--line)]">12</td>
                <td className="p-2">-</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-[var(--muted)]">The discovery phase itself also makes 1-2 LLM calls (6000 tokens each) to generate the candidate list before scoring begins. Per-candidate evidence calls are skipped when pre-existing evidence is provided (e.g., from n8n scraping).</p>
      </section>

      {/* Limitations */}
      <section className="sketch-panel p-7 space-y-4">
        <h3 className="text-3xl font-black">Known Limitations</h3>
        <ul className="list-disc list-inside space-y-2 font-medium">
          <li><span className="font-bold">D7 (Audience Authenticity)</span> is referenced in the knockout rules but is not defined in the dimension registry. The D7 knockout can never fire under the current code. This is a known gap.</li>
          <li><span className="font-bold">The LLM discovery phase can hallucinate</span> 30-50% of candidates. Profile verification eliminates most, but some bad profiles may still reach scoring.</li>
          <li><span className="font-bold">D5 and D8 scores can only increase</span> through the risk audit. There is no mechanism to correct a false positive on risk if the initial scorer was too harsh.</li>
          <li><span className="font-bold">Estimated reach is only populated</span> from n8n scraping or LLM estimation. It may be missing for many candidates.</li>
        </ul>
      </section>
    </div>
  );
};
