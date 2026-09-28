import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.config import settings
from app.utils.logger import logger

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Ensure database schema is created and seeded."""
    logger.info(f"Initializing database at: {settings.DATABASE_PATH}")
    
    schema_path = Path(__file__).resolve().parent.parent / "src" / "database" / "schema.sql"
    with get_db() as conn:
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
        else:
            logger.warning("schema.sql not found, skipping migration execution")

        # Check if already seeded
        cursor = conn.execute("SELECT count(*) as count FROM qualifications;")
        count = cursor.fetchone()["count"]
        if count == 0:
            logger.info("Database empty, running initial seed...")
            seed_database(conn)
        else:
            logger.info(f"Database already contains {count} qualifications. Skipping initial seed.")

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
        )
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO qualifications (
            id, nqr_code, title, sector, nsqf_level, duration_hours,
            min_education, min_education_rank, work_type, physical_intensity,
            skills_acquired, curriculum_summary, entry_criteria, certification_body,
            nqr_link, verification_status, verification_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, quals)

    # 2. Local Opportunities (Dated batches)
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
        )
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO local_opportunities (
            id, qualification_id, centre_or_employer_name, type, district, block,
            address, latitude, longitude, batch_start_date, batch_end_date,
            total_seats, available_seats, sc_reserved_seats, batch_status,
            hostel_available, stipend_amount_inr, free_toolkit_provided, source,
            verified_by_worker_id, verified_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, opps)

    # 3. Seed Beneficiary (Rajesh Kumar)
    conn.execute("""
        INSERT OR IGNORE INTO beneficiaries (
            id, name, phone, gender, age, category, preferred_language,
            district, block, village, contact_preference, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        'ben_rajesh_kumar', 'Rajesh Kumar', '+919876543210', 'male', 22, 'SC',
        'hi', 'Moradabad', 'Chhajlet', 'Village Chhajlet', 'voice', now, now
    ))

    # 4. Seed Consent
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

    # 5. Seed Interview Session
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

    # 6. Seed Profile Answers
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

    # 7. Seed Referral
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

    # 8. Seed Planning Brief (District Moradabad)
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
