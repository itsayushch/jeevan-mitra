-- ============================================================================
-- JEEVAN-MITRA 2.0 RELATIONAL DATABASE SCHEMA
-- Ministry of Social Justice & Empowerment (MoSJE) - PM-AJAY GIA Component
-- Schema supporting all 11 core tables & 6 AI layers
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
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_beneficiaries_district_block ON beneficiaries(district, block);
CREATE INDEX IF NOT EXISTS idx_beneficiaries_category ON beneficiaries(category);

-- 2. DPDP Act Compliant Consents Table
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

-- 3. Conversational Interview Sessions Table (Layer 1)
CREATE TABLE IF NOT EXISTS interview_sessions (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  channel TEXT CHECK(channel IN ('web_app', 'kiosk', 'whatsapp', 'ivr')) NOT NULL DEFAULT 'web_app',
  status TEXT CHECK(status IN ('in_progress', 'profile_extracted', 'confirmed', 'completed', 'abandoned')) NOT NULL DEFAULT 'in_progress',
  current_question_index INTEGER NOT NULL DEFAULT 0,
  last_question TEXT,
  language TEXT NOT NULL DEFAULT 'hi',
  transcript_history TEXT NOT NULL DEFAULT '[]', -- JSON array of InterviewTurn objects
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_interview_sessions_beneficiary ON interview_sessions(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON interview_sessions(status);

-- 4. Structured Profile Answers Table (Layer 2)
CREATE TABLE IF NOT EXISTS profile_answers (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  session_id TEXT,
  field_name TEXT NOT NULL,
  field_value TEXT NOT NULL, -- Stored as string or JSON
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

-- 5. Verified NQR Qualification Catalogue (Layer 3 Closed Document Set)
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
  verification_status TEXT CHECK(verification_status IN ('verified', 'pending', 'deprecated')) NOT NULL DEFAULT 'verified',
  verification_date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_qualifications_sector ON qualifications(sector);
CREATE INDEX IF NOT EXISTS idx_qualifications_nsqf ON qualifications(nsqf_level);
CREATE INDEX IF NOT EXISTS idx_qualifications_work_type ON qualifications(work_type);

-- 6. Maintained Dated Local Opportunities Table (Batches & Seats)
CREATE TABLE IF NOT EXISTS local_opportunities (
  id TEXT PRIMARY KEY,
  qualification_id TEXT NOT NULL,
  centre_or_employer_name TEXT NOT NULL,
  type TEXT CHECK(type IN ('training_centre', 'employer_apprenticeship', 'enterprise_cluster')) NOT NULL DEFAULT 'training_centre',
  district TEXT NOT NULL,
  block TEXT NOT NULL,
  address TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  batch_start_date TEXT NOT NULL,
  batch_end_date TEXT NOT NULL,
  total_seats INTEGER NOT NULL DEFAULT 30,
  available_seats INTEGER NOT NULL DEFAULT 15,
  sc_reserved_seats INTEGER NOT NULL DEFAULT 10,
  batch_status TEXT CHECK(batch_status IN ('active', 'upcoming', 'full', 'completed', 'cancelled')) NOT NULL DEFAULT 'active',
  hostel_available INTEGER NOT NULL DEFAULT 0,
  stipend_amount_inr INTEGER NOT NULL DEFAULT 0,
  free_toolkit_provided INTEGER NOT NULL DEFAULT 1,
  source TEXT NOT NULL DEFAULT 'pm_ajay_portal',
  verified_by_worker_id TEXT,
  verified_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (qualification_id) REFERENCES qualifications(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_local_opps_location ON local_opportunities(district, block);
CREATE INDEX IF NOT EXISTS idx_local_opps_status ON local_opportunities(batch_status);
CREATE INDEX IF NOT EXISTS idx_local_opps_qual ON local_opportunities(qualification_id);

-- 7. Grounded Recommendations Table (Layer 3 RAG & State Machine)
CREATE TABLE IF NOT EXISTS recommendations (
  id TEXT PRIMARY KEY,
  beneficiary_id TEXT NOT NULL,
  session_id TEXT,
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
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(id) ON DELETE CASCADE,
  FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE SET NULL,
  FOREIGN KEY (qualification_id) REFERENCES qualifications(id) ON DELETE RESTRICT,
  FOREIGN KEY (local_opportunity_id) REFERENCES local_opportunities(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_recommendations_beneficiary ON recommendations(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_state ON recommendations(match_state);

-- 8. Field-Worker Referrals Table (Layer 4)
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

-- 9. Post-Skilling & Livelihood Outcomes Table
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

-- 10. District Planning Briefs Table (Layer 5)
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

-- 11. Immutable Audit Events Ledger (Layer 3/4 Governance & State Invariant Auditing)
CREATE TABLE IF NOT EXISTS audit_events (
  id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  actor_name TEXT NOT NULL,
  actor_role TEXT CHECK(actor_role IN ('beneficiary', 'field_worker', 'district_officer', 'system')) NOT NULL,
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

-- 12. Drift & Bias Advisory Queue (Layer 6)
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
