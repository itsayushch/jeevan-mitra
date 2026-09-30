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
    # Normalize actor_role to ensure compliance with database CHECK constraint ('beneficiary', 'field_worker', 'district_officer', 'system')
    role_map = {
        'admin': 'system',
        'catalogue_admin': 'system',
        'super_admin': 'system',
        'counselor': 'field_worker',
        'anonymous': 'beneficiary',
        'guest': 'beneficiary',
        'authenticated_user': 'beneficiary'
    }
    actor_role = role_map.get(actor_role, actor_role)
    if actor_role not in ('beneficiary', 'field_worker', 'district_officer', 'system'):
        actor_role = 'system'

    event_id = f"aud_{uuid.uuid4().hex[:12]}"
    now = timestamp or datetime.now(timezone.utc).isoformat()
    
    old_json = json.dumps(old_values) if old_values is not None else None
    new_json = json.dumps(new_values) if new_values is not None else None
    meta_json = json.dumps(metadata) if metadata is not None else None

    try:
        # Migrate old kwargs into metadata_json if provided
        meta_dict = metadata or {}
        if actor_name:
            meta_dict['legacy_actor_name'] = actor_name
        if actor_role:
            meta_dict['legacy_actor_role'] = actor_role
            
        final_meta_json = json.dumps(meta_dict) if meta_dict else None
            
        conn.execute("""
            INSERT INTO audit_events (
                id, actor_user_id, action,
                entity_type, entity_id, before_json, after_json, metadata_json, created_at, request_id, outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            event_id, actor_id, action,
            entity_type, entity_id, old_json, new_json, final_meta_json, now, None, "SUCCESS"
        ))
        logger.debug(f"Audit event recorded: {event_id} | {action} on {entity_type}:{entity_id} by {actor_role}:{actor_id}")
    except Exception as e:
        logger.error(f"Failed to record audit event: {e}")
        # In strict audit environments, re-raise; for resilience, raise so caller commits fail if audit fails
        raise e

    return event_id
