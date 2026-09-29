from fastapi import APIRouter, HTTPException, Depends
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.database import get_db
from app.models import BeneficiaryCreate, BeneficiaryUpdate, AnonymousSessionCreate, ExportSummaryRequest
from app.services.session_service import SessionService
from app.services.profile_service import ProfileService
from app.services.export_service import ExportService
from app.dependencies.auth import get_current_actor, Actor

router = APIRouter(tags=["Beneficiaries"])

# ============================================================================
# A2. Anonymous Session & Self-Profile Routes
# ============================================================================
@router.post("/sessions", status_code=201)
def create_anonymous_session(
    data: Optional[AnonymousSessionCreate] = None,
    actor: Actor = Depends(get_current_actor)
):
    """
    Creates a privacy-preserving anonymous session ID and token.
    Allows beneficiaries to complete interviews and get recommendations without an account.
    """
    with get_db() as conn:
        return SessionService.create_session(conn, data, actor_id=actor.actor_id)

@router.get("/beneficiaries/me")
def get_my_profile(actor: Actor = Depends(get_current_actor)):
    """
    Retrieves the caller's profile based on session token or authenticated credentials.
    """
    with get_db() as conn:
        return ProfileService.get_profile_for_actor(conn, actor)

@router.patch("/beneficiaries/me")
def update_my_profile(updates: BeneficiaryUpdate, actor: Actor = Depends(get_current_actor)):
    """
    Updates the caller's profile in their active session or beneficiary record.
    """
    with get_db() as conn:
        return ProfileService.update_profile_for_actor(conn, actor, updates)

@router.delete("/beneficiaries/me")
def delete_my_profile(actor: Actor = Depends(get_current_actor)):
    """
    DPDP Right to Erasure: Permanently purges all interview turns, profile answers,
    recommendations, and referral records for the active caller.
    """
    with get_db() as conn:
        return ProfileService.delete_profile_for_actor(conn, actor)

@router.post("/beneficiaries/me/export-summary")
def export_my_summary(
    body: Optional[ExportSummaryRequest] = None,
    actor: Actor = Depends(get_current_actor)
):
    """
    Exports a privacy-safe printable summary of confirmed profile fields and recommendations.
    """
    with get_db() as conn:
        return ExportService.generate_summary_export(
            conn=conn,
            interview_id=actor.session_id,
            beneficiary_id=actor.beneficiary_id,
            actor_id=actor.actor_id
        )

# ============================================================================
# Standard Beneficiary CRUD Routes (Backwards Compatibility)
# ============================================================================
@router.post("/beneficiaries", status_code=201)
def create_beneficiary(data: BeneficiaryCreate):
    ben_id = f"ben_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO beneficiaries (
                id, name, phone, gender, age, category, preferred_language,
                district, block, village, contact_preference, owner_type, owner_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            ben_id, data.name, data.phone, data.gender, data.age, data.category,
            data.preferred_language, data.district, data.block, data.village,
            data.contact_preference, data.owner_type or "authenticated_user",
            data.owner_id, now, now
        ))
        row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (ben_id,)).fetchone()
        return dict(row)

@router.get("/beneficiaries")
def list_beneficiaries(district: Optional[str] = None, block: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM beneficiaries WHERE 1=1"
        params = []
        if district:
            query += " AND district = ?"
            params.append(district)
        if block:
            query += " AND block = ?"
            params.append(block)
        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

@router.get("/beneficiaries/{beneficiary_id}")
def get_beneficiary(beneficiary_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Beneficiary not found")
        return dict(row)

@router.patch("/beneficiaries/{beneficiary_id}")
def update_beneficiary(beneficiary_id: str, updates: BeneficiaryUpdate):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Beneficiary not found")

        update_dict = updates.model_dump(exclude_unset=True)
        if not update_dict:
            return dict(existing)

        set_clauses = [f"{k} = ?" for k in update_dict.keys()]
        set_clauses.append("updated_at = ?")
        params = list(update_dict.values()) + [now, beneficiary_id]

        conn.execute(f"UPDATE beneficiaries SET {', '.join(set_clauses)} WHERE id = ?;", params)
        row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        return dict(row)
