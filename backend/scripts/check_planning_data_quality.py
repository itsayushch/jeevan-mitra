#!/usr/bin/env python3
"""Check and report planning data quality metrics for a district."""
import argparse
import sys
import json
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import get_db
from app.services.planning_aggregation_service import PlanningAggregationService


def main():
    parser = argparse.ArgumentParser(description="Check planning data quality")
    parser.add_argument("--district-id", required=True, help="District name/ID (e.g. Moradabad)")
    args = parser.parse_args()

    with get_db() as conn:
        service = PlanningAggregationService(conn)
        res = service.get_data_quality_metrics(args.district_id)
        dq = res["data_quality"]

        print(f"=== PLANNING DATA QUALITY REPORT: {args.district_id} ===")
        print(f"  Stale or expired opportunities: {dq['stale_or_expired_opportunities_count']}")
        print(f"  Opportunities due for re-verification (<14 days): {dq['opportunities_due_reverification_count']}")
        print(f"  Overdue case follow-ups: {dq['overdue_follow_ups_count']}")
        print(f"  Outcomes pending verification: {dq['outcomes_pending_verification_count']}")
        print(f"  Active opportunities missing capacity data: {dq['active_opportunities_missing_capacity_count']}")
        print(f"  Cases without referral consent: {dq['cases_without_referral_consent_count']}")
        print(f"  Language distribution: {dq.get('language_distribution', {})}")
        print(f"  Opportunity submission channels: {dq.get('opportunity_submissions_by_mode', {})}")
        print(f"  Explainability quality: {dq.get('explainability_quality', {})}")
        print("======================================================")


if __name__ == "__main__":
    main()
