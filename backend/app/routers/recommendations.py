from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
from app.database import get_db
from app.models import GenerateRecommendationsRequest, RecommendationMatchRequest
from app.services.recommendation_service import RecommendationService
from app.ai_layers.layer3_matching.matching_engine import MatchingEngine
from app.dependencies.auth import get_current_actor, Actor
import uuid
import json
from datetime import datetime, timezone

router = APIRouter(tags=["Recommendations"])

# ============================================================================
# A5. Deterministic Recommendations Endpoints
# ============================================================================
@router.post("/recommendations/generate")
def generate_recommendations(
    req: GenerateRecommendationsRequest,
    actor: Actor = Depends(get_current_actor)
):
    """
    Deterministic matching and recommendation engine based on verified catalog and confirmed profile answers.
    """
    with get_db() as conn:
        return RecommendationService.generate_recommendations(conn, req, actor_id=actor.actor_id)

@router.get("/recommendations/{recommendation_id}")
def get_recommendation_detail(recommendation_id: str):
    """
    Retrieves detailed structured recommendation record with verification snapshot.
    """
    with get_db() as conn:
        return RecommendationService.get_recommendation_by_id(conn, recommendation_id)

@router.get("/interviews/{interview_id}/recommendations")
def get_interview_recommendations(interview_id: str):
    """
    Retrieves recommendations generated for a specific interview session.
    """
    with get_db() as conn:
        recs = RecommendationService.get_recommendations_for_interview(conn, interview_id)
        return {
            "interview_id": interview_id,
            "count": len(recs),
            "recommendations": recs
        }

# ============================================================================
# Legacy Recommendations Endpoints (Backwards Compatibility)
# ============================================================================
@router.post("/recommendations/match")
def legacy_match(req: RecommendationMatchRequest, actor: Actor = Depends(get_current_actor)):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        engine = MatchingEngine(conn)
        top_matches = engine.match(req.model_dump())

        saved_recs = []
        for match in top_matches:
            rec_id = f"rec_{uuid.uuid4().hex[:10]}"
            qual = match["qualification"]
            best_opp = match["best_opportunity"]

            conn.execute("""
                INSERT INTO recommendations (
                    id, beneficiary_id, session_id, interview_id, qualification_id, local_opportunity_id,
                    rank, score, score_breakdown, match_state, explanation_text,
                    audio_explanation_script, tradeoff_summary, skill_gap_summary,
                    data_snapshot, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                rec_id, req.beneficiaryId, req.sessionId, req.interview_id or req.sessionId, qual["id"],
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

@router.get("/recommendations/beneficiary/{beneficiary_id}")
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

@router.get("/recommendations/{rec_id}/details")
def legacy_get_details(rec_id: str):
    return get_recommendation_detail(rec_id)

@router.get("/recommendations/compare/{id1}/{id2}")
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
