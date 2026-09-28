import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';
import { runMigrations } from '../src/database/migrations.js';
import { PlanningRepository } from '../src/repositories/planningRepository.js';
import { PlanningAggregationService } from '../src/ai-layers/layer5-planning/aggregationService.js';
import { PlanningNarrativeEngine } from '../src/ai-layers/layer5-planning/narrativeEngine.js';
import { QualificationRepository } from '../src/repositories/qualificationRepository.js';
import { OpportunityRepository } from '../src/repositories/opportunityRepository.js';
import { BeneficiaryRepository } from '../src/repositories/beneficiaryRepository.js';
import { RecommendationRepository } from '../src/repositories/recommendationRepository.js';

describe('Claim 2 & Layer 5: Planning Loop & Strictly Grounded Narrative Tests', () => {
  let db: Database.Database;
  let planningRepo: PlanningRepository;
  let aggregationService: PlanningAggregationService;
  let narrativeEngine: PlanningNarrativeEngine;
  let qualRepo: QualificationRepository;
  let oppRepo: OpportunityRepository;
  let benRepo: BeneficiaryRepository;
  let recRepo: RecommendationRepository;

  beforeEach(() => {
    db = new Database(':memory:');
    runMigrations(db);

    planningRepo = new PlanningRepository(db);
    aggregationService = new PlanningAggregationService(planningRepo);
    narrativeEngine = new PlanningNarrativeEngine();
    qualRepo = new QualificationRepository(db);
    oppRepo = new OpportunityRepository(db);
    benRepo = new BeneficiaryRepository(db);
    recRepo = new RecommendationRepository(db);

    // Setup Qualification: Micro-Irrigation Technician
    const irrig = qualRepo.create({
      id: 'q_irrig_plan',
      nqr_code: 'AGR/Q1003',
      title: 'Micro-Irrigation Technician',
      sector: 'Agriculture',
      nsqf_level: 3,
      duration_hours: 200,
      min_education: 'Class 8',
      min_education_rank: 2,
      work_type: 'wage',
      physical_intensity: 'medium',
      skills_acquired: ['Piping'],
      curriculum_summary: 'Irrigation',
      entry_criteria: '8th pass',
      certification_body: 'ASCI',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    // Create 15 beneficiaries in Bahjoi requesting Micro-Irrigation (Voice Demand = 15)
    for (let i = 1; i <= 15; i++) {
      const b = benRepo.create({
        name: `Beneficiary ${i}`,
        district: 'Moradabad',
        block: 'Bahjoi',
      });
      recRepo.saveRecommendations(b.id, undefined, [
        {
          qualification_id: irrig.id,
          rank: 1,
          score: 80,
          score_breakdown: { interest: 30, prior_skills: 20, access: 10, local_demand: 10, work_preference: 10 },
          match_state: 'Interest Match', // No centre in Bahjoi
          explanation_text: 'Test',
          audio_explanation_script: 'Test',
          tradeoff_summary: 'Test',
          skill_gap_summary: 'Test',
          data_snapshot: { qualification: irrig, timestamp: new Date().toISOString() },
        },
      ]);
    }
  });

  it('accurately calculates voice demand versus sanctioned capacity without errors', () => {
    const summary = aggregationService.aggregateDemandVsCapacity('Moradabad');

    expect(summary.totalBeneficiaries).toBe(15);
    expect(summary.totalVerifiedMatches).toBe(0);
    expect(summary.totalSupplyGaps).toBe(15);

    const irrigGap = summary.gaps.find((g) => g.nqr_code === 'AGR/Q1003');
    expect(irrigGap).toBeDefined();
    expect(irrigGap?.voice_demand).toBe(15);
    expect(irrigGap?.sanctioned_seats).toBe(0);
    expect(irrigGap?.gap_status).toBe('No Centre');
    expect(irrigGap?.supply_gap).toBe(15);
  });

  it('guarantees Layer 5 strictly grounds all numbers from database query results in narrative text', () => {
    const summary = aggregationService.aggregateDemandVsCapacity('Moradabad');
    const brief = narrativeEngine.generateBrief(summary, 'FY 2026-27 Q2');

    // Strict numerical assertions: narrative MUST contain the exact database numbers
    expect(brief.narrativeText).toContain('15 SC youth');
    expect(brief.narrativeText).toContain('0 candidates were successfully matched');
    expect(brief.narrativeText).toContain('unmet demand gap of 15 candidate allocations');
    expect(brief.narrativeText).toContain('Micro-Irrigation Technician');
    expect(brief.narrativeText).toContain('recorded 15 voice requests against 0 sanctioned seats');

    // Check cluster alert
    expect(brief.narrativeText).toContain('Block Bahjoi');
    expect(brief.narrativeText).toContain('nearest sanctioned centre is approximately 45 km away');

    // Traceability metadata check
    expect(brief.sourceDataTrace.totalInterviewed).toBe(15);
    expect(brief.sourceDataTrace.unmetDemand).toBe(15);
  });
});
