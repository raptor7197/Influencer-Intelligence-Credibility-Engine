import React from 'react';

interface ProgressData {
  campaign_id: string;
  run_id: string;
  current: number;
  total: number;
  candidate_name?: string;
  comment?: string;
}

interface ProgressOverlayProps {
  data: ProgressData | null;
  hasActiveRun: boolean;
}

export const ProgressOverlay: React.FC<ProgressOverlayProps> = ({ data, hasActiveRun }) => {
  if (!data && !hasActiveRun) return null;

  const isDone = data && data.current === data.total && data.total > 0;
  const pct = data?.total && data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;
  const barW = `${pct}%`;

  return (
    <div className="sketch-panel p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-lg font-black">Scoring Progress</h4>
        {data && (
          <span className="text-sm font-bold text-[var(--red)]">{data.current}/{data.total}</span>
        )}
      </div>

      <div className="w-full h-4 border-2 border-[var(--line)] bg-white overflow-hidden rounded-sm">
        <div
          className={`h-full transition-all duration-500 ease-out ${isDone ? 'bg-[var(--olive)]' : 'bg-[var(--yellow)]'}`}
          style={{ width: barW }}
        />
      </div>

      {data?.candidate_name && (
        <p className="text-sm font-medium">
          <span className="text-[var(--muted)]">current:</span> {data.candidate_name}
        </p>
      )}

      {(data?.comment || (!data && hasActiveRun)) && (
        <p className="text-xs text-[var(--muted)] italic leading-relaxed max-w-2xl">
          {isDone ? '✓ ' : ''}{data?.comment ?? 'Initializing workflow...'}
        </p>
      )}
    </div>
  );
};
