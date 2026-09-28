import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { Referral, ReferralStatus } from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class ReferralRepository {
  private db: Database.Database;
  private auditRepo: AuditRepository;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
    this.auditRepo = new AuditRepository(this.db);
  }

  createReferral(input: {
    beneficiaryId: string;
    recommendationId: string;
    localOpportunityId: string;
    assignedWorkerId: string;
    notes?: string;
  }): Referral {
    const id = `ref_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO referrals (
        id, beneficiary_id, recommendation_id, local_opportunity_id,
        assigned_worker_id, status, notes, caste_document_verified,
        income_criteria_verified, residence_proof_verified,
        sms_sent, whatsapp_sent, next_follow_up, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.beneficiaryId,
      input.recommendationId,
      input.localOpportunityId,
      input.assignedWorkerId,
      'pending',
      input.notes || null,
      0,
      0,
      0,
      0,
      0,
      null,
      now,
      now
    );

    this.auditRepo.logEvent({
      actorId: input.assignedWorkerId,
      actorName: 'Field Worker',
      actorRole: 'field_worker',
      action: 'REFERRAL_CREATED',
      entityType: 'referral',
      entityId: id,
      newValues: {
        beneficiary_id: input.beneficiaryId,
        opportunity_id: input.localOpportunityId,
        status: 'pending',
      },
      metadata: { notes: input.notes },
    });

    return this.findById(id)!;
  }

  findById(id: string): Referral | null {
    const stmt = this.db.prepare(`SELECT * FROM referrals WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  list(filters?: {
    assignedWorkerId?: string;
    status?: ReferralStatus;
    beneficiaryId?: string;
  }): Referral[] {
    let query = `SELECT * FROM referrals WHERE 1=1`;
    const params: any[] = [];

    if (filters?.assignedWorkerId) {
      query += ` AND assigned_worker_id = ?`;
      params.push(filters.assignedWorkerId);
    }
    if (filters?.status) {
      query += ` AND status = ?`;
      params.push(filters.status);
    }
    if (filters?.beneficiaryId) {
      query += ` AND beneficiary_id = ?`;
      params.push(filters.beneficiaryId);
    }

    query += ` ORDER BY created_at DESC`;

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];
    return rows.map(this.mapRow);
  }

  updateReferral(
    id: string,
    updates: {
      status?: ReferralStatus;
      notes?: string;
      caste_document_verified?: boolean;
      income_criteria_verified?: boolean;
      residence_proof_verified?: boolean;
      sms_sent?: boolean;
      whatsapp_sent?: boolean;
      next_follow_up?: string;
      actorId: string;
      actorName: string;
    }
  ): Referral | null {
    const current = this.findById(id);
    if (!current) return null;

    const now = new Date().toISOString();
    const updated = {
      ...current,
      status: updates.status ?? current.status,
      notes: updates.notes !== undefined ? updates.notes : current.notes,
      caste_document_verified:
        updates.caste_document_verified !== undefined
          ? updates.caste_document_verified
          : current.caste_document_verified,
      income_criteria_verified:
        updates.income_criteria_verified !== undefined
          ? updates.income_criteria_verified
          : current.income_criteria_verified,
      residence_proof_verified:
        updates.residence_proof_verified !== undefined
          ? updates.residence_proof_verified
          : current.residence_proof_verified,
      sms_sent: updates.sms_sent !== undefined ? updates.sms_sent : current.sms_sent,
      whatsapp_sent:
        updates.whatsapp_sent !== undefined ? updates.whatsapp_sent : current.whatsapp_sent,
      next_follow_up:
        updates.next_follow_up !== undefined ? updates.next_follow_up : current.next_follow_up,
      updated_at: now,
    };

    const stmt = this.db.prepare(`
      UPDATE referrals
      SET status = ?, notes = ?, caste_document_verified = ?,
          income_criteria_verified = ?, residence_proof_verified = ?,
          sms_sent = ?, whatsapp_sent = ?, next_follow_up = ?, updated_at = ?
      WHERE id = ?
    `);

    stmt.run(
      updated.status,
      updated.notes || null,
      updated.caste_document_verified ? 1 : 0,
      updated.income_criteria_verified ? 1 : 0,
      updated.residence_proof_verified ? 1 : 0,
      updated.sms_sent ? 1 : 0,
      updated.whatsapp_sent ? 1 : 0,
      updated.next_follow_up || null,
      now,
      id
    );

    this.auditRepo.logEvent({
      actorId: updates.actorId,
      actorName: updates.actorName,
      actorRole: 'field_worker',
      action: 'REFERRAL_UPDATED',
      entityType: 'referral',
      entityId: id,
      oldValues: {
        status: current.status,
        caste_verified: current.caste_document_verified,
        income_verified: current.income_criteria_verified,
      },
      newValues: {
        status: updated.status,
        caste_verified: updated.caste_document_verified,
        income_verified: updated.income_criteria_verified,
      },
    });

    return this.findById(id);
  }

  private mapRow(row: any): Referral {
    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      recommendation_id: row.recommendation_id,
      local_opportunity_id: row.local_opportunity_id,
      assigned_worker_id: row.assigned_worker_id,
      status: row.status,
      notes: row.notes || undefined,
      caste_document_verified: Boolean(row.caste_document_verified),
      income_criteria_verified: Boolean(row.income_criteria_verified),
      residence_proof_verified: Boolean(row.residence_proof_verified),
      sms_sent: Boolean(row.sms_sent),
      whatsapp_sent: Boolean(row.whatsapp_sent),
      next_follow_up: row.next_follow_up || undefined,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}
