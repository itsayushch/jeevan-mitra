import sqlite3
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.database import get_connection

def reset_demo_data():
    conn = get_connection()
    
    conn.execute("DELETE FROM local_opportunities WHERE id LIKE 'synth_opp_%'")
    conn.execute("DELETE FROM qualifications WHERE id LIKE 'synth_qual_%'")
    conn.execute("DELETE FROM beneficiaries WHERE id LIKE 'synth_ben_%'")
    conn.execute("DELETE FROM interview_sessions WHERE beneficiary_id LIKE 'synth_ben_%'")
    conn.execute("DELETE FROM profile_answers WHERE beneficiary_id LIKE 'synth_ben_%'")
    conn.execute("DELETE FROM recommendations WHERE beneficiary_id LIKE 'synth_ben_%'")
    
    conn.commit()
    conn.close()
    print("Demo data reset successfully.")

if __name__ == '__main__':
    reset_demo_data()
