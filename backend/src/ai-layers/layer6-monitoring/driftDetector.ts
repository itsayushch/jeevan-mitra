import Database from 'better-sqlite3';
import { getDatabase } from '../../database/connection.js';
import { DriftAdvisory } from '../../types/index.js';

export class DriftDetector {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  /**
   * Scans recommendation records for gender skew, geographic neglect, or unconfirmed spikes
   */
  scanForDrift(district: string = 'Moradabad'): DriftAdvisory[] {
    const advisories: DriftAdvisory[] = [];

    // 1. Check for Gender Skew in Technical vs Tailoring Trades
    const genderTradeStmt = this.db.prepare(`
      SELECT 
        b.gender,
        q.sector,
        COUNT(r.id) as count
      FROM recommendations r
      JOIN beneficiaries b ON r.beneficiary_id = b.id
      JOIN qualifications q ON r.qualification_id = q.id
      WHERE b.district = ? AND b.gender IN ('male', 'female')
      GROUP BY b.gender, q.sector
    `);
    const genderRows = genderTradeStmt.all(district) as any[];

    let femaleTechCount = 0;
    let femaleApparelCount = 0;
    let maleTechCount = 0;

    for (const r of genderRows) {
      if (r.gender === 'female') {
        if (r.sector === 'Apparel' || r.sector === 'Handicrafts') {
          femaleApparelCount += r.count;
        } else if (r.sector === 'Green Energy' || r.sector === 'Automotive' || r.sector === 'Electronics') {
          femaleTechCount += r.count;
        }
      } else if (r.gender === 'male') {
        if (r.sector === 'Green Energy' || r.sector === 'Automotive' || r.sector === 'Electronics') {
          maleTechCount += r.count;
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
    const blockMatchStmt = this.db.prepare(`
      SELECT 
        b.block,
        r.match_state,
        COUNT(r.id) as count
      FROM recommendations r
      JOIN beneficiaries b ON r.beneficiary_id = b.id
      WHERE b.district = ?
      GROUP BY b.block, r.match_state
    `);
    const blockRows = blockMatchStmt.all(district) as any[];

    const blockStats: Record<string, { interest: number; verified: number }> = {};
    for (const r of blockRows) {
      if (!blockStats[r.block]) blockStats[r.block] = { interest: 0, verified: 0 };
      if (r.match_state === 'Interest Match') blockStats[r.block].interest += r.count;
      if (r.match_state === 'Verified Match') blockStats[r.block].verified += r.count;
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
