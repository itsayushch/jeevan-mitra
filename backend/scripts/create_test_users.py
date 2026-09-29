import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.database import get_connection

def create_test_users():
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    
    personas = [
        ('synth_ben_hindi_txt', '[SYNTHETIC] Hindi Text First', '+910000000001', 'hi', 'sms'),
        ('synth_ben_eng', '[SYNTHETIC] English Speaker', '+910000000002', 'en', 'voice'),
        ('synth_ben_hinglish', '[SYNTHETIC] Hindi-English', '+910000000003', 'hi-en', 'voice'),
        ('synth_ben_local', '[SYNTHETIC] Local Only', '+910000000004', 'hi', 'voice'),
        ('synth_ben_low_edu', '[SYNTHETIC] Low Education', '+910000000005', 'hi', 'voice'),
        ('synth_ben_self_emp', '[SYNTHETIC] Self Employment', '+910000000006', 'hi', 'voice'),
        ('synth_ben_no_opp', '[SYNTHETIC] No Verified Opportunity', '+910000000007', 'hi', 'voice'),
        ('synth_ben_ai_fail', '[SYNTHETIC] AI Provider Failure', '+910000000008', 'hi', 'voice'),
        ('synth_ben_prof_corr', '[SYNTHETIC] Profile Correction', '+910000000009', 'hi', 'voice'),
        ('synth_ben_counselor', '[SYNTHETIC] Counselor Referral', '+910000000010', 'hi', 'voice'),
    ]
    
    ben_data = []
    for p in personas:
        ben_data.append((
            p[0], p[1], p[2], 'female' if 'eng' in p[0] else 'male', 25, 'SC',
            p[3], 'Moradabad', 'Moradabad Rural', 'Demo Village', p[4], now, now
        ))
        
    conn.executemany("""
        INSERT OR REPLACE INTO beneficiaries (
            id, name, phone, gender, age, category, preferred_language,
            district, block, village, contact_preference, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, ben_data)
    
    # Add some dummy interview sessions for these test users
    sessions = []
    for p in personas:
        sessions.append((
            f'sess_{p[0]}', p[0], 'web_app', 'in_progress', 0,
            'Welcome, what is your educational background?', p[3], '[]', now, now
        ))
        
    conn.executemany("""
        INSERT OR REPLACE INTO interview_sessions (
            id, beneficiary_id, channel, status, current_question_index,
            last_question, language, transcript_history, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, sessions)
    
    conn.commit()
    conn.close()
    print("Seed complete:")
    print(f"- Test users created: {len(ben_data)}")
    print(f"- Interview sessions created: {len(sessions)}")

if __name__ == '__main__':
    create_test_users()
