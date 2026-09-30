import os
import sys
import sqlite3
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def migrate_table(sqlite_cursor, pg_session, table_name, columns, pg_engine):
    print(f"Migrating {table_name}...")
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"{table_name}: 0 rows found.")
        return 0
        
    # Build insert statement
    cols_str = ", ".join(columns)
    params_str = ", ".join([f":{col}" for col in columns])
    insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({params_str})"
    if "postgresql" in str(pg_engine.url):
        insert_sql += " ON CONFLICT DO NOTHING"
    else:
        insert_sql = insert_sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
    
    migrated = 0
    for row in rows:
        # sqlite3.Row to dict
        data = dict(row)
        pg_session.execute(text(insert_sql), data)
        migrated += 1
        
    pg_session.commit()
    print(f"{table_name}: Migrated {migrated} / {len(rows)}")
    return migrated

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite-db", required=True, help="Path to source SQLite DB")
    args = parser.parse_args()

    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        print("Error: DATABASE_URL environment variable is not set.")
        sys.exit(1)

    if not os.path.exists(args.sqlite_db):
        print(f"Error: Source SQLite DB not found at {args.sqlite_db}")
        sys.exit(1)

    # Source DB
    sqlite_conn = sqlite3.connect(args.sqlite_db)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    # Destination DB
    pg_engine = create_engine(pg_url)
    Session = sessionmaker(bind=pg_engine)
    session = Session()

    tables = [
        ("training_courses", ["id", "title", "slug", "short_description", "long_description", "sector", "nsqf_level", "duration_hours", "difficulty", "language_code", "thumbnail_url", "source_name", "source_url", "verification_status", "verified_at", "last_updated_at", "is_published"]),
        ("training_modules", ["id", "course_id", "title", "sequence_number", "estimated_minutes", "learning_objectives", "summary", "is_published"]),
        ("training_lessons", ["id", "module_id", "title", "sequence_number", "content_markdown", "plain_language_summary", "key_points", "practical_steps", "safety_notes", "quiz_questions", "source_references", "last_reviewed_at", "reviewed_by"]),
        ("training_resources", ["id", "course_id", "lesson_id", "resource_type", "title", "file_url", "language_code", "is_verified", "uploaded_at"]),
        ("learner_course_progress", ["id", "beneficiary_id", "course_id", "status", "progress_percent", "started_at", "last_opened_at", "completed_at"]),
        ("learner_lesson_progress", ["id", "beneficiary_id", "lesson_id", "is_completed", "last_position", "completed_at", "bookmarked_at"]),
        ("content_feedback", ["id", "beneficiary_id", "course_id", "lesson_id", "rating", "feedback_type", "comment", "created_at"])
    ]

    try:
        results = {}
        for table_name, columns in tables:
            migrated_count = migrate_table(cursor, session, table_name, columns, pg_engine)
            results[table_name] = migrated_count

        print("\nMigration Summary:")
        print(f"Courses migrated: {results['training_courses']}")
        print(f"Modules migrated: {results['training_modules']}")
        print(f"Lessons migrated: {results['training_lessons']}")
        print(f"Resources migrated: {results['training_resources']}")
        print(f"Progress records migrated (Course): {results['learner_course_progress']}")
        print(f"Progress records migrated (Lesson/Bookmarks): {results['learner_lesson_progress']}")
        
    except Exception as e:
        session.rollback()
        print(f"Failed during migration: {e}")
        sys.exit(1)
    finally:
        session.close()
        sqlite_conn.close()

if __name__ == "__main__":
    main()
