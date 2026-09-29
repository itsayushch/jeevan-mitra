-- ============================================================================
-- JEEVAN-MITRA 2.0 RELATIONAL DATABASE SCHEMA
-- Ministry of Social Justice & Empowerment (MoSJE) - PM-AJAY GIA Component
-- Schema supporting Trust, Verification, Recommendations, Consent, Auditing & AI
-- ============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. Beneficiaries Table
CREATE TABLE IF NOT EXISTS beneficiaries (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  phone TEXT,
  gender TEXT CHECK(gender IN ('male', 'female', 'other', 'prefer_not_to_say')) NOT NULL DEFAULT 'prefer_not_to_say',
  age INTEGER,
  category TEXT NOT NULL DEFAULT 'SC',
  preferred_language TEXT NOT NULL DEFAULT 'hi',
  district TEXT NOT NULL,
  block TEXT NOT NULL,
  village TEXT,
  contact_preference TEXT CHECK(contact_preference IN ('voice', 'whatsapp', 'sms', 'field_worker')) NOT NULL DEFAULT 'voice',
  owner_type TEXT CHECK(owner_type IN ('anonymous', 'authenticated_user', 'counselor_assisted')) NOT NULL DEFAULT 'authenticated_user',
  owner_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_beneficiaries_district_block ON beneficiaries(district, block);
CREATE INDEX IF NOT EXISTS idx_beneficiaries_category ON beneficiaries(category);

-- 2. Anonymous Sessions Table (A2 Privacy-preserving lifecycle)
CREATE TABLE IF NOT EXISTS anonymous_sessions (
  id TEXT PRIMARY KEY,
  session_token TEXT UNIQUE NOT NULL,
  owner_type TEXT CHECK(owner_type IN ('anonymous', 'authenticated_user', 'counselor_assisted')) NOT NULL DEFAULT 'anonymous',
  owner_id TEXT,
  expires_at TEXT NOT NULL,
  metadata TEXT DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_anon_sessions_token ON anonymous_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_anon_sessions_expires ON anonymous_sessions(expires_at);

-- 3. Consent Records Table (A1 Versioned Consent Enforcement)
CREATE TABLE IF NOT EXISTS consent_records (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  beneficiary_id TEXT,
  consent_type TEXT CHECK(consent_type IN ('ai_processing', 'profile_storage', 'counselor_referral', 'analytics', 'export_summary', 'dpdp_general')) NOT NULL,
  policy_version TEXT NOT NULL DEFAULT '1.0',
  status TEXT CHECK(status IN ('granted', 'revoked')) NOT NULL DEFAULT 'granted',
  revoked_at TEXT,
  revocation_reason TEXT,
  user_language TEXT NOT NULL DEFAULT 'hi',
  capture_channel TEXT NOT NULL DEFAULT 'web_app',
  timestamp TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_consent_records_beneficiary ON consent_records(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_consent_records_session ON consent_records(session_id);
CREATE INDEX IF NOT EXISTS idx_consent_records_type ON consent_records(consent_type, status);

-- Legacy Consents Table (Kept for backwards compatibility)
CREATE TABLE IF NOT EXISTS consents (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  purpose TEXT NOT NULL,
  notice_version TEXT NOT NULL DEFAULT '1.0',
  audio_consent_recorded INTEGER NOT NULL DEFAULT 1,
  voice_retention_choice TEXT CHECK(voice_retention_choice IN ('do_not_keep', 'keep_for_quality')) NOT NULL DEFAULT 'do_not_keep',
  dpdp_affirmative_consent INTEGER NOT NULL DEFAULT 1,
  timestamp TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_consents_beneficiary ON consents(beneficiary_id);

-- 4. Conversational Interview Sessions Table (A3 State Machine)
CREATE TABLE IF NOT EXISTS interview_sessions (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT,
  session_id TEXT,
  channel TEXT CHECK(channel IN ('web_app', 'kiosk', 'whatsapp', 'ivr')) NOT NULL DEFAULT 'web_app',
  status TEXT CHECK(status IN ('not_started', 'collecting', 'awaiting_confirmation', 'ready_for_matching', 'recommendations_generated', 'referred', 'completed', 'in_progress', 'profile_extracted', 'confirmed', 'abandoned')) NOT NULL DEFAULT 'not_started',
  current_question_index INTEGER NOT NULL DEFAULT 0,
  last_question TEXT,
  language TEXT NOT NULL DEFAULT 'hi',
  transcript_history TEXT NOT NULL DEFAULT '[]', -- JSON array of InterviewTurn objects
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interview_sessions_beneficiary ON interview_sessions(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_session ON interview_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);

-- 5. Interview Turns Table (A3 Field Provenance & State)
CREATE TABLE IF NOT EXISTS interview_turns (
  id TEXT PRIMARY KEY,
  interview_id TEXT NOT NULL,
  turn_index INTEGER NOT NULL,
  speaker TEXT CHECK(speaker IN ('user', 'ai', 'system')) NOT NULL,
  text TEXT NOT NULL,
  mode TEXT CHECK(mode IN ('standard', 'guided_fallback', 'clarification')) NOT NULL DEFAULT 'standard',
  extracted_fields TEXT DEFAULT '{}',
  created_at TEXT NOT NULL,
  FOREIGN KEY (interview_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_turns_interview ON interview_turns(interview_id);

-- 6. Profile Field Values Table (A3 Provenance & Confirmation Status)
CREATE TABLE IF NOT EXISTS profile_field_values (
  id TEXT PRIMARY KEY,
  interview_id TEXT NOT NULL,
  beneficiary_id TEXT,
  field_name TEXT NOT NULL,
  field_value TEXT NOT NULL,
  source TEXT CHECK(source IN ('user', 'ai_inferred', 'counselor', 'system')) NOT NULL DEFAULT 'ai_inferred',
  confidence REAL NOT NULL DEFAULT 1.0,
  user_confirmed INTEGER NOT NULL DEFAULT 0,
  previous_value TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (interview_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_field_values_interview ON profile_field_values(interview_id);
CREATE INDEX IF NOT EXISTS idx_field_values_field ON profile_field_values(field_name);

-- 7. Profile Revisions Table
CREATE TABLE IF NOT EXISTS profile_revisions (
  id TEXT PRIMARY KEY,
  interview_id TEXT NOT NULL,
  revision_number INTEGER NOT NULL DEFAULT 1,
  profile_snapshot TEXT NOT NULL, -- JSON
  created_by TEXT NOT NULL DEFAULT 'user',
  created_at TEXT NOT NULL,
  FOREIGN KEY (interview_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_revisions_interview ON profile_revisions(interview_id);

-- Legacy Profile Answers Table (Kept for backwards compatibility)
CREATE TABLE IF NOT EXISTS profile_answers (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  session_id TEXT,
  field_name TEXT NOT NULL,
  field_value TEXT NOT NULL,
  confidence_score REAL NOT NULL DEFAULT 1.0,
  confirmation_status TEXT CHECK(confirmation_status IN ('unconfirmed', 'confirmed', 'corrected')) NOT NULL DEFAULT 'unconfirmed',
  source TEXT CHECK(source IN ('voice_extraction', 'beneficiary_edit', 'worker_correction')) NOT NULL DEFAULT 'voice_extraction',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
  FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_profile_answers_beneficiary ON profile_answers(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_profile_answers_field ON profile_answers(field_name);

-- 8. Verified NQR Qualification Catalogue (A4 Closed Official Catalogue)
CREATE TABLE IF NOT EXISTS qualifications (
  id TEXT PRIMARY KEY,
  nqr_code TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  sector TEXT NOT NULL,
  nsqf_level INTEGER NOT NULL,
  duration_hours INTEGER NOT NULL,
  min_education TEXT NOT NULL,
  min_education_rank INTEGER NOT NULL, -- 0: None, 1: 5th, 2: 8th, 3: 10th, 4: 12th, 5: Degree
  work_type TEXT CHECK(work_type IN ('wage', 'self_employment', 'both')) NOT NULL,
  physical_intensity TEXT CHECK(physical_intensity IN ('light', 'medium', 'medium_high', 'high')) NOT NULL DEFAULT 'light',
  skills_acquired TEXT NOT NULL, -- JSON array of strings
  curriculum_summary TEXT NOT NULL,
  entry_criteria TEXT NOT NULL,
  certification_body TEXT NOT NULL,
  nqr_link TEXT NOT NULL,
  official_source_url TEXT,
  verification_status TEXT CHECK(verification_status IN ('verified', 'pending', 'deprecated')) NOT NULL DEFAULT 'verified',
  verification_date TEXT NOT NULL,
  last_verified_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_qualifications_sector ON qualifications(sector);
CREATE INDEX IF NOT EXISTS idx_qualifications_nsqf ON qualifications(nsqf_level);
CREATE INDEX IF NOT EXISTS idx_qualifications_work_type ON qualifications(work_type);

-- 9. Maintained Dated Local Opportunities Table (A4 Separated Local Batches & Seats)
CREATE TABLE IF NOT EXISTS local_opportunities (
  id TEXT PRIMARY KEY,
  qualification_id TEXT NOT NULL,
  centre_or_employer_name TEXT NOT NULL,
  type TEXT CHECK(type IN ('training_centre', 'employer_apprenticeship', 'enterprise_cluster', 'job', 'self_employment_support', 'other')) NOT NULL DEFAULT 'training_centre',
  district TEXT NOT NULL,
  block TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'Uttar Pradesh',
  address TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  batch_start_date TEXT NOT NULL,
  batch_end_date TEXT NOT NULL,
  total_seats INTEGER NOT NULL DEFAULT 30,
  available_seats INTEGER NOT NULL DEFAULT 15,
  sc_reserved_seats INTEGER NOT NULL DEFAULT 10,
  batch_status TEXT CHECK(batch_status IN ('active', 'upcoming', 'full', 'completed', 'cancelled')) NOT NULL DEFAULT 'active',
  availability TEXT CHECK(availability IN ('verified_open', 'unknown', 'expired', 'closed')) NOT NULL DEFAULT 'verified_open',
  hostel_available INTEGER NOT NULL DEFAULT 0,
  stipend_amount_inr INTEGER NOT NULL DEFAULT 0,
  free_toolkit_provided INTEGER NOT NULL DEFAULT 1,
  source TEXT NOT NULL DEFAULT 'pm_ajay_portal',
  source_url TEXT,
  contact_details TEXT,
  is_archived INTEGER NOT NULL DEFAULT 0,
  verified_by_worker_id TEXT,
  verified_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (qualification_id) REFERENCES qualifications(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_local_opps_location ON local_opportunities(district, block);
CREATE INDEX IF NOT EXISTS idx_local_opps_status ON local_opportunities(batch_status);
CREATE INDEX IF NOT EXISTS idx_local_opps_avail ON local_opportunities(availability);
CREATE INDEX IF NOT EXISTS idx_local_opps_qual ON local_opportunities(qualification_id);

-- 10. Evidence Sources Table (A4 Evidence Tracking)
CREATE TABLE IF NOT EXISTS evidence_sources (
  id TEXT PRIMARY KEY,
  qualification_id TEXT,
  local_opportunity_id TEXT,
  source_type TEXT NOT NULL, -- nqr_portal, pm_ajay_portal, dsc_portal, field_verification
  source_url TEXT NOT NULL,
  title TEXT NOT NULL,
  verified_by TEXT NOT NULL,
  verification_date TEXT NOT NULL,
  evidence_note TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (qualification_id) REFERENCES qualifications(id) ON DELETE CASCADE,
  FOREIGN KEY (local_opportunity_id) REFERENCES local_opportunities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_evidence_qual ON evidence_sources(qualification_id);
CREATE INDEX IF NOT EXISTS idx_evidence_opp ON evidence_sources(local_opportunity_id);

-- 11. Grounded Recommendations Table (A5 Deterministic Matching & Provenance)
CREATE TABLE IF NOT EXISTS recommendations (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT,
  session_id TEXT,
  interview_id TEXT,
  qualification_id TEXT NOT NULL,
  local_opportunity_id TEXT,
  rank INTEGER NOT NULL,
  score REAL NOT NULL,
  score_breakdown TEXT NOT NULL, -- JSON
  match_state TEXT CHECK(match_state IN ('Interest Match', 'Verified Match')) NOT NULL DEFAULT 'Interest Match',
  explanation_text TEXT NOT NULL,
  audio_explanation_script TEXT NOT NULL,
  tradeoff_summary TEXT NOT NULL,
  skill_gap_summary TEXT NOT NULL,
  data_snapshot TEXT NOT NULL, -- JSON
  ranking_factors TEXT, -- JSON
  hard_constraint_result TEXT, -- JSON
  matched_skills TEXT, -- JSON array
  skill_gaps TEXT, -- JSON array
  local_opportunity_status TEXT NOT NULL DEFAULT 'unknown', -- verified_open, unknown, expired, closed
  caveat TEXT DEFAULT 'This is a guidance recommendation, not confirmation of admission or placement.',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
  FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE SET NULL,
  FOREIGN KEY (qualification_id) REFERENCES qualifications(id) ON DELETE RESTRICT,
  FOREIGN KEY (local_opportunity_id) REFERENCES local_opportunities(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_recommendations_beneficiary ON recommendations(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_interview ON recommendations(interview_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_state ON recommendations(match_state);

-- 12. Counselor Referral Cases Table (A7 Counselor Referral Lifecycle)
CREATE TABLE IF NOT EXISTS referral_cases (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT,
  interview_id TEXT,
  recommendation_id TEXT,
  local_opportunity_id TEXT,
  referral_reason TEXT CHECK(referral_reason IN ('no_verified_local_option', 'user_requested_human_help', 'accessibility_support_required', 'complex_eligibility_query', 'low_confidence_profile', 'technical_issue')) NOT NULL,
  consent_verification_state TEXT NOT NULL DEFAULT 'verified',
  assigned_counselor_id TEXT,
  status TEXT CHECK(status IN ('new', 'assigned', 'contacted', 'in_progress', 'resolved', 'closed')) NOT NULL DEFAULT 'new',
  priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) NOT NULL DEFAULT 'medium',
  follow_up_date TEXT,
  outcome TEXT,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
  FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE SET NULL,
  FOREIGN KEY (local_opportunity_id) REFERENCES local_opportunities(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_referral_cases_counselor ON referral_cases(assigned_counselor_id);
CREATE INDEX IF NOT EXISTS idx_referral_cases_status ON referral_cases(status);
CREATE INDEX IF NOT EXISTS idx_referral_cases_ben ON referral_cases(beneficiary_id);

-- 13. Counselor Notes Table
CREATE TABLE IF NOT EXISTS counselor_notes (
  id TEXT PRIMARY KEY,
  referral_case_id TEXT NOT NULL,
  counselor_id TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (referral_case_id) REFERENCES referral_cases(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_counselor_notes_case ON counselor_notes(referral_case_id);

-- Legacy Referrals Table (Kept for backwards compatibility)
CREATE TABLE IF NOT EXISTS referrals (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  recommendation_id TEXT NOT NULL,
  local_opportunity_id TEXT NOT NULL,
  assigned_worker_id TEXT NOT NULL,
  status TEXT CHECK(status IN ('pending', 'counselor_contacted', 'documents_verified', 'enrolled', 'rejected', 'ineligible')) NOT NULL DEFAULT 'pending',
  notes TEXT,
  caste_document_verified INTEGER NOT NULL DEFAULT 0,
  income_criteria_verified INTEGER NOT NULL DEFAULT 0,
  residence_proof_verified INTEGER NOT NULL DEFAULT 0,
  sms_sent INTEGER NOT NULL DEFAULT 0,
  whatsapp_sent INTEGER NOT NULL DEFAULT 0,
  next_follow_up TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
  FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE RESTRICT,
  FOREIGN KEY (local_opportunity_id) REFERENCES local_opportunities(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_referrals_worker ON referrals(assigned_worker_id);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status);

-- 14. Export Audits Table (A8 Privacy-Safe Summary Export)
CREATE TABLE IF NOT EXISTS export_audits (
  id TEXT PRIMARY KEY,
  interview_id TEXT,
  beneficiary_id TEXT,
  exported_by TEXT NOT NULL,
  export_type TEXT NOT NULL DEFAULT 'summary',
  consent_verified INTEGER NOT NULL DEFAULT 1,
  metadata TEXT DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_export_audits_ben ON export_audits(beneficiary_id);

-- 15. Post-Skilling & Livelihood Outcomes Table
CREATE TABLE IF NOT EXISTS outcomes (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  referral_id TEXT,
  enrolment_status TEXT CHECK(enrolment_status IN ('enrolled', 'completed', 'dropped_out')) NOT NULL DEFAULT 'enrolled',
  completion_status TEXT CHECK(completion_status IN ('in_progress', 'passed', 'failed', 'dropped_out')) NOT NULL DEFAULT 'in_progress',
  dropout_reason TEXT,
  employment_status TEXT CHECK(employment_status IN ('unemployed', 'wage_employed', 'self_employed', 'enterprise_started')) NOT NULL DEFAULT 'unemployed',
  employer_or_enterprise_name TEXT,
  monthly_income_inr REAL DEFAULT 0,
  toolkit_received INTEGER NOT NULL DEFAULT 0,
  seed_grant_applied INTEGER NOT NULL DEFAULT 0,
  follow_up_date TEXT,
  notes TEXT,
  recorded_by_worker_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
  FOREIGN KEY (referral_id) REFERENCES referrals(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_outcomes_beneficiary ON outcomes(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_employment ON outcomes(employment_status);

-- 16. District Planning Briefs Table (Layer 5)
CREATE TABLE IF NOT EXISTS planning_briefs (
  id TEXT PRIMARY KEY,
  district TEXT NOT NULL,
  period TEXT NOT NULL,
  total_beneficiaries_interviewed INTEGER NOT NULL,
  total_verified_matches INTEGER NOT NULL,
  total_supply_gaps INTEGER NOT NULL,
  aggregation_snapshot TEXT NOT NULL, -- JSON
  generated_narrative TEXT NOT NULL,
  suggested_policy_actions TEXT NOT NULL, -- JSON array
  reviewer_sign_off_status TEXT CHECK(reviewer_sign_off_status IN ('draft', 'under_review', 'signed_off', 'rejected')) NOT NULL DEFAULT 'draft',
  signed_off_by TEXT,
  signed_off_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_planning_briefs_district ON planning_briefs(district, period);

-- 17. Immutable Audit Events Ledger (Layer 3/4 Governance & State Invariant Auditing)
CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  actor_name TEXT NOT NULL,
  actor_role TEXT CHECK(actor_role IN ('beneficiary', 'field_worker', 'district_officer', 'counselor', 'system', 'admin')) NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  old_values TEXT, -- JSON
  new_values TEXT, -- JSON
  metadata TEXT, -- JSON
  timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_action ON audit_events(action);

-- 18. Drift & Bias Advisory Queue (Layer 6)
CREATE TABLE IF NOT EXISTS drift_advisories (
  id TEXT PRIMARY KEY,
  district TEXT NOT NULL,
  flag_type TEXT NOT NULL,
  severity TEXT CHECK(severity IN ('low', 'medium', 'high')) NOT NULL DEFAULT 'medium',
  headline TEXT NOT NULL,
  evidence TEXT NOT NULL, -- JSON
  suggested_human_action TEXT NOT NULL,
  status TEXT CHECK(status IN ('open', 'acknowledged', 'resolved')) NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_drift_district ON drift_advisories(district);
