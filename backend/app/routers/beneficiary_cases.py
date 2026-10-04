from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.schemas.cases import BeneficiaryCaseResponse
from app.schemas.referrals import BeneficiaryReferralResponse
from app.services.case_management_service import CaseManagementService
from app.services.referral_service import ReferralService
from app.services.referral_state_machine import ReferralStateMachine
from app.dependencies.auth import require_authenticated_user, Actor
from app.utils.audit_events import log_audit_event

router = APIRouter(tags=["Beneficiary Cases & Referrals"])

@router.get("/me/cases")
def get_my_cases(
    user: Actor = Depends(require_authenticated_user),
    accept_language: Optional[str] = Header(None)
) -> List[Dict[str, Any]]:
    ben_id = user.beneficiary_id or user.actor_id
    lang = "hi" if (accept_language and "hi" in accept_language.lower()) else "en"

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM beneficiary_cases
            WHERE beneficiary_id = ?
            ORDER BY updated_at DESC;
        """, (ben_id,)).fetchall()

        results = []
        for r in rows:
            c = dict(r)
            status = c.get("case_status", "NEW")
            results.append({
                "id": c["id"],
                "case_status": status,
                "display_status": "Active Review" if status in ("NEW", "OPEN", "IN_REVIEW") else status.replace("_", " ").title(),
                "next_step": "A local field counselor is reviewing suitable opportunities for you.",
                "next_follow_up_at": c.get("next_follow_up_at"),
                "can_request_support": status not in ("CLOSED", "COMPLETED")
            })
        return results

@router.get("/me/cases/{case_id}")
def get_my_case_detail(
    case_id: str,
    user: Actor = Depends(require_authenticated_user),
    accept_language: Optional[str] = Header(None)
) -> Dict[str, Any]:
    ben_id = user.beneficiary_id or user.actor_id

    with get_db() as conn:
        case = CaseManagementService.get_case(conn, case_id)
        if not case or case.get("beneficiary_id") != ben_id:
            raise HTTPException(status_code=404, detail="Case not found.")

        # ONLY return beneficiary-safe notes
        safe_notes = CaseManagementService.get_notes(conn, case_id, include_staff_only=False)

        # Referrals for this case (sanitized)
        ref_rows = conn.execute("""
            SELECT id, referral_status, local_opportunity_id, updated_at
            FROM referrals WHERE case_id = ? ORDER BY updated_at DESC;
        """, (case_id,)).fetchall()

        lang = "hi" if (accept_language and "hi" in accept_language.lower()) else "en"
        sanitized_refs = []
        for r in ref_rows:
            st = ReferralStateMachine.to_beneficiary_status(r["referral_status"], lang=lang)
            sanitized_refs.append({
                "referralId": r["id"],
                "status": r["referral_status"],
                "displayStatus": st["title"],
                "nextStep": st["description"],
                "updatedAt": r["updated_at"]
            })

        return {
            "id": case["id"],
            "case_status": case["case_status"],
            "display_status": "Active Review" if case["case_status"] in ("NEW", "OPEN", "IN_REVIEW") else case["case_status"].replace("_", " ").title(),
            "next_follow_up_at": case.get("next_follow_up_at"),
            "notes": safe_notes,
            "referrals": sanitized_refs,
            "created_at": case["created_at"],
            "updated_at": case["updated_at"]
        }

@router.get("/me/referrals")
def get_my_referrals(
    user: Actor = Depends(require_authenticated_user),
    accept_language: Optional[str] = Header(None)
) -> List[Dict[str, Any]]:
    ben_id = user.beneficiary_id or user.actor_id
    lang = "hi" if (accept_language and "hi" in accept_language.lower()) else "en"

    with get_db() as conn:
        rows = conn.execute("""
            SELECT r.id, r.case_id, r.referral_status, r.local_opportunity_id,
                   r.next_follow_up_at, r.created_at, r.updated_at,
                   o.title as opportunity_title
            FROM referrals r
            LEFT JOIN local_opportunities o ON r.local_opportunity_id = o.id
            WHERE r.beneficiary_id = ?
            ORDER BY r.updated_at DESC;
        """, (ben_id,)).fetchall()

        results = []
        for r in rows:
            st = ReferralStateMachine.to_beneficiary_status(r["referral_status"], lang=lang)
            results.append({
                "referralId": r["id"],
                "caseId": r["case_id"],
                "opportunityTitle": r["opportunity_title"],
                "batchName": r["opportunity_title"],
                "status": r["referral_status"],
                "displayStatus": st["title"],
                "nextStep": st["description"],
                "nextFollowUpAt": r["next_follow_up_at"],
                "canRequestSupport": r["referral_status"] not in ("CANCELLED", "CLOSED", "BENEFICIARY_DECLINED"),
                "updatedAt": r["updated_at"]
            })
        return results

@router.get("/me/referrals/{referral_id}")
def get_my_referral_detail(
    referral_id: str,
    user: Actor = Depends(require_authenticated_user),
    accept_language: Optional[str] = Header(None)
) -> Dict[str, Any]:
    ben_id = user.beneficiary_id or user.actor_id
    lang = "hi" if (accept_language and "hi" in accept_language.lower()) else "en"

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref or ref.get("beneficiary_id") != ben_id:
            raise HTTPException(status_code=404, detail="Referral not found.")

        # Opportunity public details
        opp_row = conn.execute("""
            SELECT o.id, o.title, o.stipend_amount,
                   o.district_id, o.block_id,
                   p.name as provider_name, p.address_line as provider_address
            FROM local_opportunities o
            LEFT JOIN opportunity_providers p ON o.provider_id = p.id
            WHERE o.id = ?;
        """, (ref.get("local_opportunity_id"),)).fetchone()

        opp_details = dict(opp_row) if opp_row else {}

        # Safe status history (bilingual title and timestamp only)
        hist_rows = conn.execute("""
            SELECT new_status, created_at FROM referral_status_history
            WHERE referral_id = ?
            ORDER BY created_at ASC;
        """, (referral_id,)).fetchall()

        timeline = []
        for h in hist_rows:
            st = ReferralStateMachine.to_beneficiary_status(h["new_status"], lang=lang)
            timeline.append({
                "status": h["new_status"],
                "title": st["title"],
                "description": st["description"],
                "timestamp": h["created_at"]
            })

        curr_st = ReferralStateMachine.to_beneficiary_status(ref.get("referral_status", "READY_TO_SEND"), lang=lang)

        return {
            "referralId": ref["id"],
            "caseId": ref.get("case_id"),
            "status": ref.get("referral_status"),
            "displayStatus": curr_st["title"],
            "nextStep": curr_st["description"],
            "nextFollowUpAt": ref.get("next_follow_up_at"),
            "canRequestSupport": ref.get("referral_status") not in ("CANCELLED", "CLOSED", "BENEFICIARY_DECLINED"),
            "opportunity": opp_details,
            "timeline": timeline,
            "referredAt": ref.get("referred_at"),
            "updatedAt": ref.get("updated_at")
        }

@router.post("/me/referrals/{referral_id}/support-request")
def request_referral_support(
    referral_id: str,
    payload: Dict[str, Any],
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    ben_id = user.beneficiary_id or user.actor_id

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref or ref.get("beneficiary_id") != ben_id:
            raise HTTPException(status_code=404, detail="Referral not found.")

        query_text = payload.get("message") or payload.get("support_reason") or "Beneficiary requested follow-up support on this referral."

        # Add safe note to case if case exists
        if ref.get("case_id"):
            CaseManagementService.add_note(
                conn=conn,
                case_id=ref["case_id"],
                author_user_id=user.actor_id,
                note_text=f"Beneficiary Support Request: {query_text}",
                note_type="GENERAL",
                visibility="BENEFICIARY_SAFE"
            )

        log_audit_event(
            conn=conn,
            actor_id=user.actor_id,
            actor_name=user.actor_name,
            actor_role=user.actor_role,
            action="referral.support_requested",
            entity_type="referral",
            entity_id=referral_id,
            metadata={"message": query_text}
        )

        return {
            "status": "success",
            "message": "Your support request has been logged. Your assigned counselor will contact you shortly."
        }

@router.post("/me/referrals/{referral_id}/decline")
def decline_referral(
    referral_id: str,
    payload: Dict[str, Any],
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    ben_id = user.beneficiary_id or user.actor_id

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref or ref.get("beneficiary_id") != ben_id:
            raise HTTPException(status_code=404, detail="Referral not found.")

        reason = payload.get("reason", "Beneficiary declined the opportunity.")

        try:
            ReferralService.transition_status(
                conn=conn,
                referral_id=referral_id,
                to_status="BENEFICIARY_DECLINED",
                actor=user,
                reason=reason,
                note=f"Beneficiary declined directly via portal: {reason}"
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

        return {
            "status": "success",
            "message": "You have declined this referral. Your counselor has been informed."
        }
