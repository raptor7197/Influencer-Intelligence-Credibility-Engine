import React, { useEffect, useState } from 'react';
import type { Campaign, DiscoveryRun } from '../../types/api';
import { apiClient } from '../../services/apiClient';
import { useToast } from '../../context/ToastContext';

interface DiscoveryRunsProps {
  campaignId: string;
  onBack: () => void;
}

const STATUS_COLOR_MAP: Record<string, string> = {
  completed: 'tag-yellow',
  failed: 'bg-[var(--red-soft)] text-[var(--ink)]',
  queued: 'bg-white',
  running: 'bg-[var(--olive)]',
  processing: 'bg-[var(--olive)]',
};

const RunDetail: React.FC<{ run: DiscoveryRun }> = ({ run }) => {
  const [open, setOpen] = useState(false);
  const sc = STATUS_COLOR_MAP[run.status] || 'bg-white';
  const date = run.created_at
    ? new Date(run.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className="border-2 border-[var(--line)] overflow-hidden bg-[#fffdf8]">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between p-3 hover:bg-[var(--yellow)] transition-colors text-left">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-type font-bold">#{run.id.slice(0, 8)}</span>
          <span className={`tag uppercase ${sc}`}>{run.status}</span>
          {run.result_count != null && <span className="text-sm text-[var(--red)] font-bold">{run.result_count} found</span>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {date && <span className="text-xs font-type text-[var(--muted)]">{date}</span>}
          <svg className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </div>
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2 text-sm">
          {run.error && (
            <div className="p-2 bg-[var(--red-soft)] font-medium border-l-4 border-[var(--red)]">
              <span className="label-type block mb-1">Error</span>
              {run.error}
            </div>
          )}
          {run.n8n_run_id && (
            <div>
              <span className="label-type">n8n Run ID</span>
              <p className="font-type break-all">{run.n8n_run_id}</p>
            </div>
          )}
          {run.raw_input && (
            <div>
              <span className="label-type">Input</span>
              <pre className="mt-1 p-2 bg-[#eeece6] text-xs overflow-x-auto whitespace-pre-wrap max-h-40 overflow-y-auto border-2 border-[var(--line)]">{run.raw_input}</pre>
            </div>
          )}
          {run.raw_output && (
            <div>
              <span className="label-type">Output</span>
              <pre className="mt-1 p-2 bg-[#eeece6] text-xs overflow-x-auto whitespace-pre-wrap max-h-40 overflow-y-auto border-2 border-[var(--line)]">{run.raw_output}</pre>
            </div>
          )}
          {run.result_count != null && (
            <p className="text-[var(--muted)]">{run.result_count} candidate{run.result_count !== 1 ? 's' : ''} found in this run.</p>
          )}
        </div>
      )}
    </div>
  );
};

export const DiscoveryRuns: React.FC<DiscoveryRunsProps> = ({ campaignId, onBack }) => {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedRun, setSelectedRun] = useState<DiscoveryRun | null>(null);
  const { showToast } = useToast();

  const fetchCampaign = async () => {
    try {
      const data = await apiClient.get<Campaign>(`/campaigns/${campaignId}`);
      setCampaign(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaign();
  }, [campaignId]);

  const runs = campaign?.discovery_runs || [];
  const hasActiveRun = runs.some(r => r.status === 'queued' || r.status === 'running' || r.status === 'processing');

  useEffect(() => {
    if (!hasActiveRun) return;
    const interval = setInterval(fetchCampaign, 5000);
    return () => clearInterval(interval);
  }, [hasActiveRun]);

  if (loading) return <div className="text-center py-20 font-type text-[var(--muted)]">Loading runs...</div>;

  return (
    <div className="space-y-10">
      <div className="flex items-center justify-between solid-rule pt-8">
        <div>
          <button onClick={onBack} className="link-underline">← Back to Discovery</button>
          <h2 className="text-5xl md:text-6xl font-black tracking-tight mt-2">
            Discovery Runs
            {campaign && <span className="text-2xl text-[var(--muted)] ml-4">for {campaign.org_name}</span>}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {hasActiveRun && <span className="tag tag-yellow animate-pulse">Running...</span>}
          <button onClick={fetchCampaign} className="sketch-button sketch-button-secondary px-4 py-2">⟳ Refresh</button>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-xl text-[var(--muted)]">No discovery runs yet.</p>
          <p className="text-sm text-[var(--muted)] mt-2">Runs appear here when you trigger discovery from the campaign page.</p>
        </div>
      ) : selectedRun ? (
        <div className="space-y-6">
          <button onClick={() => setSelectedRun(null)} className="link-underline">← All Runs</button>
          <div className="sketch-panel p-6 space-y-4">
            <div className="flex items-center gap-3">
              <span className="font-type text-lg font-bold">#{selectedRun.id.slice(0, 8)}</span>
              <span className={`tag uppercase ${STATUS_COLOR_MAP[selectedRun.status] || 'bg-white'}`}>{selectedRun.status}</span>
              <span className="text-xs text-[var(--muted)]">
                {selectedRun.created_at ? new Date(selectedRun.created_at).toLocaleString() : ''}
              </span>
            </div>

            {selectedRun.error && (
              <div className="p-3 bg-[var(--red-soft)] font-medium border-l-4 border-[var(--red)]">
                <span className="label-type block mb-1">Error</span>
                {selectedRun.error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="sketch-panel-soft p-3">
                <span className="label-type">Status</span>
                <p className="font-bold">{selectedRun.status}</p>
              </div>
              <div className="sketch-panel-soft p-3">
                <span className="label-type">Results</span>
                <p className="font-bold">{selectedRun.result_count ?? 'N/A'}</p>
              </div>
              {selectedRun.n8n_run_id && (
                <div className="col-span-2 sketch-panel-soft p-3">
                  <span className="label-type">n8n Run ID</span>
                  <p className="font-type break-all">{selectedRun.n8n_run_id}</p>
                </div>
              )}
            </div>

            {selectedRun.raw_input && (
              <div>
                <span className="label-type text-lg">Raw Input</span>
                <pre className="mt-2 p-4 bg-[#eeece6] text-sm overflow-x-auto whitespace-pre-wrap max-h-80 overflow-y-auto border-2 border-[var(--line)]">{selectedRun.raw_input}</pre>
              </div>
            )}

            {selectedRun.raw_output && (
              <div>
                <span className="label-type text-lg">Raw Output</span>
                <pre className="mt-2 p-4 bg-[#eeece6] text-sm overflow-x-auto whitespace-pre-wrap max-h-80 overflow-y-auto border-2 border-[var(--line)]">{selectedRun.raw_output}</pre>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-3 max-w-3xl">
          {runs.map((run) => (
            <button key={run.id} onClick={() => setSelectedRun(run)} className="w-full text-left block">
              <RunDetail run={run} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
