from fastapi import APIRouter, HTTPException, Depends, Query, Response, Request
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.database import get_db
from app.models import GenerateBriefRequest, SignOffRequest
from app.ai_layers.layer5_planning.aggregation_service import AggregationService as LegacyAggregationService
from app.ai_layers.layer5_planning.narrative_engine import NarrativeEngine
from app.dependencies.auth import get_current_actor, require_authenticated_user, Actor
from app.core.settings import settings
from app.services.planning_aggregation_service import PlanningAggregationService
from app.services.planning_snapshot_service import PlanningSnapshotService
from app.services.planning_export_service import PlanningExportService
from app.schemas.planning import (
    PlanningOverviewResponse,
    DemandReportResponse,
    SupplyReportResponse,
    GapReportResponse,
    ReferralFunnelResponse,
    OutcomesResponse,
    DataQualityResponse,
    GeographicCoverageResponse,
    SnapshotCreateRequest,
    SnapshotReviewRequest,
    SnapshotApproveRequest,
    SnapshotResponse,
    ExportCreateRequest,
    ExportResponse,
)
from app.utils.audit_events import log_audit_event, log_isolated_audit_event

router = APIRouter(prefix="/planning", tags=["District-Planning"])

PLANNING_STAFF_ROLES = {"district_admin", "district_officer", "auditor", "super_admin"}


def _actor_to_dict(actor: Actor) -> Dict[str, Any]:
    district = None
    if actor.scopes:
        for s in actor.scopes:
            d = s.get("district_id") or s.get("district")
            if d:
                district = d
                break
    if not district and actor.db_user:
        district = actor.db_user.get("district") or actor.db_user.get("assigned_district")
    if not district and actor.actor_role == "district_officer":
        district = settings.OFFICER_DISTRICT
    return {
        "id": actor.actor_id,
        "role": actor.actor_role,
        "name": actor.actor_name,
        "district": district or "",
        "roles": actor.roles,
        "scopes": actor.scopes,
    }


def _enforce_planning_access(actor: Actor, target_district: str) -> Dict[str, Any]:
    user_dict = _actor_to_dict(actor)
    role = actor.actor_role or ""

    # Check role
    has_planning_role = any(r in PLANNING_STAFF_ROLES for r in actor.roles) or role in PLANNING_STAFF_ROLES
    if not has_planning_role:
        log_isolated_audit_event(
            actor_id=actor.actor_id,
            actor_name=actor.actor_name or "Staff",
            actor_role=role,
            action="SECURITY_ACCESS_DENIED",
            entity_type="planning_dashboard",
            entity_id=target_district,
            old_values=None,
            new_values={"role": role, "required_roles": list(PLANNING_STAFF_ROLES)},
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden: district planning requires district_admin, auditor, or super_admin role",
        )

    # Check geographic scope (super_admin has global access)
    if "super_admin" not in actor.roles and role != "super_admin":
        user_dist = user_dict.get("district") or ""
        if user_dist.strip().lower() != target_district.strip().lower():
            log_isolated_audit_event(
                actor_id=actor.actor_id,
                actor_name=actor.actor_name or "Staff",
                actor_role=role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="planning_dashboard",
                entity_id=target_district,
                old_values={"authorized_district": user_dist},
                new_values={"attempted_district": target_district},
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "DISTRICT_SCOPE_VIOLATION",
                    "authorized_district": user_dist,
                    "attempted_district": target_district,
                },
            )

    return user_dict


# =============================================================================
# SPRINT 6: AUTHORITATIVE DASHBOARD AGGREGATIONS
# =============================================================================

