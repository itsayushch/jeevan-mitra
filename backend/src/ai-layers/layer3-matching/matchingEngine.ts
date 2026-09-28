import {
  Qualification,
  LocalOpportunity,
  ScoreBreakdown,
  Recommendation,
  MatchState,
  LanguageCode,
} from '../../types/index.js';
import { QualificationRepository } from '../../repositories/qualificationRepository.js';
import { OpportunityRepository } from '../../repositories/opportunityRepository.js';
import { ExplanationGenerator } from './explanationGenerator.js';
import { MatchStateMachine } from './stateMachine.js';
import { getBlockCoordinates, calculateDistanceKm } from '../../utils/distance.js';
import { logger } from '../../utils/logger.js';

export interface MatchingCandidateInput {
  beneficiaryId: string;
  sessionId?: string;
  district: string;
  block: string;
  educationLevel: string;
  interests: string[];
  skills: string[];
  mobilityRadiusKm: number;
  accessibilityNeeds: string;
  workPreference: 'wage' | 'self_employment' | 'both';
  preferredLanguage?: LanguageCode;
}

export class MatchingEngine {
  private qualRepo: QualificationRepository;
  private oppRepo: OpportunityRepository;
  private explanationGen: ExplanationGenerator;

  constructor(qualRepo?: QualificationRepository, oppRepo?: OpportunityRepository) {
    this.qualRepo = qualRepo || new QualificationRepository();
    this.oppRepo = oppRepo || new OpportunityRepository();
    this.explanationGen = new ExplanationGenerator();
  }

  /**
   * Run deterministic hard filters + weighted scoring to produce top 3 ranked recommendations
   */
  async match(input: MatchingCandidateInput): Promise<
    Array<Omit<Recommendation, 'id' | 'beneficiary_id' | 'created_at' | 'updated_at'>>
  > {
    logger.debug('MatchingEngine: Running grounded matching against verified NQR catalogue', {
      district: input.district,
      block: input.block,
      education: input.educationLevel,
    });

    const userEduRank = this.educationToRank(input.educationLevel);
    const userCoords = getBlockCoordinates(input.block);

    // 1. Fetch all verified qualifications (Closed Document Set - Guardrail)
    const verifiedQuals = await this.qualRepo.listVerified();

    const scoredList: Array<{
      qualification: Qualification;
      bestOpportunity: (LocalOpportunity & { distance_km: number }) | null;
      score: number;
      scoreBreakdown: ScoreBreakdown;
      matchState: MatchState;
    }> = [];

    for (const qual of verifiedQuals) {
      // Hard Filter 1: Minimum Education Requirement
      if (userEduRank < qual.min_education_rank) {
        continue;
      }

      // Hard Filter 2: Accessibility & Physical Constraint Check
      if (
        input.accessibilityNeeds.toLowerCase().includes('light') &&
        qual.physical_intensity === 'high'
      ) {
        continue;
      }

      // Check available opportunities in this district
      const liveBatches = await this.oppRepo.findLiveBatches(
        qual.id,
        input.district,
        userCoords.lat,
        userCoords.lon,
        input.mobilityRadiusKm
      );

      const bestOpp = liveBatches.length > 0 ? liveBatches[0] : null;

      // Calculate 5-Factor Weighted Score (Max 100)
      const interestScore = this.calculateInterestScore(qual, input.interests);
      const skillScore = this.calculateSkillScore(qual, input.skills);
      const accessScore = this.calculateAccessScore(bestOpp, input.mobilityRadiusKm);
      const demandScore = this.calculateDemandScore(qual.id, input.district, bestOpp);
      const prefScore = this.calculatePreferenceScore(qual.work_type, input.workPreference);

      const totalScore = Math.round(
        interestScore + skillScore + accessScore + demandScore + prefScore
      );

      // Claim 1 State Assignment:
      // Verified Match only if a verified active batch exists with seats
      const matchState: MatchState = MatchStateMachine.determineInitialState(
        bestOpp !== null && bestOpp.batch_status === 'active' && bestOpp.available_seats > 0
      );

      scoredList.push({
        qualification: qual,
        bestOpportunity: bestOpp,
        score: totalScore,
        scoreBreakdown: {
          interest: interestScore,
          prior_skills: skillScore,
          access: accessScore,
          local_demand: demandScore,
          work_preference: prefScore,
        },
        matchState,
      });
    }

    // Sort by score descending
    scoredList.sort((a, b) => b.score - a.score);

    // Take top 3 distinct qualifications
    const top3 = scoredList.slice(0, 3);

    return top3.map((item, index) => {
      const explanations = this.explanationGen.generateExplanation({
        qualification: item.qualification,
        opportunity: item.bestOpportunity,
        matchState: item.matchState,
        scoreBreakdown: item.scoreBreakdown,
        beneficiaryInterest: input.interests,
        beneficiarySkills: input.skills,
        lang: input.preferredLanguage || 'hi',
      });

      return {
        session_id: input.sessionId,
        qualification_id: item.qualification.id,
        local_opportunity_id: item.bestOpportunity ? item.bestOpportunity.id : null,
        rank: index + 1,
        score: item.score,
        score_breakdown: item.scoreBreakdown,
        match_state: item.matchState,
        explanation_text: explanations.explanationText,
        audio_explanation_script: explanations.audioExplanationScript,
        tradeoff_summary: explanations.tradeoffSummary,
        skill_gap_summary: explanations.skillGapSummary,
        data_snapshot: {
          qualification: item.qualification,
          opportunity: item.bestOpportunity,
          timestamp: new Date().toISOString(),
        },
      };
    });
  }

