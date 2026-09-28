import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import { Recommendation, MatchState, ActorRole } from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class UnauthorizedStateTransitionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnauthorizedStateTransitionError';
  }
}

export class RecommendationRepository {
  private db: Database.Database;
  private auditRepo: AuditRepository;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
    this.auditRepo = new AuditRepository(this.db);
  }

  saveRecommendations(
    beneficiaryId: string,
    sessionId: string | undefined,
    recommendations: Array<Omit<Recommendation, 'id' | 'beneficiary_id' | 'created_at' | 'updated_at'>>
  ): Recommendation[] {
    const now = new Date().toISOString();

    // Remove older recommendations for this session/beneficiary to keep fresh rankings
    const deleteStmt = this.db.prepare(`
      DELETE FROM recommendations WHERE beneficiary_id = ?
    `);
    deleteStmt.run(beneficiaryId);

    const insertStmt = this.db.prepare(`
      INSERT INTO recommendations (
        id, beneficiary_id, session_id, qualification_id, local_opportunity_id,
        rank, score, score_breakdown, match_state, explanation_text,
        audio_explanation_script, tradeoff_summary, skill_gap_summary,
        data_snapshot, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const saved: Recommendation[] = [];

    const transaction = this.db.transaction((recs) => {
      for (const rec of recs) {
        const id = `rec_${uuidv4()}`;
        insertStmt.run(
          id,
          beneficiaryId,
          sessionId || null,
          rec.qualification_id,
          rec.local_opportunity_id || null,
          rec.rank,
          rec.score,
          JSON.stringify(rec.score_breakdown),
          rec.match_state,
          rec.explanation_text,
          rec.audio_explanation_script,
          rec.tradeoff_summary || (rec as any).tradeoffSummary || '',
          rec.skill_gap_summary || (rec as any).skillGapSummary || '',
          JSON.stringify(rec.data_snapshot),
          now,
          now
        );

        saved.push({
          id,
          beneficiary_id: beneficiaryId,
          session_id: sessionId,
          qualification_id: rec.qualification_id,
          local_opportunity_id: rec.local_opportunity_id,
          rank: rec.rank,
          score: rec.score,
          score_breakdown: rec.score_breakdown,
          match_state: rec.match_state,
          explanation_text: rec.explanation_text,
          audio_explanation_script: rec.audio_explanation_script,
          tradeoff_summary: rec.tradeoff_summary || (rec as any).tradeoffSummary || '',
          skill_gap_summary: rec.skill_gap_summary || (rec as any).skillGapSummary || '',
          data_snapshot: rec.data_snapshot,
          created_at: now,
          updated_at: now,
        });

        // Audit initial creation of match state
        this.auditRepo.logEvent({
          actorId: 'system_matching_layer',
          actorName: 'Layer 3 Grounded Matcher',
          actorRole: 'system',
          action: 'RECOMMENDATION_GENERATED',
          entityType: 'recommendation',
          entityId: id,
          oldValues: null,
          newValues: {
            rank: rec.rank,
            score: rec.score,
            match_state: rec.match_state,
            qualification_id: rec.qualification_id,
            local_opportunity_id: rec.local_opportunity_id,
          },
          metadata: { beneficiary_id: beneficiaryId },
        });
      }
    });

    transaction(recommendations);
    return saved;
  }

  findById(id: string): Recommendation | null {
    const stmt = this.db.prepare(`SELECT * FROM recommendations WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapRow(row);
  }

  getByBeneficiaryId(beneficiaryId: string): Recommendation[] {
    const stmt = this.db.prepare(`
      SELECT * FROM recommendations
      WHERE beneficiary_id = ?
      ORDER BY rank ASC
    `);
    const rows = stmt.all(beneficiaryId) as any[];
    return rows.map(this.mapRow);
  }

  /**
   * CLAIM 1 HARD ENFORCEMENT:
   * Upgrading match_state to 'Verified Match' CANNOT be done by 'system' or 'beneficiary'.
   * It requires an authenticated human field worker / district officer action,
   * logged immutably in audit_events.
   */
  transitionMatchState(params: {
    recommendationId: string;
    newMatchState: MatchState;
    actorId: string;
    actorName: string;
    actorRole: ActorRole;
    localOpportunityId?: string;
    reason?: string;
  }): Recommendation {
    const current = this.findById(params.recommendationId);
    if (!current) {
      throw new Error(`Recommendation ${params.recommendationId} not found.`);
    }

    if (params.newMatchState === 'Verified Match') {
      if (params.actorRole !== 'field_worker' && params.actorRole !== 'district_officer') {
        throw new UnauthorizedStateTransitionError(
          `Security Invariant Violation: Generative layer or unauthorized actor '${params.actorRole}' attempted to upgrade recommendation to 'Verified Match'. Only human field workers or district officers can verify local seat availability.`
        );
      }
      if (!params.localOpportunityId && !current.local_opportunity_id) {
        throw new Error(
          `Cannot verify match: A verified local opportunity with confirmed batch availability must be linked.`
        );
      }
    }

    const now = new Date().toISOString();
    const targetOppId = params.localOpportunityId || current.local_opportunity_id;

    const stmt = this.db.prepare(`
      UPDATE recommendations
      SET match_state = ?, local_opportunity_id = ?, updated_at = ?
      WHERE id = ?
    `);
    stmt.run(params.newMatchState, targetOppId || null, now, params.recommendationId);

    // Immutable audit record
    this.auditRepo.logEvent({
      actorId: params.actorId,
      actorName: params.actorName,
      actorRole: params.actorRole,
      action: 'MATCH_STATE_TRANSITION',
      entityType: 'recommendation',
      entityId: params.recommendationId,
      oldValues: {
        match_state: current.match_state,
        local_opportunity_id: current.local_opportunity_id,
      },
      newValues: {
        match_state: params.newMatchState,
        local_opportunity_id: targetOppId,
      },
      metadata: {
        reason: params.reason || 'Human field worker confirmed live batch and seats',
        beneficiary_id: current.beneficiary_id,
      },
    });

    return this.findById(params.recommendationId)!;
  }

  private mapRow(row: any): Recommendation {
    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      session_id: row.session_id || undefined,
      qualification_id: row.qualification_id,
      local_opportunity_id: row.local_opportunity_id || null,
      rank: row.rank,
      score: row.score,
      score_breakdown: JSON.parse(row.score_breakdown || '{}'),
      match_state: row.match_state,
      explanation_text: row.explanation_text,
      audio_explanation_script: row.audio_explanation_script,
      tradeoff_summary: row.tradeoff_summary,
      skill_gap_summary: row.skill_gap_summary,
      data_snapshot: JSON.parse(row.data_snapshot || '{}'),
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}
