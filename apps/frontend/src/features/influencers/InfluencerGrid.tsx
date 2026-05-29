import React, { useEffect, useState } from 'react';
import { apiClient } from '../../services/apiClient';
import type { Influencer } from '../../types/api';
import { useToast } from '../../context/ToastContext';
import { InfluencerCard } from './InfluencerCard';

interface InfluencerGridProps {
  campaignId: string;
  onSelect: (influencerId: string) => void;
  onStatusChange?: (influencerId: string, status: string) => void;
  isProcessing?: boolean;
}

export const InfluencerGrid: React.FC<InfluencerGridProps> = ({ campaignId, onSelect, onStatusChange, isProcessing = false }) => {
  const { showToast } = useToast();
  const [influencers, setInfluencers] = useState<Influencer[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchInfluencers = async () => {
    try {
      const data = await apiClient.get<Influencer[]>(`/campaigns/${campaignId}/influencers`);
      setInfluencers(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to fetch influencers', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (influencerId: string, status: string) => {
    try {
      await apiClient.patch(`/campaigns/${campaignId}/influencers/${influencerId}/status`, { status });
      setInfluencers(prev => prev.map(inf => inf.id === influencerId ? { ...inf, status } : inf));
      showToast(`Influencer marked as ${status}`, 'success');
    } catch (err: any) {
      showToast(err.message || 'Failed to update status', 'error');
    }
  };

  useEffect(() => {
    fetchInfluencers();
  }, [campaignId, showToast]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-72 sketch-panel-soft animate-pulse"></div>
        ))}
      </div>
    );
  }

  if (influencers.length === 0) {
    return (
      <div className="text-center py-20 sketch-panel-soft border-dashed">
        <h3 className="text-3xl font-black mb-2">{isProcessing ? 'Scoring in Progress...' : 'No Influencers Yet'}</h3>
        <p className="text-[var(--muted)] max-w-sm mx-auto">{isProcessing ? 'Candidates are being evaluated — results appear here once scoring completes.' : 'Trigger a discovery run to identify influencers who align with your mission.'}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {influencers.map((influencer) => (
        <InfluencerCard 
          key={influencer.id} 
          influencer={influencer} 
          onClick={() => onSelect(influencer.id)} 
          onStatusChange={onStatusChange ?? handleStatusChange}
        />
      ))}
    </div>
  );
};
