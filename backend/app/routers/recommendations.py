from fastapi import APIRouter, HTTPException
import uuid
import json
from datetime import datetime, timezone
from app.database import get_db
from app.models import RecommendationMatchRequest
from app.ai_layers.layer3_matching.matching_engine import MatchingEngine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.post("/match")
def match_recommendations(req: RecommendationMatchRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        engine = MatchingEngine(conn)
        top_matches = engine.match(req.model_dump())

        # Persist recommendations to DB
        saved_recs = []
        for match in top_matches:
            rec_id = f"rec_{uuid.uuid4().hex[:10]}"
            qual = match["qualification"]
            best_opp = match["best_opportunity"]

            conn.execute("""
                INSERT INTO recommendations (
                    id, beneficiary_id, session_id, qualification_id, local_opportunity_id,
                    rank, score, score_breakdown, match_state, explanation_text,
                    audio_explanation_script, tradeoff_summary, skill_gap_summary,
                    data_snapshot, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                rec_id, req.beneficiaryId, req.sessionId, qual["id"],
                best_opp["id"] if best_opp else None,
                match["rank"], match["score"], json.dumps(match["score_breakdown"]),
                match["match_state"], match["explanation_text"], match["audio_explanation_script"],
                match["tradeoff_summary"], match["skill_gap_summary"],
                json.dumps({"qualification": qual, "opportunity": best_opp}),
                now, now
            ))

            rec_obj = dict(match)
            rec_obj["id"] = rec_id
            saved_recs.append(rec_obj)

        return {
            "beneficiary_id": req.beneficiaryId,
            "count": len(saved_recs),
            "recommendations": saved_recs
        }

@router.get("/beneficiary/{beneficiary_id}")
def get_by_beneficiary(beneficiary_id: str):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT r.*, q.title as qualification_title, q.sector, q.nsqf_level, q.work_type,
                   o.centre_or_employer_name, o.batch_start_date, o.available_seats, o.stipend_amount_inr
            FROM recommendations r
            JOIN qualifications q ON r.qualification_id = q.id
            LEFT JOIN local_opportunities o ON r.local_opportunity_id = o.id
            WHERE r.beneficiary_id = ?
            ORDER BY r.rank ASC;
        """, (beneficiary_id,)).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["score_breakdown"] = json.loads(d.get("score_breakdown") or "{}")
            results.append(d)

        return results

@router.get("/{rec_id}/details")
def get_details(rec_id: str):
    with get_db() as conn:
        row = conn.execute("""
            SELECT r.*, q.title as qualification_title, q.sector, q.nsqf_level, q.work_type,
                   q.curriculum_summary, q.entry_criteria, q.certification_body, q.nqr_link,
                   o.centre_or_employer_name, o.address, o.batch_start_date, o.batch_end_date,
                   o.available_seats, o.stipend_amount_inr, o.free_toolkit_provided
            FROM recommendations r
            JOIN qualifications q ON r.qualification_id = q.id
            LEFT JOIN local_opportunities o ON r.local_opportunity_id = o.id
            WHERE r.id = ?;
        """, (rec_id,)).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        res = dict(row)
        res["score_breakdown"] = json.loads(res.get("score_breakdown") or "{}")
        return res

@router.get("/compare/{id1}/{id2}")
def compare_recommendations(id1: str, id2: str):
    with get_db() as conn:
        r1 = conn.execute("SELECT * FROM recommendations WHERE id = ?;", (id1,)).fetchone()
        r2 = conn.execute("SELECT * FROM recommendations WHERE id = ?;", (id2,)).fetchone()

        if not r1 or not r2:
            raise HTTPException(status_code=404, detail="One or both recommendations not found")

        return {
            "option_1": dict(r1),
            "option_2": dict(r2)
        }
