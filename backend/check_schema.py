import sqlite3
from pathlib import Path

db_path = Path("c:/Users/DELL/JEEVAN-MITRA 2.0/backend/jeevanmitra.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(qualifications)")
print("QUALIFICATIONS:")
for row in cursor.fetchall():
    print(row)

cursor.execute("PRAGMA table_info(local_opportunities)")
print("LOCAL_OPPORTUNITIES:")
for row in cursor.fetchall():
    print(row)
