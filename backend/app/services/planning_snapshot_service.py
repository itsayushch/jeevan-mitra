import json
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from app.services.planning_aggregation_service import PlanningAggregationService
from app.utils.audit_events import log_audit_event
from app.schemas.planning import SnapshotCreateRequest


class PlanningSnapshotService:
    """Service managing immutable planning snapshots.
    Guarantees that snapshot aggregation data is never mutated after generation,
    all exports reference valid snapshots, and actions are auditable.
    """

    @staticmethod
    def create_snapshot(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        req: SnapshotCreateRequest,
    ) -> Dict[str, Any]:
        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, req.district_id)

        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"

        # Gather complete authoritative aggregates
        overview = agg_service.get_overview_aggregation(req.district_id, req.block_id)
        demand = agg_service.get_demand_metrics(req.district_id, req.block_id, req.period_start, req.period_end)
        supply = agg_service.get_supply_metrics(req.district_id, req.block_id)
        gaps = agg_service.get_gap_metrics(req.district_id, req.block_id)
        funnel = agg_service.get_referral_funnel_metrics(req.district_id, req.block_id)
        outcomes = agg_service.get_outcome_metrics(req.district_id, req.block_id)
        data_quality = agg_service.get_data_quality_metrics(req.district_id, req.block_id)
        geo_coverage = agg_service.get_geographic_coverage(req.district_id)

        full_aggregation = {
            "overview": overview,
            "demand": demand,
            "supply": supply,
            "gaps": gaps,
            "funnel": funnel,
            "outcomes": outcomes,
            "data_quality": data_quality,
            "geographic_coverage": geo_coverage,
        }

        filter_snapshot = {
            "district_id": req.district_id,
            "block_id": req.block_id,
            "period_start": req.period_start,
            "period_end": req.period_end,
            "privacy_threshold": 5,
        }

        # Insert immutable snapshot record
        conn.execute("""
            INSERT INTO planning_snapshots (
                id, district_id, block_id, period_start, period_end,
                generated_by_user_id, generated_at, metric_version,
                filter_snapshot_json, aggregation_snapshot_json,
                data_freshness_at, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'v1', ?, ?, ?, 'GENERATED', ?);
        """, (
            snapshot_id, req.district_id, req.block_id, req.period_start, req.period_end,
            current_user.get("id"), now_iso,
            json.dumps(filter_snapshot), json.dumps(full_aggregation),
            now_iso, req.notes,
        ))

        # Insert normalized metrics into planning_snapshot_metrics
        metrics_to_insert = [
            ("DEMAND", "beneficiaries_profiled", overview.get("beneficiaries_profiled") or 0, overview.get("is_suppressed")),
            ("DEMAND", "interest_matches", overview.get("interest_matches") or 0, overview.get("is_suppressed")),
            ("DEMAND", "verified_matches", overview.get("verified_matches") or 0, overview.get("is_suppressed")),
            ("SUPPLY", "active_opportunities", overview.get("active_verified_opportunities") or 0, False),
            ("SUPPLY", "available_capacity", overview.get("available_verified_capacity") or 0, False),
            ("GAP", "planning_supply_gaps", overview.get("planning_supply_gaps") or 0, overview.get("is_suppressed")),
            ("REFERRAL_FUNNEL", "referrals_created", overview.get("referrals_created") or 0, overview.get("is_suppressed")),
            ("REFERRAL_FUNNEL", "enrolments", overview.get("enrolments") or 0, overview.get("is_suppressed")),
            ("OUTCOME", "verified_livelihoods", overview.get("verified_livelihoods") or 0, overview.get("is_suppressed")),
            ("DATA_QUALITY", "stale_or_expired_opportunities", data_quality["data_quality"]["stale_or_expired_opportunities_count"], False),
            ("DATA_QUALITY", "opportunities_due_reverification", data_quality["data_quality"]["opportunities_due_reverification_count"], False),
            ("DATA_QUALITY", "overdue_follow_ups", data_quality["data_quality"]["overdue_follow_ups_count"], False),
            ("DATA_QUALITY", "cases_without_referral_consent", data_quality["data_quality"]["cases_without_referral_consent_count"], False),
        ]

        for group, key, val, supp in metrics_to_insert:
            m_id = f"m_{uuid.uuid4().hex[:12]}"
            conn.execute("""
                INSERT INTO planning_snapshot_metrics (
                    id, snapshot_id, metric_group, metric_key,
                    dimension_json, metric_value, is_suppressed, created_at
                ) VALUES (?, ?, ?, ?, '{}', ?, ?, ?);
            """, (m_id, snapshot_id, group, key, float(val), 1 if supp else 0, now_iso))

        # Log audit record
        log_audit_event(
            conn,
            actor_id=current_user.get("id"),
            actor_name=current_user.get("name", "Staff"),
            actor_role=current_user.get("role", "staff"),
            action="PLANNING_SNAPSHOT_GENERATED",
            entity_type="planning_snapshot",
            entity_id=snapshot_id,
            old_values=None,
            new_values={"district_id": req.district_id, "status": "GENERATED"},
        )

        return {
            "id": snapshot_id,
            "district_id": req.district_id,
            "block_id": req.block_id,
            "period_start": req.period_start,
            "period_end": req.period_end,
            "status": "GENERATED",
            "generated_by_user_id": current_user.get("id"),
            "generated_at": now_iso,
            "metric_version": "v1",
            "data_freshness_at": now_iso,
            "reviewed_by_user_id": None,
            "reviewed_at": None,
            "approved_by_user_id": None,
            "approved_at": None,
            "notes": req.notes,
            "aggregation": full_aggregation,
        }

    @staticmethod
    def get_snapshot(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        snapshot_id: str,
    ) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM planning_snapshots WHERE id = ?;", (snapshot_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning snapshot not found")

        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, row["district_id"])

        return {
            "id": row["id"],
            "district_id": row["district_id"],
            "block_id": row["block_id"],
            "period_start": row["period_start"],
            "period_end": row["period_end"],
            "status": row["status"],
            "generated_by_user_id": row["generated_by_user_id"],
            "generated_at": row["generated_at"],
            "metric_version": row["metric_version"],
            "data_freshness_at": row["data_freshness_at"],
            "reviewed_by_user_id": row["reviewed_by_user_id"],
            "reviewed_at": row["reviewed_at"],
            "approved_by_user_id": row["approved_by_user_id"],
            "approved_at": row["approved_at"],
            "notes": row["notes"],
            "aggregation": json.loads(row["aggregation_snapshot_json"] or "{}"),
        }

    @staticmethod
    def list_snapshots(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        district_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        target_dist = district_id or current_user.get("district") or current_user.get("assigned_district") or "Moradabad"
        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, target_dist)

        query = "SELECT * FROM planning_snapshots WHERE district_id = ? ORDER BY generated_at DESC;"
        rows = conn.execute(query, (target_dist,)).fetchall()

        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "district_id": r["district_id"],
                "block_id": r["block_id"],
                "period_start": r["period_start"],
                "period_end": r["period_end"],
                "status": r["status"],
                "generated_by_user_id": r["generated_by_user_id"],
                "generated_at": r["generated_at"],
                "metric_version": r["metric_version"],
                "data_freshness_at": r["data_freshness_at"],
                "reviewed_by_user_id": r["reviewed_by_user_id"],
                "reviewed_at": r["reviewed_at"],
                "approved_by_user_id": r["approved_by_user_id"],
                "approved_at": r["approved_at"],
                "notes": r["notes"],
                "aggregation": json.loads(r["aggregation_snapshot_json"] or "{}"),
            })
        return results

    @staticmethod
    def review_snapshot(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        snapshot_id: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM planning_snapshots WHERE id = ?;", (snapshot_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning snapshot not found")

        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, row["district_id"])

        if current_user.get("role") not in ["district_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only district_admin or super_admin can review snapshots")

        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE planning_snapshots
            SET status = 'REVIEWED', reviewed_by_user_id = ?, reviewed_at = ?, notes = COALESCE(?, notes)
            WHERE id = ?;
        """, (current_user.get("id"), now_iso, notes, snapshot_id))

        log_audit_event(
            conn,
            actor_id=current_user.get("id"),
            actor_name=current_user.get("name", "Staff"),
            actor_role=current_user.get("role", "staff"),
            action="PLANNING_SNAPSHOT_REVIEWED",
            entity_type="planning_snapshot",
            entity_id=snapshot_id,
            old_values={"status": row["status"]},
            new_values={"status": "REVIEWED", "reviewed_at": now_iso},
        )

        return PlanningSnapshotService.get_snapshot(conn, current_user, snapshot_id)

    @staticmethod
    def approve_snapshot(
        conn: sqlite3.Connection,
        current_user: Dict[str, Any],
        snapshot_id: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM planning_snapshots WHERE id = ?;", (snapshot_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning snapshot not found")

        agg_service = PlanningAggregationService(conn)
        agg_service.check_district_scope(current_user, row["district_id"])

        if current_user.get("role") not in ["district_admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only district_admin or super_admin can approve snapshots")

        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE planning_snapshots
            SET status = 'APPROVED', approved_by_user_id = ?, approved_at = ?, notes = COALESCE(?, notes)
            WHERE id = ?;
        """, (current_user.get("id"), now_iso, notes, snapshot_id))

        log_audit_event(
            conn,
            actor_id=current_user.get("id"),
            actor_name=current_user.get("name", "Staff"),
            actor_role=current_user.get("role", "staff"),
            action="PLANNING_SNAPSHOT_APPROVED",
            entity_type="planning_snapshot",
            entity_id=snapshot_id,
            old_values={"status": row["status"]},
            new_values={"status": "APPROVED", "approved_at": now_iso},
        )

        return PlanningSnapshotService.get_snapshot(conn, current_user, snapshot_id)
