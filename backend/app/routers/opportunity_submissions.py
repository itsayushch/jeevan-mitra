from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.dependencies.auth import get_current_actor, require_authenticated_user, Actor
from app.schemas.opportunities import (
    OpportunitySubmissionCreate,
    OpportunitySubmissionReview,
    OpportunitySubmissionResponse
)
from app.services.opportunity_submission_service import OpportunitySubmissionService

router = APIRouter(tags=["Opportunity Submissions"])

def require_staff_user(actor: Actor = Depends(require_authenticated_user)) -> Actor:
    if not actor.is_staff():
        raise HTTPException(status_code=403, detail="Staff access required.")
    return actor

@router.post("/opportunity-submissions", response_model=OpportunitySubmissionResponse, status_code=201)
def submit_opportunity(
    data: OpportunitySubmissionCreate,
    actor: Actor = Depends(get_current_actor),
    accept_language: Optional[str] = Header(None, alias="Accept-Language")
):
    """
    Submits a candidate local opportunity via text or transcribed voice.
    Both modes share unified validation, normalization, and an initial SUBMITTED state.
    """
    user_id = actor.actor_id if actor.actor_role != "anonymous" else None
    actor_name = actor.actor_name if hasattr(actor, "actor_name") else "Anonymous"
    actor_role = actor.actor_role if hasattr(actor, "actor_role") else "guest"
    pref_lang = getattr(actor, "preferred_language", None)

    with get_db() as conn:
        sub = OpportunitySubmissionService.create_submission(
            conn=conn,
            data=data,
            user_id=user_id,
            actor_name=actor_name,
            actor_role=actor_role,
            preferred_language=pref_lang,
            accept_language=accept_language
        )
        conn.commit()
        return sub

@router.get("/opportunity-submissions/me", response_model=List[OpportunitySubmissionResponse])
def get_my_submissions(
    actor: Actor = Depends(require_authenticated_user)
):
    """
    Returns opportunity submissions created by the current user.
    """
    with get_db() as conn:
        return OpportunitySubmissionService.list_my_submissions(conn, actor.actor_id)

@router.get("/staff/opportunity-submissions", response_model=List[OpportunitySubmissionResponse])
def list_submissions_staff(
    status: Optional[str] = Query(None, description="Filter submissions by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    staff: Actor = Depends(require_staff_user)
):
    """
    Staff queue to view candidate opportunity submissions (text & voice).
    """
    with get_db() as conn:
        return OpportunitySubmissionService.list_all_submissions(conn, status=status, limit=limit, offset=offset)

@router.get("/staff/opportunity-submissions/{submission_id}", response_model=OpportunitySubmissionResponse)
def get_submission_staff(
    submission_id: str,
    staff: Actor = Depends(require_staff_user)
):
    """
    Staff details view for a candidate opportunity submission.
    """
    with get_db() as conn:
        return OpportunitySubmissionService.get_submission_by_id(conn, submission_id)

@router.patch("/staff/opportunity-submissions/{submission_id}", response_model=OpportunitySubmissionResponse)
def review_submission_staff(
    submission_id: str,
    data: OpportunitySubmissionReview,
    staff: Actor = Depends(require_staff_user)
):
    """
    Staff review: transitions submission status (UNDER_REVIEW, LINKED_TO_OPPORTUNITY, REJECTED, CLOSED)
    and logs the review action.
    """
    with get_db() as conn:
        updated = OpportunitySubmissionService.review_submission(
            conn=conn,
            sub_id=submission_id,
            review_data=data,
            reviewer_id=staff.actor_id,
            reviewer_name=staff.actor_name,
            reviewer_role=staff.actor_role
        )
        conn.commit()
        return updated
