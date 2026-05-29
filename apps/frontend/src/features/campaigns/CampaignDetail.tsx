import React, { useEffect, useRef, useState } from 'react';
import type { Campaign, ProfileInput as ProfileInputType } from '../../types/api';
import { apiClient } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import { useSse } from '../../hooks/useSse';
import { ProfileInput } from '../discovery/ProfileInput';
import { InfluencerGrid } from '../influencers/InfluencerGrid';
import { ProgressOverlay } from '../discovery/ProgressOverlay';

interface CampaignDetailProps {
  campaignId: string;
  onBack: () => void;
  onInfluencerSelect: (influencerId: string) => void;
}

interface ProgressData {
  campaign_id: string;
  run_id: string;
  current: number;
  total: number;
  candidate_name?: string;
  comment?: string;
}

export const CampaignDetail: React.FC<CampaignDetailProps> = ({ campaignId, onBack, onInfluencerSelect }) => {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [showProfileInput, setShowProfileInput] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const { showToast } = useToast();

  const fetchCampaign = async () => {
    try {
      const data = await apiClient.get<Campaign>(`/campaigns/${campaignId}`);
      setCampaign(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch campaign detail', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaign();
  }, [campaignId, showToast]);

  const hasActiveRun = campaign?.discovery_runs?.some(
    r => r.status === 'queued' || r.status === 'running' || r.status === 'processing'
  );

  useEffect(() => {
    if (!hasActiveRun) return;
    const interval = setInterval(fetchCampaign, 5000);
    return () => clearInterval(interval);
  }, [hasActiveRun]);

  useEffect(() => {
    const onFocus = () => fetchCampaign();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);

  const progressTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    return () => {
      if (progressTimerRef.current) {
        clearTimeout(progressTimerRef.current);
      }
    };
  }, []);

  useSse((event) => {
    if (event.type === 'discovery.progress') {
      if (progressTimerRef.current) clearTimeout(progressTimerRef.current);
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
      if (progressTimerRef.current) clearTimeout(progressTimerRef.current);
      setProgress(null);
      fetchCampaign();
    }
    if (event.type === 'campaign.created') {
      setProgress(null);
      fetchCampaign();
    }
  });

  const handleAnalyzeProfiles = async (profiles: ProfileInputType[]) => {
    setAnalyzing(true);
    try {
      await apiClient.post(`/campaigns/${campaignId}/discover`, { profiles });
      showToast(`Analyzing ${profiles.length} influencers...`, 'success');
      setShowProfileInput(false);
      await fetchCampaign();
    } catch (err: any) {
      showToast(err.message || 'Analysis failed', 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="text-center py-20 font-type">Loading details...</div>;
  if (!campaign) return <div className="text-center py-20 font-type">Campaign not found.</div>;

  return (
    <div className="space-y-10">
      <div className="flex flex-col xl:flex-row xl:justify-between xl:items-start gap-6 solid-rule pt-8">
        <div className="space-y-2">
          <button onClick={onBack} className="link-underline">
            ← Back to Discovery
          </button>
          <h2 className="text-5xl md:text-6xl font-black tracking-tight">{campaign.org_name}</h2>
          <p className="text-xl text-[var(--muted)] max-w-3xl">{campaign.campaign_goal}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {hasActiveRun && !progress && (
            <span className="tag tag-yellow animate-pulse">Running...</span>
          )}
          <button
            onClick={fetchCampaign}
            className="sketch-button sketch-button-secondary px-4 py-2"
          >
            ⟳ Refresh
          </button>
          {!showProfileInput && (
            <button
              onClick={() => setShowProfileInput(true)}
              className="sketch-button"
            >
              + Add Influencers
            </button>
          )}
        </div>
      </div>

      {(hasActiveRun || progress) && (
        <ProgressOverlay data={progress} hasActiveRun={hasActiveRun} />
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[320px_1fr] gap-10">
        <div className="space-y-8">
          <div className="sketch-panel sketch-panel-yellow p-6">
            <h3 className="text-3xl font-black mb-4 dashed-rule pb-3">Target Details</h3>
            <dl className="space-y-4">
              <div>
                <dt className="label-type">Audience</dt>
                <dd className="text-lg font-medium">{campaign.target_audience || 'General'}</dd>
              </div>
              <div>
                <dt className="label-type">Geographic Focus</dt>
                <dd className="text-lg font-medium">{campaign.geo_focus || 'Global'}</dd>
              </div>
              <div>
                <dt className="label-type">Language</dt>
                <dd className="text-lg font-medium">{campaign.language}</dd>
              </div>
              <div>
                <dt className="label-type">Categories</dt>
                <dd className="flex flex-wrap gap-1 mt-1">
                  {campaign.categories?.map(c => (
                    <span key={c} className="tag">{c}</span>
                  ))}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div>
          {showProfileInput ? (
            <div className="space-y-4">
              <button
                onClick={() => setShowProfileInput(false)}
                className="link-underline"
              >
                ← Cancel
              </button>
              <ProfileInput onAnalyze={handleAnalyzeProfiles} loading={analyzing} />
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center justify-between dashed-rule pt-7">
                <div>
                  <h3 className="text-5xl font-black">Discovery Results</h3>
                  <p className="font-type mt-3">Showing top matches for current target details.</p>
                </div>
              </div>
              <InfluencerGrid campaignId={campaign.id} onSelect={onInfluencerSelect} isProcessing={hasActiveRun} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
