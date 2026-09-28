import { PrismaClient } from '@prisma/client';
import { getDb } from '../../database/connection.js';
import { DriftAdvisory } from '../../types/index.js';

export class DriftDetector {
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  /**
   * Scans recommendation records for gender skew, geographic neglect, or unconfirmed spikes
   */
  async scanForDrift(district: string = 'Moradabad'): Promise<DriftAdvisory[]> {
    const advisories: DriftAdvisory[] = [];

    // 1. Check for Gender Skew in Technical vs Tailoring Trades
    // Using Prisma's raw query since this requires joining across tables
    const genderRows = await this.prisma.$queryRaw<any[]>`
      SELECT 
        b.gender,
        q.sector,
        COUNT(r.id) as count
      FROM "Recommendation" r
      JOIN "Beneficiary" b ON r.beneficiary_id = b.id
      JOIN "Qualification" q ON r.qualification_id = q.id
      WHERE b.district = ${district} AND b.gender IN ('male', 'female')
      GROUP BY b.gender, q.sector
    `;

    let femaleTechCount = 0;
    let femaleApparelCount = 0;
    let maleTechCount = 0;

    for (const r of genderRows) {
      // Prisma raw query numeric results might be BigInt, convert to Number
      const count = Number(r.count);
      if (r.gender === 'female') {
        if (r.sector === 'Apparel' || r.sector === 'Handicrafts') {
          femaleApparelCount += count;
        } else if (r.sector === 'Green Energy' || r.sector === 'Automotive' || r.sector === 'Electronics') {
          femaleTechCount += count;
        }
      } else if (r.gender === 'male') {
        if (r.sector === 'Green Energy' || r.sector === 'Automotive' || r.sector === 'Electronics') {
          maleTechCount += count;
        }
      }
    }

    const totalFemale = femaleApparelCount + femaleTechCount;
    if (totalFemale > 10 && (femaleTechCount / totalFemale) < 0.15) {
      advisories.push({
        id: `drift_gender_${Date.now()}`,
        district,
        flag_type: 'gender_skew',
        severity: 'high',
        headline: `Potential Gender Skew Detected in ${district} Recommendations`,
        evidence: {
          femaleTechCount,
          femaleApparelCount,
          ratioTech: Math.round((femaleTechCount / totalFemale) * 100),
          totalFemaleEvaluated: totalFemale,
        },
        suggested_human_action:
          'Audit intake interview re-prompting: Ensure female beneficiaries expressing mechanical or green energy interests are proactively offered Solar and Electrical pathways without stereotypical filtering.',
        created_at: new Date().toISOString(),
      });
    }

    // 2. Check for Spike in "Interest Match" (Unconfirmed Batches) in Specific Blocks
    const blockRows = await this.prisma.$queryRaw<any[]>`
      SELECT 
        b.block,
        r.match_state,
        COUNT(r.id) as count
      FROM "Recommendation" r
      JOIN "Beneficiary" b ON r.beneficiary_id = b.id
      WHERE b.district = ${district}
      GROUP BY b.block, r.match_state
    `;

    const blockStats: Record<string, { interest: number; verified: number }> = {};
    for (const r of blockRows) {
      const block = String(r.block);
      const count = Number(r.count);
      if (!blockStats[block]) blockStats[block] = { interest: 0, verified: 0 };
      if (r.match_state === 'Interest Match') blockStats[block].interest += count;
      if (r.match_state === 'Verified Match') blockStats[block].verified += count;
    }

    for (const [block, stats] of Object.entries(blockStats)) {
      const total = stats.interest + stats.verified;
      if (total >= 5 && (stats.interest / total) > 0.70) {
        advisories.push({
          id: `drift_unconfirmed_${block}_${Date.now()}`,
          district,
          flag_type: 'unconfirmed_spike',
          severity: 'medium',
          headline: `Spike in Unconfirmed Batches in Block ${block} (${Math.round((stats.interest / total) * 100)}% unverified)`,
          evidence: {
            block,
            totalRecommendations: total,
            unconfirmedMatches: stats.interest,
            verifiedMatches: stats.verified,
          },
          suggested_human_action: `Dispatch field workers to verify training centre capacity or sanction additional GIA batches in ${block}.`,
          created_at: new Date().toISOString(),
        });
      }
    }

    return advisories;
  }
}
