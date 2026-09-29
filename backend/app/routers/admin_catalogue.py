from fastapi import APIRouter, Depends, HTTPException, status
from app.services.catalogue_freshness_service import CatalogueFreshnessService

router = APIRouter(tags=["Admin Catalogue"])

@router.get("/admin/catalogue/stale-records")
async def get_stale_records():
    try:
        return CatalogueFreshnessService.get_stale_records()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/catalogue/run-freshness-check")
async def run_freshness_check():
    try:
        return CatalogueFreshnessService.run_freshness_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/system/catalogue-freshness")
async def get_system_freshness():
    try:
        return CatalogueFreshnessService.get_system_freshness_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
