import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { DriftAdvisory } from '../types/index.js';

export class MonitoringRepository {
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async recordAdvisory(input: Omit<DriftAdvisory, 'id' | 'created_at'>): Promise<DriftAdvisory> {
    const id = `drift_${uuidv4()}`;

    const advisory = await this.prisma.driftAdvisory.create({
      data: {
        id,
        district: input.district,
        flag_type: input.flag_type,
        severity: input.severity,
        headline: input.headline,
        evidence: JSON.stringify(input.evidence),
        suggested_human_action: input.suggested_human_action,
        status: 'open',
      },
    });

    return {
      id: advisory.id,
      district: advisory.district,
      flag_type: advisory.flag_type as any,
      severity: advisory.severity as any,
      headline: advisory.headline,
      evidence: typeof advisory.evidence === 'string' ? JSON.parse(advisory.evidence || '{}') : advisory.evidence,
      suggested_human_action: advisory.suggested_human_action,
      created_at: typeof advisory.created_at === 'string' ? advisory.created_at : advisory.created_at.toISOString(),
    };
  }

  async listAdvisories(filters?: { district?: string; status?: 'open' | 'acknowledged' | 'resolved' }): Promise<DriftAdvisory[]> {
    const where: any = {};
    if (filters?.district) where.district = filters.district;
    if (filters?.status) where.status = filters.status;

    const rows = await this.prisma.driftAdvisory.findMany({
      where,
      orderBy: { created_at: 'desc' },
    });

    return rows.map((r) => ({
      id: r.id,
      district: r.district,
      flag_type: r.flag_type as any,
      severity: r.severity as any,
      headline: r.headline,
      evidence: typeof r.evidence === 'string' ? JSON.parse(r.evidence || '{}') : r.evidence,
      suggested_human_action: r.suggested_human_action,
      created_at: typeof r.created_at === 'string' ? r.created_at : r.created_at.toISOString(),
    }));
  }

  async updateStatus(id: string, status: 'open' | 'acknowledged' | 'resolved'): Promise<boolean> {
    try {
      await this.prisma.driftAdvisory.update({
        where: { id },
        data: { status },
      });
      return true;
    } catch (e) {
      return false;
    }
  }
}
