/**
 * JeevanMitra 2.0 API Client
 * Connects frontend interview, consent, recommendation, and referral flows
 * directly to the verified backend service.
 */

const API_BASE = '/api/v1';

export interface AnonymousSession {
  session_token: string;
  session_id: string;
  expires_at: string;
}

export interface ConsentRecord {
  consent_id: string;
  consent_type: string;
  status: 'granted' | 'revoked';
  timestamp: string;
}

export interface InterviewSessionResponse {
  interview_id: string;
  session_id: string;
  status: string;
  current_question_index: number;
  last_question?: string;
  language: string;
}

export interface InterviewTurnResponse {
  turn_id: string;
  speaker: 'user' | 'ai' | 'system';
  mode: 'standard' | 'guided_fallback' | 'clarification';
  extracted_fields: Record<string, any>;
  next_question?: string;
  clarification_needed?: boolean;
}

export interface RecommendationItem {
  recommendation_id: string;
  score: number;
  qualification: {
    id: string;
    nqr_code: string;
    title: string;
    sector: string;
    nsqf_level: number;
    duration_hours: number;
    official_url: string;
  };
  why_recommended: string[];
  matched_skills: string[];
  skill_gaps: string[];
  local_availability: {
    status: 'verified_open' | 'unknown' | 'expired' | 'closed';
    district?: string;
    centre_name?: string;
    batch_start_date?: string;
    stipend_amount_inr?: number;
    source_url?: string;
    last_verified_at?: string;
  };
  caveat: string;
}

export interface RecommendationsResponse {
  count: number;
  recommendations: RecommendationItem[];
  counselor_handoff_recommended?: boolean;
}

export interface ReferralResponse {
  referral_id: string;
  status: string;
  priority: string;
  referral_reason: string;
  assigned_counselor_id?: string;
  created_at: string;
}

export interface SummaryExport {
  interview_id: string;
  status: string;
  confirmed_profile: Record<string, any>;
  recommendations: RecommendationItem[];
  caveat: string;
  generated_at: string;
}

export interface PlanningMatrixCell {
  block: string;
  qualification_id: string;
  qualification_title: string;
  nqr_code: string;
  demand_count: number | null;
  verified_seats: number | null;
  total_seats: number | null;
  gap: number | null;
  nearest_verified_centre_km: number | null;
  nearest_verified_centre_name: string | null;
  share_of_demand_with_no_verified_batch: number | null;
  coverage: number | null;
  severity_score: number | null;
  suppressed: boolean;
  suppression_reason: string | null;
  source: {
    query_id: string;
    demand_row_ids: string[];
    supply_batch_ids: string[];
  };
}

export interface PlanningMatrix {
  district: string;
  period: string | null;
  generated_at: string;
  status: 'ok' | 'insufficient_data';
  message?: string;
  query_id: string;
  data_basis: {
    demand_records_total: number;
    supply_batches_considered: number;
    supply_eligibility_filter: string;
    k_anonymity_threshold: number;
    distance_cap_km: number;
  };
  gap_scoring: {
    formula: string;
    distance_cap_km: number;
    k_anonymity_threshold: number;
  };
  matrix: PlanningMatrixCell[];
  metrics: {
    total_demand_records: number;
    demand_with_verified_match_count: number;
    demand_with_verified_match_share: number;
    blocks_with_demand: number;
    qualifications_demanded: number;
    suppressed_cell_count: number;
    supply_batches_considered: number;
    total_unmet_demand: number;
  };
}

export interface PlanningBrief {
  brief_id: string;
  district: string;
  period: string;
  status: string;
  generated_at: string;
  generated_narrative: string;
  narrative_meta: {
    provider: string;
    rewritten_by_llm: boolean;
    validation: string;
    template_first: boolean;
  };
  top_gaps: {
    block: string;
    qualification_title: string;
    demand_count: number;
    verified_seats: number;
    gap: number;
    severity_score: number;
  }[];
  suggested_policy_actions: string[];
}

