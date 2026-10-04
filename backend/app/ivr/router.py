from typing import List
from fastapi import APIRouter, Depends, status
from app.database import get_db
from app.ivr.schemas import (
    IVRSessionStartRequest,
    IVRDigitInputRequest,
    IVRSessionResponse,
    IVREventResponse,
)
from app.ivr.service import IVRService
from app.dependencies.auth import get_current_actor, Actor

router = APIRouter(prefix="/ivr", tags=["IVR Simulator"])


@router.post(
    "/simulate/start",
    response_model=IVRSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_simulation(
    req: IVRSessionStartRequest, actor: Actor = Depends(get_current_actor)
) -> IVRSessionResponse:
    """
    Initializes a new simulated IVR call session.
    Returns initial Hindi welcome prompt, actions, and accepted keypad digits.
    """
    with get_db() as conn:
        return IVRService.start_session(conn, req)


@router.post("/simulate/{session_id}/input", response_model=IVRSessionResponse)
def submit_digit(
    session_id: str,
    req: IVRDigitInputRequest,
    actor: Actor = Depends(get_current_actor),
) -> IVRSessionResponse:
    """
    Submits a simulated DTMF keypad press ('0'-'9', '#').
    Deterministically updates session state, persists events, and returns the next Hindi prompt.
    """
    with get_db() as conn:
        return IVRService.process_digit_input(conn, session_id, req)


@router.get("/simulate/{session_id}", response_model=IVRSessionResponse)
def get_session(
    session_id: str, actor: Actor = Depends(get_current_actor)
) -> IVRSessionResponse:
    """
    Retrieves current state, status, and active prompt for a simulated call session.
    Does not expose sensitive raw caller phone numbers.
    """
    with get_db() as conn:
        return IVRService.get_session_detail(conn, session_id)


@router.get("/simulate/{session_id}/events", response_model=List[IVREventResponse])
def get_session_events(
    session_id: str, actor: Actor = Depends(get_current_actor)
) -> List[IVREventResponse]:
    """
    Returns ordered audit history of keypad inputs, state transitions, and prompts for the session.
    """
    with get_db() as conn:
        return IVRService.get_session_events(conn, session_id)


@router.post("/simulate/{session_id}/expire", response_model=IVRSessionResponse)
def expire_session(
    session_id: str, actor: Actor = Depends(get_current_actor)
) -> IVRSessionResponse:
    """
    Development/testing endpoint to manually expire an active IVR session.
    Allows automated verification of session timeout and expiry handling.
    """
    with get_db() as conn:
        return IVRService.force_expire_session(conn, session_id)
