from fastapi import APIRouter, HTTPException, Response, Depends
import uuid
import json
import csv
import io
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models import GenerateBriefRequest, SignOffRequest
from app.ai_layers.layer5_planning.aggregation_service import AggregationService
from app.ai_layers.layer5_planning.narrative_engine import NarrativeEngine
from app.dependencies.roles import (
    require_district_officer_or_admin,
    enforce_district_scope,
    PlanningActor,
)
from app.utils.audit_events import log_audit_event

router = APIRouter(prefix="/planning", tags=["District-Planning"])

VALID_SIGN_OFF_TRANSITIONS = {
    "draft": {"under_review", "signed_off"},
    "under_review": {"signed_off", "rejected"},
    "signed_off": set(),
    "rejected": set(),
}


# ============================================================================
# Layer 5: District Planning Endpoints (district_officer/admin, district-scoped)
# ============================================================================
@router.post("/briefs/generate", status_code=201)
def generate_brief(req: GenerateBriefRequest, actor: PlanningActor = Depends(require_district_officer_or_admin)):
    """Generates a planning brief: aggregation snapshot + template-first narrative."""
    enforce_district_scope(actor, req.district)
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        matrix = AggregationService(conn).get_demand_supply_matrix(req.district, req.period)
        if matrix["status"] == "insufficient_data":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": "insufficient_data",
                    "message": matrix["message"],
                    "data_basis": matrix["data_basis"],
                },
            )

        brief_result = NarrativeEngine.generate_brief(matrix)
        narrative = brief_result["narrative"]

        brief_id = f"brief_{uuid.uuid4().hex[:10]}"
        metrics = matrix["metrics"]
        suggested_actions = _suggested_actions(matrix)

        conn.execute("""
            INSERT INTO planning_briefs (
                id, district, period, total_beneficiaries_interviewed, total_verified_matches,
                total_supply_gaps, aggregation_snapshot, generated_narrative, suggested_policy_actions,
                reviewer_sign_off_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?);
        """, (
            brief_id, req.district, req.period,
            metrics["total_demand_records"],
            metrics["demand_with_verified_match_count"],
            metrics["total_unmet_demand"],
            json.dumps(matrix), narrative,
            json.dumps(suggested_actions),
            now, now
        ))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="BRIEF_GENERATED",
            entity_type="planning_brief",
            entity_id=brief_id,
            metadata={
                "district": req.district,
                "period": req.period,
                "query_id": matrix["query_id"],
                "narrative_validation": brief_result["narrative_meta"]["validation"],
            },
        )

        return {
            "brief_id": brief_id,
            "district": req.district,
            "period": req.period,
            "status": "draft",
            "generated_at": now,
            "generated_narrative": narrative,
            "narrative_meta": brief_result["narrative_meta"],
            "top_gaps": [
                {
                    "block": c["block"],
                    "qualification_title": c["qualification_title"],
                    "demand_count": c["demand_count"],
                    "verified_seats": c["verified_seats"],
                    "gap": c["gap"],
                    "severity_score": c["severity_score"],
                }
                for c in matrix["matrix"] if not c["suppressed"]
            ][:5],
            "suggested_policy_actions": suggested_actions,
        }


