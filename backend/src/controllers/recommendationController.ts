import { Request, Response } from 'express';
import { z } from 'zod';
import { MatchingEngine } from '../ai-layers/layer3-matching/matchingEngine.js';
import { RecommendationRepository } from '../repositories/recommendationRepository.js';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';
import { SessionRepository } from '../repositories/sessionRepository.js';
import { OpportunityRepository } from '../repositories/opportunityRepository.js';
import { QualificationRepository } from '../repositories/qualificationRepository.js';

export const runMatchSchema = z.object({
  beneficiaryId: z.string(),
  sessionId: z.string().optional(),
});

export class RecommendationController {
  private matchingEngine: MatchingEngine;
  private recRepo: RecommendationRepository;
  private beneficiaryRepo: BeneficiaryRepository;
  private sessionRepo: SessionRepository;
  private oppRepo: OpportunityRepository;
  private qualRepo: QualificationRepository;

  constructor() {
    this.oppRepo = new OpportunityRepository();
    this.qualRepo = new QualificationRepository();
    this.matchingEngine = new MatchingEngine(this.qualRepo, this.oppRepo);
    this.recRepo = new RecommendationRepository();
    this.beneficiaryRepo = new BeneficiaryRepository();
    this.sessionRepo = new SessionRepository();
  }

  match = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const data = runMatchSchema.parse(req.body);
      const beneficiary = await this.beneficiaryRepo.findById(data.beneficiaryId);
      if (!beneficiary) {
        res.status(404).json({ error: 'Beneficiary not found' });
        return;
      }

      // Load profile answers
      const answers = await this.sessionRepo.getProfileAnswers(data.beneficiaryId);
      const ansMap: Record<string, string> = {};
      for (const a of answers) {
        ansMap[a.field_name] = a.field_value;
      }

      const educationLevel = ansMap['education_level'] || 'Class 8';
      let interests: string[] = ['Vocational', 'Machinery'];
      try {
        if (ansMap['interests']) {
          interests = ansMap['interests'].startsWith('[')
            ? JSON.parse(ansMap['interests'])
            : ansMap['interests'].split(',').map((s) => s.trim());
        }
      } catch {
        interests = ['Vocational'];
      }

      let skills: string[] = [];
      try {
        if (ansMap['skills']) {
          skills = ansMap['skills'].startsWith('[')
            ? JSON.parse(ansMap['skills'])
            : ansMap['skills'].split(',').map((s) => s.trim());
        }
      } catch {
        skills = [];
      }

      const mobilityRadiusKm = Number(ansMap['mobility_radius_km']) || 10;
      const accessibilityNeeds = ansMap['accessibility_needs'] || 'None';
      const workPreference = (ansMap['work_preference'] as any) || 'both';

      // Execute Layer 3 Grounded Matching
      const recommendations = await this.matchingEngine.match({
        beneficiaryId: beneficiary.id,
        sessionId: data.sessionId,
        district: beneficiary.district,
        block: beneficiary.block,
        educationLevel,
        interests,
        skills,
        mobilityRadiusKm,
        accessibilityNeeds,
        workPreference,
        preferredLanguage: beneficiary.preferred_language,
      });

      const saved = await this.recRepo.saveRecommendations(
        beneficiary.id,
        data.sessionId,
        recommendations
      );

