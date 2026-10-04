import uuid
import json
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Optional, List, Dict, Any
from app.utils.audit_events import log_audit_event
from app.services.match_state_service import MatchStateService
from app.services.referral_state_machine import ReferralStateMachine
from app.models import (
    CreateReferralRequest, AssignCounselorRequest,
    UpdateReferralStatusRequest, AddCounselorNoteRequest
)
from app.dependencies.consent import verify_consent
from app.utils.errors import EntityNotFoundException, UnauthorizedAccessException, ValidationException

class ReferralService:
    ALLOWED_REASONS = [
        'no_verified_local_option',
        'user_requested_human_help',
        'accessibility_support_required',
        'complex_eligibility_query',
        'low_confidence_profile',
        'technical_issue'
    ]

    ALLOWED_STATUSES = ['new', 'assigned', 'contacted', 'documents_verified', 'enrolled', 'in_progress', 'completed', 'dropped_out']

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def create_legacy_referral(conn: Connection, data: CreateReferralRequest, actor) -> Dict[str, Any]:
        target_ben_id = data.beneficiary_id or getattr(actor, "beneficiary_id", None)
        target_interview_id = data.interview_id or getattr(actor, "session_id", None)

        # Mandatory Consent Check: Counselor referral consent is strictly required
        verify_consent(conn, "counselor_referral", target_ben_id, getattr(actor, "session_id", None) or target_interview_id)

        if data.referral_reason not in ReferralService.ALLOWED_REASONS:
            raise ValidationException(f"Invalid referral reason '{data.referral_reason}'. Must be one of {ReferralService.ALLOWED_REASONS}")

        case_id = f"case_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        conn.execute("""
            INSERT INTO referral_cases (
                id, beneficiary_id, interview_id, recommendation_id, local_opportunity_id,
                referral_reason, consent_verification_state, status, priority, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'verified', 'new', ?, ?, ?, ?);
        """, (
            case_id, target_ben_id, target_interview_id, data.recommendation_id,
            data.local_opportunity_id, data.referral_reason, data.priority or "medium",
            data.notes, now, now
        ))

        # Also create entry in legacy referrals table if recommendation and opportunity exist
        if data.recommendation_id and data.local_opportunity_id:
            legacy_id = f"ref_{uuid.uuid4().hex[:10]}"
            conn.execute("""
                INSERT OR IGNORE INTO referrals (
                    id, beneficiary_id, recommendation_id, local_opportunity_id, assigned_worker_id,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'unassigned', 'pending', ?, ?, ?);
            """, (legacy_id, target_ben_id or "anonymous", data.recommendation_id, data.local_opportunity_id, data.notes, now, now))

        log_audit_event(
            conn=conn,
            actor_id=getattr(actor, "actor_id", "system"),
            actor_name=getattr(actor, "actor_name", "System"),
            actor_role=getattr(actor, "actor_role", "beneficiary"),
            action="REFERRAL_CASE_CREATED",
            entity_type="referral_case",
            entity_id=case_id,
            new_values=data.model_dump()
        )

        row = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (case_id,)).fetchone()
        res = dict(row)
        res["user_safe_message"] = "Your referral request has been submitted for career counselor review. Support staff will review local options and follow up based on resource availability."
        return res

    @staticmethod
    def create_referral(
        conn: Connection,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        if len(args) >= 1 and (hasattr(args[0], 'referral_reason') or isinstance(args[0], CreateReferralRequest)):
            data = args[0]
            actor = args[1] if len(args) > 1 else kwargs.get("actor")
            return ReferralService.create_legacy_referral(conn, data, actor)
        elif "data" in kwargs and (hasattr(kwargs["data"], 'referral_reason') or isinstance(kwargs["data"], CreateReferralRequest)):
            return ReferralService.create_legacy_referral(conn, kwargs["data"], kwargs.get("actor"))
        else:
            case_id = args[0] if len(args) > 0 else kwargs.get("case_id")
            recommendation_id = args[1] if len(args) > 1 else kwargs.get("recommendation_id")
            actor = args[2] if len(args) > 2 else kwargs.get("actor")
            note = args[3] if len(args) > 3 else kwargs.get("note")
            return ReferralService.create_canonical_referral(conn, case_id=case_id, recommendation_id=recommendation_id, actor=actor, note=note)

    @staticmethod
    def create_canonical_referral(
        conn: Connection,
        case_id: str,
        recommendation_id: str,
        actor,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the atomic 11-step referral creation sequence.
        Enforces that a referral is created ONLY from a valid, current VERIFIED_MATCH.
        """
        now = ReferralService._now()
        now_dt = datetime.now(timezone.utc)

        # 1. Check actor role
        allowed_roles = {"field_worker", "district_admin", "super_admin"}
        if not any(r in allowed_roles for r in actor.roles):
            raise PermissionError("Only authorized field workers or administrators can create referrals.")

        # 2. Resolve case and worker scope
        case_row = conn.execute("SELECT * FROM beneficiary_cases WHERE id = ?", (case_id,)).fetchone()
        if not case_row:
            raise ValueError(f"Beneficiary case '{case_id}' not found.")
        case = dict(case_row)
        beneficiary_id = case["beneficiary_id"]

        if not actor.check_scope(case.get("district_id"), case.get("block_id")):
            raise PermissionError("Access denied: beneficiary case is outside worker's assigned geographic scope.")

        # 3. Resolve recommendation and linked qualification & opportunity
        # Query recommendation from recommendations table or recommendation_match_state
        rec_row = conn.execute("""
            SELECT * FROM recommendations WHERE id = ?;
        """, (recommendation_id,)).fetchone()

        if rec_row:
            rec = dict(rec_row)
            qualification_id = rec["qualification_id"]
            local_opp_id = rec.get("local_opportunity_id")
        else:
            # Check recommendation_match_state
            rms_row = conn.execute("""
                SELECT * FROM recommendation_match_state
                WHERE id = ? OR (beneficiary_id = ? AND qualification_id = ?);
            """, (recommendation_id, beneficiary_id, recommendation_id)).fetchone()
            if not rms_row:
                raise ValueError(f"Recommendation '{recommendation_id}' not found.")
            rec = dict(rms_row)
            qualification_id = rec["qualification_id"]
            local_opp_id = rec.get("local_opportunity_id")

        if not local_opp_id:
            raise ValueError("Recommendation does not have a linked local opportunity. Referral cannot be created.")

        # 4. Live recalculate/validate match state
        match_info = MatchStateService.get_or_compute_match(
            conn=conn,
            beneficiary_id=beneficiary_id,
            qualification_id=qualification_id,
            district_id=case.get("district_id"),
            block_id=case.get("block_id")
        )

        if match_info.get("matchState") != "VERIFIED_MATCH" or not match_info.get("canRequestReferral"):
            raise ValueError(
                f"Referral eligibility check failed: current match state is '{match_info.get('matchState')}'. "
                "Referrals require an active, non-expired, verified local opportunity with available capacity."
            )

        # 5. Check local opportunity status, capacity, and expiry
        opp_row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?", (local_opp_id,)).fetchone()
        if not opp_row:
            raise ValueError(f"Linked opportunity '{local_opp_id}' not found.")
        opp = dict(opp_row)

        if opp.get("status") != "ACTIVE":
            raise ValueError(f"Local opportunity is not ACTIVE (current status: '{opp.get('status')}').")

        # Expiry check
        expires_at_str = opp.get("verification_expires_at")
        if expires_at_str:
            exp_dt = None
            try:
                exp_dt = datetime.fromisoformat(str(expires_at_str).replace("Z", "+00:00"))
            except Exception:
                pass
            if exp_dt is not None and exp_dt <= now_dt:
                raise ValueError("Local opportunity verification has expired.")

        # Capacity check
        seats = opp.get("seats_available") if opp.get("seats_available") is not None else opp.get("available_seats")
        if seats is not None and seats <= 0:
            raise ValueError("Local opportunity has zero available capacity.")

        # Geographic scope check on opportunity
        if not actor.check_scope(opp.get("district_id"), opp.get("block_id")):
            raise PermissionError("Access denied: local opportunity is outside worker's assigned geographic scope.")

        # 6. Check beneficiary consent
        consent_row = conn.execute("""
            SELECT * FROM consent_records
            WHERE (beneficiary_id = ? OR session_id = ?)
              AND (status = 'active' OR status = 'granted' OR status = 'confirmed')
            ORDER BY timestamp DESC LIMIT 1;
        """, (beneficiary_id, beneficiary_id)).fetchone()

        if not consent_row:
            # Check legacy consents table
            legacy_consent = conn.execute("""
                SELECT * FROM consents
                WHERE (beneficiary_id = ? OR session_id = ?)
                  AND (dpdp_affirmative_consent = 1 OR counselor_referral = 1)
                ORDER BY timestamp DESC LIMIT 1;
            """, (beneficiary_id, beneficiary_id)).fetchone()
            if not legacy_consent:
                raise ValueError("Beneficiary consent record missing or revoked. Cannot create referral without affirmative consent.")

        # 7. Check for duplicate active referral for same beneficiary and opportunity
        existing_ref = conn.execute("""
            SELECT id FROM referrals
            WHERE beneficiary_id = ? AND local_opportunity_id = ?
              AND referral_status NOT IN ('CANCELLED', 'CLOSED', 'BENEFICIARY_DECLINED', 'NOT_ELIGIBLE', 'LOST_TO_FOLLOW_UP', 'OPPORTUNITY_CLOSED');
        """, (beneficiary_id, local_opp_id)).fetchone()

        if existing_ref:
            raise ValueError(f"An active referral ({existing_ref['id']}) already exists for this beneficiary and local opportunity.")

        # 8. Create referral record
        ref_id = f"ref_{uuid.uuid4().hex[:10]}"
        eligibility_snapshot = {
            "qualification_id": qualification_id,
            "local_opportunity_id": local_opp_id,
            "provider_id": opp.get("provider_id"),
            "district_id": case.get("district_id"),
            "block_id": case.get("block_id"),
            "match_state_at_referral": match_info.get("matchState"),
            "opportunity_seats_available_at_referral": seats,
            "verification_expires_at": expires_at_str,
            "referral_note": note,
            "referred_by_worker_id": actor.actor_id,
            "referred_at": now
        }

        conn.execute("""
            INSERT INTO referrals (
                id, case_id, beneficiary_id, recommendation_id, qualification_id,
                local_opportunity_id, provider_id, created_by_worker_id, assigned_worker_id,
                referral_status, status, referral_reason, beneficiary_consent_confirmed_at,
                eligibility_snapshot_json, referred_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'READY_TO_SEND', 'pending', ?, ?, ?, ?, ?, ?);
        """, (
            ref_id, case_id, beneficiary_id, recommendation_id, qualification_id,
            local_opp_id, opp.get("provider_id"), actor.actor_id, actor.actor_id,
            note, now, json.dumps(eligibility_snapshot), now, now, now
        ))

        # 9. Append referral status history
        hist_id = f"rhist_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO referral_status_history (
                id, referral_id, previous_status, new_status, actor_user_id, reason, note, created_at
            ) VALUES (?, ?, NULL, 'READY_TO_SEND', ?, 'Initial referral creation', ?, ?);
        """, (hist_id, ref_id, actor.actor_id, note, now))

        # 10. Audit event
        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="referral.created",
            entity_type="referral",
            entity_id=ref_id,
            metadata={
                "case_id": case_id,
                "beneficiary_id": beneficiary_id,
                "local_opportunity_id": local_opp_id,
                "initial_status": "READY_TO_SEND"
            }
        )

        # 11. Update case record
        conn.execute("""
            UPDATE beneficiary_cases
            SET latest_referral_id = ?, latest_recommendation_id = ?,
                case_status = 'REFERRAL_IN_PROGRESS', updated_at = ?
            WHERE id = ?;
        """, (ref_id, recommendation_id, now, case_id))

        return ReferralService.get_referral(conn, ref_id)

    @staticmethod
    def get_referral(conn: Connection, referral_id: str) -> Optional[Dict[str, Any]]:
        row = conn.execute("SELECT * FROM referrals WHERE id = ?", (referral_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("eligibility_snapshot_json") and isinstance(d["eligibility_snapshot_json"], str):
            try:
                d["eligibility_snapshot_json"] = json.loads(d["eligibility_snapshot_json"])
            except Exception:
                pass
        return d

    @staticmethod
    def list_referrals(
        conn: Connection,
        actor,
        case_id: Optional[str] = None,
        beneficiary_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM referrals WHERE 1=1"
        params = []

        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)

        if beneficiary_id:
            query += " AND beneficiary_id = ?"
            params.append(beneficiary_id)

        if status:
            query += " AND (UPPER(referral_status) = UPPER(?) OR UPPER(status) = UPPER(?))"
            params.extend([status, status])

        # Staff scoping check
        if not ("super_admin" in actor.roles or "admin" in actor.roles or "beneficiary" in actor.roles):
            if actor.scopes:
                scoped_dists = [s.get("district_id") for s in actor.scopes if s.get("district_id")]
                if scoped_dists:
                    placeholders = ",".join("?" for _ in scoped_dists)
                    query += f""" AND local_opportunity_id IN (
                        SELECT id FROM local_opportunities WHERE district_id IN ({placeholders})
                    )"""
                    params.extend(scoped_dists)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        rows = conn.execute(query, tuple(params)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if d.get("eligibility_snapshot_json") and isinstance(d["eligibility_snapshot_json"], str):
                try:
                    d["eligibility_snapshot_json"] = json.loads(d["eligibility_snapshot_json"])
                except Exception:
                    pass
            results.append(d)
        return results

    @staticmethod
    def transition_status(
        conn: Connection,
        referral_id: str,
        to_status: str,
        actor,
        reason: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a validated referral state machine transition.
        """
        now = ReferralService._now()
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise ValueError(f"Referral '{referral_id}' not found.")

        current_status = ref.get("referral_status") or "DRAFT"
        target_status = to_status.upper()

        if not ReferralStateMachine.is_valid_transition(current_status, target_status):
            allowed = ReferralStateMachine.get_allowed_next_statuses(current_status)
            raise ValueError(
                f"Invalid referral transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions from '{current_status}': {allowed}"
            )

        # Check actor authorization
        allowed_roles = {"field_worker", "district_admin", "super_admin"}
        is_beneficiary_declining = (
            target_status == "BENEFICIARY_DECLINED"
            and "beneficiary" in actor.roles
            and (ref.get("beneficiary_id") == actor.actor_id or ref.get("beneficiary_id") == actor.beneficiary_id)
        )
        if not is_beneficiary_declining and not any(r in allowed_roles for r in actor.roles):
            raise PermissionError("Only field workers and administrators can transition referral statuses.")

        # Update referral
        closure_fields = ""
        closure_params = []
        if ReferralStateMachine.is_terminal_status(target_status):
            closure_fields = ", closed_at = ?, closure_reason = ?"
            closure_params = [now, reason or target_status]

        query = f"""
            UPDATE referrals
            SET referral_status = ?, status = ?, updated_at = ? {closure_fields}
            WHERE id = ?;
        """
        params = [target_status, target_status.lower(), now] + closure_params + [referral_id]
        conn.execute(query, tuple(params))

        # Append status history
        hist_id = f"rhist_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO referral_status_history (
                id, referral_id, previous_status, new_status, actor_user_id, reason, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (hist_id, referral_id, current_status, target_status, actor.actor_id, reason, note, now))

        # Audit event
        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="referral.transitioned",
            entity_type="referral",
            entity_id=referral_id,
            old_values={"referral_status": current_status},
            new_values={"referral_status": target_status},
            metadata={"reason": reason, "note": note}
        )

        # Update parent case status if terminal or progressing
        if ref.get("case_id"):
            case_status = "ACTIVE_FOLLOW_UP"
            if target_status == "COMPLETED":
                case_status = "COMPLETED"
            elif target_status in ("CLOSED", "CANCELLED"):
                case_status = "CLOSED"
            conn.execute("UPDATE beneficiary_cases SET case_status = ?, updated_at = ? WHERE id = ?;", (case_status, now, ref["case_id"]))

        return ReferralService.get_referral(conn, referral_id)

    @staticmethod
    def log_contact_attempt(
        conn: Connection,
        referral_id: str,
        data: Dict[str, Any],
        actor
    ) -> Dict[str, Any]:
        now = ReferralService._now()
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise ValueError(f"Referral '{referral_id}' not found.")

        attempt_id = f"catt_{uuid.uuid4().hex[:10]}"
        channel = data.get("channel", "PHONE").upper()
        outcome = data.get("attempt_outcome", "CONNECTED").upper()
        summary = data.get("summary")
        next_follow_up = data.get("next_follow_up_at")

        conn.execute("""
            INSERT INTO referral_contact_attempts (
                id, referral_id, actor_user_id, channel, attempt_outcome, summary, attempted_at, next_follow_up_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (attempt_id, referral_id, actor.actor_id, channel, outcome, summary, now, next_follow_up))

        # Update referral last_contact_attempt_at and next_follow_up_at
        conn.execute("""
            UPDATE referrals
            SET last_contact_attempt_at = ?, next_follow_up_at = COALESCE(?, next_follow_up_at), updated_at = ?
            WHERE id = ?;
        """, (now, next_follow_up, now, referral_id))

        # Also update case last_contacted_at
        if ref.get("case_id"):
            conn.execute("""
                UPDATE beneficiary_cases
                SET last_contacted_at = ?, next_follow_up_at = COALESCE(?, next_follow_up_at), updated_at = ?
                WHERE id = ?;
            """, (now, next_follow_up, now, ref["case_id"]))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="referral.contact_attempt_logged",
            entity_type="referral",
            entity_id=referral_id,
            metadata={"channel": channel, "attempt_outcome": outcome, "attempt_id": attempt_id}
        )

        row = conn.execute("SELECT * FROM referral_contact_attempts WHERE id = ?", (attempt_id,)).fetchone()
        return dict(row)

    @staticmethod
    def record_outcome(
        conn: Connection,
        referral_id: str,
        data: Dict[str, Any],
        actor
    ) -> Dict[str, Any]:
        now = ReferralService._now()
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise ValueError(f"Referral '{referral_id}' not found.")

        outcome_id = f"out_{uuid.uuid4().hex[:10]}"
        outcome_type = data.get("outcome_type", "OTHER").upper()
        occurred_at = data.get("occurred_at") or now
        evidence_summary = data.get("evidence_summary")

        conn.execute("""
            INSERT INTO referral_outcomes (
                id, referral_id, outcome_type, outcome_status, occurred_at,
                recorded_by_user_id, evidence_summary, created_at, updated_at
            ) VALUES (?, ?, ?, 'REPORTED', ?, ?, ?, ?, ?);
        """, (outcome_id, referral_id, outcome_type, occurred_at, actor.actor_id, evidence_summary, now, now))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="referral.outcome_recorded",
            entity_type="referral_outcome",
            entity_id=outcome_id,
            metadata={"referral_id": referral_id, "outcome_type": outcome_type, "outcome_status": "REPORTED"}
        )

        row = conn.execute("SELECT * FROM referral_outcomes WHERE id = ?", (outcome_id,)).fetchone()
        return dict(row)

    @staticmethod
    def verify_outcome(
        conn: Connection,
        outcome_id: str,
        status: str,
        actor,
        evidence_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        now = ReferralService._now()
        row = conn.execute("SELECT * FROM referral_outcomes WHERE id = ?", (outcome_id,)).fetchone()
        if not row:
            raise ValueError(f"Outcome '{outcome_id}' not found.")
        old_status = row["outcome_status"]
        new_status = status.upper()

        if new_status not in ("VERIFIED", "REJECTED", "PENDING_VERIFICATION"):
            raise ValueError("Outcome status must be 'VERIFIED', 'REJECTED', or 'PENDING_VERIFICATION'.")

        conn.execute("""
            UPDATE referral_outcomes
            SET outcome_status = ?, verified_by_user_id = ?,
                evidence_summary = COALESCE(?, evidence_summary), updated_at = ?
            WHERE id = ?;
        """, (new_status, actor.actor_id, evidence_summary, now, outcome_id))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="referral.outcome_verified",
            entity_type="referral_outcome",
            entity_id=outcome_id,
            old_values={"outcome_status": old_status},
            new_values={"outcome_status": new_status},
            metadata={"verified_by": actor.actor_id}
        )

        updated = conn.execute("SELECT * FROM referral_outcomes WHERE id = ?", (outcome_id,)).fetchone()
        return dict(updated)

    @staticmethod
    def get_referral_history(conn: Connection, referral_id: str) -> List[Dict[str, Any]]:
        rows = conn.execute("SELECT * FROM referral_status_history WHERE referral_id = ? ORDER BY created_at ASC;", (referral_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_contact_attempts(conn: Connection, referral_id: str) -> List[Dict[str, Any]]:
        rows = conn.execute("SELECT * FROM referral_contact_attempts WHERE referral_id = ? ORDER BY attempted_at DESC;", (referral_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_outcomes(conn: Connection, referral_id: str) -> List[Dict[str, Any]]:
        rows = conn.execute("SELECT * FROM referral_outcomes WHERE referral_id = ? ORDER BY created_at DESC;", (referral_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_my_referrals(conn: Connection, actor) -> List[Dict[str, Any]]:
        target_ben_id = getattr(actor, "beneficiary_id", None)
        session_id = getattr(actor, "session_id", None) or getattr(actor, "actor_id", None)

        rows = conn.execute("""
            SELECT * FROM referral_cases
            WHERE (beneficiary_id IS NOT NULL AND beneficiary_id = ?)
               OR (interview_id IS NOT NULL AND interview_id = ?)
            ORDER BY created_at DESC;
        """, (target_ben_id or "", session_id or "")).fetchall()

        return [dict(r) for r in rows]

    @staticmethod
    def list_counselor_referrals(conn: Connection, actor, status: Optional[str] = None) -> List[Dict[str, Any]]:
        actor_role = getattr(actor, "actor_role", None)
        roles = getattr(actor, "roles", [])
        if actor_role not in ["counselor", "admin", "district_officer", "field_worker"] and not any(r in ["counselor", "admin", "district_officer", "field_worker", "district_admin", "super_admin"] for r in roles):
            raise UnauthorizedAccessException("Only authorized counselors and administrators may access the counselor queue.")

        query = "SELECT * FROM referral_cases WHERE 1=1"
        params = []

        if actor_role == "counselor":
            query += " AND (assigned_counselor_id = ? OR assigned_counselor_id IS NULL)"
            params.append(actor.actor_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def assign_counselor(conn: Connection, referral_id: str, data: AssignCounselorRequest, actor) -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("ReferralCase", referral_id)

        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE referral_cases
            SET assigned_counselor_id = ?, status = 'assigned', updated_at = ?
            WHERE id = ?;
        """, (data.counselor_id, now, referral_id))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="REFERRAL_COUNSELOR_ASSIGNED",
            entity_type="referral_case",
            entity_id=referral_id,
            new_values={"assigned_counselor_id": data.counselor_id, "status": "assigned"}
        )

        row = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        return dict(row)

    @staticmethod
    def update_status(conn: Connection, referral_id: str, data: UpdateReferralStatusRequest, actor) -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("ReferralCase", referral_id)

        actor_role = getattr(actor, "actor_role", None)
        if actor_role == "counselor" and existing["assigned_counselor_id"] != actor.actor_id:
            raise UnauthorizedAccessException("You are not assigned to this referral case.")

        current_status = existing["status"]
        valid_transitions = {
            "new": ["assigned"],
            "assigned": ["contacted", "in_progress"],
            "contacted": ["documents_verified", "in_progress"],
            "documents_verified": ["enrolled", "in_progress"],
            "enrolled": ["in_progress"],
            "in_progress": ["completed", "dropped_out"],
            "completed": [],
            "dropped_out": []
        }

        if current_status in valid_transitions and data.status not in valid_transitions[current_status]:
            if current_status != data.status: # Allow no-op status updates
                from app.utils.errors import ValidationException
                raise ValidationException(f"Invalid state transition from {current_status} to {data.status}")

        now = datetime.now(timezone.utc).isoformat()
        set_clauses = ["status = ?", "updated_at = ?"]
        params = [data.status, now]

        if data.outcome:
            set_clauses.append("outcome = ?")
            params.append(data.outcome)
        if data.notes:
            set_clauses.append("notes = ?")
            params.append(data.notes)

        params.append(referral_id)
        conn.execute(f"UPDATE referral_cases SET {', '.join(set_clauses)} WHERE id = ?;", params)

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="REFERRAL_STATUS_UPDATED",
            entity_type="referral_case",
            entity_id=referral_id,
            old_values={"status": existing["status"]},
            new_values={"status": data.status, "outcome": data.outcome}
        )

        row = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        return dict(row)

    @staticmethod
    def add_counselor_note(conn: Connection, referral_id: str, data: AddCounselorNoteRequest, actor) -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("ReferralCase", referral_id)

        actor_role = getattr(actor, "actor_role", None)
        if actor_role == "counselor" and existing["assigned_counselor_id"] != actor.actor_id:
            raise UnauthorizedAccessException("You are not assigned to this referral case.")

        note_id = f"note_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        counselor_id = data.counselor_id or actor.actor_id

        conn.execute("""
            INSERT INTO counselor_notes (id, referral_case_id, counselor_id, note, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (note_id, referral_id, counselor_id, data.note, now))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="COUNSELOR_NOTE_ADDED",
            entity_type="counselor_note",
            entity_id=note_id,
            metadata={"referral_case_id": referral_id}
        )

        row = conn.execute("SELECT * FROM counselor_notes WHERE id = ?;", (note_id,)).fetchone()
        return dict(row)