class ApiService {
  private sessionToken: string | null = null;
  private sessionId: string | null = null;
  private officerKey: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.sessionToken = window.sessionStorage.getItem('jm_session_token');
      this.sessionId = window.sessionStorage.getItem('jm_session_id');
      this.officerKey = window.sessionStorage.getItem('jm_officer_key');
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.sessionToken) {
      headers['X-Session-Token'] = this.sessionToken;
    }
    return headers;
  }

  private getOfficerHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'X-Officer-API-Key': this.officerKey || '',
    };
  }

  public setOfficerKey(key: string) {
    this.officerKey = key;
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('jm_officer_key', key);
    }
  }

  public getOfficerKey(): string | null {
    return this.officerKey;
  }

  /**
   * Layer 5: District demand vs verified-supply matrix (district_officer/admin)
   */
  async getPlanningMatrix(district: string, period?: string): Promise<PlanningMatrix> {
    const params = new URLSearchParams({ district });
    if (period) params.set('period', period);
    const res = await fetch(`${API_BASE}/planning/matrix?${params.toString()}`, {
      headers: this.getOfficerHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch planning matrix: ${res.statusText}`);
    return res.json();
  }

  /**
   * Layer 5: Generate a planning brief (aggregation snapshot + narrative)
   */
  async generatePlanningBrief(district: string, period: string): Promise<PlanningBrief> {
    const res = await fetch(`${API_BASE}/planning/briefs/generate`, {
      method: 'POST',
      headers: this.getOfficerHeaders(),
      body: JSON.stringify({ district, period }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail?.message || `Brief generation failed: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Layer 5: Fetch a stored brief
   */
  async getPlanningBrief(briefId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/planning/briefs/${briefId}`, {
      headers: this.getOfficerHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch brief: ${res.statusText}`);
    return res.json();
  }

  /**
   * Layer 5: Sign-off lifecycle (submit_for_review / sign_off)
   */
  async signOffBrief(
    briefId: string,
    officerName: string,
    action: 'submit_for_review' | 'sign_off' = 'sign_off'
  ): Promise<{ brief_id: string; status: string; signed_off_by: string; timestamp: string }> {
    const res = await fetch(`${API_BASE}/planning/briefs/${briefId}/sign-off`, {
      method: 'POST',
      headers: this.getOfficerHeaders(),
      body: JSON.stringify({ officer_name: officerName, action }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail?.message || `Sign-off failed: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Layer 5: Export a signed-off brief (CSV download or PDF-ready JSON)
   */
  async exportBrief(briefId: string, format: 'csv' | 'json' = 'csv'): Promise<any> {
    const res = await fetch(
      `${API_BASE}/planning/briefs/${briefId}/export?format=${format}`,
      { headers: this.getOfficerHeaders() }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body?.detail?.message || `Export failed: ${res.statusText}`);
    }
    if (format === 'json') return res.json();
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `planning_brief_${briefId}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    return { downloaded: true };
  }

  public setSession(token: string, id: string) {
    this.sessionToken = token;
    this.sessionId = id;
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('jm_session_token', token);
      window.sessionStorage.setItem('jm_session_id', id);
    }
  }

  public getSessionToken(): string | null {
    return this.sessionToken;
  }

  public getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * A2: Initialize an anonymous session
   */
  async createAnonymousSession(): Promise<AnonymousSession> {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!res.ok) throw new Error(`Failed to create session: ${res.statusText}`);
    const data: AnonymousSession = await res.json();
    this.setSession(data.session_token, data.session_id);
    return data;
  }

  /**
   * A1: Record affirmative versioned consent
   */
  async recordConsent(
    consentType: 'ai_processing' | 'profile_storage' | 'counselor_referral' | 'analytics' | 'export_summary' | 'dpdp_general',
    granted: boolean = true,
    userLanguage: string = 'hi'
  ): Promise<ConsentRecord> {
    const res = await fetch(`${API_BASE}/consents`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        session_id: this.sessionId,
        consent_type: consentType,
        policy_version: '1.0',
        user_language: userLanguage,
        capture_channel: 'web_app',
        granted,
      }),
    });
    if (!res.ok) throw new Error(`Consent recording failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A3: Start a new interview
   */
  async startInterview(language: string = 'hi'): Promise<InterviewSessionResponse> {
    const res = await fetch(`${API_BASE}/interviews/start`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        channel: 'web_app',
        language,
        session_id: this.sessionId,
      }),
    });
    if (!res.ok) throw new Error(`Interview start failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A3: Submit an interview turn (message)
   */
  async submitTurn(
    interviewId: string,
    message: string,
    speaker: 'user' | 'ai' = 'user'
  ): Promise<InterviewTurnResponse> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}/turns`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        text: message,
        speaker,
      }),
    });
    if (!res.ok) throw new Error(`Turn submission failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A3: Confirm profile fields before matching
   */
  async confirmProfile(
    interviewId: string,
    fields: Record<string, any>
  ): Promise<{ status: string; confirmed_fields: Record<string, any> }> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}/confirm-profile`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        confirmed_fields: fields,
      }),
    });
    if (!res.ok) throw new Error(`Profile confirmation failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A5: Generate verified recommendations based on confirmed profile
   */
  async generateRecommendations(interviewId: string): Promise<RecommendationsResponse> {
    const res = await fetch(`${API_BASE}/recommendations/generate`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        interview_id: interviewId,
      }),
    });
    if (!res.ok) throw new Error(`Recommendation generation failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A7: Create a counselor referral
   */
  async createReferral(
    interviewId: string,
    reason: string = 'user_requested_human_help',
    recommendationId?: string
  ): Promise<ReferralResponse> {
    const res = await fetch(`${API_BASE}/referrals`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        interview_id: interviewId,
        referral_reason: reason,
        recommendation_id: recommendationId,
      }),
    });
    if (!res.ok) throw new Error(`Referral request failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A8: Export privacy-safe printable summary
   */
  async exportSummary(interviewId: string): Promise<SummaryExport> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}/summary`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Export summary failed: ${res.statusText}`);
    return res.json();
  }

  /**
   * A2: DPDP Full Right to Erasure
   */
  async deleteMyData(): Promise<{ status: string; message: string }> {
    const res = await fetch(`${API_BASE}/beneficiaries/me`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Data deletion failed: ${res.statusText}`);
    const data = await res.json();
    this.sessionToken = null;
    this.sessionId = null;
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem('jm_session_token');
      window.sessionStorage.removeItem('jm_session_id');
      window.sessionStorage.removeItem('jeevanmitra-journey');
    }
    return data;
  }

  /**
   * A4: Fetch official verified qualifications
   */
  async getQualifications(sector?: string, limit: number = 20): Promise<any> {
    const params = new URLSearchParams();
    if (sector) params.set('sector', sector);
    params.set('limit', limit.toString());
    const res = await fetch(`${API_BASE}/catalogue/qualifications?${params.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch qualifications: ${res.statusText}`);
    return res.json();
  }

  /**
   * A4: Fetch verified local opportunities
   */
  async getOpportunities(district: string = 'Moradabad'): Promise<any> {
    const res = await fetch(`${API_BASE}/catalogue/opportunities?district=${encodeURIComponent(district)}`);
    if (!res.ok) throw new Error(`Failed to fetch opportunities: ${res.statusText}`);
    return res.json();
  }
}

export const api = new ApiService();
