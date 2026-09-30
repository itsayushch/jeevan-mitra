import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
from app.config import settings
from app.utils.logger import logger
from app.db.session import get_db, DBWrapper

def get_connection() -> sqlite3.Connection:
    logger.warning("get_connection() is deprecated, use get_db() context manager")
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column_def: str, col_name: str):
    table_check = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,)).fetchone()
    if not table_check:
        return
    cursor = conn.execute(f"PRAGMA table_info({table});")
    existing_cols = [row["name"] for row in cursor.fetchall()]
    if col_name not in existing_cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_def};")

def run_migrations(conn: sqlite3.Connection):
    """Run incremental column migrations on existing tables."""
    # local_opportunities
    _add_column_if_missing(conn, "local_opportunities", "state TEXT NOT NULL DEFAULT 'Uttar Pradesh'", "state")
    _add_column_if_missing(conn, "local_opportunities", "availability TEXT DEFAULT 'verified_open'", "availability")
    _add_column_if_missing(conn, "local_opportunities", "source_url TEXT", "source_url")
    _add_column_if_missing(conn, "local_opportunities", "contact_details TEXT", "contact_details")
    _add_column_if_missing(conn, "local_opportunities", "is_archived INTEGER NOT NULL DEFAULT 0", "is_archived")

    # qualifications
    _add_column_if_missing(conn, "qualifications", "official_source_url TEXT", "official_source_url")
    _add_column_if_missing(conn, "qualifications", "last_verified_at TEXT", "last_verified_at")

    # recommendations
    _add_column_if_missing(conn, "recommendations", "interview_id TEXT", "interview_id")
    _add_column_if_missing(conn, "recommendations", "ranking_factors TEXT", "ranking_factors")
    _add_column_if_missing(conn, "recommendations", "hard_constraint_result TEXT", "hard_constraint_result")
    _add_column_if_missing(conn, "recommendations", "matched_skills TEXT", "matched_skills")
    _add_column_if_missing(conn, "recommendations", "skill_gaps TEXT", "skill_gaps")
    _add_column_if_missing(conn, "recommendations", "local_opportunity_status TEXT DEFAULT 'unknown'", "local_opportunity_status")
    _add_column_if_missing(conn, "recommendations", "caveat TEXT DEFAULT 'This is a guidance recommendation, not confirmation of admission or placement.'", "caveat")

    # beneficiaries
    _add_column_if_missing(conn, "beneficiaries", "owner_type TEXT DEFAULT 'authenticated_user'", "owner_type")
    _add_column_if_missing(conn, "beneficiaries", "owner_id TEXT", "owner_id")

    # users
    _add_column_if_missing(conn, "users", "preferred_language TEXT NOT NULL DEFAULT 'en'", "preferred_language")

    # interview_sessions
    _add_column_if_missing(conn, "interview_sessions", "session_id TEXT", "session_id")
    _add_column_if_missing(conn, "consent_records", "session_id TEXT", "session_id")
    _add_column_if_missing(conn, "referral_cases", "session_id TEXT", "session_id")

def init_database():
    """Ensure database schema is created via Alembic, migrated, and seeded."""
    logger.info(f"Initializing database at: {settings.DATABASE_URL}")
    import alembic.config
    import alembic.command
    
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = alembic.config.Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(alembic_ini.parent / "alembic"))
    
    # Use dynamic URL for test compatibility
    db_url = settings.DATABASE_URL
    if settings.DATABASE_PATH and db_url.startswith("sqlite") and "memory" not in db_url:
        db_path = Path(settings.DATABASE_PATH).absolute().as_posix()
        db_url = f"sqlite:///{db_path}"
    
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    
    if "memory" in db_url:
        from app.db.session import get_engine
        engine = get_engine()
        from alembic import context
        with engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            alembic.command.upgrade(alembic_cfg, "head")
    else:
        alembic.command.upgrade(alembic_cfg, "head")
        
    with get_db() as conn:
        logger.info("Database schema applied.")
        cols = conn.execute("PRAGMA table_info(audit_events);").fetchall()
        print(f"DEBUG: audit_events columns in {db_url}: {cols}")
        # Seed default values if empty
        check = conn.execute("SELECT COUNT(*) as count FROM qualifications;").fetchone()
        if check and check['count'] == 0:
            seed_database(conn)


