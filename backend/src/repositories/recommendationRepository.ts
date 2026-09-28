import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { Recommendation, MatchState, ActorRole } from '../types/index.js';
import { AuditRepository } from './auditRepository.js';

export class UnauthorizedStateTransitionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnauthorizedStateTransitionError';
  }
}

export class RecommendationRepository {
  private prisma: PrismaClient;
  private auditRepo: AuditRepository;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
    this.auditRepo = new AuditRepository(this.prisma);
  }

  async saveRecommendations(
    beneficiaryId: string,
    sessionId: string | undefined,
    recommendations: Array<Omit<Recommendation, 'id' | 'beneficiary_id' | 'created_at' | 'updated_at'>>
  ): Promise<Recommendation[]> {
    const saved: Recommendation[] = [];

    await this.prisma.$transaction(async (tx) => {
      // Remove older recommendations for this session/beneficiary to keep fresh rankings
      await tx.recommendation.deleteMany({
        where: { beneficiary_id: beneficiaryId },
      });

      for (const rec of recommendations) {
        const id = `rec_${uuidv4()}`;
        const createdRow = await tx.recommendation.create({
          data: {
            id,
            beneficiary_id: beneficiaryId,
            session_id: sessionId || null,
            qualification_id: rec.qualification_id,
            local_opportunity_id: rec.local_opportunity_id || null,
            rank: rec.rank,
            score: rec.score,
            score_breakdown: JSON.stringify(rec.score_breakdown),
            match_state: rec.match_state,
            explanation_text: rec.explanation_text,
            audio_explanation_script: rec.audio_explanation_script,
            tradeoff_summary: rec.tradeoff_summary || (rec as any).tradeoffSummary || '',
            skill_gap_summary: rec.skill_gap_summary || (rec as any).skillGapSummary || '',
            data_snapshot: JSON.stringify(rec.data_snapshot),
          },
        });

        saved.push(this.mapRow(createdRow));

        // Audit initial creation of match state
        // We can create audit events in transaction or normally, but we use the shared instance which might not be inside tx.
        // Prisma transaction can't be easily passed to auditRepo if it doesn't take tx, so we will use the tx directly.
        await tx.auditEvent.create({
          data: {
            id: `audit_${uuidv4()}`,
            actor_id: 'system_matching_layer',
            actor_name: 'Layer 3 Grounded Matcher',
            actor_role: 'system',
            action: 'RECOMMENDATION_GENERATED',
            entity_type: 'recommendation',
            entity_id: id,
            old_values: null,
            new_values: JSON.stringify({
              rank: rec.rank,
              score: rec.score,
              match_state: rec.match_state,
              qualification_id: rec.qualification_id,
              local_opportunity_id: rec.local_opportunity_id,
            }),
            metadata: JSON.stringify({ beneficiary_id: beneficiaryId }),
          },
        });
      }
    });

    return saved;
  }

  async findById(id: string): Promise<Recommendation | null> {
    const row = await this.prisma.recommendation.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapRow(row);
  }

  async getByBeneficiaryId(beneficiaryId: string): Promise<Recommendation[]> {
    const rows = await this.prisma.recommendation.findMany({
      where: { beneficiary_id: beneficiaryId },
      orderBy: { rank: 'asc' },
    });
    return rows.map(this.mapRow);
  }

  /**
   * CLAIM 1 HARD ENforcement:
   * Upgrading match_state to 'Verified Match' CANNOT be done by 'system' or 'beneficiary'.
   * It requires an authenticated human field worker / district officer action,
   * logged immutably in audit_events.
   */
  async transitionMatchState(params: {
    recommendationId: string;
    newMatchState: MatchState;
    actorId: string;
    actorName: string;
    actorRole: ActorRole;
    localOpportunityId?: string;
    reason?: string;
  }): Promise<Recommendation> {
    const current = await this.findById(params.recommendationId);
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

    const targetOppId = params.localOpportunityId || current.local_opportunity_id;

    const updatedRow = await this.prisma.recommendation.update({
      where: { id: params.recommendationId },
      data: {
        match_state: params.newMatchState,
        local_opportunity_id: targetOppId || null,
      },
    });

    // Immutable audit record
    await this.auditRepo.logEvent({
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

    return this.mapRow(updatedRow);
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
      score_breakdown: typeof row.score_breakdown === 'string' ? JSON.parse(row.score_breakdown || '{}') : row.score_breakdown,
      match_state: row.match_state as MatchState,
      explanation_text: row.explanation_text,
      audio_explanation_script: row.audio_explanation_script,
      tradeoff_summary: row.tradeoff_summary,
      skill_gap_summary: row.skill_gap_summary,
      data_snapshot: typeof row.data_snapshot === 'string' ? JSON.parse(row.data_snapshot || '{}') : row.data_snapshot,
      created_at: typeof row.created_at === 'string' ? row.created_at : row.created_at.toISOString(),
      updated_at: typeof row.updated_at === 'string' ? row.updated_at : row.updated_at.toISOString(),
    };
  }
}
