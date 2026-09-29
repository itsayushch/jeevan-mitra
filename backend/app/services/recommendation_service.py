import uuid
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models import GenerateRecommendationsRequest
from app.utils.distance import calculate_distance_km, get_block_coordinates
from app.ai_layers.layer2_extraction.validation import education_to_rank
from app.ai_layers.layer3_matching.explanation_generator import ExplanationGenerator
from app.services.catalogue_service import CatalogueService
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException
from app.ai_layers.layer5_planning.demand_record_service import DemandRecordService, current_period_label
from app.utils.logger import logger
from app.ai_layers.layer3_matching.ml_adapter import rerank_candidates

class RecommendationService:
    @staticmethod
    def generate_recommendations(
        conn, req, actor_id: str = "system"
    ) -> dict:
        from datetime import datetime, timezone
        import json
        import httpx
        from app.config import settings
        import uuid
        
        target_interview_id = req.interview_id or req.session_id
        
        # Build profile context
        confirmed_profile = {}
        if target_interview_id:
            f_rows = conn.execute("SELECT field_name, field_value FROM profile_field_values WHERE interview_id = ? AND user_confirmed = 1;", (target_interview_id,)).fetchall()
            for r in f_rows:
                try:
                    confirmed_profile[r["field_name"]] = json.loads(r["field_value"])
                except:
                    confirmed_profile[r["field_name"]] = r["field_value"]

        # RAG context (mocked for prototype)
        rag_docs = [
            "Mushroom Cultivation: Covers oyster and button mushroom farming. Requires Class 8. Duration 200 hours. High local demand. Sector: Agriculture. NSQF: 3. Code: AGR/Q0401.",
            "Solar PV Installation: Install, test solar panels. Requires Class 10. Duration 300 hours. Green energy. Sector: Electronics. NSQF: 4. Code: ELE/Q5901.",
            "Retail Operations: Inventory management, merchandising. Requires Class 10. Duration 250 hours. Sector: Retail. NSQF: 4. Code: RAS/Q0104.",
            "Tractor Mechanic: Engine repair, hydraulics. Requires Class 8. Duration 200 hours. Sector: Automotive. NSQF: 3. Code: ASC/Q1001."
        ]
        context = " \n".join(rag_docs)
        
        prompt = f"User Profile: {json.dumps(confirmed_profile)}\n\nCatalogue Context:\n{context}\n\nBased on the user's profile and the context, recommend exactly 3 courses. Format your response strictly as a JSON object with a single key 'recommendations', containing an array of objects matching this exact structure: {{\"recommendation_id\": \"uuid\", \"qualification\": {{\"id\": \"uuid\", \"title\": \"Course Name\", \"nsqf_level\": 3, \"duration_hours\": 200, \"sector\": \"Sector Name\", \"official_url\": \"\", \"nqr_code\": \"\"}}, \"why_recommended\": [\"Reason 1\"], \"caveat\": \"Caveat\", \"matched_skills\": [], \"skill_gaps\": [], \"local_availability\": {{\"status\": \"verified_open\", \"district\": \"Moradabad\", \"centre_name\": \"Local Centre\"}}}}."

        groq_key = settings.GROQ_API_KEY
        try:
            resp = httpx.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {groq_key}'},
                json={
                    'model': settings.GROQ_MODEL,
                    'messages': [
                        {'role': 'system', 'content': 'You are a career counselor AI. Output ONLY valid JSON.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'response_format': {'type': 'json_object'},
                    'temperature': 0.1
                },
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()['choices'][0]['message']['content']
            recs = json.loads(data).get('recommendations', [])
            
            # Ensure unique IDs
            for rec in recs:
                rec['recommendation_id'] = str(uuid.uuid4())
                if 'qualification' in rec:
                    rec['qualification']['id'] = str(uuid.uuid4())
                    
        except Exception as e:
            # Fallback
            print(f"RAG Error: {e}")
            recs = []

        return {
            "interview_id": target_interview_id,
            "count": len(recs),
            "recommendations": recs,
            "metrics": {}
        }

    @staticmethod
    def get_recommendation_by_id(conn: sqlite3.Connection, rec_id: str) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM recommendations WHERE id = ?;", (rec_id,)).fetchone()
        if not row:
            raise EntityNotFoundException("Recommendation", rec_id)

        d = dict(row)
        qual_row = conn.execute("SELECT * FROM qualifications WHERE id = ?;", (d["qualification_id"],)).fetchone()
        opp_row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?;", (d["local_opportunity_id"],)).fetchone() if d.get("local_opportunity_id") else None

        qual_row = dict(qual_row) if qual_row else None
        opp_row = dict(opp_row) if opp_row else None
        qual_info = {
            "id": qual_row["nqr_code"] if qual_row else d["qualification_id"],
            "nqr_code": qual_row["nqr_code"] if qual_row else "",
            "sector": qual_row["sector"] if qual_row else "",
            "duration_hours": qual_row["duration_hours"] if qual_row else None,
            "title": qual_row["title"] if qual_row else "Qualification",
            "nsqf_level": qual_row["nsqf_level"] if qual_row else None,
            "official_url": (qual_row.get("official_source_url") or qual_row.get("nqr_link")) if qual_row else ""
        }

        return {
            "recommendation_id": d["id"],
            "qualification": qual_info,
            "ranking_factors": json.loads(d.get("ranking_factors") or "{}"),
            "why_recommended": [d["explanation_text"]] if d.get("explanation_text") else [],
            "matched_skills": json.loads(d.get("matched_skills") or "[]"),
            "skill_gaps": json.loads(d.get("skill_gaps") or "[]"),
            "local_availability": {
                "status": d.get("local_opportunity_status") or "unknown",
                "centre_name": opp_row.get("centre_or_employer_name") if opp_row else None,
                "district": opp_row["district"] if opp_row else None,
                "source_url": opp_row.get("source_url") if opp_row else None,
                "last_verified_at": opp_row.get("verified_at") if opp_row else None
            },
            "caveat": d.get("caveat") or "This is a guidance recommendation, not confirmation of admission or placement.",
            "score": d["score"]
        }

    @staticmethod
    def get_recommendations_for_interview(conn: sqlite3.Connection, interview_id: str) -> List[Dict[str, Any]]:
        rows = conn.execute("""
            SELECT id FROM recommendations
            WHERE interview_id = ? OR session_id = ?
            ORDER BY rank ASC;
        """, (interview_id, interview_id)).fetchall()

        return [RecommendationService.get_recommendation_by_id(conn, r["id"]) for r in rows]
