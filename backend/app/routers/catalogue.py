from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import QualificationCreate, QualificationUpdate, OpportunityCreate, OpportunityUpdate
from app.services.catalogue_service import CatalogueService
from app.dependencies.auth import require_admin_or_worker, Actor

router = APIRouter(tags=["Catalogue"])

# ============================================================================
# Public Catalogue Read Endpoints (A4)
# ============================================================================
@router.get("/catalogue/qualifications")
def list_qualifications(sector: Optional[str] = None):
    with get_db() as conn:
        quals = CatalogueService.list_qualifications(conn, sector=sector)
        return {
            "count": len(quals),
            "qualifications": quals
        }

@router.get("/catalogue/qualifications/{qualification_id}")
def get_qualification(qualification_id: str):
    with get_db() as conn:
        return CatalogueService.get_qualification_detail(conn, qualification_id)

@router.get("/catalogue/opportunities")
def list_opportunities(
    district: Optional[str] = None,
    block: Optional[str] = None,
    qualification_id: Optional[str] = None
):
    with get_db() as conn:
        opps = CatalogueService.list_opportunities(conn, district=district, block=block, qualification_id=qualification_id)
        return {
            "count": len(opps),
            "opportunities": opps
        }

@router.post("/catalogue/nqr/ask")
def ask_nqr_question(query: str = Query(..., min_length=3, max_length=500)):
    from app.services.nqr_rag_service import nqr_rag_service
    answer = nqr_rag_service.ask(query)
    return {"query": query, "answer": answer}

# ============================================================================
# Protected Admin / Worker Catalogue Management Endpoints (A4)
# ============================================================================
@router.post("/admin/catalogue/qualifications", status_code=201)
def create_qualification(
    data: QualificationCreate,
    admin: Actor = Depends(require_admin_or_worker)
):
    with get_db() as conn:
        return CatalogueService.create_qualification(conn, data, actor_id=admin.actor_id)

@router.patch("/admin/catalogue/qualifications/{qualification_id}")
def update_qualification(
    qualification_id: str,
    data: QualificationUpdate,
    admin: Actor = Depends(require_admin_or_worker)
):
    with get_db() as conn:
        return CatalogueService.update_qualification(conn, qualification_id, data, actor_id=admin.actor_id)

@router.post("/admin/catalogue/opportunities", status_code=201)
def create_opportunity(
    data: OpportunityCreate,
    admin: Actor = Depends(require_admin_or_worker)
):
    with get_db() as conn:
        return CatalogueService.create_opportunity(conn, data, actor_id=admin.actor_id)

@router.patch("/admin/catalogue/opportunities/{opportunity_id}")
def update_opportunity(
    opportunity_id: str,
    data: OpportunityUpdate,
    admin: Actor = Depends(require_admin_or_worker)
):
    with get_db() as conn:
        return CatalogueService.update_opportunity(conn, opportunity_id, data, actor_id=admin.actor_id)

@router.post("/admin/catalogue/opportunities/{opportunity_id}/archive")
def archive_opportunity(
    opportunity_id: str,
    admin: Actor = Depends(require_admin_or_worker)
):
    with get_db() as conn:
        return CatalogueService.archive_opportunity(conn, opportunity_id, actor_id=admin.actor_id)
