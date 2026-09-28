import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { Outcome, EmploymentOutcome } from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class OutcomeRepository {
  private db: Database.Database;
  private auditRepo: AuditRepository;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
    this.auditRepo = new AuditRepository(this.db);
  }

  createOutcome(input: {
    beneficiaryId: string;
    referralId?: string;
    enrolmentStatus?: 'enrolled' | 'completed' | 'dropped_out';
    completionStatus?: 'in_progress' | 'passed' | 'failed' | 'dropped_out';
    dropoutReason?: string;
    employmentStatus?: EmploymentOutcome;
    employerOrEnterpriseName?: string;
    monthlyIncomeInr?: number;
    toolkitReceived?: boolean;
    seedGrantApplied?: boolean;
    followUpDate?: string;
    notes?: string;
    recordedByWorkerId: string;
  }): Outcome {
    const id = `out_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO outcomes (
        id, beneficiary_id, referral_id, enrolment_status,
        completion_status, dropout_reason, employment_status,
        employer_or_enterprise_name, monthly_income_inr,
        toolkit_received, seed_grant_applied, follow_up_date,
        notes, recorded_by_worker_id, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.beneficiaryId,
      input.referralId || null,
      input.enrolmentStatus || 'enrolled',
      input.completionStatus || 'in_progress',
      input.dropoutReason || null,
      input.employmentStatus || 'unemployed',
      input.employerOrEnterpriseName || null,
      input.monthlyIncomeInr ?? 0,
      input.toolkitReceived ? 1 : 0,
      input.seedGrantApplied ? 1 : 0,
      input.followUpDate || null,
      input.notes || null,
      input.recordedByWorkerId,
      now,
      now
    );

    this.auditRepo.logEvent({
      actorId: input.recordedByWorkerId,
      actorName: 'Field Worker',
      actorRole: 'field_worker',
      action: 'OUTCOME_RECORDED',
      entityType: 'outcome',
      entityId: id,
      newValues: {
        enrolment_status: input.enrolmentStatus,
        employment_status: input.employmentStatus,
        monthly_income: input.monthlyIncomeInr,
      },
      metadata: { beneficiary_id: input.beneficiaryId },
    });

    return this.findById(id)!;
  }

  findById(id: string): Outcome | null {
    const stmt = this.db.prepare(`SELECT * FROM outcomes WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  findByBeneficiaryId(beneficiaryId: string): Outcome[] {
    const stmt = this.db.prepare(`
      SELECT * FROM outcomes
      WHERE beneficiary_id = ?
      ORDER BY created_at DESC
    `);
    const rows = stmt.all(beneficiaryId) as any[];
    return rows.map(this.mapRow);
  }

  list(filters?: { employmentStatus?: EmploymentOutcome }): Outcome[] {
    let query = `SELECT * FROM outcomes WHERE 1=1`;
    const params: any[] = [];

    if (filters?.employmentStatus) {
      query += ` AND employment_status = ?`;
      params.push(filters.employmentStatus);
    }

    query += ` ORDER BY created_at DESC`;

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];
    return rows.map(this.mapRow);
  }

  updateOutcome(
    id: string,
    updates: Partial<Omit<Outcome, 'id' | 'beneficiary_id' | 'created_at' | 'updated_at'>>,
    workerId: string
  ): Outcome | null {
    const current = this.findById(id);
    if (!current) return null;

    const now = new Date().toISOString();
    const updated = { ...current, ...updates, updated_at: now };

    const stmt = this.db.prepare(`
      UPDATE outcomes
      SET enrolment_status = ?, completion_status = ?, dropout_reason = ?,
          employment_status = ?, employer_or_enterprise_name = ?,
          monthly_income_inr = ?, toolkit_received = ?, seed_grant_applied = ?,
          follow_up_date = ?, notes = ?, recorded_by_worker_id = ?, updated_at = ?
      WHERE id = ?
    `);

    stmt.run(
      updated.enrolment_status,
      updated.completion_status,
      updated.dropout_reason || null,
      updated.employment_status,
      updated.employer_or_enterprise_name || null,
      updated.monthly_income_inr,
      updated.toolkit_received ? 1 : 0,
      updated.seed_grant_applied ? 1 : 0,
      updated.follow_up_date || null,
      updated.notes || null,
      workerId,
      now,
      id
    );

    this.auditRepo.logEvent({
      actorId: workerId,
      actorName: 'Field Worker',
      actorRole: 'field_worker',
      action: 'OUTCOME_UPDATED',
      entityType: 'outcome',
      entityId: id,
      oldValues: {
        enrolment_status: current.enrolment_status,
        employment_status: current.employment_status,
      },
      newValues: {
        enrolment_status: updated.enrolment_status,
        employment_status: updated.employment_status,
      },
    });

    return this.findById(id);
  }

  private mapRow(row: any): Outcome {
    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      referral_id: row.referral_id || undefined,
      enrolment_status: row.enrolment_status,
      completion_status: row.completion_status,
      dropout_reason: row.dropout_reason || undefined,
      employment_status: row.employment_status,
      employer_or_enterprise_name: row.employer_or_enterprise_name || undefined,
      monthly_income_inr: row.monthly_income_inr,
      toolkit_received: Boolean(row.toolkit_received),
      seed_grant_applied: Boolean(row.seed_grant_applied),
      follow_up_date: row.follow_up_date || undefined,
      notes: row.notes || undefined,
      recorded_by_worker_id: row.recorded_by_worker_id,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}
