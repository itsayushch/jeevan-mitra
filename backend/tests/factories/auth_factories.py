import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.core.security import hasher, create_access_token

DEFAULT_PASSWORD = "SecurePassword123!"

def create_user(
    conn,
    user_id: str,
    email: str,
    display_name: str,
    role_key: str,
    password: str = DEFAULT_PASSWORD,
    district_id: Optional[str] = None,
    block_id: Optional[str] = None,
    scope_type: str = "district",
    is_active: int = 1,
    is_superuser: int = 0
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    pw_hash = hasher.hash(password)

    # 1. Insert user
    conn.execute("""
        INSERT INTO users (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, email, pw_hash, display_name, is_active, is_superuser, now, now))

    # 2. Assign role
    role_row = conn.execute("SELECT id FROM roles WHERE key = ?", (role_key,)).fetchone()
    if not role_row:
        # Create role if missing
        role_id = f"role_{role_key}"
        conn.execute("INSERT INTO roles (id, key, display_name, description, created_at) VALUES (?, ?, ?, ?, ?)",
                     (role_id, role_key, role_key.replace("_", " ").title(), f"{role_key} role", now))
    else:
        role_id = role_row["id"]

    conn.execute("INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)", (user_id, role_id, now))

    # 3. Assign scope if district_id provided
    if district_id:
        scope_id = f"scope_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO user_scopes (id, user_id, district_id, block_id, scope_type, assigned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scope_id, user_id, district_id, block_id, scope_type, now))

    return {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "role": role_key,
        "district_id": district_id,
        "block_id": block_id
    }

def create_catalogue_manager(conn, user_id: str = "usr_cat_mgr_a", email: str = "cat_mgr@example.com") -> Dict[str, Any]:
    return create_user(
        conn,
        user_id=user_id,
        email=email,
        display_name="Catalogue Manager Alpha",
        role_key="catalogue_manager"
    )

def create_beneficiary_actor(
    conn,
    user_id: str = "usr_ben_a",
    email: str = "beneficiary_a@example.com",
    district_id: str = "District Alpha",
    block_id: str = "Block Alpha-1"
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    user = create_user(
        conn,
        user_id=user_id,
        email=email,
        display_name="Beneficiary Alpha",
        role_key="beneficiary",
        district_id=district_id,
        block_id=block_id,
        scope_type="block"
    )

    # Insert beneficiary record
    ben_id = user_id
    conn.execute("""
        INSERT INTO beneficiaries (
            id, name, district, block, owner_type, owner_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ben_id, "Beneficiary Alpha", district_id, block_id,
        "authenticated_user", user_id, now, now
    ))

    # Insert confirmed profile answers for recommendations
    answers = [
        ("district", district_id),
        ("block", block_id),
        ("education", "10th Pass"),
        ("work_preference", "wage"),
        ("interests", json.dumps(["electrical", "repair", "solar"]))
    ]
    for fn, fv in answers:
        conn.execute("""
            INSERT INTO profile_answers (
                id, beneficiary_id, field_name, field_value, confirmation_status, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'confirmed', 'beneficiary_edit', ?, ?)
        """, (f"ans_{uuid.uuid4().hex[:8]}", ben_id, fn, fv, now, now))

    # Also insert consent record
    conn.execute("""
        INSERT INTO consent_records (
            id, beneficiary_id, consent_type, status, timestamp
        ) VALUES (?, ?, ?, ?, ?)
    """, (f"con_{uuid.uuid4().hex[:8]}", ben_id, "dpdp_general", "granted", now))

    return user

def create_field_worker_alpha(
    conn,
    user_id: str = "usr_fw_alpha",
    email: str = "worker_alpha@example.com",
    district_id: str = "District Alpha",
    block_id: str = "Block Alpha-1"
) -> Dict[str, Any]:
    return create_user(
        conn,
        user_id=user_id,
        email=email,
        display_name="Field Worker Alpha",
        role_key="field_worker",
        district_id=district_id,
        block_id=block_id,
        scope_type="block"
    )

def create_field_worker_beta(
    conn,
    user_id: str = "usr_fw_beta",
    email: str = "worker_beta@example.com",
    district_id: str = "District Beta",
    block_id: str = "Block Beta-1"
) -> Dict[str, Any]:
    return create_user(
        conn,
        user_id=user_id,
        email=email,
        display_name="Field Worker Beta",
        role_key="field_worker",
        district_id=district_id,
        block_id=block_id,
        scope_type="block"
    )

def create_auditor_alpha(
    conn,
    user_id: str = "usr_auditor_alpha",
    email: str = "auditor_alpha@example.com",
    district_id: str = "District Alpha"
) -> Dict[str, Any]:
    return create_user(
        conn,
        user_id=user_id,
        email=email,
        display_name="Auditor Alpha",
        role_key="auditor",
        district_id=district_id,
        scope_type="district"
    )

def create_super_admin(
    conn,
    user_id: str = "usr_super_admin",
    email: str = "admin@example.com"
) -> Dict[str, Any]:
    return create_user(
        conn,
        user_id=user_id,
        email=email,
        display_name="Super Administrator",
        role_key="super_admin",
        is_superuser=1
    )

def get_auth_headers(user_id: str, session_id: Optional[str] = None) -> Dict[str, str]:
    sid = session_id or f"sess_{uuid.uuid4().hex[:8]}"
    token = create_access_token(subject=user_id, session_id=sid)
    return {
        "Authorization": f"Bearer {token}",
        "X-Session-ID": sid,
        "Content-Type": "application/json"
    }
