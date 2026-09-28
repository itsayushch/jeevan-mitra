import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';
import { runMigrations } from '../src/database/migrations.js';
import { RecommendationRepository, UnauthorizedStateTransitionError } from '../src/repositories/recommendationRepository.js';
import { BeneficiaryRepository } from '../src/repositories/beneficiaryRepository.js';
import { QualificationRepository } from '../src/repositories/qualificationRepository.js';
import { OpportunityRepository } from '../src/repositories/opportunityRepository.js';
import { AuditRepository } from '../src/repositories/auditRepository.js';

describe('Claim 1: The Verified Match Protocol Data-Layer Invariant Tests', () => {
  let db: Database.Database;
  let recRepo: RecommendationRepository;
  let benRepo: BeneficiaryRepository;
  let qualRepo: QualificationRepository;
  let oppRepo: OpportunityRepository;
  let auditRepo: AuditRepository;

  beforeEach(() => {
    db = new Database(':memory:');
    runMigrations(db);

    recRepo = new RecommendationRepository(db);
    benRepo = new BeneficiaryRepository(db);
    qualRepo = new QualificationRepository(db);
    oppRepo = new OpportunityRepository(db);
    auditRepo = new AuditRepository(db);
  });

  it('strictly blocks AI / system actor from upgrading Interest Match to Verified Match', () => {
    // 1. Create beneficiary
    const ben = benRepo.create({
      name: 'Ramesh SC Beneficiary',
      district: 'Moradabad',
      block: 'Chhajlet',
    });

    // 2. Create qualification
    const qual = qualRepo.create({
      id: 'qual_test_01',
      nqr_code: 'TEST/Q001',
      title: 'Solar Technician',
      sector: 'Green Energy',
      nsqf_level: 3,
      duration_hours: 200,
      min_education: 'Class 8',
      min_education_rank: 2,
      work_type: 'wage',
      physical_intensity: 'medium',
      skills_acquired: ['Solar Wiring'],
      curriculum_summary: 'Test summary',
      entry_criteria: '8th pass',
      certification_body: 'SCGJ',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    // 3. Save initial recommendation in Interest Match state
    const saved = recRepo.saveRecommendations(ben.id, undefined, [
      {
        qualification_id: qual.id,
        rank: 1,
        score: 75,
        score_breakdown: { interest: 30, prior_skills: 15, access: 10, local_demand: 10, work_preference: 10 },
        match_state: 'Interest Match',
        explanation_text: 'Test explanation',
        audio_explanation_script: 'Test audio script',
        tradeoff_summary: 'Test tradeoff',
        skill_gap_summary: 'Test skill gap',
        data_snapshot: { qualification: qual, timestamp: new Date().toISOString() },
      },
    ]);

    const recId = saved[0].id;
    expect(saved[0].match_state).toBe('Interest Match');

    // 4. Attempt forbidden upgrade by 'system' / generative model
    expect(() => {
      recRepo.transitionMatchState({
        recommendationId: recId,
        newMatchState: 'Verified Match',
        actorId: 'generative_ai_agent',
        actorName: 'LLM Orchestrator',
        actorRole: 'system', // FORBIDDEN!
        localOpportunityId: 'opp_fake',
      });
    }).toThrow(UnauthorizedStateTransitionError);

    // 5. Attempt forbidden upgrade by 'beneficiary'
    expect(() => {
      recRepo.transitionMatchState({
        recommendationId: recId,
        newMatchState: 'Verified Match',
        actorId: ben.id,
        actorName: ben.name,
        actorRole: 'beneficiary', // FORBIDDEN!
        localOpportunityId: 'opp_fake',
      });
    }).toThrow(UnauthorizedStateTransitionError);

    // Verify database state remains intact and uncorrupted
    const unchanged = recRepo.findById(recId);
    expect(unchanged?.match_state).toBe('Interest Match');
  });

  it('allows authorized human field worker to upgrade match state and records immutable audit log', () => {
    const ben = benRepo.create({
      name: 'Geeta Kumari',
      district: 'Moradabad',
      block: 'Moradabad Rural',
    });

    const qual = qualRepo.create({
      id: 'qual_test_02',
      nqr_code: 'TEST/Q002',
      title: 'Sewing Machine Operator',
      sector: 'Apparel',
      nsqf_level: 2,
      duration_hours: 210,
      min_education: 'Class 5',
      min_education_rank: 1,
      work_type: 'self_employment',
      physical_intensity: 'light',
      skills_acquired: ['Stitching'],
      curriculum_summary: 'Apparel summary',
      entry_criteria: '5th pass',
      certification_body: 'AMHSSC',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    const opp = oppRepo.create({
      qualification_id: qual.id,
      centre_or_employer_name: 'PMKK Moradabad',
      type: 'training_centre',
      district: 'Moradabad',
      block: 'Moradabad Rural',
      address: 'Main Bazar',
      latitude: 28.8,
      longitude: 78.7,
      batch_start_date: '2026-11-01',
      batch_end_date: '2027-01-01',
      total_seats: 30,
      available_seats: 12,
      sc_reserved_seats: 12,
      batch_status: 'active',
      hostel_available: false,
      stipend_amount_inr: 1000,
      free_toolkit_provided: true,
      source: 'test',
      verified_at: '2026-09-01',
    });

    const saved = recRepo.saveRecommendations(ben.id, undefined, [
      {
        qualification_id: qual.id,
        rank: 1,
        score: 85,
        score_breakdown: { interest: 30, prior_skills: 20, access: 15, local_demand: 10, work_preference: 10 },
        match_state: 'Interest Match',
        explanation_text: 'Test',
        audio_explanation_script: 'Test audio',
        tradeoff_summary: 'Test',
        skill_gap_summary: 'Test',
        data_snapshot: { qualification: qual, timestamp: new Date().toISOString() },
      },
    ]);

    const recId = saved[0].id;

    // Authorized human field worker transition
    const upgraded = recRepo.transitionMatchState({
      recommendationId: recId,
      newMatchState: 'Verified Match',
      actorId: 'worker_ramesh_01',
      actorName: 'Ramesh Kumar (VLE)',
      actorRole: 'field_worker',
      localOpportunityId: opp.id,
      reason: 'Physically checked classroom and open seats at PMKK Moradabad',
    });

    expect(upgraded.match_state).toBe('Verified Match');
    expect(upgraded.local_opportunity_id).toBe(opp.id);

    // Verify immutable audit event was logged
    const auditLogs = auditRepo.getEventsByEntity('recommendation', recId);
    expect(auditLogs.length).toBeGreaterThanOrEqual(1);

    const transitionLog = auditLogs.find((l) => l.action === 'MATCH_STATE_TRANSITION');
    expect(transitionLog).toBeDefined();
    expect(transitionLog?.actor_role).toBe('field_worker');
    expect(transitionLog?.old_values).toEqual({ match_state: 'Interest Match', local_opportunity_id: null });
    expect(transitionLog?.new_values).toEqual({ match_state: 'Verified Match', local_opportunity_id: opp.id });
  });
});
