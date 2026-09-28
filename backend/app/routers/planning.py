from fastapi import APIRouter, HTTPException, Response
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models import GenerateBriefRequest, SignOffRequest
from app.ai_layers.layer5_planning.aggregation_service import AggregationService
from app.ai_layers.layer5_planning.narrative_engine import NarrativeEngine

router = APIRouter(prefix="/planning", tags=["District-Planning"])

@router.get("/supply-gap-matrix")
def get_supply_gap_matrix(district: str = "Moradabad"):
    with get_db() as conn:
        service = AggregationService(conn)
        return service.get_demand_supply_matrix(district)

@router.post("/generate-brief", status_code=201)
def generate_brief(req: GenerateBriefRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        service = AggregationService(conn)
        matrix = service.get_demand_supply_matrix(req.district)
        narrative = NarrativeEngine.generate_brief_narrative(matrix)

        brief_id = f"brief_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO planning_briefs (
                id, district, period, total_beneficiaries_interviewed, total_verified_matches,
                total_supply_gaps, aggregation_snapshot, generated_narrative, suggested_policy_actions,
                reviewer_sign_off_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?);
        """, (
            brief_id, req.district, req.period,
            matrix["metrics"]["beneficiaries_interviewed"],
            matrix["metrics"]["verified_matches"],
            matrix["metrics"]["planning_supply_gaps"],
            json.dumps(matrix), narrative,
            json.dumps(["Deploy Mobile Skilling Unit for Block Bahjoi", "Sanction additional Mushroom & Solar batches"]),
            now, now
        ))

        return {
            "brief_id": brief_id,
            "district": req.district,
            "period": req.period,
            "generated_narrative": narrative,
            "status": "draft"
        }

@router.get("/briefs")
def list_briefs(district: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM planning_briefs WHERE 1=1"
        params = []
        if district:
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

@router.get("/briefs/{brief_id}")
def get_brief_by_id(brief_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM planning_briefs WHERE id = ?;", (brief_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planning brief not found")
        d = dict(row)
        d["aggregation_snapshot"] = json.loads(d.get("aggregation_snapshot") or "{}")
        d["suggested_policy_actions"] = json.loads(d.get("suggested_policy_actions") or "[]")
        return d

@router.post("/briefs/{brief_id}/sign-off")
def sign_off_brief(brief_id: str, req: SignOffRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("""
            UPDATE planning_briefs
            SET reviewer_sign_off_status = 'signed_off', signed_off_by = ?, signed_off_at = ?, updated_at = ?
            WHERE id = ?;
        """, (req.officer_name, now, now, brief_id))

        return {
            "brief_id": brief_id,
            "status": "signed_off",
            "signed_off_by": req.officer_name,
            "timestamp": now
        }

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
