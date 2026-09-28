import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { Outcome, EmploymentOutcome } from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class OutcomeRepository {
  private prisma: PrismaClient;
  private auditRepo: AuditRepository;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
    this.auditRepo = new AuditRepository(this.prisma);
  }

  async createOutcome(input: {
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
  }): Promise<Outcome> {
    const id = `out_${uuidv4()}`;

    const outcome = await this.prisma.outcome.create({
      data: {
        id,
        beneficiary_id: input.beneficiaryId,
        referral_id: input.referralId || null,
        enrolment_status: input.enrolmentStatus || 'enrolled',
        completion_status: input.completionStatus || 'in_progress',
        dropout_reason: input.dropoutReason || null,
        employment_status: input.employmentStatus || 'unemployed',
        employer_or_enterprise_name: input.employerOrEnterpriseName || null,
        monthly_income_inr: input.monthlyIncomeInr ?? 0,
        toolkit_received: input.toolkitReceived || false,
        seed_grant_applied: input.seedGrantApplied || false,
        follow_up_date: input.followUpDate ? new Date(input.followUpDate) : null,
        notes: input.notes || null,
        recorded_by_worker_id: input.recordedByWorkerId,
      },
    });

    await this.auditRepo.logEvent({
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

    return this.mapRow(outcome);
  }

  async findById(id: string): Promise<Outcome | null> {
    const row = await this.prisma.outcome.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async findByBeneficiaryId(beneficiaryId: string): Promise<Outcome[]> {
    const rows = await this.prisma.outcome.findMany({
      where: { beneficiary_id: beneficiaryId },
      orderBy: { created_at: 'desc' },
    });
    return rows.map(this.mapRow);
  }

  async list(filters?: { employmentStatus?: EmploymentOutcome }): Promise<Outcome[]> {
    const where: any = {};
    if (filters?.employmentStatus) {
      where.employment_status = filters.employmentStatus;
    }

    const rows = await this.prisma.outcome.findMany({
      where,
      orderBy: { created_at: 'desc' },
    });
    return rows.map(this.mapRow);
  }

  async updateOutcome(
    id: string,
    updates: Partial<Omit<Outcome, 'id' | 'beneficiary_id' | 'created_at' | 'updated_at'>>,
    workerId: string
  ): Promise<Outcome | null> {
    const current = await this.findById(id);
    if (!current) return null;

    const data: any = {};
    if (updates.enrolment_status !== undefined) data.enrolment_status = updates.enrolment_status;
    if (updates.completion_status !== undefined) data.completion_status = updates.completion_status;
    if (updates.dropout_reason !== undefined) data.dropout_reason = updates.dropout_reason;
    if (updates.employment_status !== undefined) data.employment_status = updates.employment_status;
    if (updates.employer_or_enterprise_name !== undefined) data.employer_or_enterprise_name = updates.employer_or_enterprise_name;
    if (updates.monthly_income_inr !== undefined) data.monthly_income_inr = updates.monthly_income_inr;
    if (updates.toolkit_received !== undefined) data.toolkit_received = updates.toolkit_received;
    if (updates.seed_grant_applied !== undefined) data.seed_grant_applied = updates.seed_grant_applied;
    if (updates.follow_up_date !== undefined) data.follow_up_date = updates.follow_up_date ? new Date(updates.follow_up_date) : null;
    if (updates.notes !== undefined) data.notes = updates.notes;
    data.recorded_by_worker_id = workerId;

    const updatedRow = await this.prisma.outcome.update({
      where: { id },
      data,
    });

    await this.auditRepo.logEvent({
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
        enrolment_status: updatedRow.enrolment_status,
        employment_status: updatedRow.employment_status,
      },
    });

    return this.mapRow(updatedRow);
  }

  private mapRow(row: any): Outcome {
    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      referral_id: row.referral_id || undefined,
      enrolment_status: row.enrolment_status as any,
      completion_status: row.completion_status as any,
      dropout_reason: row.dropout_reason || undefined,
      employment_status: row.employment_status as any,
      employer_or_enterprise_name: row.employer_or_enterprise_name || undefined,
      monthly_income_inr: row.monthly_income_inr,
      toolkit_received: Boolean(row.toolkit_received),
      seed_grant_applied: Boolean(row.seed_grant_applied),
      follow_up_date: row.follow_up_date ? row.follow_up_date.toISOString() : undefined,
      notes: row.notes || undefined,
      recorded_by_worker_id: row.recorded_by_worker_id,
      created_at: row.created_at.toISOString(),
      updated_at: row.updated_at.toISOString(),
    };
  }
}
