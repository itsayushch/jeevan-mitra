from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
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

@router.get("/admin/qualifications/{qualification_id}", response_model=QualificationResponse)
def get_admin_qualification(
    qualification_id: str,
    user: Actor = Depends(require_authenticated_user)
):
    allowed = {"catalogue_manager", "field_worker", "district_admin", "auditor", "admin", "super_admin"}
    if not any(r in allowed for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff access required.")
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
    allowed = {"catalogue_manager", "district_admin", "admin", "super_admin"}
    if not any(r in allowed for r in user.roles):
        raise HTTPException(status_code=403, detail="Catalogue manager credentials required.")
    with get_db() as conn:
        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        return QualificationCatalogueService.create_qualification(conn, payload, user_id=user.actor_id)

@router.patch("/admin/qualifications/{qualification_id}", response_model=QualificationResponse)
def update_qualification(
    qualification_id: str,
    data: QualificationUpdate,
    user: Actor = Depends(require_authenticated_user)
):
    allowed = {"catalogue_manager", "district_admin", "admin", "super_admin"}
    if not any(r in allowed for r in user.roles):
        raise HTTPException(status_code=403, detail="Catalogue manager credentials required.")
    with get_db() as conn:
        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        qual = QualificationCatalogueService.update_qualification(conn, qualification_id, payload, user_id=user.actor_id)
        if not qual:
            raise HTTPException(status_code=404, detail="Qualification not found")
        return qual

@router.post("/admin/qualifications/{qualification_id}/map-course", status_code=201)
def map_course_to_qualification(
    qualification_id: str,
    data: Dict[str, Any],
    user: Actor = Depends(require_authenticated_user)
):
    allowed = {"catalogue_manager", "district_admin", "admin", "super_admin"}
    if not any(r in allowed for r in user.roles):
        raise HTTPException(status_code=403, detail="Catalogue manager credentials required.")
    course_id = data.get("training_course_id")
    if not course_id:
        raise HTTPException(status_code=400, detail="training_course_id is required")
    rel_type = data.get("relationship_type", "direct")
    with get_db() as conn:
        qual = QualificationCatalogueService.get_qualification(conn, qualification_id)
        if not qual:
            raise HTTPException(status_code=404, detail="Qualification not found")
        return QualificationCatalogueService.map_course(conn, qualification_id, course_id, rel_type)
