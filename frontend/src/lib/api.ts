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

export interface ConversationProfile {
  district?: string | null;
  block?: string | null;
  education?: string | null;
  interests?: string[];
  traditional_or_existing_skills?: string[];
  mobility?: number | null;
  self_employment_or_wage_preference?: string | null;
  current_work?: string | null;
  access_needs?: string | null;
}
export interface InterviewTurnResponse {
  next_question?: string;
  inferred_profile?: ConversationProfile;
  is_final?: boolean;
  extraction_provider?: 'gemini' | 'guided';
  missing_fields?: string[];
}

export interface RecommendationItem {
  recommendation_id: string;
  score: number;
  ranking_factors?: { ml_score?: number; ml_training_data?: string };
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
  ranking_method?: string;
  no_result_reason?: string;
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
  private jwtToken: string | null = null;
  private officerKey: string | null = null;
  private workerKey: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.sessionToken = window.sessionStorage.getItem('jm_session_token');
      this.sessionId = window.sessionStorage.getItem('jm_session_id');
      this.jwtToken = window.sessionStorage.getItem('jm_jwt_token');
      this.officerKey = window.sessionStorage.getItem('jm_officer_key');
      this.workerKey = window.sessionStorage.getItem('jm_worker_key') || 'test-worker-key';
    }
  }

  public async login(username: string, password: string = 'password123'): Promise<any> {
    const res = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) throw new Error('Login failed');
    const data = await res.json();
    this.setJwtToken(data.access_token);
    return data;
  }

  public setJwtToken(token: string) {
    this.jwtToken = token;
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('jm_jwt_token', token);
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.jwtToken) {
      headers['Authorization'] = `Bearer ${this.jwtToken}`;
    }
    if (this.sessionToken) {
      headers['X-Session-Token'] = this.sessionToken;
    }
    return headers;
  }

  private getOfficerHeaders(): Record<string, string> {
    if (this.jwtToken) return this.getHeaders();
    return {
      'Content-Type': 'application/json',
      'X-Officer-API-Key': this.officerKey || '',
    };
  }

  private getWorkerHeaders(): Record<string, string> {
    if (this.jwtToken) return this.getHeaders();
    return {
      'Content-Type': 'application/json',
      'X-Worker-API-Key': this.workerKey || '',
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

  public setWorkerKey(key: string) {
    this.workerKey = key;
    if (typeof window !== 'undefined') {
      window.sessionStorage.setItem('jm_worker_key', key);
    }
  }

  public getWorkerKey(): string | null {
    return this.workerKey;
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
    speaker: 'user' | 'ai' = 'user',
    language: string = 'en',
    mode: string = 'conversational'
  ): Promise<InterviewTurnResponse> {
    const res = await fetch(`${API_BASE}/interviews/${interviewId}/turns`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        text: message,
        speaker,
        language,
        mode,
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
    const data = await res.json();
    return { ...data, referral_id: data.referral_id || data.id };
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

  /**
   * RAG: Ask questions about NQR curriculum
   */
  async askNqrQuestion(query: string): Promise<{ query: string, answer: string }> {
    const res = await fetch(`${API_BASE}/catalogue/nqr/ask?query=${encodeURIComponent(query)}`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to ask NQR question: ${res.statusText}`);
    return res.json();
  }

  /**
   * Worker API: Get all cases
   */
  async getWorkerCases(): Promise<any> {
    const res = await fetch(`${API_BASE}/worker/cases`, {
      headers: this.getWorkerHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch worker cases: ${res.statusText}`);
    return res.json();
  }

  /**
   * Worker API: Get case details
   */
  async getWorkerCaseDetails(beneficiaryId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/worker/cases/${beneficiaryId}`, {
      headers: this.getWorkerHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch worker case details: ${res.statusText}`);
    return res.json();
  }

  /**
   * Worker API: Verify opportunity
   */
  async verifyOpportunity(opportunityId: string, payload: { batch_status: string, available_seats: number, notes: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/worker/opportunities/${opportunityId}/verify`, {
      method: 'POST',
      headers: this.getWorkerHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Failed to verify opportunity: ${res.statusText}`);
    return res.json();
  }

  /**
   * Worker API: Approve referral
   */
  async approveReferral(beneficiaryId: string, payload: { recommendation_id: string, local_opportunity_id: string, notes: string, caste_document_verified: boolean, income_criteria_verified: boolean, residence_proof_verified: boolean }): Promise<any> {
    const res = await fetch(`${API_BASE}/worker/cases/${beneficiaryId}/referral`, {
      method: 'POST',
      headers: this.getWorkerHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Failed to approve referral: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Update Referral Status (Outcome Workflow)
   */
  async updateReferralStatus(referralId: string, payload: { status: string, outcome?: string, notes?: string }): Promise<any> {
    const res = await fetch(`${API_BASE}/counselor/referrals/${referralId}/status`, {
      method: 'PATCH',
      headers: this.getOfficerHeaders(), // counselor is officer/admin
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || `Failed to update status: ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Get Counselor Referrals
   */
  async getCounselorReferrals(): Promise<any> {
    const res = await fetch(`${API_BASE}/counselor/referrals`, {
      headers: this.getOfficerHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch counselor referrals: ${res.statusText}`);
    return res.json();
  }
}

export const api = new ApiService();
