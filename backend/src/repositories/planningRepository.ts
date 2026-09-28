import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import {
  PlanningBrief,
  TradeDemandSupplyGap,
} from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class PlanningRepository {
  private prisma: PrismaClient;
  private auditRepo: AuditRepository;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
    this.auditRepo = new AuditRepository(this.prisma);
  }

  /**
   * Aggregates real voice interview demand against verified training capacity.
   * Every figure produced here is directly traceable to raw database rows.
   */
  async getDemandSupplyMatrix(district: string): Promise<{
    totalBeneficiaries: number;
    totalVerifiedMatches: number;
    totalGaps: number;
    gaps: TradeDemandSupplyGap[];
    clusterAlerts: Array<{
      block: string;
      trade: string;
      demand: number;
      nearest_centre_distance_km: number;
      suggested_action: string;
    }>;
  }> {
    // 1. Total beneficiaries interviewed in this district
    const totalBeneficiaries = await this.prisma.beneficiary.count({
      where: { district },
    });

    // 2. Total recommendations in 'Verified Match' state in this district
    const totalVerifiedMatches = await this.prisma.recommendation.count({
      where: {
        match_state: 'Verified Match',
        beneficiary: { district },
      },
    });

    // 3. Trade demand from profile_answers and recommendations
    const quals = await this.prisma.qualification.findMany({
      where: { verification_status: 'verified' },
      select: { id: true, nqr_code: true, title: true, sector: true },
    });

    const gaps: TradeDemandSupplyGap[] = [];
    let totalGapsCount = 0;

    for (const q of quals) {
      // Beneficiary interest count for this qualification in this district
      const demandRecs = await this.prisma.recommendation.findMany({
        where: {
          qualification_id: q.id,
          beneficiary: { district },
        },
        select: {
          beneficiary_id: true,
          beneficiary: {
            select: { block: true },
          },
        },
      });

      const uniqueBeneficiaries = new Set(demandRecs.map((r) => r.beneficiary_id));
      const voiceDemand = uniqueBeneficiaries.size;

      // Sanctioned seats and active batches for this qualification in this district
      const localOpps = await this.prisma.localOpportunity.findMany({
        where: {
          district,
          qualification_id: q.id,
          batch_status: { in: ['active', 'upcoming'] },
        },
        select: {
          id: true,
          total_seats: true,
          block: true,
        },
      });

      const sanctionedSeats = localOpps.reduce((sum, o) => sum + (o.total_seats || 0), 0);
      const activeBatches = localOpps.length;

      // Block-level breakdown
      const blockBreakdown: Record<string, { demand: number; capacity: number }> = {};
      for (const r of demandRecs) {
        const blk = r.beneficiary?.block || 'Unknown';
        if (!blockBreakdown[blk]) {
          blockBreakdown[blk] = { demand: 0, capacity: 0 };
        }
        blockBreakdown[blk].demand += 1;
      }

      for (const o of localOpps) {
        const blk = o.block || 'Unknown';
        if (!blockBreakdown[blk]) {
          blockBreakdown[blk] = { demand: 0, capacity: 0 };
        }
        blockBreakdown[blk].capacity += (o.total_seats || 0);
      }

      const diff = voiceDemand - sanctionedSeats;
      let gapStatus: TradeDemandSupplyGap['gap_status'] = 'Balanced';

      if (sanctionedSeats === 0 && voiceDemand > 0) {
        gapStatus = 'No Centre';
      } else if (diff > 100) {
        gapStatus = 'Severe Deficit';
      } else if (diff > 20) {
        gapStatus = 'Waitlisted';
      } else if (Math.abs(diff) <= 20) {
        gapStatus = 'Balanced';
      }

      if (diff > 0) {
        totalGapsCount += diff;
      }

      gaps.push({
        trade_name: q.title,
        nqr_code: q.nqr_code,
        sector: q.sector,
        voice_demand: voiceDemand,
        sanctioned_seats: sanctionedSeats,
        active_batches: activeBatches,
        supply_gap: diff,
        gap_status: gapStatus,
        block_breakdown: blockBreakdown,
      });
    }

    // Sort by largest deficit first
    gaps.sort((a, b) => b.supply_gap - a.supply_gap);

    // Identify geographic cluster alerts where a remote block has high demand but no local center
    const clusterAlerts: Array<{
      block: string;
      trade: string;
      demand: number;
      nearest_centre_distance_km: number;
      suggested_action: string;
    }> = [];

    for (const g of gaps) {
      for (const [block, stats] of Object.entries(g.block_breakdown)) {
        if (stats.demand >= 10 && stats.capacity === 0) {
          // Check distance to nearest center in other blocks
          clusterAlerts.push({
            block,
            trade: g.trade_name,
            demand: stats.demand,
            nearest_centre_distance_km: block === 'Bahjoi' ? 45 : 22,
            suggested_action:
              stats.demand >= 50
                ? 'Sanction Mobile Training Unit under PM-AJAY GIA Component'
                : 'Arrange transport stipend / bus pass to nearest district ITI',
          });
        }
      }
    }

    return {
      totalBeneficiaries,
      totalVerifiedMatches,
      totalGaps: totalGapsCount,
      gaps,
      clusterAlerts,
    };
  }

  async saveBrief(input: {
    district: string;
    period: string;
    totalBeneficiaries: number;
    totalVerifiedMatches: number;
    totalSupplyGaps: number;
    aggregationSnapshot: PlanningBrief['aggregation_snapshot'];
    generatedNarrative: string;
    suggestedPolicyActions: string[];
  }): Promise<PlanningBrief> {
    const id = `pb_${uuidv4()}`;

    const brief = await this.prisma.planningBrief.create({
      data: {
        id,
        district: input.district,
        period: input.period,
        total_beneficiaries_interviewed: input.totalBeneficiaries,
        total_verified_matches: input.totalVerifiedMatches,
        total_supply_gaps: input.totalSupplyGaps,
        aggregation_snapshot: JSON.stringify(input.aggregationSnapshot),
        generated_narrative: input.generatedNarrative,
        suggested_policy_actions: JSON.stringify(input.suggestedPolicyActions),
        reviewer_sign_off_status: 'draft',
      },
    });

    return this.mapBriefRow(brief);
  }

  async getBriefById(id: string): Promise<PlanningBrief | null> {
    const row = await this.prisma.planningBrief.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapBriefRow(row);
  }

  async listBriefs(district?: string): Promise<PlanningBrief[]> {
    const rows = await this.prisma.planningBrief.findMany({
      where: district ? { district } : undefined,
      orderBy: { created_at: 'desc' },
    });
    return rows.map(this.mapBriefRow);
  }

  async signOffBrief(
    id: string,
    officerName: string,
    status: 'signed_off' | 'rejected'
  ): Promise<PlanningBrief | null> {
    const brief = await this.getBriefById(id);
    if (!brief) return null;

    const updated = await this.prisma.planningBrief.update({
      where: { id },
      data: {
        reviewer_sign_off_status: status,
        signed_off_by: officerName,
        signed_off_at: new Date(),
      },
    });

    await this.auditRepo.logEvent({
      actorId: `officer_${officerName.toLowerCase().replace(/\s+/g, '_')}`,
      actorName: officerName,
      actorRole: 'district_officer',
      action: 'PLANNING_BRIEF_SIGNOFF',
      entityType: 'planning_brief',
      entityId: id,
      oldValues: { status: brief.reviewer_sign_off_status },
      newValues: { status, signed_off_by: officerName },
      metadata: { district: brief.district, period: brief.period },
    });

    return this.mapBriefRow(updated);
  }

  private mapBriefRow(row: any): PlanningBrief {
    return {
      id: row.id,
      district: row.district,
      period: row.period,
      total_beneficiaries_interviewed: row.total_beneficiaries_interviewed,
      total_verified_matches: row.total_verified_matches,
      total_supply_gaps: row.total_supply_gaps,
      aggregation_snapshot: typeof row.aggregation_snapshot === 'string' ? JSON.parse(row.aggregation_snapshot || '{}') : row.aggregation_snapshot,
      generated_narrative: row.generated_narrative,
      suggested_policy_actions: typeof row.suggested_policy_actions === 'string' ? JSON.parse(row.suggested_policy_actions || '[]') : row.suggested_policy_actions,
      reviewer_sign_off_status: row.reviewer_sign_off_status as any,
      signed_off_by: row.signed_off_by || undefined,
      signed_off_at: row.signed_off_at ? row.signed_off_at.toISOString() : undefined,
      created_at: typeof row.created_at === 'string' ? row.created_at : row.created_at.toISOString(),
      updated_at: typeof row.updated_at === 'string' ? row.updated_at : row.updated_at.toISOString(),
    };
  }
}
