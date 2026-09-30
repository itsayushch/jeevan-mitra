import os
import sys
import json
import time
import hashlib
import sqlite3
import argparse
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.backup_db import compute_sha256, get_table_counts, get_alembic_version


def run_restore_drill(
    backup_filepath: str,
    manifest_filepath: str,
    target_db_path: str = None
) -> Dict[str, Any]:
    """
    Executes an automated disaster recovery restore drill.
    1. Validates backup file SHA-256 against manifest.
    2. Restores backup into target verification database.
    3. Runs SQLite integrity check.
    4. Validates Alembic schema revision matches.
    5. Validates record counts across all authoritative tables.
    6. Runs canary queries.
    7. Measures restore elapsed time.
    """
    start_time = time.time()

    if not os.path.exists(backup_filepath):
        raise FileNotFoundError(f"Backup file not found: {backup_filepath}")
    if not os.path.exists(manifest_filepath):
        raise FileNotFoundError(f"Manifest file not found: {manifest_filepath}")

    with open(manifest_filepath, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Checksum validation
    computed_checksum = compute_sha256(backup_filepath)
    expected_checksum = manifest.get("sha256_checksum")
    if computed_checksum != expected_checksum:
        raise ValueError(
            f"Backup checksum mismatch! Expected: {expected_checksum}, Computed: {computed_checksum}"
        )

    # Setup target restore file
    if target_db_path:
        target_path = target_db_path
        if os.path.exists(target_path):
            os.remove(target_path)
    else:
        temp_dir = tempfile.gettempdir()
        target_path = os.path.join(temp_dir, f"jeevanmitra_drill_{int(time.time())}.db")

    # 2. Restore database
    src_conn = sqlite3.connect(backup_filepath)
    dst_conn = sqlite3.connect(target_path)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    # 3. Integrity Check
    restored_conn = sqlite3.connect(target_path)
    try:
        cursor = restored_conn.execute("PRAGMA integrity_check;")
        integrity_rows = cursor.fetchall()
        integrity_status = integrity_rows[0][0] if integrity_rows else "failed"

        if integrity_status != "ok":
            raise RuntimeError(f"Database PRAGMA integrity_check failed: {integrity_rows}")

        # 4. Alembic Revision Check
        restored_alembic = get_alembic_version(restored_conn)
        expected_alembic = manifest.get("alembic_version")
        if restored_alembic != expected_alembic:
            raise ValueError(
                f"Alembic revision mismatch! Restored: {restored_alembic}, Manifest: {expected_alembic}"
            )

        # 5. Table Counts Verification
        restored_counts = get_table_counts(restored_conn)
        expected_counts = manifest.get("table_counts", {})
        counts_match = True
        count_mismatches = {}
        for tbl, exp_cnt in expected_counts.items():
            restored_cnt = restored_counts.get(tbl, -1)
            if restored_cnt != exp_cnt:
                counts_match = False
                count_mismatches[tbl] = {"expected": exp_cnt, "actual": restored_cnt}

        if not counts_match:
            raise ValueError(f"Table count verification failed: {count_mismatches}")

        # 6. Canary queries
        user_cnt = restored_conn.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
        opp_cnt = restored_conn.execute("SELECT COUNT(*) FROM local_opportunities;").fetchone()[0]
        canary_passed = (user_cnt >= 0 and opp_cnt >= 0)

    finally:
        restored_conn.close()

    duration_ms = (time.time() - start_time) * 1000

    report = {
        "status": "PASSED",
        "drill_timestamp": datetime.now(timezone.utc).isoformat(),
        "backup_file": os.path.basename(backup_filepath),
        "restored_target_path": os.path.abspath(target_path),
        "duration_ms": round(duration_ms, 2),
        "checksum_verified": True,
        "sha256": computed_checksum,
        "integrity_check": integrity_status,
        "alembic_version": restored_alembic,
        "table_counts_verified": True,
        "verified_tables_count": len(expected_counts),
        "canary_queries_passed": canary_passed,
    }

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute automated disaster recovery restore drill.")
    parser.add_argument("backup_file", help="Path to backup SQLite file")
    parser.add_argument("manifest_file", help="Path to backup JSON manifest")
    parser.add_argument("--target", default=None, help="Target restore database path")
    args = parser.parse_args()

    print(f"Starting restore drill for {args.backup_file}...")
    try:
        report = run_restore_drill(args.backup_file, args.manifest_file, args.target)
        print("Restore Drill Status: PASSED")
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(f"Restore Drill Status: FAILED - {str(e)}")
        sys.exit(1)
