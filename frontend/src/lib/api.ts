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
  whyRecommended?: {
    shortExplanation: string;
    reasons: { factor: string; text: string }[];
    generatedBy: string;
    locale: string;
  };
  explanationFacts?: {
    factor: string;
    labelKey: string;
    value: string;
    source: string;
    confidence: string;
  }[];
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
  match_state?: 'VERIFIED_MATCH' | 'INTEREST_MATCH';
  can_request_referral?: boolean;
  can_request_worker_support?: boolean;
  canRequestReferral?: boolean;
  canRequestWorkerSupport?: boolean;
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

class ApiService {
  private sessionToken: string | null = null;
  private sessionId: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.sessionToken = window.sessionStorage.getItem('jm_session_token');
      this.sessionId = window.sessionStorage.getItem('jm_session_id');
    }
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.sessionToken) {
      headers['X-Session-Token'] = this.sessionToken;
    }
    if (typeof window !== 'undefined') {
      const jwtToken = window.localStorage.getItem('jm_jwt_token');
      if (jwtToken) {
        headers['Authorization'] = `Bearer ${jwtToken}`;
      }
      const locale = window.localStorage.getItem('jeevanmitra.locale') || window.localStorage.getItem('jeevanmitra-language') || 'en';
      headers['Accept-Language'] = locale;
    }
    return headers;
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
