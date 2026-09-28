import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
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
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async logEvent(input: CreateAuditInput): Promise<AuditEvent> {
    const id = `audit_${uuidv4()}`;

    const event = await this.prisma.auditEvent.create({
      data: {
        id,
        actor_id: input.actorId,
        actor_name: input.actorName,
        actor_role: input.actorRole,
        action: input.action,
        entity_type: input.entityType,
        entity_id: input.entityId,
        old_values: input.oldValues ? JSON.stringify(input.oldValues) : null,
        new_values: input.newValues ? JSON.stringify(input.newValues) : null,
        metadata: input.metadata ? JSON.stringify(input.metadata) : null,
      },
    });

    return this.mapRowToAuditEvent(event);
  }

  async getEventsByEntity(entityType: string, entityId: string): Promise<AuditEvent[]> {
    const rows = await this.prisma.auditEvent.findMany({
      where: {
        entity_type: entityType,
        entity_id: entityId,
      },
      orderBy: { timestamp: 'desc' },
    });
    return rows.map(this.mapRowToAuditEvent);
  }

  async getRecentEvents(limit: number = 50): Promise<AuditEvent[]> {
    const rows = await this.prisma.auditEvent.findMany({
      orderBy: { timestamp: 'desc' },
      take: limit,
    });
    return rows.map(this.mapRowToAuditEvent);
  }

  private mapRowToAuditEvent(row: any): AuditEvent {
    return {
      id: row.id,
      actor_id: row.actor_id,
      actor_name: row.actor_name,
      actor_role: row.actor_role as ActorRole,
      action: row.action,
      entity_type: row.entity_type,
      entity_id: row.entity_id,
      old_values: row.old_values ? JSON.parse(row.old_values) : null,
      new_values: row.new_values ? JSON.parse(row.new_values) : null,
      metadata: row.metadata ? JSON.parse(row.metadata) : null,
      timestamp: row.timestamp.toISOString(),
    };
  }
}
