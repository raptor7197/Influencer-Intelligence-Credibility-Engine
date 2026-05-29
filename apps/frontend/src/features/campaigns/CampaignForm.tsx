import React, { useState } from 'react';
import { apiClient } from '../../services/apiClient';
import type { Campaign } from '../../types/api';
import { useToast } from '../../context/ToastContext';

interface CampaignFormProps {
  onSuccess: (campaign: Campaign) => void;
}

export const CampaignForm: React.FC<CampaignFormProps> = ({ onSuccess }) => {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    org_name: '',
    outreach_person: '',
    campaign_goal: '',
    target_audience: '',
    geo_focus: '',
    language: 'English',
    categories: '',
    exclusions: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...formData,
        categories: formData.categories.split(',').map(c => c.trim()).filter(Boolean),
        exclusions: formData.exclusions.split(',').map(e => e.trim()).filter(Boolean),
      };
      const campaign = await apiClient.post<Campaign>('/campaigns', payload);
      showToast('Campaign created successfully!', 'success');
      onSuccess(campaign);
    } catch (err: any) {
      showToast(err.message || 'Failed to create campaign', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-3xl mx-auto p-8 sketch-panel">
      <h2 className="text-5xl font-black mb-8">New Campaign</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="label-type block mb-1">Organization Name</label>
          <input
            required
            name="org_name"
            value={formData.org_name}
            onChange={handleChange}
            className="sketch-input"
            placeholder="e.g. Open Paws"
          />
        </div>
        <div>
          <label className="label-type block mb-1">Outreach Person</label>
          <input
            required
            name="outreach_person"
            value={formData.outreach_person}
            onChange={handleChange}
            className="sketch-input"
            placeholder="Your Name"
          />
        </div>
      </div>

      <div>
        <label className="label-type block mb-1">Campaign Goal</label>
        <textarea
          required
          name="campaign_goal"
          value={formData.campaign_goal}
          onChange={handleChange}
          rows={3}
          className="sketch-input"
          placeholder="Describe what you want to achieve..."
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="label-type block mb-1">Target Audience</label>
          <input
            name="target_audience"
            value={formData.target_audience}
            onChange={handleChange}
            className="sketch-input"
            placeholder="e.g. Gen Z in UK"
          />
        </div>
        <div>
          <label className="label-type block mb-1">Geographic Focus</label>
          <input
            name="geo_focus"
            value={formData.geo_focus}
            onChange={handleChange}
            className="sketch-input"
            placeholder="e.g. United Kingdom"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="label-type block mb-1">Language</label>
          <select
            name="language"
            value={formData.language}
            onChange={handleChange}
            className="sketch-input"
          >
            <option>English</option>
            <option>Spanish</option>
            <option>French</option>
            <option>German</option>
          </select>
        </div>
        <div>
          <label className="label-type block mb-1">Categories (comma separated)</label>
          <input
            name="categories"
            value={formData.categories}
            onChange={handleChange}
            className="sketch-input"
            placeholder="e.g. lifestyle, food, tech"
          />
        </div>
      </div>

      <div>
        <label className="label-type block mb-1">Exclusions (comma separated)</label>
        <input
          name="exclusions"
          value={formData.exclusions}
          onChange={handleChange}
          className="sketch-input"
          placeholder="e.g. hunting, fast fashion"
        />
      </div>

      <button
        disabled={loading}
        type="submit"
        className="w-full sketch-button"
      >
        {loading ? 'Creating...' : 'Create Campaign'}
      </button>
    </form>
  );
};
