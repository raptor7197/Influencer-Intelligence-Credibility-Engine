import React, { useEffect, useState } from 'react';
import type { Campaign } from '../../types/api';
import { apiClient } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';
import { useSse } from '../../hooks/useSse';

interface CampaignListProps {
  onSelect: (campaign: Campaign) => void;
  onCreateNew: () => void;
}

export const CampaignList: React.FC<CampaignListProps> = ({ onSelect, onCreateNew }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  const fetchCampaigns = async () => {
    try {
      const data = await apiClient.get<Campaign[]>('/campaigns');
      setCampaigns(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch campaigns', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, [showToast]);

  useEffect(() => {
    const onFocus = () => fetchCampaigns();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, []);

  useSse((event) => {
    if (event.type === 'campaign.created' || event.type === 'discovery.completed') {
      fetchCampaigns();
    }
  });

  if (loading) {
    return <div className="text-center py-20 font-type animate-pulse">Loading campaigns...</div>;
  }

  return (
    <div className="space-y-10">
      <div className="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-6">
        <div>
          <h2 className="text-6xl md:text-7xl font-black tracking-tight leading-none">Overview</h2>
          <div className="mt-3 h-2 w-72 bg-[#d36d68] rotate-[-1deg]"></div>
          <p className="font-type mt-6 text-lg">Welcome back. Here's what's happening today.</p>
        </div>
        <div className="w-full xl:w-80 bg-white border-b-2 border-[var(--line)] px-4 py-3 flex items-center gap-3">
          <span className="text-3xl text-gray-500">⌕</span>
          <span className="font-type text-gray-400">Search influencers...</span>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-12">
        <section className="space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 dashed-rule pt-7">
            <h3 className="text-4xl font-black flex items-center gap-3">
              <span className="text-[var(--red)]">⚑</span>
              Active Campaigns
            </h3>
            <button className="link-underline">View All</button>
          </div>
        <button
          onClick={onCreateNew}
          className="sketch-button bg-[var(--red-soft)] text-[var(--ink)]"
        >
          New Campaign
        </button>

      {campaigns.length === 0 ? (
        <div className="text-center py-20 sketch-panel-soft border-dashed">
          <p className="text-[var(--muted)] mb-4 font-type">No campaigns yet. Create your first one to get started.</p>
          <button
            onClick={onCreateNew}
            className="link-underline"
          >
            Create Campaign
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {campaigns.map((c) => (
            <div
              key={c.id}
              onClick={() => onSelect(c)}
              className={`sketch-card p-7 cursor-pointer group ${c.status === 'active' ? 'sketch-panel-yellow' : ''}`}
            >
              <div className="flex items-start justify-between gap-4 mb-5">
                <h3 className="text-2xl font-black leading-tight">
                {c.org_name}
              </h3>
                <span className={`tag ${c.status === 'active' ? '' : 'tag-yellow'} uppercase`}>
                  {c.status}
                </span>
              </div>
              <p className="text-lg text-[var(--muted)] line-clamp-3 mb-6 leading-relaxed">
                {c.campaign_goal}
              </p>
              <div className="dashed-rule pt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <span className="font-type text-sm">{c.geo_focus || 'Global'} / {c.language}</span>
                <span className="link-underline">Details →</span>
              </div>
            </div>
          ))}
        </div>
      )}
        </section>

        <aside className="space-y-6">
          <div className="solid-rule pt-5">
            <div className="flex items-center gap-3">
              <span className="w-5 h-5 rounded-full bg-[var(--red)] border-2 border-[var(--line)]"></span>
              <h3 className="text-3xl font-black leading-tight">Recent<br />Discoveries</h3>
            </div>
          </div>
          <div className="space-y-4">
            {campaigns
              .flatMap(c => (c.discovery_runs ?? []).map(r => ({ ...r, org_name: c.org_name, campaign_id: c.id })))
              .sort((a, b) => {
                if (!a.created_at || !b.created_at) return a.created_at ? -1 : b.created_at ? 1 : 0;
                return b.created_at.localeCompare(a.created_at);
              })
              .slice(0, 10)
              .map((run) => {
                const campaign = campaigns.find(c => c.id === run.campaign_id);
                return (
                  <button
                    key={run.id}
                    onClick={() => campaign && onSelect(campaign)}
                    className="w-full flex items-center justify-between gap-4 dashed-rule pt-4 text-left"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="avatar-sketch w-12 h-12 shrink-0">{run.org_name.charAt(0)}</div>
                      <div className="min-w-0">
                        <div className="font-black truncate">{run.org_name}</div>
                        <div className="font-type text-xs text-[var(--muted)] truncate">{run.status} · {run.result_count ?? 0} candidates</div>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={`tag uppercase ${run.status === 'completed' ? 'tag-yellow' : run.status === 'failed' ? 'bg-red-200' : 'bg-gray-200'}`}>
                        {run.status}
                      </span>
                    </div>
                  </button>
                );
              })}
            {campaigns.every(c => !c.discovery_runs?.length) && (
              <p className="font-type text-sm text-[var(--muted)] italic">No discovery runs yet.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};
