export type LanguageCode = 'hi' | 'bho' | 'awa' | 'en' | 'bn' | 'ta' | 'te';

export type Channel = 'web_app' | 'kiosk' | 'whatsapp' | 'ivr';

export type MatchState = 'Interest Match' | 'Verified Match';

export type WorkPreference = 'wage' | 'self_employment' | 'both';

export type ConfirmationStatus = 'unconfirmed' | 'confirmed' | 'corrected';

export type AnswerSource = 'voice_extraction' | 'beneficiary_edit' | 'worker_correction';

export type ActorRole = 'beneficiary' | 'field_worker' | 'district_officer' | 'system';

export type BatchStatus = 'active' | 'upcoming' | 'full' | 'completed' | 'cancelled';

export type ReferralStatus =
  | 'pending'
  | 'counselor_contacted'
  | 'documents_verified'
  | 'enrolled'
  | 'rejected'
  | 'ineligible';

export type EmploymentOutcome =
  | 'unemployed'
  | 'wage_employed'
  | 'self_employed'
  | 'enterprise_started';

export interface Beneficiary {
  id: string;
  name: string;
  phone?: string;
  gender: 'male' | 'female' | 'other' | 'prefer_not_to_say';
  age?: number;
  category: string; // 'SC'
  preferred_language: LanguageCode;
  district: string;
  block: string;
  village?: string;
  contact_preference: 'voice' | 'whatsapp' | 'sms' | 'field_worker';
  created_at: string;
  updated_at: string;
}

export interface Consent {
  id: string;
  beneficiary_id: string;
  purpose: string;
  notice_version: string;
  audio_consent_recorded: boolean;
  voice_retention_choice: 'do_not_keep' | 'keep_for_quality';
  dpdp_affirmative_consent: boolean;
  timestamp: string;
}

export interface InterviewTurn {
  turn_number: number;
  question_id: string;
  question_text: string;
  audio_prompt_url?: string;
  beneficiary_audio_url?: string;
  transcript: string;
  confidence: number;
  clarification_needed: boolean;
  timestamp: string;
}

export interface InterviewSession {
  id: string;
  beneficiary_id: string;
  channel: Channel;
  status: 'in_progress' | 'profile_extracted' | 'confirmed' | 'completed' | 'abandoned';
  current_question_index: number;
  last_question?: string;
  language: LanguageCode;
  transcript_history: InterviewTurn[];
  created_at: string;
  updated_at: string;
}

export interface ProfileAnswer {
  id: string;
  beneficiary_id: string;
  session_id?: string;
  field_name:
    | 'education_level'
    | 'current_work'
    | 'family_occupation'
    | 'interests'
    | 'skills'
    | 'mobility_radius_km'
    | 'accessibility_needs'
    | 'work_preference'
    | 'district'
    | 'block';
  field_value: string;
  confidence_score: number;
  confirmation_status: ConfirmationStatus;
  source: AnswerSource;
  created_at: string;
  updated_at: string;
}

export interface ExtractedBeneficiaryProfile {
  education_level: { value: string; confidence: number; confirmed: boolean };
  current_work: { value: string; confidence: number; confirmed: boolean };
  family_occupation: { value: string; confidence: number; confirmed: boolean };
  interests: { value: string[]; confidence: number; confirmed: boolean };
  skills: { value: string[]; confidence: number; confirmed: boolean };
  mobility_radius_km: { value: number; confidence: number; confirmed: boolean };
  accessibility_needs: { value: string; confidence: number; confirmed: boolean };
  work_preference: { value: WorkPreference; confidence: number; confirmed: boolean };
  district: { value: string; confidence: number; confirmed: boolean };
  block: { value: string; confidence: number; confirmed: boolean };
  requires_clarification: string[];
}

export interface Qualification {
  id: string;
  nqr_code: string;
  title: string;
  sector: string;
  nsqf_level: number;
  duration_hours: number;
  min_education: string;
  min_education_rank: number; // 0: None, 1: 5th, 2: 8th, 3: 10th, 4: 12th, 5: Degree
  work_type: WorkPreference;
  physical_intensity: 'light' | 'medium' | 'medium_high' | 'high';
  skills_acquired: string[];
  curriculum_summary: string;
  entry_criteria: string;
  certification_body: string;
  nqr_link: string;
  verification_status: 'verified' | 'pending' | 'deprecated';
  verification_date: string;
}

