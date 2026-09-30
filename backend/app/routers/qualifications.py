from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from app.database import get_db
from app.schemas.qualifications import QualificationCreate, QualificationUpdate, QualificationResponse, QualificationBeneficiaryResponse
from app.services.qualification_catalogue_service import QualificationCatalogueService
from app.dependencies.auth import require_authenticated_user, Actor

router = APIRouter(tags=["Qualifications"])

@router.get("/qualifications", response_model=List[QualificationBeneficiaryResponse])
def list_qualifications(sector: Optional[str] = None, limit: int = 20):
    with get_db() as conn:
        quals = QualificationCatalogueService.get_qualifications(conn, sector=sector, limit=limit)
        return quals

@router.get("/qualifications/{qualification_id}", response_model=QualificationBeneficiaryResponse)
def get_qualification(qualification_id: str):
    with get_db() as conn:
        qual = QualificationCatalogueService.get_qualification(conn, qualification_id)
        if not qual:
            raise HTTPException(status_code=404, detail="Qualification not found")
        return qual

@router.post("/admin/qualifications", status_code=201, response_model=QualificationResponse)
def create_qualification(
    data: QualificationCreate,
    user: Actor = Depends(require_authenticated_user)
):
    with get_db() as conn:
        return QualificationCatalogueService.create_qualification(conn, data.dict(exclude_unset=True), user_id=user.actor_id)

@router.patch("/admin/qualifications/{qualification_id}", response_model=QualificationResponse)
def update_qualification(
    qualification_id: str,
    data: QualificationUpdate,
    user: Actor = Depends(require_authenticated_user)
):
    with get_db() as conn:
        qual = QualificationCatalogueService.update_qualification(conn, qualification_id, data.dict(exclude_unset=True), user_id=user.actor_id)
        if not qual:
            raise HTTPException(status_code=404, detail="Qualification not found")
        return qual
