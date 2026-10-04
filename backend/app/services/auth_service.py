import os
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from app.core.security import (
    hasher, create_access_token, generate_refresh_token, hash_refresh_token
)
from app.schemas.auth import LoginRequest, ChangePasswordRequest, BootstrapAdminRequest
from app.utils.audit_events import log_audit_event
from app.core.settings import settings

class AuthService:
    @staticmethod
    def login(conn, req: LoginRequest, ip_address: str, user_agent: str):
        # Allow passing normalized username or phone
        identifier = req.email_or_phone.lower().strip()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? OR phone = ?;",
            (identifier, identifier)
        ).fetchone()

        if not user:
            # We don't distinguish user not found vs password wrong to prevent enumeration
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = user["id"]

        if not user["is_active"]:
            log_audit_event(conn, actor_id=user_id, actor_name="System", actor_role="system", action="LOGIN_FAILED", entity_type="users", entity_id=user_id, metadata={"reason": "Account disabled", "ip": ip_address})
            raise HTTPException(status_code=401, detail="Account is disabled")

        if user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > datetime.now(timezone.utc):
            log_audit_event(conn, actor_id=user_id, actor_name="System", actor_role="system", action="LOGIN_FAILED", entity_type="users", entity_id=user_id, metadata={"reason": "Account locked", "ip": ip_address})
            raise HTTPException(status_code=401, detail="Account is temporarily locked")

        # Verify password
        if not user["password_hash"] or not hasher.verify(req.password, user["password_hash"]):
            failed_count = user["failed_login_count"] + 1
            locked_until = None
            if failed_count >= 5:
                # Lock for 15 minutes
                import datetime as dt
                locked_until = (datetime.now(timezone.utc) + dt.timedelta(minutes=15)).isoformat()
            
            conn.execute(
                "UPDATE users SET failed_login_count = ?, locked_until = ? WHERE id = ?;",
                (failed_count, locked_until, user_id)
            )
            log_audit_event(conn, actor_id=user_id, actor_name="System", actor_role="system", action="LOGIN_FAILED", entity_type="users", entity_id=user_id, metadata={"reason": "Invalid credentials", "ip": ip_address})
            conn.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Reset failed count on success
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE users SET failed_login_count = 0, locked_until = NULL, last_login_at = ? WHERE id = ?;",
            (now, user_id)
        )

        # Generate tokens
        refresh_token_plain = generate_refresh_token()
        refresh_token_hashed = hash_refresh_token(refresh_token_plain)
        
        # Issue for 30 days
        import datetime as dt
        expires_at = (datetime.now(timezone.utc) + dt.timedelta(days=30)).isoformat()
        
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

        conn.execute("""
            INSERT INTO refresh_tokens (
                id, user_id, token_hash, issued_at, expires_at, user_agent_hash, ip_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            session_id, user_id, refresh_token_hashed, now, expires_at, 
            str(hash(user_agent)) if user_agent else None,
            str(hash(ip_address)) if ip_address else None
        ))

        access_token = create_access_token(subject=user_id, session_id=session_id)
        
        log_audit_event(conn, actor_id=user_id, actor_name=user["display_name"], actor_role="beneficiary", action="LOGIN_SUCCESS", entity_type="users", entity_id=user_id, metadata={"ip": ip_address})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_plain,
            "session_id": session_id
        }

    @staticmethod
    def refresh(conn, plain_refresh_token: str, ip_address: str, user_agent: str):
        hashed_token = hash_refresh_token(plain_refresh_token)
        
        record = conn.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = ?;",
            (hashed_token,)
        ).fetchone()

        if not record:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
            
        user_id = record["user_id"]
        session_id = record["id"]

        # Check if revoked or expired
        if record["revoked_at"]:
            # Token reuse detected! Revoke all sessions for this user!
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE refresh_tokens SET revoked_at = ?, revoked_reason = ? WHERE user_id = ? AND revoked_at IS NULL;",
                (now, "Token reuse detected", user_id)
            )
            log_audit_event(conn, actor_id=user_id, actor_name="System", actor_role="system", action="TOKEN_REUSE_DETECTED", entity_type="refresh_tokens", entity_id=session_id, metadata={"ip": ip_address})
            conn.commit()  # Ensure revocation is committed before raising exception
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if datetime.fromisoformat(record["expires_at"]) < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        # Rotate token
        now = datetime.now(timezone.utc).isoformat()
        new_refresh_plain = generate_refresh_token()
        new_refresh_hashed = hash_refresh_token(new_refresh_plain)
        new_session_id = f"sess_{uuid.uuid4().hex[:12]}"
        
        import datetime as dt
        new_expires_at = (datetime.now(timezone.utc) + dt.timedelta(days=30)).isoformat()
        
        # Revoke old token
        conn.execute(
            "UPDATE refresh_tokens SET revoked_at = ?, revoked_reason = ?, last_used_at = ? WHERE id = ?;",
            (now, "Rotated", now, session_id)
        )
        
        # Insert new token
        conn.execute("""
            INSERT INTO refresh_tokens (
                id, user_id, token_hash, issued_at, expires_at, rotated_from_id, user_agent_hash, ip_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            new_session_id, user_id, new_refresh_hashed, now, new_expires_at, session_id,
            str(hash(user_agent)) if user_agent else None,
            str(hash(ip_address)) if ip_address else None
        ))

        access_token = create_access_token(subject=user_id, session_id=new_session_id)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_plain,
            "session_id": new_session_id
        }

    @staticmethod
    def logout(conn, plain_refresh_token: str, user_id: str):
        hashed_token = hash_refresh_token(plain_refresh_token)
        now = datetime.now(timezone.utc).isoformat()
        
        record = conn.execute(
            "SELECT id FROM refresh_tokens WHERE token_hash = ? AND user_id = ?;",
            (hashed_token, user_id)
        ).fetchone()
        
        if record:
            conn.execute(
                "UPDATE refresh_tokens SET revoked_at = ?, revoked_reason = 'Logout' WHERE id = ?;",
                (now, record["id"])
            )
            log_audit_event(conn, actor_id=user_id, actor_name="User", actor_role="beneficiary", action="LOGOUT", entity_type="refresh_tokens", entity_id=record["id"])

    @staticmethod
    def change_password(conn, user_id: str, req: ChangePasswordRequest):
        user = conn.execute("SELECT password_hash FROM users WHERE id = ?;", (user_id,)).fetchone()
        if not user or not user["password_hash"]:
            raise HTTPException(status_code=400, detail="Cannot change password for this account type")
            
        if not hasher.verify(req.current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect current password")
            
        new_hash = hasher.hash(req.new_password)
        now = datetime.now(timezone.utc).isoformat()
        
        # Update password
        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?;",
            (new_hash, now, user_id)
        )
        
        # Revoke all other sessions
        conn.execute(
            "UPDATE refresh_tokens SET revoked_at = ?, revoked_reason = 'Password changed' WHERE user_id = ? AND revoked_at IS NULL;",
            (now, user_id)
        )
        
        log_audit_event(conn, actor_id=user_id, actor_name="User", actor_role="beneficiary", action="PASSWORD_CHANGED", entity_type="users", entity_id=user_id)

    @staticmethod
    def bootstrap_admin(conn, req: BootstrapAdminRequest, ip_address: str):
        bootstrap_enabled = os.environ.get("BOOTSTRAP_ADMIN_ENABLED", "false").lower() == "true"
        if not bootstrap_enabled:
            raise HTTPException(status_code=403, detail="Bootstrap disabled")
            
        expected_secret = os.environ.get("BOOTSTRAP_SECRET")
        if not expected_secret or req.bootstrap_secret != expected_secret:
            raise HTTPException(status_code=403, detail="Invalid bootstrap secret")
            
        # Check if any active super_admin exists
        super_admins = conn.execute("""
            SELECT u.id FROM users u 
            JOIN user_roles ur ON u.id = ur.user_id 
            JOIN roles r ON ur.role_id = r.id 
            WHERE r.key = 'super_admin' AND u.is_active = 1
            LIMIT 1;
        """).fetchone()
        
        if super_admins:
            raise HTTPException(status_code=403, detail="Super admin already exists")
            
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        pw_hash = hasher.hash(req.password)
        
        conn.execute("""
            INSERT INTO users (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, 1, ?, ?)
        """, (user_id, req.email.lower().strip(), pw_hash, req.display_name, now, now))
        
        role = conn.execute("SELECT id FROM roles WHERE key = 'super_admin'").fetchone()
        if not role:
            raise HTTPException(status_code=500, detail="Super admin role not found in database")
            
        conn.execute("""
            INSERT INTO user_roles (user_id, role_id, assigned_at)
            VALUES (?, ?, ?)
        """, (user_id, role["id"], now))
        
        log_audit_event(conn, actor_id=user_id, actor_name=req.display_name, actor_role="super_admin", action="ADMIN_BOOTSTRAPPED", entity_type="users", entity_id=user_id, metadata={"ip": ip_address})
        return {"message": "Admin created successfully"}