      res.json({
        beneficiaryId: beneficiary.id,
        count: saved.length,
        recommendations: saved,
      });
    } catch (err) {
      next(err);
    }
  };

  getByBeneficiary = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const beneficiaryId = String(req.params.beneficiaryId);
      const recs = await this.recRepo.getByBeneficiaryId(beneficiaryId);
      res.json({
        beneficiaryId,
        recommendations: recs,
      });
    } catch (err) {
      next(err);
    }
  };

  getDetails = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const id = String(req.params.id);
      const rec = await this.recRepo.findById(id);
      if (!rec) {
        res.status(404).json({ error: 'Recommendation not found' });
        return;
      }
      res.json(rec);
    } catch (err) {
      next(err);
    }
  };

  /**
   * Screen 7: Pathway comparison matrix
   */
  compare = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const id1 = String(req.params.id1);
      const id2 = String(req.params.id2);
      const rec1 = await this.recRepo.findById(id1);
      const rec2 = await this.recRepo.findById(id2);

      if (!rec1 || !rec2) {
        res.status(404).json({ error: 'One or both recommendations not found for comparison' });
        return;
      }

      const q1 = rec1.data_snapshot.qualification;
      const q2 = rec2.data_snapshot.qualification;
      const opp1 = rec1.data_snapshot.opportunity;
      const opp2 = rec2.data_snapshot.opportunity;

      const matrix = {
        optionA: {
          id: rec1.id,
          tradeName: q1.title,
          nsqfLevel: `Level ${q1.nsqf_level}`,
          duration: `${q1.duration_hours} Hours`,
          workPattern: q1.work_type === 'wage' ? 'Wage / Company' : q1.work_type === 'self_employment' ? 'Self-emp.' : 'Flexible',
          travelNeed: opp1 ? `${opp1.block} (~12 km)` : 'Not confirmed',
          physicalNeed: q1.physical_intensity,
          batchStatus: opp1 ? opp1.batch_status : 'Pending verification',
          matchState: rec1.match_state,
          canApply: rec1.match_state === 'Verified Match',
        },
        optionB: {
          id: rec2.id,
          tradeName: q2.title,
          nsqfLevel: `Level ${q2.nsqf_level}`,
          duration: `${q2.duration_hours} Hours`,
          workPattern: q2.work_type === 'wage' ? 'Wage / Company' : q2.work_type === 'self_employment' ? 'Self-emp.' : 'Flexible',
          travelNeed: opp2 ? `${opp2.block} (~5 km)` : 'Not confirmed',
          physicalNeed: q2.physical_intensity,
          batchStatus: opp2 ? opp2.batch_status : 'Pending verification',
          matchState: rec2.match_state,
          canApply: rec2.match_state === 'Verified Match',
        },
        conversationalTradeoffAudioScript: `Comparing ${q1.title} and ${q2.title}: ${rec1.tradeoff_summary} Meanwhile, ${rec2.tradeoff_summary}`,
      };

      res.json(matrix);
    } catch (err) {
      next(err);
    }
  };

  /**
   * Screen 8: Training centre and batch details
   */
  getCentreDetails = async (req: Request, res: Response, next: any): Promise<void> => {
    try {
      const id = String(req.params.id);
      const rec = await this.recRepo.findById(id);
      if (!rec) {
        res.status(404).json({ error: 'Recommendation not found' });
        return;
      }

      const opp = rec.data_snapshot.opportunity;
      const qual = rec.data_snapshot.qualification;

      if (!opp) {
        res.json({
          hasConfirmedBatch: false,
          message: 'No live local batch is currently verified for this qualification.',
          qualification: qual,
          matchState: rec.match_state,
        });
        return;
      }

      res.json({
        hasConfirmedBatch: true,
        matchState: rec.match_state,
        centreName: opp.centre_or_employer_name,
        address: opp.address,
        district: opp.district,
        block: opp.block,
        courseTitle: `${qual.title} (NSQF L${qual.nsqf_level})`,
        batchStartDate: opp.batch_start_date,
        batchEndDate: opp.batch_end_date,
        totalSeats: opp.total_seats,
        availableSeats: opp.available_seats,
        scReservedSeats: opp.sc_reserved_seats,
        amenities: {
          freeToolkit: opp.free_toolkit_provided,
          stipend: opp.stipend_amount_inr > 0 ? `₹${opp.stipend_amount_inr}/month` : 'Applicable PM-AJAY stipend',
          hostel: opp.hostel_available ? 'Free Boarding & Lodging' : 'Day Scholar only',
        },
        verificationBadge: {
          status: 'Verified by District Team',
          verifiedAt: opp.verified_at,
        },
        transportInfo: 'Direct bus connectivity from block centre (approx. 35-45 mins commute)',
      });
    } catch (err) {
      next(err);
    }
  };
}
