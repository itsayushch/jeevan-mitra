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

export interface StaffCaseItem {
  id: string;
  beneficiary_id: string;
  assigned_worker_id?: string | null;
  status: 'OPEN' | 'IN_PROGRESS' | 'REFERRED' | 'CLOSED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  district: string;
  state: string;
  target_sector?: string | null;
  notes_count?: number;
  follow_up_due_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseNoteItem {
  id: string;
  author_name: string;
  author_role: string;
  note_type: string;
  content: string;
  is_staff_only: boolean;
  created_at: string;
}

export interface CaseAssignmentHistoryItem {
  id: string;
  from_worker_id?: string | null;
  to_worker_id: string;
  assigned_by_id: string;
  reason?: string | null;
  assigned_at: string;
}

export interface StaffCaseDetail {
  case: StaffCaseItem;
  notes: CaseNoteItem[];
  assignments: CaseAssignmentHistoryItem[];
}

export interface StaffReferralItem {
  id: string;
  case_id: string;
  opportunity_id: string;
  opportunity_title?: string;
  provider_name?: string;
  qualification_title?: string;
  district: string;
  status:
    | 'READY_TO_SEND'
    | 'REFERRED'
    | 'CONTACTED'
    | 'ENROLLED'
    | 'TRAINING_STARTED'
    | 'COMPLETED'
    | 'DROPPED_OUT'
    | 'REJECTED'
    | 'BENEFICIARY_DECLINED'
    | 'CLOSED';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ContactAttemptRecord {
  id: string;
  referral_id: string;
  channel: 'PHONE' | 'IN_PERSON' | 'SMS' | 'WHATSAPP';
  successful: boolean;
  notes?: string;
  attempted_at: string;
}

export interface OutcomeRecord {
  id: string;
  referral_id: string;
  outcome_type: 'ENROLLED' | 'COMPLETED' | 'JOB_OFFER' | 'SELF_EMPLOYMENT_STARTED' | 'DROPPED_OUT';
  status: 'REPORTED' | 'VERIFIED' | 'REJECTED';
  evidence_summary?: string;
  reported_at: string;
  verified_at?: string;
  verified_by?: string;
}

export interface BeneficiaryCaseDisplay {
  id: string;
  status: string;
  display_status: {
    title: string;
    description: string;
  };
  district: string;
  follow_up_due_at?: string | null;
  created_at: string;
}

export interface BeneficiaryReferralDisplay {
  id: string;
  case_id: string;
  opportunity_title: string;
  provider_name: string;
  district: string;
  status: string;
  display_status: {
    title: string;
    description: string;
  };
  created_at: string;
  updated_at: string;
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

  // ==========================================
  // SPRINT 5: STAFF CASE MANAGEMENT
  // ==========================================

