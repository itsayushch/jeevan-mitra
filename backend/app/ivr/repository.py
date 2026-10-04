import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from app.ivr.constants import IVRState, IVRStatus, DEFAULT_LANGUAGE
from app.ivr.security import hash_caller_reference


class IVRRepository:
    """
    Data persistence layer for IVR sessions, events, and callback requests.
    Supports atomic transactions and prevents duplicate callbacks and event replay.
    """

    @staticmethod
    def create_session(
        conn: Any,
        session_id: str,
        provider: str = "mock",
        provider_call_id: Optional[str] = None,
        caller_reference: Optional[str] = None,
        beneficiary_id: Optional[str] = None,
        language: str = DEFAULT_LANGUAGE,
        timeout_seconds: int = 600,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires_at_iso = (now + timedelta(seconds=timeout_seconds)).isoformat()
        caller_hash = hash_caller_reference(caller_reference)
        context_str = json.dumps(initial_context or {})

        conn.execute(
            """
            INSERT INTO ivr_sessions (
                id, provider, provider_call_id, caller_reference_hash,
                beneficiary_id, current_state, language, status,
                invalid_attempt_count, current_context_json,
                started_at, updated_at, ended_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
            (
                session_id,
                provider,
                provider_call_id,
                caller_hash,
                beneficiary_id,
                IVRState.WELCOME.value,
                language,
                IVRStatus.ACTIVE.value,
                0,
                context_str,
                now_iso,
                now_iso,
                None,
                expires_at_iso,
            ),
        )

        row = conn.execute(
            "SELECT * FROM ivr_sessions WHERE id = ?;", (session_id,)
        ).fetchone()
        return dict(row)

    @staticmethod
    def get_session(conn: Any, session_id: str) -> Optional[Dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM ivr_sessions WHERE id = ?;", (session_id,)
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        if isinstance(res.get("current_context_json"), str):
            try:
                res["context"] = json.loads(res["current_context_json"])
            except Exception:
                res["context"] = {}
        else:
            res["context"] = res.get("current_context_json") or {}
        return res

    @staticmethod
    def update_session_state(
        conn: Any,
        session_id: str,
        current_state: str,
        status: str,
        invalid_attempt_count: int,
        context: Optional[Dict[str, Any]] = None,
        ended_at: Optional[str] = None,
    ) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        context_str = json.dumps(context or {})

        conn.execute(
            """
            UPDATE ivr_sessions
            SET current_state = ?,
                status = ?,
                invalid_attempt_count = ?,
                current_context_json = ?,
                updated_at = ?,
                ended_at = COALESCE(?, ended_at)
            WHERE id = ?;
        """,
            (
                current_state,
                status,
                invalid_attempt_count,
                context_str,
                now_iso,
                ended_at,
                session_id,
            ),
        )

    @staticmethod
    def append_event(
        conn: Any,
        session_id: str,
        event_type: str,
        state_before: str,
        state_after: str,
        digit: Optional[str],
        prompt_key: str,
        idempotency_key: Optional[str] = None,
        safe_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event_id = f"ievt_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(safe_payload or {})

        conn.execute(
            """
            INSERT INTO ivr_events (
                id, session_id, event_type, state_before, state_after,
                digit, prompt_key, idempotency_key, safe_payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
            (
                event_id,
                session_id,
                event_type,
                state_before,
                state_after,
                digit,
                prompt_key,
                idempotency_key,
                payload_str,
                now_iso,
            ),
        )

        row = conn.execute(
            "SELECT * FROM ivr_events WHERE id = ?;", (event_id,)
        ).fetchone()
        return dict(row)

    @staticmethod
    def get_event_by_idempotency_key(
        conn: Any, session_id: str, idempotency_key: str
    ) -> Optional[Dict[str, Any]]:
        if not idempotency_key:
            return None
        row = conn.execute(
            """
            SELECT * FROM ivr_events
            WHERE session_id = ? AND idempotency_key = ?
            ORDER BY created_at DESC LIMIT 1;
        """,
            (session_id, idempotency_key),
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        if isinstance(res.get("safe_payload_json"), str):
            try:
                res["safe_payload"] = json.loads(res["safe_payload_json"])
            except Exception:
                res["safe_payload"] = {}
        return res

    @staticmethod
    def get_events_by_session(conn: Any, session_id: str) -> List[Dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT * FROM ivr_events
            WHERE session_id = ?
            ORDER BY created_at ASC;
        """,
            (session_id,),
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if isinstance(d.get("safe_payload_json"), str):
                try:
                    d["safe_payload"] = json.loads(d["safe_payload_json"])
                except Exception:
                    d["safe_payload"] = {}
            results.append(d)
        return results

    @staticmethod
    def get_or_create_callback_request(
        conn: Any,
        session_id: str,
        beneficiary_id: Optional[str] = None,
        callback_reason: str = "general_help",
        assigned_worker_id: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Idempotent callback creation: returns existing callback request if already created for this session.
        """
        existing = conn.execute(
            """
            SELECT * FROM ivr_callback_requests WHERE session_id = ?;
        """,
            (session_id,),
        ).fetchone()

        if existing:
            return dict(existing)

        cb_id = f"icb_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            INSERT INTO ivr_callback_requests (
                id, session_id, beneficiary_id, callback_reason,
                status, assigned_worker_id, case_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'requested', ?, ?, ?, ?);
        """,
            (
                cb_id,
                session_id,
                beneficiary_id,
                callback_reason,
                assigned_worker_id,
                case_id,
                now_iso,
                now_iso,
            ),
        )

        row = conn.execute(
            "SELECT * FROM ivr_callback_requests WHERE id = ?;", (cb_id,)
        ).fetchone()
        return dict(row)

    @staticmethod
    def get_callback_request(conn: Any, session_id: str) -> Optional[Dict[str, Any]]:
        row = conn.execute(
            "SELECT * FROM ivr_callback_requests WHERE session_id = ?;", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def expire_session(conn: Any, session_id: str) -> Optional[Dict[str, Any]]:
        now_iso = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            UPDATE ivr_sessions
            SET current_state = ?, status = ?, ended_at = ?, updated_at = ?
            WHERE id = ?;
        """,
            (
                IVRState.EXPIRED.value,
                IVRStatus.EXPIRED.value,
                now_iso,
                now_iso,
                session_id,
            ),
        )
        row = conn.execute(
            "SELECT * FROM ivr_sessions WHERE id = ?;", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def expire_stale_sessions(conn: Any) -> int:
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor = conn.execute(
            """
            UPDATE ivr_sessions
            SET current_state = ?, status = ?, ended_at = ?, updated_at = ?
            WHERE status = 'active' AND expires_at < ?;
        """,
            (
                IVRState.EXPIRED.value,
                IVRStatus.EXPIRED.value,
                now_iso,
                now_iso,
                now_iso,
            ),
        )
        return cursor.rowcount if hasattr(cursor, "rowcount") else 0
