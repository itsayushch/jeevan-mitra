import os
import sys
import json
import time
import hashlib
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

# Add backend root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.settings import settings


TABLES_TO_VERIFY = [
    "users",
    "user_roles",
    "user_scopes",
    "beneficiaries",
    "qualifications",
    "local_opportunities",
    "recommendations",
    "beneficiary_cases",
    "referrals",
    "planning_snapshots",
    "planning_exports",
    "audit_events",
    "alembic_version"
]


def compute_sha256(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_table_counts(conn: sqlite3.Connection) -> Dict[str, int]:
    counts = {}
    for table in TABLES_TO_VERIFY:
        try:
            row = conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()
            counts[table] = row[0] if row else 0
        except Exception:
            counts[table] = -1  # Table not present
    return counts


def get_alembic_version(conn: sqlite3.Connection) -> str:
    try:
        row = conn.execute("SELECT version_num FROM alembic_version LIMIT 1;").fetchone()
        return str(row[0]) if row and row[0] else "unknown"
    except Exception:
        return "unknown"


def create_backup(
    source_db_path: str = None,
    backup_dir: str = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Creates an atomic point-in-time SQLite backup using sqlite3.Connection.backup.
    Computes SHA-256 checksum and writes a metadata manifest JSON.
    """
    source_path = source_db_path or settings.DATABASE_PATH
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source database not found: {source_path}")

    b_dir = Path(backup_dir) if backup_dir else Path(source_path).parent / "backups"
    b_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"jeevanmitra_backup_{timestamp_str}.db"
    backup_meta_filename = f"jeevanmitra_backup_{timestamp_str}.json"

    backup_filepath = str(b_dir / backup_filename)
    meta_filepath = str(b_dir / backup_meta_filename)

    start_time = time.time()

    # Perform atomic backup
    src_conn = sqlite3.connect(source_path)
    dst_conn = sqlite3.connect(backup_filepath)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    duration_ms = (time.time() - start_time) * 1000

    # Compute checksum and collect manifest data
    checksum = compute_sha256(backup_filepath)
    file_size = os.path.getsize(backup_filepath)

    check_conn = sqlite3.connect(backup_filepath)
    try:
        alembic_rev = get_alembic_version(check_conn)
        table_counts = get_table_counts(check_conn)
    finally:
        check_conn.close()

    manifest: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_db": os.path.abspath(source_path),
        "backup_file": os.path.basename(backup_filepath),
        "backup_path": os.path.abspath(backup_filepath),
        "sha256_checksum": checksum,
        "file_size_bytes": file_size,
        "duration_ms": round(duration_ms, 2),
        "alembic_version": alembic_rev,
        "table_counts": table_counts,
        "release_version": settings.RELEASE_VERSION,
        "environment": settings.APP_ENV,
    }

    with open(meta_filepath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return backup_filepath, meta_filepath, manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create atomic JeevanMitra SQLite backup.")
    parser.add_argument("--source", default=None, help="Source database file path")
    parser.add_argument("--dest", default=None, help="Backup destination directory")
    args = parser.parse_args()

    print("Initiating atomic database backup...")
    b_path, m_path, manifest = create_backup(args.source, args.dest)
    print(f"Backup created: {b_path}")
    print(f"Manifest written: {m_path}")
    print(f"SHA-256: {manifest['sha256_checksum']}")
    print(f"Alembic revision: {manifest['alembic_version']}")
    print(f"Size: {manifest['file_size_bytes']} bytes | Duration: {manifest['duration_ms']}ms")