@router.get("/matrix")
def get_matrix(
    district: str,
    period: Optional[str] = None,
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    """Demand vs verified-supply matrix for a district. Every figure is query-derived."""
    enforce_district_scope(actor, district)
    with get_db() as conn:
        return AggregationService(conn).get_demand_supply_matrix(district, period)


@router.get("/briefs/{brief_id}")
def get_brief_by_id(
    brief_id: str,
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM planning_briefs WHERE id = ?;", (brief_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        d = dict(row)
        enforce_district_scope(actor, d["district"])
        d["aggregation_snapshot"] = json.loads(d.get("aggregation_snapshot") or "{}")
        d["suggested_policy_actions"] = json.loads(d.get("suggested_policy_actions") or "[]")
        return d


@router.post("/briefs/{brief_id}/sign-off")
def sign_off_brief(
    brief_id: str,
    req: SignOffRequest,
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    """
    Reviewer sign-off lifecycle: draft -> under_review -> signed_off.
    action='submit_for_review' moves draft -> under_review;
    action='sign_off' moves draft/under_review -> signed_off.
    Every transition is written to the audit_events ledger.
    """
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM planning_briefs WHERE id = ?;", (brief_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        brief = dict(row)
        enforce_district_scope(actor, brief["district"])

        current_status = brief["reviewer_sign_off_status"]
        target_status = "under_review" if req.action == "submit_for_review" else "signed_off"

        if target_status not in VALID_SIGN_OFF_TRANSITIONS.get(current_status, set()):
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "INVALID_SIGN_OFF_TRANSITION",
                    "message": f"Cannot move brief from '{current_status}' to '{target_status}'.",
                    "current_status": current_status,
                },
            )

        conn.execute("""
            UPDATE planning_briefs
            SET reviewer_sign_off_status = ?, signed_off_by = ?, signed_off_at = ?, updated_at = ?
            WHERE id = ?;
        """, (
            target_status,
            actor.actor_name if req.action == "sign_off" else brief.get("signed_off_by"),
            now if req.action == "sign_off" else brief.get("signed_off_at"),
            now, brief_id,
        ))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="BRIEF_SIGNED_OFF" if req.action == "sign_off" else "BRIEF_UNDER_REVIEW",
            entity_type="planning_brief",
            entity_id=brief_id,
            old_values={"reviewer_sign_off_status": current_status},
            new_values={
                "reviewer_sign_off_status": target_status,
                "signed_off_by": actor.actor_name,
                "notes": req.notes,
            },
        )

        return {
            "brief_id": brief_id,
            "status": target_status,
            "signed_off_by": actor.actor_name,
            "timestamp": now,
        }


@router.get("/briefs/{brief_id}/export")
def export_brief(
    brief_id: str,
    format: str = "csv",
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    """
    Exports a signed-off brief (CSV, or PDF-ready JSON with format=json).
    A brief is NOT exportable until a district officer signs it off.
    """
    with get_db() as conn:
        row = conn.execute("SELECT * FROM planning_briefs WHERE id = ?;", (brief_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        brief = dict(row)
        enforce_district_scope(actor, brief["district"])

        if brief["reviewer_sign_off_status"] != "signed_off":
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "BRIEF_NOT_SIGNED_OFF",
                    "message": (
                        f"Brief is '{brief['reviewer_sign_off_status']}'; "
                        "export requires reviewer sign-off."
                    ),
                    "current_status": brief["reviewer_sign_off_status"],
                },
            )

        snapshot = json.loads(brief.get("aggregation_snapshot") or "{}")
        matrix = snapshot.get("matrix", [])

        if format == "json":
            return {
                "brief_id": brief["id"],
                "district": brief["district"],
                "period": brief["period"],
                "generated_at": brief["created_at"],
                "signed_off_by": brief.get("signed_off_by"),
                "signed_off_at": brief.get("signed_off_at"),
                "narrative": brief.get("generated_narrative"),
                "suggested_policy_actions": json.loads(brief.get("suggested_policy_actions") or "[]"),
                "aggregation": snapshot,
                "export_format": "pdf_ready_json",
            }

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "block", "qualification", "nqr_code", "demand_count", "verified_seats",
            "total_seats", "gap", "nearest_verified_centre_km",
            "share_of_demand_with_no_verified_batch", "coverage", "severity_score", "suppressed",
        ])
        for c in matrix:
            writer.writerow([
                c["block"], c["qualification_title"], c["nqr_code"],
                c["demand_count"], c["verified_seats"], c["total_seats"], c["gap"],
                c["nearest_verified_centre_km"], c["share_of_demand_with_no_verified_batch"],
                c["coverage"], c["severity_score"], c["suppressed"],
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=planning_brief_{brief_id}.csv"
            },
        )