  private educationToRank(edu: string): number {
    const e = (edu || '').toLowerCase();
    if (e.includes('grad') || e.includes('ba') || e.includes('bsc') || e.includes('degree')) return 5;
    if (e.includes('12') || e.includes('inter')) return 4;
    if (e.includes('10') || e.includes('matric') || e.includes('high')) return 3;
    if (e.includes('8') || e.includes('middle')) return 2;
    if (e.includes('5') || e.includes('primary')) return 1;
    return 0; // None / informal literacy
  }

  private calculateInterestScore(qual: Qualification, userInterests: string[]): number {
    if (!userInterests || userInterests.length === 0) return 12;
    const combinedInterests = userInterests.join(' ').toLowerCase();
    const qualText = `${qual.title} ${qual.sector} ${qual.skills_acquired.join(' ')}`.toLowerCase();

    let matches = 0;
    const tokens = combinedInterests.split(/\s+/).filter((t) => t.length > 3);
    for (const t of tokens) {
      if (qualText.includes(t)) matches++;
    }

    if (matches >= 3) return 30;
    if (matches === 2) return 25;
    if (matches === 1) return 18;
    return 10;
  }

  private calculateSkillScore(qual: Qualification, userSkills: string[]): number {
    if (!userSkills || userSkills.length === 0) return 8;
    const combinedSkills = userSkills.join(' ').toLowerCase();
    const qualSkills = qual.skills_acquired.join(' ').toLowerCase();

    let matches = 0;
    const tokens = combinedSkills.split(/\s+/).filter((t) => t.length > 3);
    for (const t of tokens) {
      if (qualSkills.includes(t)) matches++;
    }

    if (matches >= 2) return 20;
    if (matches === 1) return 15;
    return 8;
  }

  private calculateAccessScore(
    opp: (LocalOpportunity & { distance_km: number }) | null,
    mobilityRadius: number
  ): number {
    if (!opp) return 4; // Qualification is valid, but no local batch yet confirmed
    if (opp.distance_km <= 5) return 20;
    if (opp.distance_km <= 15) return 16;
    if (opp.distance_km <= mobilityRadius) return 13;
    if (opp.hostel_available) return 15; // Government hostel covers distance
    return 6;
  }

  private calculateDemandScore(
    qualId: string,
    district: string,
    opp: LocalOpportunity | null
  ): number {
    if (opp && opp.batch_status === 'active' && opp.available_seats > 5) return 20;
    if (opp && opp.batch_status === 'upcoming') return 16;
    if (opp && opp.available_seats > 0) return 12;
    return 4; // Unconfirmed local demand
  }

  private calculatePreferenceScore(qualWorkType: string, userPref: string): number {
    if (userPref === 'both' || qualWorkType === 'both') return 10;
    if (userPref === qualWorkType) return 10;
    return 5;
  }
}
