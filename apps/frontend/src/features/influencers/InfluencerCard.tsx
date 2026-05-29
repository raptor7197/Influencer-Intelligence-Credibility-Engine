import React from 'react';
import type { Influencer } from '../../types/api';

const CONFIDENCE_STYLE: Record<string, string> = {
  confirmed: 'tag-yellow',
  uncertain: 'bg-white',
  unverified: 'bg-[var(--red-soft)]',
};

interface InfluencerCardProps {
  influencer: Influencer;
  onClick: () => void;
  onStatusChange?: (id: string, status: string) => void;
}

export const InfluencerCard: React.FC<InfluencerCardProps> = ({ influencer, onClick, onStatusChange }) => {
  const score = influencer.composite_score !== null && influencer.composite_score !== undefined 
    ? Math.round(influencer.composite_score * 100) 
    : 0;
  const sources = influencer.evidence_json?.sources || [];
  const confidence = influencer.evidence_json?.verification_confidence;

  return (
    <div className="sketch-card p-7 min-h-[330px]">
      <div className="cursor-pointer group" onClick={onClick}>
        <div className="flex justify-between items-start mb-6">
          <div className="flex gap-3">
            <div className="avatar-sketch w-14 h-14 text-xl group-hover:bg-[var(--yellow)] transition-all">
              {influencer.name.charAt(0)}
            </div>
            <div>
              <h4 className="text-2xl font-black leading-tight">
                {influencer.name}
              </h4>
              <div className="flex items-center gap-1.5">
                <p className="font-type text-sm text-[var(--muted)]">{influencer.handle}</p>
                {confidence && (
                  <span className={`tag text-[10px] ${CONFIDENCE_STYLE[confidence] || 'bg-white'}`}>
                    {confidence === 'confirmed' ? 'Confirmed' : confidence === 'uncertain' ? 'Uncertain' : 'Unverified'}
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className={`score-badge ${score < 80 ? 'bg-[var(--olive)] text-[var(--ink)]' : ''}`}>
            {score}
          </div>
        </div>

        <p className="text-lg text-[var(--muted)] line-clamp-3 mb-3 leading-relaxed min-h-20">
          {influencer.bio}
        </p>

        <div className="flex flex-wrap gap-2 mb-4">
          {influencer.location && (
            <span className="tag text-[10px]">{influencer.location}</span>
          )}
          {influencer.audience_category && (
            <span className="tag text-[10px]">{influencer.audience_category}</span>
          )}
          {influencer.estimated_reach && (
            <span className="tag text-[10px]">{influencer.estimated_reach.toLocaleString()} followers</span>
          )}
          {influencer.score_profile && (
            <span className={`tag text-[10px] ${influencer.score_profile === 'strong_all_round' ? 'tag-yellow' : 'bg-white'}`}>
              {influencer.score_profile.replace(/_/g, ' ')}
            </span>
          )}
        </div>

        {influencer.knocked_out && (
          <div className="mb-3 p-2 bg-[var(--red-soft)] text-xs border-2 border-[var(--line)]">
            <span className="font-bold">Knocked Out:</span> {influencer.knockout_reason || 'Failed screening'}
          </div>
        )}

        <div className="flex flex-col gap-5 pt-4 dashed-rule">
          <div className="flex items-center gap-2">
            {(influencer.platforms || []).slice(0, 3).map((p) => (
              <span key={p} className="tag text-[10px]">
                {p}
              </span>
            ))}
            {sources.length > 0 && (
              <span className="font-type text-xs text-[var(--red)] font-bold ml-1">{sources.length} source{sources.length !== 1 ? 's' : ''}</span>
            )}
          </div>
          <div className="flex items-center justify-between gap-2">
            <span className="tag tag-yellow uppercase">{influencer.recommended_channel ?? '—'}</span>
            <span className="link-underline">Review Profile</span>
          </div>
        </div>

        <div className="mt-4 progress-track">
           <div 
            className={`progress-fill transition-all duration-1000 ${
              influencer.status === 'approved' ? 'bg-[var(--green)] w-full' :
              influencer.status === 'rejected' ? 'bg-[var(--red)] w-full' :
              influencer.status === 'maybe' ? 'bg-[var(--olive)] w-full' :
              'w-0'
            }`}
           ></div>
        </div>
      </div>

      {onStatusChange && (
        <div className="grid grid-cols-2 gap-2 mt-4 pt-4 dashed-rule">
          <button
            disabled={influencer.status === 'approved'}
            onClick={(e) => { e.stopPropagation(); onStatusChange(influencer.id, 'approved'); }}
            className={`py-2 text-sm font-bold border-2 border-[var(--line)] transition-all ${
              influencer.status === 'approved' ? 'bg-[var(--green)] text-white' : 'bg-white hover:bg-[var(--green)] hover:text-white'
            }`}
          >
            Approve
          </button>
          <button
            disabled={influencer.status === 'rejected'}
            onClick={(e) => { e.stopPropagation(); onStatusChange(influencer.id, 'rejected'); }}
            className={`py-2 text-sm font-bold border-2 border-[var(--line)] transition-all ${
              influencer.status === 'rejected' ? 'bg-[var(--red)] text-white' : 'bg-white hover:bg-[var(--red)] hover:text-white'
            }`}
          >
            Reject
          </button>
        </div>
      )}
    </div>
  );
};
