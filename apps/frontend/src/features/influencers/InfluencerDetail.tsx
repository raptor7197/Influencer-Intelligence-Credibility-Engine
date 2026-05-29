import React, { useEffect, useState } from 'react';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts';
import { 
  type Influencer, 
  type OutreachDraftResponse,
  DIMENSION_LABELS 
} from '../../types/api';
import { apiClient } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';

interface InfluencerDetailProps {
  influencerId: string;
  campaignId: string;
  onBack: () => void;
  onUpdate: (updated: Influencer) => void;
}

export const InfluencerDetail: React.FC<InfluencerDetailProps> = ({ influencerId, campaignId, onBack, onUpdate }) => {
  const { showToast } = useToast();
  const [influencer, setInfluencer] = useState<Influencer | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [editData, setEditData] = useState({
    subject_line: '',
    message_body: '',
  });

  const fetchDetail = async () => {
    try {
      const data = await apiClient.get<Influencer>(`/campaigns/${campaignId}/influencers/${influencerId}`);
      setInfluencer(data);
      setEditData({
        subject_line: data.outreach_draft?.subject_line || '',
        message_body: data.outreach_draft?.message_body || '',
      });
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch influencer detail', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [influencerId, campaignId, showToast]);

  const handleGenerateDraft = async () => {
    setGenerating(true);
    try {
      const draft = await apiClient.post<OutreachDraftResponse>(
        `/campaigns/${campaignId}/influencers/${influencerId}/draft`,
        {}
      );
      if (influencer) {
        const subject = draft?.subject_line || 'Let\'s collaborate';
        const body = draft?.message_body || 'Hi there, would you be open to a conversation about collaborating?';
        const updated = { ...influencer, outreach_draft: draft };
        setInfluencer(updated);
        onUpdate(updated);
        setEditData({ subject_line: subject, message_body: body });
      }
      showToast('Draft generated successfully!', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to generate draft', 'error');
    } finally {
      setGenerating(false);
    }
  };

  const handleRegenerateDraft = async () => {
    setRegenerating(true);
    try {
      const draft = await apiClient.post<OutreachDraftResponse>(
        `/campaigns/${campaignId}/influencers/${influencerId}/draft?regenerate=true`,
        {}
      );
      if (influencer) {
        const subject = draft?.subject_line || 'Let\'s collaborate';
        const body = draft?.message_body || 'Hi there, would you be open to a conversation about collaborating?';
        const updated = { ...influencer, outreach_draft: draft };
        setInfluencer(updated);
        onUpdate(updated);
        setEditData({ subject_line: subject, message_body: body });
      }
      showToast('Draft regenerated!', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to regenerate draft', 'error');
    } finally {
      setRegenerating(false);
    }
  };

  const handleUpdateStatus = async (status: string) => {
    try {
      await apiClient.patch(`/campaigns/${campaignId}/influencers/${influencerId}/status`, { status });
      if (influencer) {
        const updated = { ...influencer, status };
        setInfluencer(updated);
        onUpdate(updated);
      }
      showToast(`Influencer marked as ${status}`, 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to update status', 'error');
    }
  };

  const handleSaveDraft = async () => {
    try {
      const draft = await apiClient.patch<OutreachDraftResponse>(
        `/campaigns/${campaignId}/influencers/${influencerId}/draft`,
        editData
      );
      if (influencer) {
        const updated = { ...influencer, outreach_draft: draft };
        setInfluencer(updated);
        onUpdate(updated);
      }
      showToast('Draft updated successfully!', 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to update draft', 'error');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="font-type text-[var(--muted)]">Loading influencer details...</div>
      </div>
    );
  }

  if (!influencer) return null;

  return (
    <div className="space-y-10">
      <button onClick={onBack} className="link-underline">
        ← Back to Discovery
      </button>

      <div className="overflow-hidden">
        <div className="pb-6 solid-rule flex flex-col lg:flex-row lg:justify-between lg:items-start gap-6">
          <div className="flex items-center gap-4">
            <div className="avatar-sketch w-20 h-20 text-3xl">
              {influencer.name.charAt(0)}
            </div>
            <div>
              <h3 className="text-5xl md:text-6xl font-black leading-tight tracking-tight">{influencer.name}</h3>
              <p className="text-xl text-[var(--muted)]">{influencer.bio || influencer.handle}</p>
            </div>
          </div>
          <div className={`tag text-lg uppercase ${
            influencer.status === 'approved' ? 'tag-yellow' :
            influencer.status === 'rejected' ? 'bg-[var(--red-soft)]' :
            influencer.status === 'maybe' ? 'bg-[var(--olive)]' :
            'bg-white'
          }`}>
            {influencer.status}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-12 pt-10">
          <div className="space-y-12">
            <section>
              <h4 className="text-3xl font-black mb-6 flex items-center gap-2">
                <span className="w-4 h-4 bg-[var(--red)] border-2 border-[var(--line)] rounded-full"></span>
                Why this influencer?
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {influencer.evidence_json?.content_values?.map((v, i) => (
                  <div key={i} className="flex gap-3 p-4 sketch-panel-soft text-sm leading-relaxed">
                    <svg className="w-5 h-5 text-[var(--red)] flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {v}
                  </div>
                ))}
                {(!influencer.evidence_json?.content_values || influencer.evidence_json.content_values.length === 0) && (
                  <p className="text-sm text-[var(--muted)] italic">No content analysis available.</p>
                )}
              </div>
            </section>

            <section className="space-y-6">
              <h4 className="text-3xl font-black mb-4">Detailed Analysis</h4>

              {influencer.dimension_scores && influencer.dimension_scores.length > 0 && (
                <div className="sketch-panel-soft p-6">
                  <h5 className="label-type mb-4">Score Overview</h5>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={influencer.dimension_scores.map(d => ({
                          dimension: (DIMENSION_LABELS[d.dimension] || d.dimension).replace(/\s/g, '\n'),
                          score: d.score,
                        }))}>
                          <PolarGrid stroke="var(--line)" strokeDasharray="3 3" />
                          <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 10, fill: 'var(--muted)' }} />
                          <PolarRadiusAxis domain={[0, 10]} tick={false} axisLine={false} />
                          <Radar name="Score" dataKey="score" stroke="var(--red)" fill="var(--red-soft)" fillOpacity={0.3} strokeWidth={2} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={influencer.dimension_scores.map(d => ({
                          dimension: (DIMENSION_LABELS[d.dimension] || d.dimension).slice(0, 12),
                          score: d.score,
                        }))} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                          <XAxis type="number" domain={[0, 10]} tick={false} axisLine={false} />
                          <YAxis type="category" dataKey="dimension" tick={{ fontSize: 11, fill: 'var(--ink)', fontWeight: 700 }} width={120} axisLine={false} tickLine={false} />
                          <Tooltip
                            contentStyle={{ background: 'var(--paper)', border: '2px solid var(--line)', borderRadius: 0, fontSize: 12 }}
                          />
                          <Bar dataKey="score" radius={[0, 3, 3, 0]} barSize={18}>
                            {influencer.dimension_scores.map((d, i) => (
                              <Cell key={i} fill={d.score >= 7 ? 'var(--green)' : d.score >= 4 ? 'var(--olive)' : 'var(--red)'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-4">
                {influencer.dimension_scores?.map((score) => (
                  <div key={score.id} className="group p-6 sketch-panel-soft">
                    <div className="flex justify-between items-center mb-4">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-black">
                          {DIMENSION_LABELS[score.dimension] || score.dimension}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-32 progress-track">
                          <div 
                            className={`progress-fill transition-all duration-1000 ${
                              score.score >= 7 ? '' : score.score >= 4 ? 'bg-[var(--olive)]' : 'bg-[var(--red)]'
                            }`}
                            style={{ width: `${score.score * 10}%` }}
                          ></div>
                        </div>
                        <span className="text-xl font-black text-[var(--red)] w-12 text-right">
                          {score.score}/10
                        </span>
                      </div>
                    </div>
                    <p className="text-base text-[var(--muted)] leading-relaxed mb-4">{score.rationale}</p>
                    {score.uncertainty && (
                      <div className="mt-4 p-3 bg-[var(--red-soft)] text-xs text-[var(--ink)] flex gap-2 border-2 border-[var(--line)]">
                        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        {score.uncertainty}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* Risks & Controversy */}
            <section>
              <h4 className="text-3xl font-black mb-4 text-[var(--ink)]">▲ Risks & Concerns</h4>
              <div className="p-6 space-y-3">
                {influencer.evidence_json?.risk_controversy?.map((r, i) => (
                  <div key={i} className="flex gap-3 text-base text-[var(--muted)]">
                    <span className="font-black">◊</span>
                    {r}
                  </div>
                ))}
                {(!influencer.evidence_json?.risk_controversy || influencer.evidence_json.risk_controversy.length === 0) && (
                  <p className="text-sm text-[var(--muted)] italic">No specific risks identified.</p>
                )}
              </div>
            </section>

            {influencer.evidence_json?.sources && influencer.evidence_json.sources.length > 0 && (
              <section>
                <h4 className="text-3xl font-black mb-4">Sources</h4>
                <div className="space-y-2">
                  {influencer.evidence_json.sources.map((url, i) => (
                    <a key={i} href={url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm link-underline p-3 sketch-panel-soft transition-all">
                      <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                      <span className="truncate">{url}</span>
                    </a>
                  ))}
                </div>
              </section>
            )}
          </div>

          <div className="space-y-8">
            <div className="sketch-panel sketch-panel-yellow p-6 text-center">
              <div className="label-type">Overall Match</div>
              <div className="text-4xl font-black mt-1">
                {Math.round((influencer.composite_score || 0) * 100)}/100
              </div>
            </div>

            <div className="sketch-panel-soft p-6 space-y-4">
              <h5 className="label-type">Audience Overview</h5>
              <div className="space-y-3">
                {influencer.evidence_json?.audience_profile?.map((ap, i) => (
                  <div key={i} className="text-sm text-[var(--muted)] font-medium pb-2 dashed-rule last:border-0">{ap}</div>
                ))}
                {(!influencer.evidence_json?.audience_profile || influencer.evidence_json.audience_profile.length === 0) && (
                  <p className="text-xs text-[var(--muted)] italic">No audience data available.</p>
                )}
              </div>
              <div className="pt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="label-type">Reach</p>
                  <p className="text-sm font-bold">{influencer.estimated_reach?.toLocaleString() ?? '—'}</p>
                </div>
                <div>
                  <p className="label-type">Location</p>
                  <p className="text-sm font-bold">{influencer.location}</p>
                </div>
                <div className="col-span-2">
                  <p className="label-type">Contact via</p>
                  <div className="flex items-center gap-1 mt-1">
                    <span className="w-2 h-2 bg-[var(--red)] rounded-full"></span>
                    <p className="text-sm font-black uppercase tracking-tighter">{influencer.recommended_channel}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Sources */}
            {influencer.evidence_json?.sources && influencer.evidence_json.sources.length > 0 && (
              <div className="sketch-panel-soft p-6">
                <h5 className="label-type mb-3">
                  Profile Links <span className="text-[var(--red)]">({influencer.evidence_json.sources.length})</span>
                </h5>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {influencer.evidence_json.sources.map((url, i) => (
                    <a key={i} href={url} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-2 text-xs link-underline truncate p-2 transition-colors">
                      <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                      <span className="truncate">{url}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Outreach Draft Section */}
            <div className="space-y-4">
              <h5 className="text-3xl font-black solid-rule pt-4">Outreach Editor</h5>

              {influencer.outreach_draft ? (
                <div className="sketch-panel p-6 space-y-4">
                  <div>
                    <label className="label-type block mb-1">Subject</label>
                    <input
                      className="sketch-input"
                      value={editData.subject_line}
                      onChange={(e) => setEditData({ ...editData, subject_line: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label-type block mb-1">Message</label>
                    <textarea
                      rows={8}
                      className="sketch-input text-sm leading-relaxed"
                      value={editData.message_body}
                      onChange={(e) => setEditData({ ...editData, message_body: e.target.value })}
                    />
                  </div>

                  <div className="flex gap-2 pt-2">
                    <button onClick={handleSaveDraft} className="flex-1 sketch-button py-2.5">Save</button>
                    <button onClick={handleRegenerateDraft} disabled={regenerating} className="sketch-button sketch-button-secondary px-4 py-2.5">
                      {regenerating ? 'Regenerating...' : 'Regenerate'}
                    </button>
                  </div>

                  <div className="space-y-4 pt-4">
                    <p className="label-type">Guidance</p>
                    <div className="space-y-2">
                      {influencer.outreach_draft.messaging_tips?.map((tip, i) => (
                        <div key={i} className="flex gap-2 text-[11px] text-[var(--muted)] bg-white p-2 border-2 border-[var(--line)]">
                          <span className="text-[var(--red)] font-bold">Tip:</span> {tip}
                        </div>
                      ))}
                    </div>
                    <div className="flex flex-wrap gap-1 mt-3">
                      {influencer.outreach_draft.framing_angles?.map((angle, i) => (
                        <span key={i} className="tag tag-yellow text-[10px]">{angle}</span>
                      ))}
                    </div>
                  </div>

                  <button 
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(editData.message_body);
                        showToast('Copied! Marking as approved...', 'success');
                        handleUpdateStatus('approved');
                      } catch {
                        showToast('Failed to copy to clipboard', 'error');
                      }
                    }}
                    className="w-full sketch-button mt-4"
                  >
                    Approve & Copy
                  </button>
                </div>
              ) : (
                <div className="p-8 border-2 border-dashed border-[var(--line)] text-center">
                  <button
                    disabled={generating}
                    onClick={handleGenerateDraft}
                    className="w-full sketch-button sketch-button-black"
                  >
                    {generating ? 'Generating Draft...' : 'Generate Draft'}
                  </button>
                </div>
              )}
            </div>

            {/* Final Decision */}
            <div className="pt-4 dashed-rule">
               <div className="grid grid-cols-2 gap-3">
                  <button 
                    disabled={influencer.status === 'approved'}
                    onClick={() => handleUpdateStatus('approved')}
                    className={`py-3 font-bold border-2 border-[var(--line)] transition-all ${
                      influencer.status === 'approved' ? 'bg-[var(--yellow)]' : 'bg-white hover:bg-[var(--yellow)]'
                    }`}
                  >
                    Approve
                  </button>
                  <button 
                    disabled={influencer.status === 'rejected'}
                    onClick={() => handleUpdateStatus('rejected')}
                    className={`py-3 font-bold border-2 border-[var(--line)] transition-all ${
                      influencer.status === 'rejected' ? 'bg-[var(--red-soft)]' : 'bg-white hover:bg-[var(--red-soft)]'
                    }`}
                  >
                    Reject
                  </button>
                  <button 
                    disabled={influencer.status === 'maybe'}
                    onClick={() => handleUpdateStatus('maybe')}
                    className={`py-3 col-span-2 font-bold border-2 border-[var(--line)] transition-all ${
                      influencer.status === 'maybe' ? 'bg-[var(--olive)]' : 'bg-[#eeece6] hover:bg-[var(--olive)]'
                    }`}
                  >
                    Maybe
                  </button>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
