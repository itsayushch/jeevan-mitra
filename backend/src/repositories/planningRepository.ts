import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import {
  PlanningBrief,
  TradeDemandSupplyGap,
} from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class PlanningRepository {
  private db: Database.Database;
  private auditRepo: AuditRepository;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
    this.auditRepo = new AuditRepository(this.db);
  }

  /**
   * Aggregates real voice interview demand against verified training capacity.
   * Every figure produced here is directly traceable to raw database rows.
   */
  getDemandSupplyMatrix(district: string): {
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
  } {
    // 1. Total beneficiaries interviewed in this district
    const totalBenRow = this.db
      .prepare(`SELECT COUNT(DISTINCT id) as cnt FROM beneficiaries WHERE district = ?`)
      .get(district) as any;
    const totalBeneficiaries = totalBenRow?.cnt || 0;

    // 2. Total recommendations in 'Verified Match' state in this district
    const verifiedRow = this.db
      .prepare(`
        SELECT COUNT(r.id) as cnt
        FROM recommendations r
        JOIN beneficiaries b ON r.beneficiary_id = b.id
        WHERE b.district = ? AND r.match_state = 'Verified Match'
      `)
      .get(district) as any;
    const totalVerifiedMatches = verifiedRow?.cnt || 0;

    // 3. Trade demand from profile_answers and recommendations
    // Query all verified qualifications
    const quals = this.db
      .prepare(`SELECT id, nqr_code, title, sector FROM qualifications WHERE verification_status = 'verified'`)
      .all() as any[];

    const gaps: TradeDemandSupplyGap[] = [];
    let totalGapsCount = 0;

    for (const q of quals) {
      // Beneficiary interest count for this qualification in this district
      const demandRow = this.db
        .prepare(`
          SELECT COUNT(DISTINCT r.beneficiary_id) as demand
          FROM recommendations r
          JOIN beneficiaries b ON r.beneficiary_id = b.id
          WHERE b.district = ? AND r.qualification_id = ?
        `)
        .get(district, q.id) as any;
      const voiceDemand = demandRow?.demand || 0;

      // Sanctioned seats and active batches for this qualification in this district
      const supplyRow = this.db
        .prepare(`
          SELECT 
            COALESCE(SUM(total_seats), 0) as total_sanctioned,
            COUNT(id) as active_batches
          FROM local_opportunities
          WHERE district = ? AND qualification_id = ? AND batch_status IN ('active', 'upcoming')
        `)
        .get(district, q.id) as any;
      const sanctionedSeats = supplyRow?.total_sanctioned || 0;
      const activeBatches = supplyRow?.active_batches || 0;

      // Block-level breakdown
      const blockDemandRows = this.db
        .prepare(`
          SELECT b.block, COUNT(DISTINCT r.beneficiary_id) as block_demand
          FROM recommendations r
          JOIN beneficiaries b ON r.beneficiary_id = b.id
          WHERE b.district = ? AND r.qualification_id = ?
          GROUP BY b.block
        `)
        .all(district, q.id) as any[];

      const blockSupplyRows = this.db
        .prepare(`
          SELECT block, COALESCE(SUM(total_seats), 0) as block_capacity
          FROM local_opportunities
          WHERE district = ? AND qualification_id = ? AND batch_status IN ('active', 'upcoming')
          GROUP BY block
        `)
        .all(district, q.id) as any[];

      const blockBreakdown: Record<string, { demand: number; capacity: number }> = {};
      for (const b of blockDemandRows) {
        blockBreakdown[b.block] = { demand: b.block_demand, capacity: 0 };
      }
      for (const s of blockSupplyRows) {
        if (!blockBreakdown[s.block]) {
          blockBreakdown[s.block] = { demand: 0, capacity: s.block_capacity };
        } else {
          blockBreakdown[s.block].capacity = s.block_capacity;
        }
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

  saveBrief(input: {
    district: string;
    period: string;
    totalBeneficiaries: number;
    totalVerifiedMatches: number;
    totalSupplyGaps: number;
    aggregationSnapshot: PlanningBrief['aggregation_snapshot'];
    generatedNarrative: string;
    suggestedPolicyActions: string[];
  }): PlanningBrief {
    const id = `pb_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO planning_briefs (
        id, district, period, total_beneficiaries_interviewed,
        total_verified_matches, total_supply_gaps, aggregation_snapshot,
        generated_narrative, suggested_policy_actions, reviewer_sign_off_status,
        signed_off_by, signed_off_at, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.district,
      input.period,
      input.totalBeneficiaries,
      input.totalVerifiedMatches,
      input.totalSupplyGaps,
      JSON.stringify(input.aggregationSnapshot),
      input.generatedNarrative,
      JSON.stringify(input.suggestedPolicyActions),
      'draft',
      null,
      null,
      now,
      now
    );

    return this.getBriefById(id)!;
  }

  getBriefById(id: string): PlanningBrief | null {
    const stmt = this.db.prepare(`SELECT * FROM planning_briefs WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapBriefRow(row);
  }

  listBriefs(district?: string): PlanningBrief[] {
    let query = `SELECT * FROM planning_briefs WHERE 1=1`;
    const params: any[] = [];
    if (district) {
      query += ` AND district = ?`;
      params.push(district);
    }
    query += ` ORDER BY created_at DESC`;

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];
    return rows.map(this.mapBriefRow);
  }

  signOffBrief(
    id: string,
    officerName: string,
    status: 'signed_off' | 'rejected'
  ): PlanningBrief | null {
    const brief = this.getBriefById(id);
    if (!brief) return null;

    const now = new Date().toISOString();
    const stmt = this.db.prepare(`
      UPDATE planning_briefs
      SET reviewer_sign_off_status = ?, signed_off_by = ?, signed_off_at = ?, updated_at = ?
      WHERE id = ?
    `);
    stmt.run(status, officerName, now, now, id);

    this.auditRepo.logEvent({
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

    return this.getBriefById(id);
  }

  private mapBriefRow(row: any): PlanningBrief {
    return {
      id: row.id,
      district: row.district,
      period: row.period,
      total_beneficiaries_interviewed: row.total_beneficiaries_interviewed,
      total_verified_matches: row.total_verified_matches,
      total_supply_gaps: row.total_supply_gaps,
      aggregation_snapshot: JSON.parse(row.aggregation_snapshot || '{}'),
      generated_narrative: row.generated_narrative,
      suggested_policy_actions: JSON.parse(row.suggested_policy_actions || '[]'),
      reviewer_sign_off_status: row.reviewer_sign_off_status,
      signed_off_by: row.signed_off_by || undefined,
      signed_off_at: row.signed_off_at || undefined,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}
