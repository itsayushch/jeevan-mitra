#!/usr/bin/env python3
"""Expire old planning exports past retention period."""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import get_db


def main():
    parser = argparse.ArgumentParser(description="Expire old planning exports past retention window")
    parser.add_argument("--dry-run", action="store_true", help="Report without mutating database")
    args = parser.parse_args()

    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        expired_rows = conn.execute("""
            SELECT id, snapshot_id, export_type, expires_at 
            FROM planning_exports 
            WHERE status != 'EXPIRED' AND expires_at < ?;
        """, (now_iso,)).fetchall()

        print(f"Found {len(expired_rows)} exports past expiry date.")
        for r in expired_rows:
            print(f"  Export {r['id']} (Snapshot: {r['snapshot_id']}, Type: {r['export_type']}, Expired: {r['expires_at']})")

        if args.dry_run:
            print("[DRY-RUN] No database modifications made.")
            return

        if expired_rows:
            conn.execute("""
                UPDATE planning_exports
                SET status = 'EXPIRED', file_content = NULL
                WHERE status != 'EXPIRED' AND expires_at < ?;
            """, (now_iso,))
            print(f"SUCCESS: Marked {len(expired_rows)} exports as EXPIRED and cleared cached file contents.")


if __name__ == "__main__":
    main()
