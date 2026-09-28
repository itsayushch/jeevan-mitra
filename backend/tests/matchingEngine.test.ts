import { describe, it, expect, beforeEach } from 'vitest';
import Database from 'better-sqlite3';
import { runMigrations } from '../src/database/migrations.js';
import { MatchingEngine } from '../src/ai-layers/layer3-matching/matchingEngine.js';
import { QualificationRepository } from '../src/repositories/qualificationRepository.js';
import { OpportunityRepository } from '../src/repositories/opportunityRepository.js';

describe('Layer 3: Grounded Matching & Explanation Engine Tests', () => {
  let db: Database.Database;
  let qualRepo: QualificationRepository;
  let oppRepo: OpportunityRepository;
  let matchingEngine: MatchingEngine;

  beforeEach(() => {
    db = new Database(':memory:');
    runMigrations(db);

    qualRepo = new QualificationRepository(db);
    oppRepo = new OpportunityRepository(db);
    matchingEngine = new MatchingEngine(qualRepo, oppRepo);

    // Seed test qualifications
    qualRepo.create({
      id: 'q_solar',
      nqr_code: 'SGJ/Q0101',
      title: 'Solar PV Installer',
      sector: 'Green Energy',
      nsqf_level: 4,
      duration_hours: 320,
      min_education: 'Class 10',
      min_education_rank: 3, // Requires 10th pass
      work_type: 'wage',
      physical_intensity: 'high',
      skills_acquired: ['Solar Inverter', 'Mounting', 'Roof Electricals'],
      curriculum_summary: 'Solar installations',
      entry_criteria: '10th pass',
      certification_body: 'SCGJ',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    qualRepo.create({
      id: 'q_sewing',
      nqr_code: 'AMH/Q0301',
      title: 'Sewing Machine Operator',
      sector: 'Apparel',
      nsqf_level: 2,
      duration_hours: 210,
      min_education: 'Class 5',
      min_education_rank: 1, // Requires 5th pass
      work_type: 'self_employment',
      physical_intensity: 'light',
      skills_acquired: ['Garment Stitching', 'Sewing Machine'],
      curriculum_summary: 'Tailoring basics',
      entry_criteria: '5th pass',
      certification_body: 'AMHSSC',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });

    qualRepo.create({
      id: 'q_bike',
      nqr_code: 'ASC/Q1411',
      title: 'Two-Wheeler Service Technician',
      sector: 'Automotive',
      nsqf_level: 4,
      duration_hours: 400,
      min_education: 'Class 8',
      min_education_rank: 2, // Requires 8th pass
      work_type: 'both',
      physical_intensity: 'medium',
      skills_acquired: ['Engine Overhaul', 'Brake Servicing'],
      curriculum_summary: 'Bike repair',
      entry_criteria: '8th pass',
      certification_body: 'ASDC',
      nqr_link: 'http://test',
      verification_status: 'verified',
      verification_date: '2026-01-01',
    });
  });

  it('filters out qualifications when beneficiary does not meet minimum education rank', async () => {
    // 5th pass candidate should NOT qualify for Class 10 (Solar) or Class 8 (Bike)
    const recs = await matchingEngine.match({
      beneficiaryId: 'ben_test_low_edu',
      district: 'Moradabad',
      block: 'Moradabad Rural',
      educationLevel: 'Class 5',
      interests: ['Solar Energy', 'Machines'],
      skills: ['Manual Work'],
      mobilityRadiusKm: 15,
      accessibilityNeeds: 'None',
      workPreference: 'both',
    });

    expect(recs.length).toBe(1);
    expect(recs[0].qualification_id).toBe('q_sewing');
  });

  it('filters out high physical intensity qualifications when beneficiary requires light work', async () => {
    // 10th pass candidate with light physical restriction
    const recs = await matchingEngine.match({
      beneficiaryId: 'ben_test_light',
      district: 'Moradabad',
      block: 'Moradabad Rural',
      educationLevel: 'Class 10',
      interests: ['Solar Energy', 'Garments'],
      skills: ['Tools'],
      mobilityRadiusKm: 15,
      accessibilityNeeds: 'Light Physical Work (No heavy lifting)',
      workPreference: 'both',
    });

    const hasSolar = recs.some((r) => r.qualification_id === 'q_solar');
    expect(hasSolar).toBe(false); // High intensity trade filtered out
  });

  it('assigns Verified Match when active batch with seats exists nearby', async () => {
    // Add verified local batch for Two-Wheeler in Chhajlet
    oppRepo.create({
      qualification_id: 'q_bike',
      centre_or_employer_name: 'Govt ITI Chhajlet',
      type: 'training_centre',
      district: 'Moradabad',
      block: 'Chhajlet',
      address: 'Main Road',
      latitude: 28.985,
      longitude: 78.681,
      batch_start_date: '2026-11-20',
      batch_end_date: '2027-03-31',
      total_seats: 25,
      available_seats: 10,
      sc_reserved_seats: 10,
      batch_status: 'active',
      hostel_available: false,
      stipend_amount_inr: 1200,
      free_toolkit_provided: true,
      source: 'test',
      verified_at: '2026-09-01',
    });

    const recs = await matchingEngine.match({
      beneficiaryId: 'ben_bike_interest',
      district: 'Moradabad',
      block: 'Chhajlet',
      educationLevel: 'Class 8',
      interests: ['Automotive Repair', 'Bike'],
      skills: ['Engine Overhaul'],
      mobilityRadiusKm: 10,
      accessibilityNeeds: 'None',
      workPreference: 'both',
    });

    const topRec = recs.find((r) => r.qualification_id === 'q_bike');
    expect(topRec).toBeDefined();
    expect(topRec?.match_state).toBe('Verified Match');
    expect(topRec?.score).toBeGreaterThan(80);
  });

  it('assigns Interest Match when no verified batch exists in the area', async () => {
    // Candidate in remote block Bahjoi where no batch exists
    const recs = await matchingEngine.match({
      beneficiaryId: 'ben_remote',
      district: 'Moradabad',
      block: 'Bahjoi',
      educationLevel: 'Class 8',
      interests: ['Tailoring', 'Stitching'],
      skills: ['Sewing'],
      mobilityRadiusKm: 5,
      accessibilityNeeds: 'None',
      workPreference: 'self_employment',
    });

    const sewingRec = recs.find((r) => r.qualification_id === 'q_sewing');
    expect(sewingRec).toBeDefined();
    expect(sewingRec?.match_state).toBe('Interest Match');
  });
});
