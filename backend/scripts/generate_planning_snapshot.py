#!/usr/bin/env python3
"""Generate a reproducible planning snapshot for a district."""
import argparse
import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import get_db
from app.services.planning_snapshot_service import PlanningSnapshotService
from app.schemas.planning import SnapshotCreateRequest


def main():
    parser = argparse.ArgumentParser(description="Generate immutable planning snapshot for district")
    parser.add_argument("--district-id", required=True, help="District name/ID (e.g. Moradabad)")
    parser.add_argument("--block-id", default=None, help="Optional block ID")
    parser.add_argument("--period-start", required=True, help="Period start date (YYYY-MM-DD)")
    parser.add_argument("--period-end", required=True, help="Period end date (YYYY-MM-DD)")
    parser.add_argument("--notes", default="Automated scheduled snapshot", help="Optional notes")
    args = parser.parse_args()

    # System actor for scheduled job
    system_user = {
        "id": "user_cron_scheduler",
        "role": "super_admin",
        "district": args.district_id,
        "roles": ["super_admin"],
        "scopes": [{"district_id": args.district_id}],
    }

    req = SnapshotCreateRequest(
        district_id=args.district_id,
        block_id=args.block_id,
        period_start=args.period_start,
        period_end=args.period_end,
        notes=args.notes,
    )

    with get_db() as conn:
        res = PlanningSnapshotService.create_snapshot(conn, system_user, req)
        print(f"SUCCESS: Snapshot generated successfully: ID={res['id']}, Status={res['status']}")
        print(f"  District: {res['district_id']} | Period: {res['period_start']} to {res['period_end']}")
        print(f"  Active Verified Opportunities: {res['aggregation']['overview'].get('active_verified_opportunities', 0)}")


if __name__ == "__main__":
    main()