export interface LocalOpportunity {
  id: string;
  qualification_id: string;
  centre_or_employer_name: string;
  type: 'training_centre' | 'employer_apprenticeship' | 'enterprise_cluster';
  district: string;
  block: string;
  address: string;
  latitude: number;
  longitude: number;
  batch_start_date: string;
  batch_end_date: string;
  total_seats: number;
  available_seats: number;
  sc_reserved_seats: number;
  batch_status: BatchStatus;
  hostel_available: boolean;
  stipend_amount_inr: number;
  free_toolkit_provided: boolean;
  source: string;
  verified_by_worker_id?: string;
  verified_at: string;
  created_at: string;
}

export interface ScoreBreakdown {
  interest: number;       // Max 30
  prior_skills: number;   // Max 20
  access: number;         // Max 20
  local_demand: number;   // Max 20
  work_preference: number;// Max 10
}

export interface Recommendation {
  id: string;
  beneficiary_id: string;
  session_id?: string;
  qualification_id: string;
  local_opportunity_id?: string | null;
  rank: number;
  score: number;
  score_breakdown: ScoreBreakdown;
  match_state: MatchState;
  explanation_text: string;
  audio_explanation_script: string;
  tradeoff_summary: string;
  skill_gap_summary: string;
  data_snapshot: {
    qualification: Qualification;
    opportunity?: LocalOpportunity | null;
    timestamp: string;
  };
  created_at: string;
  updated_at: string;
}

export interface Referral {
  id: string;
  beneficiary_id: string;
  recommendation_id: string;
  local_opportunity_id: string;
  assigned_worker_id: string;
  status: ReferralStatus;
  notes?: string;
  caste_document_verified: boolean;
  income_criteria_verified: boolean;
  residence_proof_verified: boolean;
  sms_sent: boolean;
  whatsapp_sent: boolean;
  next_follow_up?: string;
  created_at: string;
  updated_at: string;
}

export interface Outcome {
  id: string;
  beneficiary_id: string;
  referral_id?: string;
  enrolment_status: 'enrolled' | 'completed' | 'dropped_out';
  completion_status: 'in_progress' | 'passed' | 'failed' | 'dropped_out';
  dropout_reason?: string;
  employment_status: EmploymentOutcome;
  employer_or_enterprise_name?: string;
  monthly_income_inr: number;
  toolkit_received: boolean;
  seed_grant_applied: boolean;
  follow_up_date?: string;
  notes?: string;
  recorded_by_worker_id: string;
  created_at: string;
  updated_at: string;
}

export interface TradeDemandSupplyGap {
  trade_name: string;
  nqr_code: string;
  sector: string;
  voice_demand: number;
  sanctioned_seats: number;
  active_batches: number;
  supply_gap: number;
  gap_status: 'Severe Deficit' | 'Moderate Deficit' | 'Balanced' | 'Waitlisted' | 'No Centre';
  block_breakdown: Record<string, { demand: number; capacity: number }>;
}

export interface PlanningBrief {
  id: string;
  district: string;
  period: string; // e.g. 'FY 2026-27 Q2'
  total_beneficiaries_interviewed: number;
  total_verified_matches: number;
  total_supply_gaps: number;
  aggregation_snapshot: {
    gaps: TradeDemandSupplyGap[];
    cluster_alerts: Array<{
      block: string;
      trade: string;
      demand: number;
      nearest_centre_distance_km: number;
      suggested_action: string;
    }>;
    generated_at: string;
  };
  generated_narrative: string;
  suggested_policy_actions: string[];
  reviewer_sign_off_status: 'draft' | 'under_review' | 'signed_off' | 'rejected';
  signed_off_by?: string;
  signed_off_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  actor_id: string;
  actor_name: string;
  actor_role: ActorRole;
  action: string;
  entity_type: string;
  entity_id: string;
  old_values?: Record<string, unknown> | null;
  new_values?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
  timestamp: string;
}

export interface DriftAdvisory {
  id: string;
  district: string;
  flag_type: 'gender_skew' | 'geographic_neglect' | 'unconfirmed_spike' | 'completion_drop';
  severity: 'low' | 'medium' | 'high';
  headline: string;
  evidence: Record<string, unknown>;
  suggested_human_action: string;
  created_at: string;
}
