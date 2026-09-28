import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { Referral, ReferralStatus } from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class ReferralRepository {
  private prisma: PrismaClient;
  private auditRepo: AuditRepository;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
    this.auditRepo = new AuditRepository(this.prisma);
  }

  async createReferral(input: {
    beneficiaryId: string;
    recommendationId: string;
    localOpportunityId: string;
    assignedWorkerId: string;
    notes?: string;
  }): Promise<Referral> {
    const id = `ref_${uuidv4()}`;

    const referral = await this.prisma.referral.create({
      data: {
        id,
        beneficiary_id: input.beneficiaryId,
        recommendation_id: input.recommendationId,
        local_opportunity_id: input.localOpportunityId,
        assigned_worker_id: input.assignedWorkerId,
        status: 'pending',
        notes: input.notes || null,
        caste_document_verified: false,
        income_criteria_verified: false,
        residence_proof_verified: false,
        sms_sent: false,
        whatsapp_sent: false,
      },
    });

    await this.auditRepo.logEvent({
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

    return this.mapRow(referral);
  }

  async findById(id: string): Promise<Referral | null> {
    const row = await this.prisma.referral.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async list(filters?: {
    assignedWorkerId?: string;
    status?: ReferralStatus;
    beneficiaryId?: string;
  }): Promise<Referral[]> {
    const where: any = {};
    if (filters?.assignedWorkerId) where.assigned_worker_id = filters.assignedWorkerId;
    if (filters?.status) where.status = filters.status;
    if (filters?.beneficiaryId) where.beneficiary_id = filters.beneficiaryId;

    const rows = await this.prisma.referral.findMany({
      where,
      orderBy: { created_at: 'desc' },
    });
    return rows.map(this.mapRow);
  }

  async updateReferral(
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
  ): Promise<Referral | null> {
    const current = await this.findById(id);
    if (!current) return null;

    const data: any = {};
    if (updates.status !== undefined) data.status = updates.status;
    if (updates.notes !== undefined) data.notes = updates.notes;
    if (updates.caste_document_verified !== undefined) data.caste_document_verified = updates.caste_document_verified;
    if (updates.income_criteria_verified !== undefined) data.income_criteria_verified = updates.income_criteria_verified;
    if (updates.residence_proof_verified !== undefined) data.residence_proof_verified = updates.residence_proof_verified;
    if (updates.sms_sent !== undefined) data.sms_sent = updates.sms_sent;
    if (updates.whatsapp_sent !== undefined) data.whatsapp_sent = updates.whatsapp_sent;
    if (updates.next_follow_up !== undefined) data.next_follow_up = updates.next_follow_up ? new Date(updates.next_follow_up) : null;

    const updatedRow = await this.prisma.referral.update({
      where: { id },
      data,
    });

    await this.auditRepo.logEvent({
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
        status: updatedRow.status,
        caste_verified: updatedRow.caste_document_verified,
        income_verified: updatedRow.income_criteria_verified,
      },
    });

    return this.mapRow(updatedRow);
  }

  private mapRow(row: any): Referral {
    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      recommendation_id: row.recommendation_id,
      local_opportunity_id: row.local_opportunity_id,
      assigned_worker_id: row.assigned_worker_id,
      status: row.status as any,
      notes: row.notes || undefined,
      caste_document_verified: Boolean(row.caste_document_verified),
      income_criteria_verified: Boolean(row.income_criteria_verified),
      residence_proof_verified: Boolean(row.residence_proof_verified),
      sms_sent: Boolean(row.sms_sent),
      whatsapp_sent: Boolean(row.whatsapp_sent),
      next_follow_up: row.next_follow_up ? row.next_follow_up.toISOString() : undefined,
      created_at: row.created_at.toISOString(),
      updated_at: row.updated_at.toISOString(),
    };
  }
}
