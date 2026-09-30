import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

def create_learning_course(
    conn,
    course_id: str = "course_elec_01",
    title: str = "Basic Electrical Repair",
    slug: str = "basic-electrical-repair",
    sector: str = "Electronics",
    is_published: int = 1
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO training_courses (
            id, title, slug, short_description, long_description, sector,
            nsqf_level, duration_hours, difficulty, language_code, source_name,
            verification_status, verified_at, last_updated_at, is_published
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        course_id, title, slug, f"{title} fundamentals", f"Comprehensive course in {title}",
        sector, "3", 60, "Beginner", "hi", "National Skill Dev Corp",
        "Verified", now, now, is_published
    ))
    return {"id": course_id, "title": title, "slug": slug, "sector": sector}

def create_qualification_record(
    conn,
    qual_id: str = "qual_elec_repair_01",
    title: str = "Basic Electrical Repair Assistant",
    sector: str = "Electronics",
    nsqf_level: int = 3,
    min_education: str = "10th Pass",
    min_education_rank: int = 3,
    work_type: str = "wage",
    verification_status: str = "VERIFIED",
    user_id: str = "usr_cat_mgr_a"
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO qualifications (
            id, external_reference, nqr_code, title, description, sector,
            nsqf_level, duration_hours, min_education, min_education_rank,
            work_type, physical_intensity, skills_acquired, curriculum_summary,
            entry_criteria, certification_body, source_name, source_url,
            verification_status, verification_date, created_by_user_id,
            verified_by_user_id, verified_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        qual_id, f"NQR/{qual_id}", f"NQR_{qual_id}", title, f"Certified {title}", sector,
        nsqf_level, 200, min_education, min_education_rank,
        work_type, "low", json.dumps(["wiring", "repair", "safety", "electrical"]),
        f"Curriculum for {title}", f"Minimum {min_education}", "NSDC", "NQR Portal",
        "https://nqr.gov.in/qual/elec-01", verification_status, now[:10],
        user_id, user_id, now, now, now
    ))
    return {"id": qual_id, "title": title, "sector": sector, "nsqf_level": nsqf_level}

def create_irrelevant_qualification(
    conn,
    qual_id: str = "qual_aerospace_01",
    title: str = "Advanced Aerospace Propulsion Specialist",
    sector: str = "Aerospace & Aviation",
    nsqf_level: int = 8,
    min_education: str = "Post Graduate",
    min_education_rank: int = 8,
    work_type: str = "wage",
    verification_status: str = "VERIFIED",
    user_id: str = "usr_cat_mgr_a"
) -> Dict[str, Any]:
    return create_qualification_record(
        conn,
        qual_id=qual_id,
        title=title,
        sector=sector,
        nsqf_level=nsqf_level,
        min_education=min_education,
        min_education_rank=min_education_rank,
        work_type=work_type,
        verification_status=verification_status,
        user_id=user_id
    )

def create_provider_record(
    conn,
    provider_id: str = "prov_alpha_01",
    name: str = "Alpha Skills Training Centre",
    provider_type: str = "training_centre",
    district_id: str = "District Alpha",
    block_id: str = "Block Alpha-1",
    user_id: str = "usr_fw_alpha"
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO opportunity_providers (
            id, provider_type, name, contact_name, contact_phone, contact_email,
            address_line, district_id, block_id, pincode, status, source_name,
            created_by_user_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        provider_id, provider_type, name, "Director Sharma", "+91-9876543210",
        "contact@alphaskills.org", "Main Road, Sector 4", district_id, block_id,
        "244001", "ACTIVE", "Field Worker Survey", user_id, now, now
    ))
    return {"id": provider_id, "name": name, "district_id": district_id, "block_id": block_id}

def create_opportunity_record(
    conn,
    opp_id: str = "opp_elec_oct_01",
    qualification_id: str = "qual_elec_repair_01",
    provider_id: str = "prov_alpha_01",
    title: str = "Basic Electrical Repair — October Batch",
    district_id: str = "District Alpha",
    block_id: str = "Block Alpha-1",
    status: str = "DRAFT",
    seats_total: int = 30,
    seats_available: int = 20,
    start_days_ahead: int = 30,
    expiry_days_ahead: int = 60,
    user_id: str = "usr_fw_alpha"
) -> Dict[str, Any]:
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat()
    start_dt = (now_dt + timedelta(days=start_days_ahead)).isoformat()
    end_dt = (now_dt + timedelta(days=start_days_ahead + 90)).isoformat()
    expires_dt = (now_dt + timedelta(days=expiry_days_ahead)).isoformat()

    conn.execute("""
        INSERT INTO local_opportunities (
            id, qualification_id, provider_id, opportunity_type, title, summary,
            district_id, block_id, location_text, delivery_mode, start_date, end_date,
            batch_start_date, batch_end_date, seats_total, seats_available, total_seats, available_seats,
            stipend_amount, status, batch_status, verification_expires_at,
            created_by_user_id, updated_by_user_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        opp_id, qualification_id, provider_id, "training_centre", title,
        f"Hands-on practical training for {title}", district_id, block_id,
        "Alpha Training Complex, Room 102", "offline_centre", start_dt, end_dt,
        start_dt[:10], end_dt[:10], seats_total, seats_available, seats_total, seats_available,
        1500.0, status, "upcoming", expires_dt,
        user_id, user_id, now, now
    ))
    return {
        "id": opp_id,
        "title": title,
        "qualification_id": qualification_id,
        "provider_id": provider_id,
        "district_id": district_id,
        "block_id": block_id,
        "status": status,
        "seats_available": seats_available,
        "verification_expires_at": expires_dt
    }

def create_evidence_record(
    conn,
    opp_id: str = "opp_elec_oct_01",
    evidence_type: str = "FIELD_VISIT",
    storage_key: str = "evidence/private_inspections/alpha_centre_inspection.pdf",
    note: str = "Physical inspection conducted on site. Centre has 12 functioning repair benches and safe electrical switchboards.",
    user_id: str = "usr_fw_alpha",
    is_approved: int = 1
) -> Dict[str, Any]:
    evidence_id = f"ev_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("""
        INSERT INTO opportunity_evidence (
            id, opportunity_id, evidence_type, storage_key, external_url,
            note, submitted_by_user_id, is_approved, created_at, reviewed_at, reviewed_by_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        evidence_id, opp_id, evidence_type, storage_key, None,
        note, user_id, is_approved, now, now, user_id
    ))
    return {
        "id": evidence_id,
        "opportunity_id": opp_id,
        "evidence_type": evidence_type,
        "storage_key": storage_key,
        "is_approved": is_approved
    }
