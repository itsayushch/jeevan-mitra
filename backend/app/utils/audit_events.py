import uuid
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.utils.logger import logger

def log_audit_event(
    conn: sqlite3.Connection,
    actor_id: str,
    actor_name: str,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None
) -> str:
    """
    Log an immutable audit event for compliance, data reading, export, change, or deletion.
    """
    # Normalize actor_role to ensure compliance with database CHECK constraint
    allowed_roles = {'beneficiary', 'field_worker', 'district_officer', 'counselor', 'system', 'admin'}
    if actor_role not in allowed_roles:
        actor_role = 'beneficiary' if actor_role in ['anonymous', 'guest', 'authenticated_user'] else 'system'

    event_id = f"aud_{uuid.uuid4().hex[:12]}"
    now = timestamp or datetime.now(timezone.utc).isoformat()
    
    old_json = json.dumps(old_values) if old_values is not None else None
    new_json = json.dumps(new_values) if new_values is not None else None
    meta_json = json.dumps(metadata) if metadata is not None else None

    try:
        conn.execute("""
            INSERT INTO audit_events (
                id, actor_id, actor_name, actor_role, action,
                entity_type, entity_id, old_values, new_values, metadata, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            event_id, actor_id, actor_name, actor_role, action,
            entity_type, entity_id, old_json, new_json, meta_json, now
        ))
        logger.debug(f"Audit event recorded: {event_id} | {action} on {entity_type}:{entity_id} by {actor_role}:{actor_id}")
    except Exception as e:
        logger.error(f"Failed to record audit event: {e}")
        # In strict audit environments, re-raise; for resilience, raise so caller commits fail if audit fails
        raise e

    return event_id
