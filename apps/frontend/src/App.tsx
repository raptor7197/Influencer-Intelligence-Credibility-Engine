import { useState } from 'react';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './context/ToastContext';
import { CampaignList } from './features/campaigns/CampaignList';
import { CampaignForm } from './features/campaigns/CampaignForm';
import { CampaignDetail } from './features/campaigns/CampaignDetail';
import { DiscoveryRuns } from './features/campaigns/DiscoveryRuns';
import { InfluencerDetail } from './features/influencers/InfluencerDetail';
import { Docs } from './features/docs/Docs';
import type { Campaign } from './types/api';

type View = 'dashboard' | 'new-campaign' | 'campaign-detail' | 'influencer-detail' | 'runs' | 'docs';

function App() {
  const [view, setView] = useState<View>('dashboard');
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [selectedInfluencerId, setSelectedInfluencerId] = useState<string | null>(null);
  const [campaignDetailKey, setCampaignDetailKey] = useState(0);

  const handleCampaignCreated = (campaign: Campaign) => {
    setSelectedCampaignId(campaign.id);
    setSelectedInfluencerId(null);
    setView('campaign-detail');
  };

  const handleCampaignSelect = (campaign: Campaign) => {
    setSelectedCampaignId(campaign.id);
    setSelectedInfluencerId(null);
    setView('campaign-detail');
  };

  const handleInfluencerSelect = (influencerId: string) => {
    setSelectedInfluencerId(influencerId);
    setView('influencer-detail');
  };

  const handleBackToCampaign = () => {
    setSelectedInfluencerId(null);
    setView('campaign-detail');
    setCampaignDetailKey(k => k + 1);
  };

  const navigateTo = (target: View, options?: { campaignId?: string }) => {
    if (target !== 'influencer-detail') {
      setSelectedInfluencerId(null);
    }
    if (options?.campaignId) {
      setSelectedCampaignId(options.campaignId);
    }
    setView(target);
  };

  const handleSidebarRuns = () => {
    if (selectedCampaignId) {
      setSelectedInfluencerId(null);
      setView('runs');
    } else {
      setView('dashboard');
    }
  };

  const handleSidebarDiscovery = () => {
    if (selectedCampaignId) {
      setSelectedInfluencerId(null);
      setView('campaign-detail');
    } else {
      setView('dashboard');
    }
  };

  const currentNav = view === 'campaign-detail' ? 'discovery' : view === 'runs' ? 'runs' : view === 'docs' ? 'docs' : 'dashboard';

  return (
    <ErrorBoundary>
      <ToastProvider>
        <div className="page-shell font-ui text-[var(--ink)] lg:flex">
          <aside className="paper-sidebar lg:fixed lg:inset-y-0 lg:left-0 lg:w-80 p-6 lg:p-8 flex flex-col gap-8 z-20">
            <button className="text-left" onClick={() => setView('dashboard')}>
              <div className="text-3xl font-black leading-none tracking-tight">ImpactRank</div>
              <div className="font-type text-base mt-2 tracking-wide">Advocacy Authenticity</div>
            </button>

            <button
              onClick={() => setView('new-campaign')}
              className="sketch-button w-full bg-[var(--red-soft)] text-[var(--ink)] text-lg"
            >
              <span className="text-3xl leading-none">+</span>
              <span>New Campaign</span>
            </button>

            <nav className="space-y-3">
              <button
                onClick={() => navigateTo('dashboard')}
                className={`sidebar-link ${currentNav === 'dashboard' ? 'sidebar-link-active' : ''}`}
              >
                <span className="sketch-icon grid-icon">▦</span>
                Dashboard
              </button>
              <button
                onClick={handleSidebarDiscovery}
                className={`sidebar-link ${currentNav === 'discovery' ? 'sidebar-link-active' : ''}`}
              >
                <span className="sketch-icon rounded-full">⌾</span>
                Discovery
              </button>
              <button
                onClick={handleSidebarRuns}
                className={`sidebar-link ${currentNav === 'runs' ? 'sidebar-link-active' : ''}`}
              >
                <span className="sketch-icon">↗</span>
                Runs
              </button>
              <button
                onClick={() => setView('docs')}
                className={`sidebar-link ${currentNav === 'docs' ? 'sidebar-link-active' : ''}`}
              >
                <span className="sketch-icon">?</span>
                How the scoring algo works 
              </button>
            </nav>
          </aside>

          <main className="w-full lg:pl-80">
            <div className="max-w-[1320px] mx-auto px-5 sm:px-8 lg:px-12 py-8 lg:py-12">
            {view === 'dashboard' && (
              <CampaignList 
                onSelect={handleCampaignSelect} 
                onCreateNew={() => setView('new-campaign')} 
              />
            )}

            {view === 'new-campaign' && (
              <div className="space-y-4">
                <button 
                  onClick={() => setView('dashboard')}
                  className="link-underline"
                >
                  Back to Dashboard
                </button>
                <CampaignForm onSuccess={handleCampaignCreated} />
              </div>
            )}

            {view === 'campaign-detail' && selectedCampaignId && (
              <CampaignDetail 
                key={campaignDetailKey}
                campaignId={selectedCampaignId} 
                onBack={() => setView('dashboard')} 
                onInfluencerSelect={handleInfluencerSelect}
              />
            )}

            {view === 'runs' && selectedCampaignId && (
              <DiscoveryRuns
                campaignId={selectedCampaignId}
                onBack={() => setView('campaign-detail')}
              />
            )}

            {view === 'docs' && <Docs />}

            {view === 'influencer-detail' && selectedCampaignId && selectedInfluencerId && (
              <InfluencerDetail
                campaignId={selectedCampaignId}
                influencerId={selectedInfluencerId}
                onBack={handleBackToCampaign}
                onUpdate={(_updated) => {}}
              />
            )}
            </div>
          </main>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
