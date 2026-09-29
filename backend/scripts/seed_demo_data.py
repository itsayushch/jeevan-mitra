import sqlite3
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Add backend dir to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import get_connection, init_database

def seed_demand_records(conn, now):
    """
    Layer 5 demo data: ~200 synthetic ANONYMISED demand records across 5
    blocks of Moradabad. No name, contact, or free text - only qualification
    interest, block, mobility radius, work preference, and Verified Match
    outcome. Includes one clear planning gap: Bahjoi has 80 expressions of
    interest (incl. 38 for Mushroom Cultivation) but zero worker-verified
    batches; the nearest verified mushroom centre (KVK Chhajlet) is ~65 km away.
    """
    random.seed(42)

    # (block, qualification_id, count, had_verified_match)
    plan = [
        # Bahjoi: NO verified supply at all -> clear gap, nearest centre 40+ km
        ("Bahjoi", "qual_mushroom_07", 38, 0),
        ("Bahjoi", "qual_solar_01", 24, 0),
        ("Bahjoi", "qual_sewing_02", 18, 0),
        # Chhajlet: verified supply exists (mushroom 9, sewing 8, food 11 seats)
        ("Chhajlet", "qual_mushroom_07", 22, 1),
        ("Chhajlet", "qual_sewing_02", 16, 1),
        ("Chhajlet", "qual_food_04", 12, 1),
        # Moradabad Rural: verified supply exists (solar 14, retail 12, plumber 7 seats)
        ("Moradabad Rural", "qual_solar_01", 18, 1),
        ("Moradabad Rural", "qual_retail_06", 13, 1),
        ("Moradabad Rural", "qual_plumber_08", 7, 1),
        # Bilari: no verified supply
        ("Bilari", "qual_gda_09", 10, 0),
        ("Bilari", "qual_retail_06", 7, 0),
        # Kundarki: no verified supply
        ("Kundarki", "qual_sewing_02", 12, 0),
        ("Kundarki", "qual_food_04", 3, 0),
    ]

    work_preferences = ["wage", "self_employment", "both"]
    records = []
    for block, qual_id, count, had_match in plan:
        for _ in range(count):
            period = "FY 2026-27" if random.random() < 0.9 else "FY 2025-26"
            created = now - timedelta(days=random.randint(5, 360))
            records.append((
                f"syn_dem_{len(records):04d}", qual_id, "Moradabad", block,
                round(random.uniform(5.0, 30.0), 1),
                random.choice(work_preferences), had_match, period,
                created.isoformat(),
            ))

    conn.execute("DELETE FROM demand_records WHERE id LIKE 'syn_dem_%';")
    conn.executemany("""
        INSERT OR REPLACE INTO demand_records (
            id, qualification_id, district, block, mobility_radius_km,
            work_preference, had_verified_match, period, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, records)
    return len(records)

def seed_demo_data():
    init_database()
    conn = get_connection()
    now = datetime.now(timezone.utc)
    
    # Generate Synthetic Qualifications (10 records)
    quals = []
    for i in range(1, 15):
        is_stale = (i % 3 == 0)
        ver_date = (now - timedelta(days=200)).isoformat() if is_stale else (now - timedelta(days=10)).isoformat()
        quals.append((
            f'synth_qual_{i}', f'SYN/Q{i:04d}', f'[SYNTHETIC] Demo Qualification {i}', 'Demo Sector', 
            3 + (i%3), 200 + (i*10), f'Class {8 if i%2==0 else 10}', 2 if i%2==0 else 3, 
            'both', 'medium', json.dumps([f'Skill {i}A', f'Skill {i}B']), 
            f'Synthetic curriculum {i} for testing.', 'Basic requirements', 'Demo Certification Body',
            f'https://nqr.gov.in/synth/{i}', 'verified', ver_date
        ))

    conn.executemany("""
        INSERT OR REPLACE INTO qualifications (
            id, nqr_code, title, sector, nsqf_level, duration_hours,
            min_education, min_education_rank, work_type, physical_intensity,
            skills_acquired, curriculum_summary, entry_criteria, certification_body,
            nqr_link, verification_status, verification_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, quals)

    # Generate Synthetic Opportunities (10 records)
    opps = []
    statuses = ['verified_open', 'unknown', 'expired', 'closed']
    for i in range(1, 11):
        status = statuses[i % len(statuses)]
        is_stale = (i % 2 == 0)
        ver_date = (now - timedelta(days=40)).isoformat() if is_stale else (now - timedelta(days=5)).isoformat()
        
        opps.append((
            f'synth_opp_{i}', f'synth_qual_{i}', f'[SYNTHETIC] Demo Centre {i}', 'training_centre',
            'Moradabad', 'Moradabad Rural', f'Demo Address {i}', 28.8, 78.8,
            (now + timedelta(days=10)).isoformat(), (now + timedelta(days=100)).isoformat(),
            30, 15, 5, 'active', 0, 1000, 1, 'pm_ajay_portal', 'demo_worker', ver_date, now.isoformat(),
            status
        ))

    try:
        # Check if availability column exists before inserting
        cursor = conn.execute("PRAGMA table_info(local_opportunities)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'availability' in cols:
            conn.executemany("""
                INSERT OR REPLACE INTO local_opportunities (
                    id, qualification_id, centre_or_employer_name, type, district, block,
                    address, latitude, longitude, batch_start_date, batch_end_date,
                    total_seats, available_seats, sc_reserved_seats, batch_status,
                    hostel_available, stipend_amount_inr, free_toolkit_provided, source,
                    verified_by_worker_id, verified_at, created_at, availability
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, opps)
        else:
            conn.executemany("""
                INSERT OR REPLACE INTO local_opportunities (
                    id, qualification_id, centre_or_employer_name, type, district, block,
                    address, latitude, longitude, batch_start_date, batch_end_date,
                    total_seats, available_seats, sc_reserved_seats, batch_status,
                    hostel_available, stipend_amount_inr, free_toolkit_provided, source,
                    verified_by_worker_id, verified_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, [o[:-1] for o in opps])
    except sqlite3.OperationalError as e:
        print(f"Error inserting opps: {e}")

    demand_count = seed_demand_records(conn, now)

    conn.commit()
    conn.close()
    print("Seed complete:")
    print(f"- Qualifications created: {len(quals)}")
    print(f"- Opportunities created: {len(opps)}")
    print(f"- Anonymised demand records created: {demand_count}")

if __name__ == '__main__':
    seed_demo_data()
