import sqlite3
import json
import uuid
from datetime import datetime, timezone

db_path = "c:/Users/DELL/JEEVAN-MITRA 2.0/backend/jeevanmitra.db"

def seed_training_data():
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()
    
    # Check if courses exist
    count = conn.execute("SELECT count(*) FROM training_courses").fetchone()[0]
    if count > 0:
        print("Training courses already seeded.")
        return

    # Courses
    course_id = f"course_{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO training_courses (id, title, slug, short_description, long_description, sector, nsqf_level, duration_hours, difficulty, language_code, source_name, verification_status, verified_at, last_updated_at, is_published)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        course_id, "Basic Electrical Repair", "basic-electrical-repair", "Learn safe basic appliance and wiring checks.",
        "A full course on household electrical systems, emphasizing safety and basic repairs.", "Electrical",
        "Level 2", 30, "Beginner", "hi", "Govt Training Board", "Verified", now, now, 1
    ))
    
    # Modules
    module_id = f"module_{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO training_modules (id, course_id, title, sequence_number, estimated_minutes, learning_objectives, summary, is_published)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        module_id, course_id, "Electrical Safety Basics", 1, 60,
        json.dumps(["Identify unsafe conditions", "Use safety equipment"]),
        "Introduction to dealing with electricity safely.", 1
    ))
    
    # Lessons
    lesson_id = f"lesson_{uuid.uuid4().hex[:8]}"
    conn.execute("""
        INSERT INTO training_lessons (id, module_id, title, sequence_number, content_markdown, plain_language_summary, key_points, practical_steps, safety_notes, quiz_questions, source_references, last_reviewed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lesson_id, module_id, "Electrical Safety Basics", 1,
        "Electricity can cause shock, burns, and fire. Always switch off power before touching a wire or appliance.",
        "Turn off the switch before touching wires.",
        json.dumps(["Circuit breaker: cuts electricity during fault", "Insulation: protective covering"]),
        json.dumps(["Switch off main power.", "Confirm unplugged.", "Inspect wires.", "Use insulated tools."]),
        json.dumps(["Do not touch wires with wet hands.", "Do not repair live connections."]),
        json.dumps([{"q": "What should you do before checking a damaged appliance?", "options": ["Unplug it", "Pour water on it"], "answer": "Unplug it"}]),
        json.dumps(["Safety Handbook 2024"]), now
    ))
    
    conn.commit()
    conn.close()
    print("Seeded successfully.")

if __name__ == "__main__":
    seed_training_data()
