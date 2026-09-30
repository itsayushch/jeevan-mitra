import json
import sqlite3
from typing import List, Dict, Any, Optional
from app.utils.distance import calculate_distance_km, get_block_coordinates
from app.ai_layers.layer2_extraction.validation import education_to_rank
from app.ai_layers.layer3_matching.state_machine import MatchStateMachine
from app.ai_layers.layer3_matching.explanation_generator import ExplanationGenerator
from app.utils.logger import logger

class MatchingEngine:
    """Grounded matching engine against closed verified NQR catalogue with 5-factor scoring."""

    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn

    def match(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        district = input_data.get("district", "Moradabad")
        block = input_data.get("block", "Chhajlet")
        user_edu = input_data.get("educationLevel", "Class 8")
        interests = [i.lower() for i in input_data.get("interests", [])]
        skills = [s.lower() for s in input_data.get("skills", [])]
        mobility_radius = float(input_data.get("mobilityRadiusKm", 5.0))
        work_pref = input_data.get("workPreference", "both")
        lang = input_data.get("preferredLanguage", "hi")

        user_edu_rank = education_to_rank(user_edu)
        user_coords = get_block_coordinates(block)

        # 1. Fetch verified qualifications (support both legacy 'verified' and Sprint4 'VERIFIED')
        cursor = self.conn.execute("SELECT * FROM qualifications WHERE UPPER(verification_status) = 'VERIFIED';")
        quals = [dict(r) for r in cursor.fetchall()]

        # 2. Fetch active, non-expired local opportunities for this district
        opp_cursor = self.conn.execute("""
            SELECT * FROM local_opportunities
            WHERE (LOWER(district) = LOWER(?) OR LOWER(district_id) = LOWER(?))
                AND status IN ('ACTIVE', 'active', 'upcoming')
                AND (available_seats > 0 OR seats_available > 0)
                AND (verified_by_worker_id IS NOT NULL OR verified_by_user_id IS NOT NULL)
                AND (batch_end_date >= date('now') OR end_date >= date('now') OR batch_end_date IS NULL)
                AND (verification_expires_at IS NULL OR verification_expires_at > datetime('now'));
        """, (district, district))
        all_opps = [dict(r) for r in opp_cursor.fetchall()]

        scored_list = []

        for qual in quals:
            # Hard Filter 1: Education rank
            min_rank = qual.get("min_education_rank") or 0
            if user_edu_rank < min_rank:
                continue

            # Find matching opportunities within radius
            matching_opps = []
            for opp in all_opps:
                if opp.get("qualification_id") == qual.get("id"):
                    dist = calculate_distance_km(
                        user_coords['lat'], user_coords['lon'],
                        opp.get("latitude", user_coords['lat']), opp.get("longitude", user_coords['lon'])
                    )
                    if dist <= mobility_radius:
                        opp_with_dist = dict(opp)
                        opp_with_dist["distance_km"] = dist
                        matching_opps.append(opp_with_dist)

            matching_opps.sort(key=lambda x: x["distance_km"])
            best_opp = matching_opps[0] if matching_opps else None

            # Calculate 5-Factor Weighted Score (Max 100)
            # Factor 1: Interest match (Weight: 30)
            interest_score = 0.0
            qual_title = qual.get("title", "").lower()
            qual_sector = qual.get("sector", "").lower()
            for it in interests:
                if it in qual_title or it in qual_sector:
                    interest_score = 30.0
                    break
                elif any(word in qual_title for word in it.split()):
                    interest_score = max(interest_score, 20.0)

            # Factor 2: Skill alignment (Weight: 20)
            skill_score = 15.0 if interest_score > 0 else 10.0

            # Factor 3: Proximity & Access (Weight: 20)
            if best_opp:
                d = best_opp["distance_km"]
                access_score = max(5.0, 20.0 - (d * 2.0))
            else:
                access_score = 0.0

            # Factor 4: District demand / seat availability (Weight: 15)
            demand_score = 15.0 if best_opp else 5.0

            # Factor 5: Work preference alignment (Weight: 15)
            qual_work_type = qual.get("work_type", "both")
            if work_pref == "both" or qual_work_type == "both" or qual_work_type == work_pref:
                pref_score = 15.0
            else:
                pref_score = 5.0

            total_score = round(interest_score + skill_score + access_score + demand_score + pref_score, 1)

            # Determine initial state (Verified Match only if live verified batch exists with seats)
            avail_seats = best_opp.get("available_seats") or best_opp.get("seats_available", 0) if best_opp else 0
            has_verified_batch = best_opp is not None and avail_seats > 0
            match_state = MatchStateMachine.determine_initial_state(has_verified_batch)

            # Generate explanations
            expl = ExplanationGenerator.generate(qual, best_opp, interests, match_state, lang)

            scored_list.append({
                "qualification": qual,
                "best_opportunity": best_opp,
                "score": total_score,
                "score_breakdown": {
                    "interest": interest_score,
                    "skill": skill_score,
                    "accessibility": access_score,
                    "demand": demand_score,
                    "preference": pref_score
                },
                "match_state": match_state,
                "explanation_text": expl["explanation_text"],
                "audio_explanation_script": expl["audio_explanation_script"],
                "tradeoff_summary": expl["tradeoff_summary"],
                "skill_gap_summary": expl["skill_gap_summary"]
            })

        # Rank by score descending and return top 3
        scored_list.sort(key=lambda x: x["score"], reverse=True)
        top_matches = scored_list[:3]

        for i, match_item in enumerate(top_matches):
            match_item["rank"] = i + 1

        return top_matches