@router.get("/overview", response_model=PlanningOverviewResponse)
def get_planning_overview(
    district_id: str = Query("Moradabad", description="Target district for planning"),
    block_id: Optional[str] = Query(None, description="Optional block filter"),
    actor: Actor = Depends(get_current_actor),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_overview_aggregation(district_id, block_id)


@router.get("/demand", response_model=DemandReportResponse)
def get_planning_demand(
    district_id: str = Query("Moradabad"),
    block_id: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_demand_metrics(district_id, block_id, period_start, period_end)


@router.get("/supply", response_model=SupplyReportResponse)
def get_planning_supply(
    district_id: str = Query("Moradabad"),
    block_id: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_supply_metrics(district_id, block_id)


@router.get("/gaps", response_model=GapReportResponse)
def get_planning_gaps(
    district_id: str = Query("Moradabad"),
    block_id: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_gap_metrics(district_id, block_id)


@router.get("/referral-funnel", response_model=ReferralFunnelResponse)
def get_planning_funnel(
    district_id: str = Query("Moradabad"),
    block_id: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_referral_funnel_metrics(district_id, block_id)


@router.get("/outcomes", response_model=OutcomesResponse)
def get_planning_outcomes(
    district_id: str = Query("Moradabad"),
    block_id: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_outcome_metrics(district_id, block_id)


@router.get("/data-quality", response_model=DataQualityResponse)
def get_planning_data_quality(
    district_id: str = Query("Moradabad"),
    block_id: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_data_quality_metrics(district_id, block_id)


@router.get("/geographic-coverage", response_model=GeographicCoverageResponse)
def get_planning_geographic_coverage(
    district_id: str = Query("Moradabad"),
    actor: Actor = Depends(require_authenticated_user),
):
    _enforce_planning_access(actor, district_id)
    with get_db() as conn:
        service = PlanningAggregationService(conn)
        return service.get_geographic_coverage(district_id)


# =============================================================================
# SPRINT 6: IMMUTABLE PLANNING SNAPSHOTS
# =============================================================================

@router.post("/snapshots", response_model=SnapshotResponse, status_code=201)
def create_planning_snapshot(
    req: SnapshotCreateRequest,
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _enforce_planning_access(actor, req.district_id)
    if actor.actor_role not in ["district_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Only district_admin or super_admin can generate snapshots")

    with get_db() as conn:
        return PlanningSnapshotService.create_snapshot(conn, user_dict, req)


@router.get("/snapshots", response_model=List[SnapshotResponse])
def list_planning_snapshots(
    district_id: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    target_dist = district_id or _actor_to_dict(actor).get("district") or "Moradabad"
    user_dict = _enforce_planning_access(actor, target_dist)
    with get_db() as conn:
        return PlanningSnapshotService.list_snapshots(conn, user_dict, target_dist)


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
def get_planning_snapshot(
    snapshot_id: str,
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningSnapshotService.get_snapshot(conn, user_dict, snapshot_id)


@router.post("/snapshots/{snapshot_id}/review", response_model=SnapshotResponse)
def review_planning_snapshot(
    snapshot_id: str,
    req: SnapshotReviewRequest,
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningSnapshotService.review_snapshot(conn, user_dict, snapshot_id, req.notes)


@router.post("/snapshots/{snapshot_id}/approve", response_model=SnapshotResponse)
def approve_planning_snapshot(
    snapshot_id: str,
    req: SnapshotApproveRequest,
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningSnapshotService.approve_snapshot(conn, user_dict, snapshot_id, req.notes)


# =============================================================================
# SPRINT 6: CONTROLLED EXPORTS (CSV & PDF)
# =============================================================================

@router.post("/snapshots/{snapshot_id}/exports/csv", response_model=ExportResponse, status_code=201)
def export_snapshot_csv(
    snapshot_id: str,
    scope: str = Query("FULL_REPORT", description="Export scope"),
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningExportService.create_export(conn, user_dict, snapshot_id, "CSV", scope)


@router.post("/snapshots/{snapshot_id}/exports/pdf", response_model=ExportResponse, status_code=201)
def export_snapshot_pdf(
    snapshot_id: str,
    scope: str = Query("FULL_REPORT", description="Export scope"),
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningExportService.create_export(conn, user_dict, snapshot_id, "PDF", scope)


@router.get("/exports", response_model=List[ExportResponse])
def list_planning_exports(
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningExportService.list_exports(conn, user_dict)


@router.get("/exports/{export_id}", response_model=ExportResponse)
def get_planning_export(
    export_id: str,
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningExportService.get_export(conn, user_dict, export_id)


@router.get("/exports/{export_id}/download")
def download_planning_export(
    export_id: str,
    actor: Actor = Depends(require_authenticated_user),
):
    user_dict = _actor_to_dict(actor)
    with get_db() as conn:
        return PlanningExportService.download_export(conn, user_dict, export_id)


# =============================================================================
# LEGACY ROUTES (PRESERVED FOR BACKWARD COMPATIBILITY)
# =============================================================================

@router.get("/supply-gap-matrix")
def get_supply_gap_matrix(district: str = "Moradabad"):
    with get_db() as conn:
        service = LegacyAggregationService(conn)
        return service.get_demand_supply_matrix(district)


@router.get("/matrix")
def get_planning_matrix(
    district: str = Query("Moradabad"),
    actor: Actor = Depends(get_current_actor),
):
    _enforce_planning_access(actor, district)
    with get_db() as conn:
        return LegacyAggregationService(conn).get_demand_supply_matrix(district)


@router.post("/generate-brief", status_code=201)
@router.post("/briefs/generate", status_code=201)
def generate_brief(
    req: GenerateBriefRequest,
    actor: Actor = Depends(get_current_actor),
):
    _enforce_planning_access(actor, req.district)
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        service = LegacyAggregationService(conn)
        matrix = service.get_demand_supply_matrix(req.district)
        if matrix.get("status") == "insufficient_data":
            raise HTTPException(status_code=422, detail=matrix)
        narrative = NarrativeEngine.generate_brief(matrix)["narrative"]
        metrics = matrix.get("metrics", {})

        brief_id = f"brief_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO planning_briefs (
                id, district, period, total_beneficiaries_interviewed, total_verified_matches,
                total_supply_gaps, aggregation_snapshot, generated_narrative, suggested_policy_actions,
                reviewer_sign_off_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?);
        """, (
            brief_id, req.district, req.period,
            metrics.get("beneficiaries_interviewed", metrics.get("total_demand_records", 0)),
            metrics.get("verified_matches", metrics.get("demand_with_verified_match_count", 0)),
            metrics.get("planning_supply_gaps", metrics.get("total_unmet_demand", 0)),
            json.dumps(matrix), narrative,
            json.dumps(["Deploy Mobile Skilling Unit for Block Bahjoi", "Sanction additional Mushroom & Solar batches"]),
            now, now
        ))
        log_audit_event(
            conn, "system", "System", "system", "BRIEF_GENERATED",
            "planning_brief", brief_id, new_values={"district": req.district},
        )

        return {
            "brief_id": brief_id,
            "district": req.district,
            "period": req.period,
            "generated_narrative": narrative,
            "status": "draft"
        }


@router.get("/briefs")
def list_briefs(
    district: Optional[str] = None,
    actor: Actor = Depends(require_authenticated_user),
):
    actor_district = _actor_to_dict(actor)["district"]
    target_district = district or actor_district
    if not target_district:
        raise HTTPException(status_code=403, detail="A configured district scope is required")
    _enforce_planning_access(actor, target_district)
    with get_db() as conn:
        query = "SELECT * FROM planning_briefs WHERE 1=1"
        params = [target_district]
        if target_district:
            query += " AND district = ?"
        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["aggregation_snapshot"] = json.loads(d.get("aggregation_snapshot") or "{}")
            d["suggested_policy_actions"] = json.loads(d.get("suggested_policy_actions") or "[]")
            results.append(d)
        return results


@router.get("/briefs/{brief_id}")
def get_brief_by_id(
    brief_id: str,
    actor: Actor = Depends(require_authenticated_user),
):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM planning_briefs WHERE id = ?;", (brief_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        _enforce_planning_access(actor, row["district"])
        d = dict(row)
        d["aggregation_snapshot"] = json.loads(d.get("aggregation_snapshot") or "{}")
        d["suggested_policy_actions"] = json.loads(d.get("suggested_policy_actions") or "[]")
        return d


@router.post("/briefs/{brief_id}/sign-off")
def sign_off_brief(
    brief_id: str,
    req: SignOffRequest,
    actor: Actor = Depends(get_current_actor),
):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT district, reviewer_sign_off_status FROM planning_briefs WHERE id = ?;",
            (brief_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        _enforce_planning_access(actor, row["district"])
        old_status = row["reviewer_sign_off_status"]
        if req.action == "submit_for_review" and old_status == "draft":
            new_status, audit_action = "under_review", "BRIEF_UNDER_REVIEW"
        elif req.action == "sign_off" and old_status == "under_review":
            new_status, audit_action = "signed_off", "BRIEF_SIGNED_OFF"
        else:
            raise HTTPException(status_code=409, detail="Invalid planning brief lifecycle transition")
        conn.execute("""
            UPDATE planning_briefs
            SET reviewer_sign_off_status = ?, signed_off_by = ?, signed_off_at = ?, updated_at = ?
            WHERE id = ?;
        """, (new_status, req.officer_name, now, now, brief_id))
        log_audit_event(
            conn, actor.actor_id, actor.actor_name, actor.actor_role,
            audit_action, "planning_brief", brief_id,
            old_values={"status": old_status}, new_values={"status": new_status},
        )

        return {
            "brief_id": brief_id,
            "status": new_status,
            "signed_off_by": req.officer_name,
            "timestamp": now
        }


@router.get("/briefs/{brief_id}/export")
def export_brief(
    brief_id: str,
    format: str = Query("csv", pattern="^(csv|json)$"),
    actor: Actor = Depends(get_current_actor),
):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM planning_briefs WHERE id = ?;", (brief_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        _enforce_planning_access(actor, row["district"])
        if row["reviewer_sign_off_status"] != "signed_off":
            raise HTTPException(
                status_code=409,
                detail={"error": "BRIEF_NOT_SIGNED_OFF", "message": "Brief must be signed off before export"},
            )
        snapshot = json.loads(row["aggregation_snapshot"] or "{}")
        if format == "json":
            return {
                "export_format": "pdf_ready_json",
                "brief_id": brief_id,
                "district": row["district"],
                "period": row["period"],
                "generated_narrative": row["generated_narrative"],
                "aggregation_snapshot": snapshot,
            }
        lines = ["block,qualification,demand_count,verified_seats,gap"]
        for cell in snapshot.get("matrix", []):
            if not cell.get("suppressed"):
                lines.append(
                    f'{cell["block"]},{cell["qualification_title"]},'
                    f'{cell["demand_count"]},{cell["verified_seats"]},{cell["gap"]}'
                )
        return Response("\n".join(lines), media_type="text/csv")


@router.get("/export")
def export_plan(district: str = "Moradabad"):
    csv_content = (
        "Trade Name,Expressed Voice Demand,Sanctioned Seats,Supply Gap,Status\n"
        "Mushroom Cultivation,460,120,-340,High Deficit\n"
        "Solar PV Installer,420,120,-300,Severe Deficit\n"
        "Sewing Machine Operator,510,480,-30,Balanced Supply\n"
        "Retail Sales Associate,380,200,-180,Waitlisted\n"
    )
    return Response(content=csv_content, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=AAP_Plan_{district}_2026.csv"
    })
