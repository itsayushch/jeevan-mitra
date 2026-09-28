import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';
import { runMigrations } from '../src/database/migrations.js';
import { DriftDetector } from '../src/ai-layers/layer6-monitoring/driftDetector.js';
import { QualificationRepository } from '../src/repositories/qualificationRepository.js';
import { BeneficiaryRepository } from '../src/repositories/beneficiaryRepository.js';
import { RecommendationRepository } from '../src/repositories/recommendationRepository.js';

describe('Layer 6: Drift & Bias Detector Tests', () => {
  let db: Database.Database;
  let detector: DriftDetector;
  let qualRepo: QualificationRepository;
  let benRepo: BeneficiaryRepository;
  let recRepo: RecommendationRepository;

  beforeEach(() => {
    db = new Database(':memory:');
    runMigrations(db);

    detector = new DriftDetector(db);
    qualRepo = new QualificationRepository(db);
    benRepo = new BeneficiaryRepository(db);
    recRepo = new RecommendationRepository(db);

    const apparel = qualRepo.create({
      id: 'q_apparel',
      nqr_code: 'APP/01',
      title: 'Tailoring',
      sector: 'Apparel',
      nsqf_level: 2,
      duration_hours: 200,
      min_education: 'Class 5',
      min_education_rank: 1,
      work_type: 'self_employment',
      physical_intensity: 'light',
      skills_acquired: ['Stitching'],
      curriculum_summary: 'Sewing',
      entry_criteria: '5th pass',
      certification_body: 'AMH',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    const solar = qualRepo.create({
      id: 'q_solar_tech',
      nqr_code: 'SOL/01',
      title: 'Solar Installer',
      sector: 'Green Energy',
      nsqf_level: 4,
      duration_hours: 300,
      min_education: 'Class 10',
      min_education_rank: 3,
      work_type: 'wage',
      physical_intensity: 'medium',
      skills_acquired: ['Solar'],
      curriculum_summary: 'Solar installation',
      entry_criteria: '10th pass',
      certification_body: 'SCGJ',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    // Simulate extreme gender bias: 15 female candidates all recommended ONLY Apparel (0 in Tech)
    for (let i = 1; i <= 15; i++) {
      const b = benRepo.create({
        name: `Female Candidate ${i}`,
        gender: 'female',
        district: 'Moradabad',
        block: 'Moradabad Rural',
      });
      recRepo.saveRecommendations(b.id, undefined, [
        {
          qualification_id: apparel.id,
          rank: 1,
          score: 85,
          score_breakdown: { interest: 30, prior_skills: 20, access: 15, local_demand: 10, work_preference: 10 },
          match_state: 'Verified Match',
          explanation_text: 'Test',
          audio_explanation_script: 'Test',
          tradeoff_summary: 'Test',
          skill_gap_summary: 'Test',
          data_snapshot: { qualification: apparel, timestamp: new Date().toISOString() },
        },
      ]);
    }
  });

  it('detects gender skew and generates an advisory note for human review', () => {
    const advisories = detector.scanForDrift('Moradabad');
    const genderAdvisory = advisories.find((a) => a.flag_type === 'gender_skew');

    expect(genderAdvisory).toBeDefined();
    expect(genderAdvisory?.severity).toBe('high');
    expect(genderAdvisory?.headline).toContain('Potential Gender Skew Detected');
    expect(genderAdvisory?.suggested_human_action).toContain('Audit intake interview re-prompting');
  });
});
