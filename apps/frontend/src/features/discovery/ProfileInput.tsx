import React, { useState } from 'react';
import type { ProfileInput as ProfileInputType } from '../../types/api';

interface ProfileInputProps {
  onAnalyze: (profiles: ProfileInputType[]) => void;
  loading: boolean;
}

const EMPTY_PROFILE: ProfileInputType = {
  name: '',
  handle: '',
  platforms: [],
  estimated_reach: undefined,
  location: '',
  bio: '',
  evidence: '',
};

export const ProfileInput: React.FC<ProfileInputProps> = ({ onAnalyze, loading }) => {
  const [profiles, setProfiles] = useState<ProfileInputType[]>([{ ...EMPTY_PROFILE }]);

  const updateProfile = (index: number, field: keyof ProfileInputType, value: any) => {
    setProfiles(prev => prev.map((p, i) =>
      i === index ? { ...p, [field]: value } : p
    ));
  };

  const addProfile = () => {
    setProfiles(prev => [...prev, { ...EMPTY_PROFILE }]);
  };

  const removeProfile = (index: number) => {
    setProfiles(prev => prev.filter((_, i) => i !== index));
  };

  const handlePlatformToggle = (index: number, platform: string) => {
    setProfiles(prev => prev.map((p, i) => {
      if (i !== index) return p;
      const platforms = p.platforms || [];
      return {
        ...p,
        platforms: platforms.includes(platform)
          ? platforms.filter(pl => pl !== platform)
          : [...platforms, platform],
      };
    }));
  };

  const handleSubmit = () => {
    const valid = profiles.filter(p => p.name.trim());
    if (valid.length === 0) return;
    onAnalyze(valid);
  };

  const PLATFORMS = ['instagram', 'youtube', 'tiktok', 'twitter', 'linkedin', 'facebook', 'threads'];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-4xl font-black">Add Influencers to Analyze</h3>
        <button
          onClick={addProfile}
          className="sketch-button px-4 py-2"
        >
          + Add Profile
        </button>
      </div>

      <div className="space-y-4">
        {profiles.map((profile, index) => (
          <div key={index} className="sketch-panel p-6 space-y-4">
            <div className="flex justify-between items-center">
              <span className="label-type">Profile #{index + 1}</span>
              {profiles.length > 1 && (
                <button
                  onClick={() => removeProfile(index)}
                  className="link-underline text-[var(--red)]"
                >
                  Remove
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label-type block mb-1">Name *</label>
                <input
                  className="sketch-input"
                  placeholder="e.g. Akshay Kumar"
                  value={profile.name}
                  onChange={(e) => updateProfile(index, 'name', e.target.value)}
                />
              </div>
              <div>
                <label className="label-type block mb-1">Handle</label>
                <input
                  className="sketch-input"
                  placeholder="e.g. @akshaykumar"
                  value={profile.handle || ''}
                  onChange={(e) => updateProfile(index, 'handle', e.target.value)}
                />
              </div>
              <div>
                <label className="label-type block mb-1">Location</label>
                <input
                  className="sketch-input"
                  placeholder="e.g. Mumbai, India"
                  value={profile.location || ''}
                  onChange={(e) => updateProfile(index, 'location', e.target.value)}
                />
              </div>
              <div>
                <label className="label-type block mb-1">Estimated Reach</label>
                <input
                  type="number"
                  className="sketch-input"
                  placeholder="e.g. 10000000"
                  value={profile.estimated_reach || ''}
                  onChange={(e) => updateProfile(index, 'estimated_reach', e.target.value ? parseInt(e.target.value) : undefined)}
                />
              </div>
              <div className="md:col-span-2">
                <label className="label-type block mb-1">Bio</label>
                <textarea
                  rows={2}
                  className="sketch-input"
                  placeholder="Brief description of this influencer"
                  value={profile.bio || ''}
                  onChange={(e) => updateProfile(index, 'bio', e.target.value)}
                />
              </div>
              <div className="md:col-span-2">
                <label className="label-type block mb-1">Evidence (optional)</label>
                <textarea
                  rows={3}
                  className="sketch-input"
                  placeholder="Paste relevant info about this person: known stances on cow/buffalo welfare, dietary habits, controversies, past statements, links to articles, etc."
                  value={profile.evidence || ''}
                  onChange={(e) => updateProfile(index, 'evidence', e.target.value)}
                />
              </div>
              <div className="md:col-span-2">
                <label className="label-type block mb-2">Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {PLATFORMS.map(platform => {
                    const active = (profile.platforms || []).includes(platform);
                    return (
                      <button
                        key={platform}
                        type="button"
                        onClick={() => handlePlatformToggle(index, platform)}
                        className={`tag transition-all ${
                          active
                            ? 'bg-[var(--yellow)]'
                            : 'bg-white text-[var(--muted)]'
                        }`}
                      >
                        {platform}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading || profiles.every(p => !p.name.trim())}
        className="w-full sketch-button"
      >
        {loading ? 'AI ANALYSIS IN PROGRESS...' : `ANALYZE ${profiles.filter(p => p.name.trim()).length || 0} INFLUENCERS`}
      </button>
    </div>
  );
};
