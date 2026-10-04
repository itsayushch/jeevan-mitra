from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.database import DBWrapper, get_db_session
from app.services.journey_service import JourneyService
from app.models import JourneyResponse, JourneyStartRequest, JourneyConsentRequest, JourneyRespondRequest, JourneyConfirmProfileRequest
from app.utils.errors import ValidationException, NotFoundException
from app.dependencies.auth import Actor, get_current_actor

router = APIRouter(prefix="/journey", tags=["Journey"])

@router.post("/start", response_model=JourneyResponse)
def start_journey(
    req: JourneyStartRequest,
    actor: Actor = Depends(get_current_actor),
    db: DBWrapper = Depends(get_db_session)
):
    trusted_request = req.model_copy(update={"actor_id": actor.actor_id, "actor_role": actor.actor_role})
    return JourneyService.start_journey(db, trusted_request)

@router.post("/{journey_id}/consent", response_model=JourneyResponse)
def update_consent(journey_id: str, req: JourneyConsentRequest, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.update_consent(db, journey_id, req, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{journey_id}/respond")
def respond_journey(journey_id: str, req: JourneyRespondRequest, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.respond(db, journey_id, req.message, req.language, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{journey_id}", response_model=JourneyResponse)
def get_journey(journey_id: str, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.get_journey(db, journey_id, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{journey_id}/confirm-profile", response_model=JourneyResponse)
def confirm_profile(journey_id: str, req: JourneyConfirmProfileRequest, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.confirm_profile(db, journey_id, req.confirm, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{journey_id}/generate-recommendations")
def generate_recommendations(journey_id: str, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.generate_recommendations(db, journey_id, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{journey_id}/request-referral")
def request_referral(journey_id: str, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.request_referral(db, journey_id, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{journey_id}/summary")
def get_summary(journey_id: str, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.get_summary(db, journey_id, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{journey_id}")
def delete_journey(journey_id: str, actor: Actor = Depends(get_current_actor), db: DBWrapper = Depends(get_db_session)):
    try:
        return JourneyService.delete_journey(db, journey_id, actor.actor_id)
    except (ValidationException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))
