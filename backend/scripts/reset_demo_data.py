import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.database import get_connection

def reset_demo_data():
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = OFF;")
    
    c6 = conn.execute("DELETE FROM recommendations WHERE beneficiary_id LIKE 'synth_ben_%'").rowcount
    c5 = conn.execute("DELETE FROM profile_answers WHERE beneficiary_id LIKE 'synth_ben_%'").rowcount
    c4 = conn.execute("DELETE FROM interview_sessions WHERE beneficiary_id LIKE 'synth_ben_%'").rowcount
    
    c1 = conn.execute("DELETE FROM local_opportunities WHERE id LIKE 'synth_opp_%'").rowcount
    c2 = conn.execute("DELETE FROM qualifications WHERE id LIKE 'synth_qual_%'").rowcount
    c3 = conn.execute("DELETE FROM beneficiaries WHERE id LIKE 'synth_ben_%'").rowcount
    
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()
    
    print("Reset complete:")
    print(f"- Opportunities deleted: {c1}")
    print(f"- Qualifications deleted: {c2}")
    print(f"- Beneficiaries deleted: {c3}")
    print(f"- Interview sessions deleted: {c4}")
    print(f"- Profile answers deleted: {c5}")
    print(f"- Recommendations deleted: {c6}")

if __name__ == '__main__':
    reset_demo_data()