def seed_database(conn: sqlite3.Connection):
    now = datetime.now(timezone.utc).isoformat()
    
    # 1. Qualifications
    quals = [
        (
            'qual_solar_01', 'SGJ/Q0101', 'Solar PV Installer (Suryamitra)', 'Green Energy', 4, 320,
            'Class 10', 3, 'wage', 'medium_high',
            json.dumps(['Solar PV Installation', 'Electrical Inverter Wiring', 'Rooftop Mounts', 'Grid Safety']),
            'Comprehensive rooftop solar PV installation, electrical connection, and routine fault diagnosis.',
            'Class 10th standard pass or ITI electrical pass', 'Skill Council for Green Jobs (SCGJ)',
            'https://nqr.gov.in/qualifications/SGJ-Q0101', 'verified', '2026-01-15'
        ),
        (
            'qual_sewing_02', 'AMH/Q0301', 'Sewing Machine Operator', 'Apparel', 2, 210,
            'Class 5', 1, 'self_employment', 'light',
            json.dumps(['Garment Stitching', 'Sewing Machine Operation', 'Pattern Cutting', 'Finishing & Quality']),
            'Industrial and domestic sewing machine operation, standard seam stitching, garment construction.',
            'Ability to read and write (Class 5 preferred)', 'Apparel Made-Ups & Home Furnishing Sector Skill Council',
            'https://nqr.gov.in/qualifications/AMH-Q0301', 'verified', '2026-01-20'
        ),
        (
            'qual_elec_03', 'ELE/Q5801', 'Assistant Electrician', 'Electronics', 3, 350,
            'Class 8', 2, 'both', 'medium',
            json.dumps(['Domestic Wiring', 'Conduit Installation', 'Earthing & Fuse Repair', 'Safety Protocols']),
            'Laying domestic circuits, installation of light points, test equipment usage, and safety regulations.',
            'Class 8th standard pass', 'Electronics Sector Skills Council of India',
            'https://nqr.gov.in/qualifications/ELE-Q5801', 'verified', '2026-02-01'
        ),
        (
            'qual_food_04', 'FIC/Q9001', 'Small Fruit & Agro Processing Entrepreneur', 'Food Processing', 4, 240,
            'Class 8', 2, 'self_employment', 'light',
            json.dumps(['Pickle & Jam Processing', 'FSSAI Hygiene Standards', 'Packaging & Labeling', 'Costing & Accounts']),
            'Value addition to perishable farm produce, hygiene compliance, cottage packaging, and mandi linkage.',
            'Class 8th pass with interest in food micro-enterprise', 'Food Industry Capacity & Skill Initiative (FICSI)',
            'https://nqr.gov.in/qualifications/FIC-Q9001', 'verified', '2026-02-10'
        ),
        (
            'qual_tractor_05', 'ASC/Q1901', 'Tractor Mechanic & Service Assistant', 'Agriculture', 4, 300,
            'Class 8', 2, 'both', 'high',
            json.dumps(['Diesel Engine Overhaul', 'Hydraulics Inspection', 'Transmission & Brakes', 'Farm Implement Hitching']),
            'Routine servicing and overhaul of agricultural tractors, diesel engines, and power tillers.',
            'Class 8th pass with mechanical aptitude', 'Agriculture Skill Council of India (ASCI)',
            'https://nqr.gov.in/qualifications/ASC-Q1901', 'verified', '2026-02-15'
        ),
        (
            'qual_retail_06', 'RAS/Q0102', 'Retail Sales Associate', 'Retail', 3, 200,
            'Class 10', 3, 'wage', 'light',
            json.dumps(['Customer Assistance', 'Point-of-Sale (POS) Billing', 'Inventory Tagging', 'Visual Merchandising']),
            'Frontline retail sales, POS machine operations, inventory handling, and customer dispute resolution.',
            'Class 10th standard pass with basic numeracy', 'Retailers Association\'s Skill Council of India (RASCI)',
            'https://nqr.gov.in/qualifications/RAS-Q0102', 'verified', '2026-02-20'
        ),
        (
            'qual_mushroom_07', 'AGR/Q7803', 'Mushroom Cultivator (Button & Oyster)', 'Agriculture', 4, 200,
            'Class 8', 2, 'self_employment', 'medium',
            json.dumps(['Spawn Substrate Preparation', 'Moisture & Humidity Controls', 'Harvesting & Grading', 'Mandi Packaging']),
            'Commercial production of button and oyster mushrooms using climate-controlled spawn bags.',
            'Class 8th pass with farming interest', 'Agriculture Skill Council of India (ASCI)',
            'https://nqr.gov.in/qualifications/AGR-Q7803', 'verified', '2026-02-25'
        ),
        (
            'qual_plumber_08', 'PSC/Q0104', 'General Plumber', 'Plumbing', 3, 240,
            'Class 8', 2, 'both', 'medium_high',
            json.dumps(['Pipe Cutting & Threading', 'Sanitary Fixture Installation', 'Drainage Maintenance', 'Leak Detection']),
            'Installation and maintenance of domestic and commercial piping systems and sanitary fixtures.',
            'Class 8th standard pass', 'Plumbing Sector Skill Council',
            'https://nqr.gov.in/qualifications/PSC-Q0104', 'verified', '2026-02-28'
        ),
        (
            'qual_gda_09', 'HSS/Q5101', 'General Duty Assistant (GDA)', 'Healthcare', 4, 360,
            'Class 10', 3, 'wage', 'medium',
            json.dumps(['Patient Vital Monitoring', 'Infection Control', 'Bedside Care & Hygiene', 'Emergency Response']),
            'Patient support services under nursing supervision in hospitals, clinics, and eldercare centres.',
            'Class 10th standard pass', 'Healthcare Sector Skill Council',
            'https://nqr.gov.in/qualifications/HSS-Q5101', 'verified', '2026-03-01'
        ),
        (
            'qual_dataentry_10', 'SSC/Q2212', 'Domestic Data Entry Operator', 'IT-ITeS', 4, 200,
            'Class 10', 3, 'wage', 'light',
            json.dumps(['Touch Typing (30 WPM)', 'MS Excel & Office Basics', 'Data Confidentiality', 'Quality Verification']),
            'Accurate alphabetic and numeric data entry, documentation, and digital record keeping.',
            'Class 10th standard pass', 'IT-ITeS SSC (NASSCOM)',
            'https://nqr.gov.in/qualifications/SSC-Q2212', 'verified', '2026-03-05'
        ),
        (
            'qual_beauty_11', 'BWS/Q0102', 'Assistant Beauty Therapist', 'Beauty & Wellness', 3, 220,
            'Class 8', 2, 'both', 'light',
            json.dumps(['Skin Care & Cleansing', 'Manicure & Pedicure', 'Basic Makeup Application', 'Salon Hygiene']),
            'Basic skincare, beauty treatments, and customer care in salons or home visits.',
            'Class 8th standard pass', 'Beauty & Wellness Sector Skill Council',
            'https://nqr.gov.in/qualifications/BWS-Q0102', 'verified', '2026-03-10'
        ),
        (
            'qual_welder_12', 'CSC/Q0204', 'Manual Metal Arc Welder (SMAW)', 'Capital Goods', 3, 300,
            'Class 8', 2, 'wage', 'high',
            json.dumps(['SMAW Welding Joints', 'Safety & PPE Usage', 'Gas Cutting Basics', 'Weld Defect Inspection']),
            'Structural and pipe welding using shielded metal arc welding techniques.',
            'Class 8th standard pass', 'Capital Goods Skill Council',
            'https://nqr.gov.in/qualifications/CSC-Q0204', 'verified', '2026-03-12'
        )
    ]

    qual_rows = []
    for q in quals:
        (
            qid, nqr_code, title, sector, nsqf_level, duration_hours,
            min_education, min_education_rank, work_type, physical_intensity,
            skills_acquired, curriculum_summary, entry_criteria, certification_body,
            nqr_link, verification_status, verification_date
        ) = q
        entry_req = json.dumps({"min_education": min_education, "entry_criteria": entry_criteria})
        v_status = 'VERIFIED' if verification_status.lower() == 'verified' else verification_status
        qual_rows.append((
            qid, nqr_code, nqr_code, title, curriculum_summary, sector, nsqf_level, duration_hours,
            entry_req, skills_acquired, min_education, min_education_rank, work_type, physical_intensity,
            skills_acquired, curriculum_summary, entry_criteria, certification_body, nqr_link,
            certification_body, nqr_link, '1.0', f"{verification_date}T00:00:00Z",
            v_status, verification_date, now, now
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO qualifications (
            id, external_reference, nqr_code, title, description, sector, nsqf_level, duration_hours,
            entry_requirements_json, skills_json, min_education, min_education_rank, work_type, physical_intensity,
            skills_acquired, curriculum_summary, entry_criteria, certification_body, nqr_link,
            source_name, source_url, source_version, source_verified_at, verification_status,
            verification_date, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, qual_rows)

    # 2. Opportunity Providers
    providers = [
        ('prov_solar_moradabad_01', 'training_centre', 'Govt ITI Moradabad Training Centre', 'Moradabad', 'Moradabad Rural', 28.8386, 78.7733, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_sewing_chhajlet_02', 'training_centre', 'Pradhan Mantri Kaushal Kendra Chhajlet', 'Moradabad', 'Chhajlet', 28.9856, 78.6811, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_food_chhajlet_04', 'enterprise_cluster', 'Chhajlet Agro-Processing Enterprise Cluster', 'Moradabad', 'Chhajlet', 28.9800, 78.6900, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_retail_moradabad_06', 'training_centre', 'Skill India Hub Moradabad Civil Lines', 'Moradabad', 'Moradabad Rural', 28.8400, 78.7800, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_mushroom_chhajlet_07', 'training_centre', 'Krishi Vigyan Kendra Mushroom Training Unit', 'Moradabad', 'Chhajlet', 28.9870, 78.6850, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_gda_moradabad_09', 'training_centre', 'District Hospital Allied Healthcare Training Cell', 'Moradabad', 'Moradabad Urban', 28.8350, 78.7750, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_plumber_moradabad_08', 'training_centre', 'Jan Shikshan Sansthan Moradabad', 'Moradabad', 'Moradabad Rural', 28.8200, 78.7200, 'ACTIVE', 'pm_ajay_portal', now, now),
        ('prov_dataentry_ghaziabad_10', 'training_centre', 'Ghaziabad Skill Development Center', 'Ghaziabad', 'Ghaziabad Urban', 28.6700, 77.4400, 'ACTIVE', 'pm_ajay_portal', now, now)
    ]
    conn.executemany("""
        INSERT OR IGNORE INTO opportunity_providers (
            id, provider_type, name, district_id, block_id, latitude, longitude, status, source_name, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, providers)

    # 3. Local Opportunities (Dated batches)
    opps = [
        (
            'opp_solar_moradabad_01', 'qual_solar_01', 'Govt ITI Moradabad Training Centre', 'training_centre',
            'Moradabad', 'Moradabad Rural', 'Kanth Road, Near RTO, Moradabad, UP', 28.8386, 78.7733,
            '2026-10-15', '2027-01-15', 30, 14, 10, 'upcoming', 0, 1500, 1, 'pm_ajay_portal', 'worker_sunita_01', '2026-09-10', now
        ),
        (
            'opp_sewing_chhajlet_02', 'qual_sewing_02', 'Pradhan Mantri Kaushal Kendra Chhajlet', 'training_centre',
            'Moradabad', 'Chhajlet', 'Main Market, Block Office Road, Chhajlet, UP', 28.9856, 78.6811,
            '2026-10-01', '2026-12-15', 25, 8, 8, 'active', 0, 1000, 1, 'pm_ajay_portal', 'worker_sunita_01', '2026-09-12', now
        ),
        (
            'opp_food_chhajlet_04', 'qual_food_04', 'Chhajlet Agro-Processing Enterprise Cluster', 'enterprise_cluster',
            'Moradabad', 'Chhajlet', 'Village Raipur, Post Chhajlet, UP', 28.9800, 78.6900,
            '2026-10-20', '2026-12-30', 20, 11, 7, 'upcoming', 0, 1200, 1, 'pm_ajay_portal', 'worker_sunita_01', '2026-09-15', now
        ),
        (
            'opp_retail_moradabad_06', 'qual_retail_06', 'Skill India Hub Moradabad Civil Lines', 'training_centre',
            'Moradabad', 'Moradabad Rural', 'Civil Lines, Near Railway Station, Moradabad', 28.8400, 78.7800,
            '2026-10-05', '2026-12-10', 35, 12, 12, 'active', 0, 1500, 0, 'pm_ajay_portal', 'worker_amit_02', '2026-09-08', now
        ),
        (
            'opp_mushroom_chhajlet_07', 'qual_mushroom_07', 'Krishi Vigyan Kendra Mushroom Training Unit', 'training_centre',
            'Moradabad', 'Chhajlet', 'KVK Campus, Chhajlet-Kanth Road, Moradabad', 28.9870, 78.6850,
            '2026-10-10', '2027-01-10', 25, 9, 8, 'active', 0, 1500, 1, 'pm_ajay_portal', 'worker_sunita_01', '2026-09-14', now
        ),
        (
            'opp_gda_moradabad_09', 'qual_gda_09', 'District Hospital Allied Healthcare Training Cell', 'training_centre',
            'Moradabad', 'Moradabad Urban', 'Civil Hospital Road, Moradabad', 28.8350, 78.7750,
            '2026-10-25', '2027-02-25', 20, 10, 8, 'upcoming', 1, 2000, 1, 'pm_ajay_portal', 'worker_sunita_01', '2026-09-20', now
        ),
        (
            'opp_plumber_moradabad_08', 'qual_plumber_08', 'Jan Shikshan Sansthan Moradabad', 'training_centre',
            'Moradabad', 'Moradabad Rural', 'Pakbara Highway, Moradabad', 28.8200, 78.7200,
            '2026-10-12', '2026-12-20', 25, 7, 7, 'active', 0, 1200, 1, 'pm_ajay_portal', 'worker_amit_02', '2026-09-18', now
        ),
        (
            'opp_dataentry_ghaziabad_10', 'qual_dataentry_10', 'Ghaziabad Skill Development Center', 'training_centre',
            'Ghaziabad', 'Ghaziabad Urban', 'RDC Raj Nagar, Ghaziabad', 28.6700, 77.4400,
            '2026-10-15', '2026-12-15', 30, 15, 10, 'upcoming', 0, 1500, 0, 'pm_ajay_portal', 'worker_amit_02', '2026-09-19', now
        )
    ]

    opp_rows = []
    for op_item in opps:
        (
            opp_id, qid, centre_name, otype,
            dist, blk, addr, lat, lon,
            b_start, b_end, t_seats, a_seats, sc_seats, b_status,
            hostel, stipend, toolkit, src, v_worker, v_at, c_at
        ) = op_item
        prov_id = f"prov_{opp_id.split('opp_')[1]}"
        status_map = 'ACTIVE' if b_status in ('active', 'upcoming') else ('FULL' if b_status == 'full' else 'CLOSED')
        expires_at = "2027-12-31T23:59:59Z"
        opp_rows.append((
            opp_id, qid, prov_id, otype, centre_name, f"Batch for {centre_name}",
            dist, blk, dist, blk, centre_name, otype, addr, lat, lon, addr,
            'offline_centre', b_start, b_end, b_start, b_end,
            t_seats, a_seats, t_seats, a_seats, sc_seats,
            stipend, stipend, toolkit, hostel,
            src, status_map, b_status, v_worker, v_at, expires_at, c_at, c_at
        ))

    conn.executemany("""
        INSERT OR IGNORE INTO local_opportunities (
            id, qualification_id, provider_id, opportunity_type, title, summary,
            district_id, block_id, district, block, centre_or_employer_name, type, address, latitude, longitude, location_text,
            delivery_mode, start_date, end_date, batch_start_date, batch_end_date,
            seats_total, seats_available, total_seats, available_seats, sc_reserved_seats,
            stipend_amount, stipend_amount_inr, free_toolkit_provided, hostel_available,
            source, status, batch_status, verified_by_worker_id, verified_at, verification_expires_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, opp_rows)

    # 4. Seed Beneficiary (Rajesh Kumar)
    conn.execute("""
        INSERT OR IGNORE INTO beneficiaries (
            id, name, phone, gender, age, category, preferred_language,
            district, block, village, contact_preference, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'ben_rajesh_kumar', 'Rajesh Kumar', '+919876543210', 'male', 22, 'SC',
        'hi', 'Moradabad', 'Chhajlet', 'Village Chhajlet', 'voice', now, now
    ))

    # 5. Seed Consent
    conn.execute("""
        INSERT OR IGNORE INTO consents (
            id, beneficiary_id, purpose, notice_version, audio_consent_recorded,
            voice_retention_choice, dpdp_affirmative_consent, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'consent_ben_rajesh_01', 'ben_rajesh_kumar',
        'PM-AJAY GIA Livelihood Matching and Training Guidance',
        '1.0', 1, 'do_not_keep', 1, now
    ))

    conn.execute("""
        INSERT OR IGNORE INTO consent_records (
            id, session_id, beneficiary_id, consent_type, policy_version, status, user_language, capture_channel, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'cr_ben_rajesh_01', 'sess_rajesh_01', 'ben_rajesh_kumar', 'ai_processing', '1.0', 'granted', 'hi', 'web_app', now
    ))

    # 6. Seed Interview Session
    conn.execute("""
        INSERT OR IGNORE INTO interview_sessions (
            id, beneficiary_id, channel, status, current_question_index,
            last_question, language, transcript_history, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'sess_rajesh_01', 'ben_rajesh_kumar', 'web_app', 'completed', 8,
        'Do you prefer wage employment or self-employment?', 'hi',
        json.dumps([
            {'speaker': 'ai', 'text': 'Tell me about your studies.'},
            {'speaker': 'user', 'text': 'I have passed 10th class.'},
            {'speaker': 'ai', 'text': 'What traditional or family skills do you have?'},
            {'speaker': 'user', 'text': 'My family does farming and pottery.'}
        ]), now, now
    ))

    # 7. Seed Profile Answers
    answers = [
        ('ans_1', 'ben_rajesh_kumar', 'sess_rajesh_01', 'education_level', 'Class 10 Pass', 0.95, 'confirmed', 'voice_extraction', now, now),
        ('ans_2', 'ben_rajesh_kumar', 'sess_rajesh_01', 'interests', json.dumps(['Farming', 'Agri-Business', 'Repair work']), 0.90, 'confirmed', 'voice_extraction', now, now),
        ('ans_3', 'ben_rajesh_kumar', 'sess_rajesh_01', 'mobility_radius_km', '5', 0.92, 'confirmed', 'voice_extraction', now, now),
        ('ans_4', 'ben_rajesh_kumar', 'sess_rajesh_01', 'work_preference', 'self_employment', 0.88, 'confirmed', 'voice_extraction', now, now),
        ('ans_5', 'ben_rajesh_kumar', 'sess_rajesh_01', 'family_trades', json.dumps(['Farming', 'Pottery']), 0.94, 'confirmed', 'voice_extraction', now, now)
    ]
    conn.executemany("""
        INSERT OR IGNORE INTO profile_answers (
            id, beneficiary_id, session_id, field_name, field_value,
            confidence_score, confirmation_status, source, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, answers)

    # 8. Seed Recommendation
    conn.execute("""
        INSERT OR IGNORE INTO recommendations (
            id, beneficiary_id, session_id, interview_id, qualification_id, local_opportunity_id,
            rank, score, score_breakdown, match_state, explanation_text,
            audio_explanation_script, tradeoff_summary, skill_gap_summary,
            data_snapshot, ranking_factors, hard_constraint_result, matched_skills, skill_gaps,
            local_opportunity_status, caveat, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'rec_seed_01', 'ben_rajesh_kumar', 'sess_rajesh_01', 'sess_rajesh_01',
        'qual_mushroom_07', 'opp_mushroom_chhajlet_07', 1, 0.91,
        json.dumps({'interest': 0.95, 'skills': 0.85, 'access': 0.90, 'demand': 0.85, 'preference': 1.0}),
        'Verified Match',
        'Mushroom cultivation aligns with your farming interests and self-employment preference.',
        'This mushroom cultivation pathway matches your farming interests.',
        'The training is nearby and supports self-employment.',
        'Practical cultivation experience may help build on your existing farming skills.',
        json.dumps({'qualification_id': 'qual_mushroom_07', 'opportunity_id': 'opp_mushroom_chhajlet_07'}),
        json.dumps({'interest': 0.95, 'skills': 0.85, 'access': 0.90, 'demand': 0.85, 'preference': 1.0}),
        json.dumps({'passed': True}),
        json.dumps(['Compost Preparation', 'Spawning']),
        json.dumps(['Cropping Management', 'Harvesting']),
        'verified_open',
        'This is a guidance recommendation, not confirmation of admission or placement.',
        now, now
    ))

    # 9. Seed Referral
    conn.execute("""
        INSERT OR IGNORE INTO referrals (
            id, beneficiary_id, recommendation_id, local_opportunity_id, assigned_worker_id,
            status, notes, caste_document_verified, income_criteria_verified, residence_proof_verified,
            sms_sent, whatsapp_sent, next_follow_up, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'ref_rajesh_01', 'ben_rajesh_kumar', 'rec_seed_01', 'opp_mushroom_chhajlet_07', 'worker_sunita_01',
        'documents_verified', 'Verified resident of Chhajlet. SC Certificate valid.', 1, 1, 1, 1, 1,
        '2026-10-05', now, now
    ))

    conn.execute("""
        INSERT OR IGNORE INTO referral_cases (
            id, beneficiary_id, interview_id, recommendation_id, local_opportunity_id,
            referral_reason, consent_verification_state, assigned_counselor_id, status, priority,
            follow_up_date, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'verified', 'worker_sunita_01', 'assigned', 'medium', '2026-10-05', 'Verified resident of Chhajlet. SC Certificate valid.', ?, ?);
    """, (
        'case_rajesh_01', 'ben_rajesh_kumar', 'sess_rajesh_01', 'rec_seed_01', 'opp_mushroom_chhajlet_07',
        'user_requested_human_help', now, now
    ))

    # 10. Seed Planning Brief (District Moradabad)
    conn.execute("""
        INSERT OR IGNORE INTO planning_briefs (
            id, district, period, total_beneficiaries_interviewed, total_verified_matches,
            total_supply_gaps, aggregation_snapshot, generated_narrative, suggested_policy_actions,
            reviewer_sign_off_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'brief_moradabad_fy26', 'Moradabad', 'FY 2026-27', 1840, 1410, 430,
        json.dumps({
            'trades': [
                {'trade': 'Mushroom Cultivation', 'demand': 460, 'capacity': 120, 'gap': -340},
                {'trade': 'Solar Technician', 'demand': 420, 'capacity': 120, 'gap': -300},
                {'trade': 'Apparel Making', 'demand': 510, 'capacity': 480, 'gap': -30},
                {'trade': 'Retail Sales', 'demand': 380, 'capacity': 200, 'gap': -180}
            ]
        }),
        'Analysis of 1,840 beneficiary voice interviews indicates acute deficit in Solar Installation and Mushroom cultivation training facilities within rural blocks.',
        json.dumps([
            'Deploy Mobile Skilling Unit for Block Bahjoi.',
            'Sanction 6 additional batches for Mushroom Cultivation at KVK Chhajlet.',
            'Expand PM Surya Ghar rooftop training seats by 300.'
        ]),
        'draft', now, now
    ))

    logger.info("Database seeding completed successfully.")
