import { describe, it, expect, beforeEach } from 'vitest';
import { MatchingEngine } from '../src/ai-layers/layer3-matching/matchingEngine.js';
import { Qualification, LocalOpportunity } from '../src/types/index.js';

describe('Layer 3: Grounded Matching & Explanation Engine Tests', () => {
  let quals: Qualification[] = [];
  let opps: LocalOpportunity[] = [];
  let matchingEngine: MatchingEngine;

  beforeEach(() => {
    quals = [
      {
        id: 'q_solar',
        nqr_code: 'SGJ/Q0101',
        title: 'Solar PV Installer',
        sector: 'Green Energy',
        nsqf_level: 4,
        duration_hours: 320,
        min_education: 'Class 10',
        min_education_rank: 3,
        work_type: 'wage',
        physical_intensity: 'high',
        skills_acquired: ['Solar Inverter', 'Mounting', 'Roof Electricals'],
        curriculum_summary: 'Solar installations',
        entry_criteria: '10th pass',
        certification_body: 'SCGJ',
        nqr_link: 'http://test',
        verification_status: 'verified',
        verification_date: '2026-01-01',
      },
      {
        id: 'q_sewing',
        nqr_code: 'AMH/Q0301',
        title: 'Sewing Machine Operator',
        sector: 'Apparel',
        nsqf_level: 2,
        duration_hours: 210,
        min_education: 'Class 5',
        min_education_rank: 1,
        work_type: 'self_employment',
        physical_intensity: 'light',
        skills_acquired: ['Garment Stitching', 'Sewing Machine'],
        curriculum_summary: 'Tailoring basics',
        entry_criteria: '5th pass',
        certification_body: 'AMHSSC',
        nqr_link: 'http://test',
        verification_status: 'verified',
        verification_date: '2026-01-01',
      },
      {
        id: 'q_bike',
        nqr_code: 'ASC/Q1411',
        title: 'Two-Wheeler Service Technician',
        sector: 'Automotive',
        nsqf_level: 4,
        duration_hours: 400,
        min_education: 'Class 8',
        min_education_rank: 2,
        work_type: 'both',
        physical_intensity: 'medium',
        skills_acquired: ['Engine Overhaul', 'Brake Servicing'],
        curriculum_summary: 'Bike repair',
        entry_criteria: '8th pass',
        certification_body: 'ASDC',
        nqr_link: 'http://test',
        verification_status: 'verified',
        verification_date: '2026-01-01',
      },
    ];

    opps = [];

    const mockQualRepo: any = {
      listVerified: async () => quals,
    };
    const mockOppRepo: any = {
      findLiveBatches: async (qualId: string, district: string, lat: number, lon: number, maxDist: number) => {
        return opps
          .filter((o) => o.qualification_id === qualId && o.district === district && o.available_seats > 0)
          .map((o) => ({ ...o, distance_km: 2.5 }));
      },
    };

    matchingEngine = new MatchingEngine(mockQualRepo, mockOppRepo);
  });

  it('filters out qualifications when beneficiary does not meet minimum education rank', async () => {
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
    expect(hasSolar).toBe(false);
  });

  it('assigns Verified Match when active batch with seats exists nearby', async () => {
    opps.push({
      id: 'opp_bike',
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
