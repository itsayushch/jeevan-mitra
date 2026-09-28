import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { AuditEvent, ActorRole } from '../types/index.js';

export interface CreateAuditInput {
  actorId: string;
  actorName: string;
  actorRole: ActorRole;
  action: string;
  entityType: string;
  entityId: string;
  oldValues?: Record<string, unknown> | null;
  newValues?: Record<string, unknown> | null;
  metadata?: Record<string, unknown> | null;
}

export class AuditRepository {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  logEvent(input: CreateAuditInput): AuditEvent {
    const id = `audit_${uuidv4()}`;
    const timestamp = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO audit_events (
        id, actor_id, actor_name, actor_role, action, entity_type, entity_id,
        old_values, new_values, metadata, timestamp
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.actorId,
      input.actorName,
      input.actorRole,
      input.action,
      input.entityType,
      input.entityId,
      input.oldValues ? JSON.stringify(input.oldValues) : null,
      input.newValues ? JSON.stringify(input.newValues) : null,
      input.metadata ? JSON.stringify(input.metadata) : null,
      timestamp
    );

    return {
      id,
      actor_id: input.actorId,
      actor_name: input.actorName,
      actor_role: input.actorRole,
      action: input.action,
      entity_type: input.entityType,
      entity_id: input.entityId,
      old_values: input.oldValues,
      new_values: input.newValues,
      metadata: input.metadata,
      timestamp,
    };
  }

  getEventsByEntity(entityType: string, entityId: string): AuditEvent[] {
    const stmt = this.db.prepare(`
      SELECT * FROM audit_events
      WHERE entity_type = ? AND entity_id = ?
      ORDER BY timestamp DESC
    `);
    const rows = stmt.all(entityType, entityId) as any[];
    return rows.map(this.mapRowToAuditEvent);
  }

  getRecentEvents(limit: number = 50): AuditEvent[] {
    const stmt = this.db.prepare(`
      SELECT * FROM audit_events
      ORDER BY timestamp DESC
      LIMIT ?
    `);
    const rows = stmt.all(limit) as any[];
    return rows.map(this.mapRowToAuditEvent);
  }

  private mapRowToAuditEvent(row: any): AuditEvent {
    return {
      id: row.id,
      actor_id: row.actor_id,
      actor_name: row.actor_name,
      actor_role: row.actor_role,
      action: row.action,
      entity_type: row.entity_type,
      entity_id: row.entity_id,
      old_values: row.old_values ? JSON.parse(row.old_values) : null,
      new_values: row.new_values ? JSON.parse(row.new_values) : null,
      metadata: row.metadata ? JSON.parse(row.metadata) : null,
      timestamp: row.timestamp,
    };
  }
}