  /**
   * Fetch staff case inbox with optional filters
   */
  async listStaffCases(params?: { status?: string; district?: string; page?: number; limit?: number }): Promise<{ cases: StaffCaseItem[]; total: number }> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.district) query.set('district', params.district);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.limit) query.set('limit', params.limit.toString());
    const res = await fetch(`${API_BASE}/staff/cases?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to list staff cases: ${res.statusText}`);
    return res.json();
  }

  /**
   * Get single case with notes and assignment history
   */
  async getStaffCase(caseId: string): Promise<StaffCaseDetail> {
    const res = await fetch(`${API_BASE}/staff/cases/${caseId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch case: ${res.statusText}`);
    return res.json();
  }

  /**
   * Create a new case for a beneficiary
   */
  async createStaffCase(data: {
    beneficiary_id: string;
    district: string;
    state?: string;
    priority?: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
    target_sector?: string;
  }): Promise<StaffCaseItem> {
    const res = await fetch(`${API_BASE}/staff/cases`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Failed to create case: ${res.statusText}`);
    return res.json();
  }

  /**
   * Assign or transfer case to another field worker
   */
  async assignStaffCase(caseId: string, assignedWorkerId: string, reason?: string): Promise<{ success: boolean; case: StaffCaseItem }> {
    const res = await fetch(`${API_BASE}/staff/cases/${caseId}/assign`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ assigned_worker_id: assignedWorkerId, reason }),
    });
    if (!res.ok) throw new Error(`Failed to assign case: ${res.statusText}`);
    return res.json();
  }

  /**
   * Add note to a case
   */
  async addStaffCaseNote(caseId: string, content: string, noteType: string = 'FIELD_UPDATE', isStaffOnly: boolean = false): Promise<CaseNoteItem> {
    const res = await fetch(`${API_BASE}/staff/cases/${caseId}/notes`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ content, note_type: noteType, is_staff_only: isStaffOnly }),
    });
    if (!res.ok) throw new Error(`Failed to add note: ${res.statusText}`);
    return res.json();
  }

  /**
   * Schedule a follow-up date for a case
   */
  async scheduleStaffFollowUp(caseId: string, dueAt: string, reason?: string): Promise<{ success: boolean; follow_up_due_at: string }> {
    const res = await fetch(`${API_BASE}/staff/cases/${caseId}/follow-up`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ follow_up_due_at: dueAt, reason }),
    });
    if (!res.ok) throw new Error(`Failed to schedule follow-up: ${res.statusText}`);
    return res.json();
  }

  // ==========================================
  // SPRINT 5: STAFF REFERRALS & OUTCOMES
  // ==========================================

  /**
   * Create a canonical referral from a verified recommendation
   */
  async createCaseReferral(caseId: string, recommendationId: string, notes?: string): Promise<StaffReferralItem> {
    const res = await fetch(`${API_BASE}/staff/cases/${caseId}/referrals`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ recommendation_id: recommendationId, notes }),
    });
    if (!res.ok) throw new Error(`Failed to create referral: ${res.statusText}`);
    return res.json();
  }

  /**
   * List staff referrals with filters
   */
  async listStaffReferrals(params?: { case_id?: string; status?: string }): Promise<{ referrals: StaffReferralItem[] }> {
    const query = new URLSearchParams();
    if (params?.case_id) query.set('case_id', params.case_id);
    if (params?.status) query.set('status', params.status);
    const res = await fetch(`${API_BASE}/staff/referrals?${query.toString()}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to list referrals: ${res.statusText}`);
    return res.json();
  }

  /**
   * Get single referral detail
   */
  async getStaffReferral(referralId: string): Promise<StaffReferralItem> {
    const res = await fetch(`${API_BASE}/staff/referrals/${referralId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to get referral: ${res.statusText}`);
    return res.json();
  }

  /**
   * Transition referral status (State Machine Guarded)
   */
  async transitionReferral(referralId: string, toStatus: string, reason?: string): Promise<StaffReferralItem> {
    const res = await fetch(`${API_BASE}/staff/referrals/${referralId}/transition`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ to_status: toStatus, reason }),
    });
    if (!res.ok) throw new Error(`Failed to transition referral: ${res.statusText}`);
    return res.json();
  }

  /**
   * Log contact attempt with beneficiary/provider
   */
  async logContactAttempt(referralId: string, channel: 'PHONE' | 'IN_PERSON' | 'SMS' | 'WHATSAPP', successful: boolean, notes?: string): Promise<ContactAttemptRecord> {
    const res = await fetch(`${API_BASE}/staff/referrals/${referralId}/contact-attempts`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ channel, successful, notes }),
    });
    if (!res.ok) throw new Error(`Failed to log contact attempt: ${res.statusText}`);
    return res.json();
  }

  /**
   * Report an outcome for a referral
   */
  async recordOutcome(
    referralId: string,
    outcomeType: 'ENROLLED' | 'COMPLETED' | 'JOB_OFFER' | 'SELF_EMPLOYMENT_STARTED' | 'DROPPED_OUT',
    evidenceSummary?: string
  ): Promise<OutcomeRecord> {
    const res = await fetch(`${API_BASE}/staff/referrals/${referralId}/outcomes`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ outcome_type: outcomeType, evidence_summary: evidenceSummary }),
    });
    if (!res.ok) throw new Error(`Failed to record outcome: ${res.statusText}`);
    return res.json();
  }

  /**
   * Verify an outcome (Supervisor / District Admin action)
   */
  async verifyOutcome(outcomeId: string, verified: boolean, notes?: string): Promise<OutcomeRecord> {
    const res = await fetch(`${API_BASE}/staff/referrals/outcomes/${outcomeId}/verify`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ verified, notes }),
    });
    if (!res.ok) throw new Error(`Failed to verify outcome: ${res.statusText}`);
    return res.json();
  }

  // ==========================================
  // SPRINT 5: BENEFICIARY SAFE PORTAL
  // ==========================================

  /**
   * Get authenticated beneficiary's own active cases (bilingual localized)
   */
  async getMyCases(): Promise<{ cases: BeneficiaryCaseDisplay[] }> {
    const res = await fetch(`${API_BASE}/me/cases`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch cases: ${res.statusText}`);
    return res.json();
  }

  /**
   * Get single beneficiary case (bilingual localized)
   */
  async getMyCase(caseId: string): Promise<BeneficiaryCaseDisplay> {
    const res = await fetch(`${API_BASE}/me/cases/${caseId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch case: ${res.statusText}`);
    return res.json();
  }

  /**
   * Get authenticated beneficiary's own referrals (bilingual localized, no staff notes)
   */
  async getMyReferrals(): Promise<{ referrals: BeneficiaryReferralDisplay[] }> {
    const res = await fetch(`${API_BASE}/me/referrals`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch referrals: ${res.statusText}`);
    return res.json();
  }

  /**
   * Get single referral with timeline
   */
  async getMyReferral(referralId: string): Promise<BeneficiaryReferralDisplay> {
    const res = await fetch(`${API_BASE}/me/referrals/${referralId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error(`Failed to fetch referral: ${res.statusText}`);
    return res.json();
  }

  /**
   * Request field worker callback or support for a referral
   */
  async requestReferralSupport(referralId: string, note?: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/me/referrals/${referralId}/support-request`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ note }),
    });
    if (!res.ok) throw new Error(`Failed to request support: ${res.statusText}`);
    return res.json();
  }

  /**
   * Beneficiary self-decline for a referral
   */
  async declineReferral(referralId: string, reason?: string): Promise<{ success: boolean; referral: BeneficiaryReferralDisplay }> {
    const res = await fetch(`${API_BASE}/me/referrals/${referralId}/decline`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) throw new Error(`Failed to decline referral: ${res.statusText}`);
    return res.json();
  }
}

export const api = new ApiService();
