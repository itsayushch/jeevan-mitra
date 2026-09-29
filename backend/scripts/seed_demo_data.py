import sqlite3
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Add backend dir to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import get_connection

def seed_demo_data():
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

    conn.commit()
    conn.close()
    print("Seed complete:")
    print(f"- Qualifications created: {len(quals)}")
    print(f"- Opportunities created: {len(opps)}")

if __name__ == '__main__':
    seed_demo_data()
