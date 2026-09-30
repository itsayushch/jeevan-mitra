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

class RecommendationService:
    @staticmethod
    def generate_recommendations(
        conn: sqlite3.Connection,
        req: GenerateRecommendationsRequest,
        actor_id: str = "system"
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        
        # 1. Retrieve confirmed profile answers
        confirmed_profile: Dict[str, Any] = {}
        target_ben_id = req.beneficiary_id
        target_interview_id = req.interview_id or req.session_id

        if target_interview_id:
            # Query confirmed fields for this interview
            f_rows = conn.execute("""
                SELECT field_name, field_value, user_confirmed, source
                FROM profile_field_values
                WHERE interview_id = ? AND user_confirmed = 1;
            """, (target_interview_id,)).fetchall()
            for r in f_rows:
                val = r["field_value"]
                try:
                    confirmed_profile[r["field_name"]] = json.loads(val)
                except Exception:
                    confirmed_profile[r["field_name"]] = val

            # Also check if interview has a linked beneficiary
            int_sess = conn.execute("SELECT beneficiary_id FROM interview_sessions WHERE id = ?;", (target_interview_id,)).fetchone()
            if int_sess and int_sess["beneficiary_id"]:
                target_ben_id = int_sess["beneficiary_id"]

        if target_ben_id and not confirmed_profile:
            # Fallback to profile_answers table
            ans_rows = conn.execute("""
                SELECT field_name, field_value FROM profile_answers
                WHERE beneficiary_id = ? AND confirmation_status = 'confirmed';
            """, (target_ben_id,)).fetchall()
            for r in ans_rows:
                val = r["field_value"]
                try:
                    confirmed_profile[r["field_name"]] = json.loads(val)
                except Exception:
                    confirmed_profile[r["field_name"]] = val

        # Extract parameters with fallbacks
        district = req.district or confirmed_profile.get("district") or "Moradabad"
        block = req.block or confirmed_profile.get("block") or "Chhajlet"
        user_edu = confirmed_profile.get("education") or confirmed_profile.get("education_level") or "Class 8"
        interests = confirmed_profile.get("interests") or []
        if isinstance(interests, str):
            interests = [interests]
        skills = confirmed_profile.get("traditional_or_existing_skills") or confirmed_profile.get("skills") or []
        if isinstance(skills, str):
            skills = [skills]
        
        mobility_raw = confirmed_profile.get("mobility") or confirmed_profile.get("mobility_radius_km") or req.mobility_radius_km or 5.0
        try:
            mobility_radius = float(mobility_raw)
        except Exception:
            m_str = str(mobility_raw).lower()
            if "local" in m_str:
                mobility_radius = 10.0
            elif "district" in m_str:
                mobility_radius = 45.0
            elif "state" in m_str:
                mobility_radius = 250.0
            else:
                mobility_radius = 5.0

        work_pref = req.work_preference or confirmed_profile.get("self_employment_or_wage_preference") or confirmed_profile.get("work_preference") or "both"
        access_needs = str(confirmed_profile.get("access_needs", "none")).lower()
        do_not_recommend = [x.lower() for x in (req.do_not_recommend or [])]
        lang = req.language or confirmed_profile.get("language") or "hi"

        user_edu_rank = education_to_rank(str(user_edu))
        user_coords = get_block_coordinates(block)

        # 2. Fetch all verified qualifications (support both legacy 'verified' and Sprint 4 'VERIFIED')
        quals_cursor = conn.execute("SELECT * FROM qualifications WHERE UPPER(verification_status) = 'VERIFIED';")
        quals = [dict(r) for r in quals_cursor.fetchall()]

        # 3. Fetch active, non-expired local opportunities for district
        opp_cursor = conn.execute("""
            SELECT * FROM local_opportunities
            WHERE (LOWER(district) = LOWER(?) OR LOWER(district_id) = LOWER(?))
              AND status NOT IN ('CLOSED', 'ARCHIVED')
              AND (available_seats > 0 OR seats_available > 0)
              AND (batch_end_date >= date('now') OR end_date >= date('now') OR batch_end_date IS NULL)
              AND (verification_expires_at IS NULL OR verification_expires_at > datetime('now'));
        """, (district, district))
        raw_opps = [dict(r) for r in opp_cursor.fetchall()]

        candidate_list = []

        for qual in quals:
            qual_id = qual["id"]
            qual_title = qual.get("title", "")
            qual_skills = json.loads(qual.get("skills_acquired") or "[]")
            qual_work_type = qual.get("work_type", "both")

            # HARD FILTER 1: Explicit "do not recommend"
            if any(dnr in qual_title.lower() or dnr in qual.get("sector", "").lower() for dnr in do_not_recommend):
                continue

            # HARD FILTER 2: Education requirement (officially known)
            min_rank = qual.get("min_education_rank", 0)
            if user_edu_rank < min_rank:
                continue

            # HARD FILTER 3: Accessibility / Physical intensity
            if "limited" in access_needs or "wheelchair" in access_needs:
                if qual.get("physical_intensity") in ["high", "medium_high"]:
                    continue

            # HARD FILTER 4: User work preference
            if work_pref in ["wage", "self_employment"]:
                if qual_work_type != "both" and qual_work_type != work_pref:
                    continue

            # Find matching local opportunities
            matching_opps = []
            for opp in raw_opps:
                if opp.get("qualification_id") == qual_id:
                    # Apply stale-data check using Sprint 4 verification_expires_at first
                    expires_at = opp.get("verification_expires_at")
                    is_expired = False
                    if expires_at:
                        try:
                            exp_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                            is_expired = exp_dt <= datetime.now(timezone.utc)
                        except Exception:
                            is_expired = True
                    elif CatalogueService._is_stale(opp.get("verified_at")):
                        is_expired = True

                    # Determine availability from Sprint 4 status field
                    opp_status = opp.get("status", "").upper()
                    if is_expired or opp_status in ("EXPIRED", "CLOSED", "ARCHIVED"):
                        opp_avail = "unknown"
                    elif opp_status == "ACTIVE":
                        opp_avail = "verified_open"
                    else:
                        # Legacy: check batch_status
                        opp_avail = opp.get("availability", "unknown")

                    # HARD FILTER 5: Travel / Mobility radius
                    dist = calculate_distance_km(
                        user_coords["lat"], user_coords["lon"],
                        opp.get("latitude", user_coords["lat"]), opp.get("longitude", user_coords["lon"])
                    )

                    if dist <= mobility_radius:
                        opp_item = dict(opp)
                        opp_item["distance_km"] = dist
                        opp_item["availability"] = opp_avail
                        matching_opps.append(opp_item)

            matching_opps.sort(key=lambda x: x["distance_km"])
            best_opp = matching_opps[0] if matching_opps else None

            # Determine local availability status
            if best_opp:
                local_status = best_opp.get("availability", "verified_open")
            else:
                local_status = "unknown"

            # SOFT RANKING FACTORS
            # 1. Interest match (30 pts)
            interest_score = 0.0
            why_reasons = []
            for it in interests:
                it_str = str(it).lower()
                if it_str in qual_title.lower() or it_str in qual.get("sector", "").lower():
                    interest_score = 30.0
                    why_reasons.append(f"Matches your confirmed interest in {it}")
                    break
                elif any(word in qual_title.lower() for word in it_str.split()):
                    interest_score = max(interest_score, 20.0)
                    why_reasons.append(f"Aligns with your preference for {it}")

            # 2. Existing skill overlap (20 pts)
            matched_skills = []
            skill_gaps = []
            for qs in qual_skills:
                if any(us.lower() in qs.lower() or qs.lower() in us.lower() for us in skills):
                    matched_skills.append(qs)
                else:
                    skill_gaps.append(qs)

            skill_score = 20.0 if matched_skills else 10.0
            if matched_skills:
                why_reasons.append(f"Builds on your existing experience in {', '.join(matched_skills[:2])}")

            # 3. Proximity & Local opportunity availability (25 pts)
            if best_opp and local_status == "verified_open":
                dist_km = best_opp["distance_km"]
                access_score = max(10.0, 25.0 - (dist_km * 2.0))
                why_reasons.append(f"Fits your mobility preference: verified training centre within {dist_km:.1f} km at {best_opp.get('centre_or_employer_name')}")
            else:
                access_score = 5.0
                why_reasons.append("National qualification pathway available within your mobility preference (local batch verification pending)")

            # 4. Work preference fit (15 pts)
            if work_pref == "both" or qual_work_type == "both" or qual_work_type == work_pref:
                pref_score = 15.0
                why_reasons.append(f"Fits your {work_pref.replace('_', ' ')} livelihood preference")
            else:
                pref_score = 5.0

            # 5. Freshness & Quality (10 pts)
            freshness_score = 10.0 if (best_opp and local_status == "verified_open") else 5.0

            total_score = round(interest_score + skill_score + access_score + pref_score + freshness_score, 1)

            # Generate structured explanation
            match_state = "Verified Match" if (best_opp and local_status == "verified_open") else "Interest Match"
            expl = ExplanationGenerator.generate(qual, best_opp, interests, match_state, lang)

            ranking_factors = {
                "interest_score": interest_score,
                "skill_alignment_score": skill_score,
                "accessibility_score": access_score,
                "preference_score": pref_score,
                "freshness_score": freshness_score
            }

            candidate_list.append({
                "qualification": {
                    "id": qual["nqr_code"],
                    "internal_id": qual["id"],
                    "title": qual_title,
                    "nsqf_level": f"Level {qual['nsqf_level']}",
                    "sector": qual["sector"],
                    "official_url": qual.get("official_source_url") or qual.get("nqr_link"),
                    "duration_hours": qual.get("duration_hours")
                },
                "why_recommended": why_reasons[:3],
                "matched_skills": matched_skills[:4],
                "skill_gaps": skill_gaps[:4],
                "local_availability": {
                    "status": local_status,
                    "district": district,
                    "source_url": best_opp.get("source_url") if best_opp else None,
                    "centre_name": best_opp.get("centre_or_employer_name") if best_opp else None,
                    "last_verified_at": best_opp.get("verified_at") if best_opp else None
                },
                "caveat": "This is a guidance recommendation, not confirmation of admission or placement.",
                "score": total_score,
                "ranking_factors": ranking_factors,
                "best_opp": best_opp,
                "match_state": match_state,
                "explanation_text": expl["explanation_text"],
                "audio_explanation_script": expl["audio_explanation_script"],
                "tradeoff_summary": expl["tradeoff_summary"],
                "skill_gap_summary": expl["skill_gap_summary"]
            })

        # Rank descending by score
        candidate_list.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = candidate_list[:3]

        # Check for no-result scenario
        if not top_candidates:
            return {
                "recommendations": [],
                "count": 0,
                "no_result_reason": "All available qualifications were excluded by constraints (education, mobility, or preferences).",
                "counselor_referral_suggested": True,
                "counselor_handoff_recommended": True,
                "referral_reason": "no_verified_local_option",
                "message": "We could not find an immediate local match for your exact constraints. We recommend requesting a human counselor referral for customized assistance."
            }

        # Persist structured recommendations in database
        saved_recs = []
        for i, item in enumerate(top_candidates):
            rec_id = f"rec_{uuid.uuid4().hex[:10]}"
            best_opp = item["best_opp"]
            qual_internal_id = item["qualification"]["internal_id"]

            conn.execute("""
                INSERT INTO recommendations (
                    id, beneficiary_id, session_id, interview_id, qualification_id,
                    local_opportunity_id, rank, score, score_breakdown, match_state,
                    explanation_text, audio_explanation_script, tradeoff_summary, skill_gap_summary,
                    data_snapshot, ranking_factors, hard_constraint_result, matched_skills,
                    skill_gaps, local_opportunity_status, caveat, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                rec_id, target_ben_id, target_interview_id, target_interview_id,
                qual_internal_id, best_opp["id"] if best_opp else None,
                i + 1, item["score"], json.dumps(item["ranking_factors"]),
                item["match_state"], item["explanation_text"], item["audio_explanation_script"],
                item["tradeoff_summary"], item["skill_gap_summary"],
                json.dumps({"qualification": item["qualification"], "local_availability": item["local_availability"]}),
                json.dumps(item["ranking_factors"]), json.dumps({"passed": True}),
                json.dumps(item["matched_skills"]), json.dumps(item["skill_gaps"]),
                item["local_availability"]["status"], item["caveat"], now, now
            ))

            clean_response = {
                "recommendation_id": rec_id,
                "qualification": item["qualification"],
                "why_recommended": item["why_recommended"],
                "matched_skills": item["matched_skills"],
                "skill_gaps": item["skill_gaps"],
                "local_availability": item["local_availability"],
                "ranking_factors": item["ranking_factors"],
                "caveat": item["caveat"],
                "score": item["score"]
            }
            saved_recs.append(clean_response)

        # Update interview status to recommendations_generated if applicable
        if target_interview_id:
            conn.execute("""
                UPDATE interview_sessions
                SET status = 'recommendations_generated', updated_at = ?
                WHERE id = ?;
            """, (now, target_interview_id))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="System Matcher",
            actor_role="system",
            action="RECOMMENDATIONS_GENERATED",
            entity_type="recommendation_set",
            entity_id=target_interview_id or rec_id,
            metadata={"count": len(saved_recs), "district": district}
        )

        return {
            "count": len(saved_recs),
            "recommendations": saved_recs,
            "counselor_referral_suggested": any(r["local_availability"]["status"] == "unknown" for r in saved_recs),
            "counselor_handoff_recommended": any(r["local_availability"]["status"] == "unknown" for r in saved_recs)
        }

    @staticmethod
    def get_recommendation_by_id(conn: sqlite3.Connection, rec_id: str) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM recommendations WHERE id = ?;", (rec_id,)).fetchone()
        if not row:
            raise EntityNotFoundException("Recommendation", rec_id)

        d = dict(row)
        qual_row = conn.execute("SELECT * FROM qualifications WHERE id = ?;", (d["qualification_id"],)).fetchone()
        opp_row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?;", (d["local_opportunity_id"],)).fetchone() if d.get("local_opportunity_id") else None

        qual_info = {
            "id": qual_row["nqr_code"] if qual_row else d["qualification_id"],
            "title": qual_row["title"] if qual_row else "Qualification",
            "nsqf_level": f"Level {qual_row['nsqf_level']}" if qual_row else "",
            "official_url": (qual_row.get("official_source_url") or qual_row.get("nqr_link")) if qual_row else ""
        }

        return {
            "recommendation_id": d["id"],
            "qualification": qual_info,
            "matched_skills": json.loads(d.get("matched_skills") or "[]"),
            "skill_gaps": json.loads(d.get("skill_gaps") or "[]"),
            "local_availability": {
                "status": d.get("local_opportunity_status") or "unknown",
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
