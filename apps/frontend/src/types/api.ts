export interface Campaign {
  id: string;
  org_name: string;
  outreach_person: string;
  campaign_goal: string;
  target_audience?: string;
  geo_focus?: string;
  language: string;
  categories?: string[];
  exclusions?: string[];
  status: string;
  created_at?: string;
  discovery_runs?: DiscoveryRun[];
}

export interface DiscoveryRun {
  id: string;
  campaign_id: string;
  status: string;
  n8n_run_id: string | null;
  result_count: number | null;
  raw_input?: string;
  raw_output?: string;
  error?: string;
  created_at?: string;
}

export interface DimensionScoreResponse {
  id: string;
  dimension: string;
  score: number;
  rationale: string;
  evidence: string[] | null;
  confidence: string | null;
  uncertainty: string | null;
}

export interface OutreachDraftResponse {
  id: string;
  subject_line: string;
  message_body: string;
  framing_angles: string[];
  messaging_tips: string[];
  is_edited: boolean;
  status: string;
}

export interface EvidenceJson {
  content_values: string[];
  public_record: string[];
  audience_profile: string[];
  risk_controversy: string[];
  sources: string[];
  verification_confidence?: 'confirmed' | 'uncertain' | 'unverified';
}

export interface Influencer {
  id: string;
  campaign_id: string;
  discovery_run_id: string;
  name: string;
  handle: string;
  platforms: string[];
  estimated_reach: number;
  location: string;
  bio: string;
  audience_category: string;
  composite_score: number;
  status: string;
  recommended_channel: string;
  dimension_scores: DimensionScoreResponse[];
  outreach_draft: OutreachDraftResponse | null;
  evidence_json?: EvidenceJson;
  knocked_out?: boolean;
  knockout_reason?: string;
  score_profile?: string;
}

export const DIMENSION_LABELS: Record<string, string> = {
  D0_ANIMAL_WELFARE_ALIGNMENT: 'Animal Welfare Alignment',
  D1_VALUES_ALIGNMENT: 'Values Alignment',
  D2_AUDIENCE_RELEVANCE: 'Audience Relevance',
  D3_CREDIBILITY_TRUST: 'Credibility & Trust',
  D4_REACHABILITY: 'Reachability',
  D5_RISK_CONTROVERSY: 'Risk & Controversy',
  D6_CAMPAIGN_FIT: 'Campaign Fit',
};

export type InfluencerStatus = 'pending' | 'approved' | 'rejected' | 'maybe';

export interface ProfileInput {
  name: string;
  handle?: string;
  platforms?: string[];
  estimated_reach?: number;
  location?: string;
  bio?: string;
  audience_category?: string;
  evidence?: string;
}

export interface DiscoverRequest {
  profiles: ProfileInput[];
}