# ============================================================================
# Legacy Endpoints (Backwards Compatibility)
# ============================================================================
@router.get("/supply-gap-matrix")
def get_supply_gap_matrix(
    district: str = "Moradabad",
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    """Legacy alias for GET /planning/matrix."""
    enforce_district_scope(actor, district)
    with get_db() as conn:
        return AggregationService(conn).get_demand_supply_matrix(district)


@router.post("/generate-brief", status_code=201)
def legacy_generate_brief(req: GenerateBriefRequest, actor: PlanningActor = Depends(require_district_officer_or_admin)):
    """Legacy alias for POST /planning/briefs/generate."""
    return generate_brief(req, actor)


@router.get("/briefs")
def list_briefs(
    district: Optional[str] = None,
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    """Lists briefs. Officers are scoped to their own district; admins may filter by any district."""
    if actor.actor_role == 'district_officer':
        enforce_district_scope(actor, district or actor.district or '')
    with get_db() as conn:
        query = "SELECT * FROM planning_briefs WHERE 1=1"
        params: List[Any] = []
        if actor.actor_role == "district_officer":
            query += " AND LOWER(district) = LOWER(?)"
            params.append(actor.district)
        elif district:
            query += " AND district = ?"
            params.append(district)
        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["aggregation_snapshot"] = json.loads(d.get("aggregation_snapshot") or "{}")
            d["suggested_policy_actions"] = json.loads(d.get("suggested_policy_actions") or "[]")
            results.append(d)
        return results


@router.get("/export")
def export_plan(
    district: str = "Moradabad",
    actor: PlanningActor = Depends(require_district_officer_or_admin),
):
    """Legacy CSV export of the district demand-vs-supply matrix (real query data)."""
    enforce_district_scope(actor, district)
    with get_db() as conn:
        matrix = AggregationService(conn).get_demand_supply_matrix(district)
        if matrix["status"] == "insufficient_data":
            raise HTTPException(status_code=422, detail={"status": "insufficient_data", "message": matrix["message"]})

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "block", "qualification", "demand_count", "verified_seats", "gap",
            "nearest_verified_centre_km", "severity_score", "suppressed",
        ])
        for c in matrix["matrix"]:
            writer.writerow([
                c["block"], c["qualification_title"], c["demand_count"],
                c["verified_seats"], c["gap"], c["nearest_verified_centre_km"],
                c["severity_score"], c["suppressed"],
            ])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=AAP_Plan_{district}.csv"},
        )


def _suggested_actions(matrix: Dict[str, Any]) -> List[str]:
    """Template-derived actions; every number comes from the aggregation query."""
    actions: List[str] = []
    visible = [c for c in matrix["matrix"] if not c["suppressed"]]
    for c in visible[:3]:
        if c["gap"] is not None and c["gap"] > 0:
            actions.append(
                f"Sanction additional worker-verified {c['qualification_title']} batches in "
                f"{c['block']}; unmet demand is {c['gap']} seats against {c['demand_count']} "
                f"expressions of interest."
            )
        if c["nearest_verified_centre_km"] is None:
            actions.append(
                f"Deploy a mobile skilling unit for {c['qualification_title']} in {c['block']}: "
                f"no worker-verified centre exists anywhere in {matrix['district']}."
            )
        elif c["nearest_verified_centre_km"] > matrix["data_basis"]["distance_cap_km"]:
            actions.append(
                f"Deploy a mobile skilling unit for {c['qualification_title']} in {c['block']}: "
                f"nearest verified centre is {c['nearest_verified_centre_km']} km away."
            )
    if not actions:
        actions.append("No sanctionable gaps met the reporting threshold; maintain existing verified capacity.")
    return actions
