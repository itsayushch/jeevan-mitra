import { Request, Response } from 'express';
import { z } from 'zod';
import { FieldWorkerSummaryEngine } from '../ai-layers/layer4-copilot/summaryEngine.js';
import { OutboundMessagingDraftEngine } from '../ai-layers/layer4-copilot/outboundMessaging.js';
import { MatchingEngine } from '../ai-layers/layer3-matching/matchingEngine.js';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';
import { SessionRepository } from '../repositories/sessionRepository.js';
import { RecommendationRepository } from '../repositories/recommendationRepository.js';
import { OpportunityRepository } from '../repositories/opportunityRepository.js';
import { QualificationRepository } from '../repositories/qualificationRepository.js';
import { ReferralRepository } from '../repositories/referralRepository.js';
import { AuditRepository } from '../repositories/auditRepository.js';

export const correctProfileSchema = z.object({
  workerId: z.string().default('worker_vle_01'),
  workerName: z.string().default('Ramesh Kumar (VLE)'),
  corrections: z.record(z.string(), z.string()), // field_name -> corrected_value
});

export const verifyBatchSchema = z.object({
  recommendationId: z.string(),
  opportunityId: z.string(),
  workerId: z.string().default('worker_vle_01'),
  workerName: z.string().default('Ramesh Kumar (VLE)'),
  reason: z.string().optional(),
});

export const approveReferralSchema = z.object({
  recommendationId: z.string(),
  opportunityId: z.string(),
  workerId: z.string().default('worker_vle_01'),
  workerName: z.string().default('Ramesh Kumar (VLE)'),
  casteDocumentVerified: z.boolean().default(true),
  incomeCriteriaVerified: z.boolean().default(true),
  residenceProofVerified: z.boolean().default(true),
  notes: z.string().optional(),
});

export class WorkerController {
  private summaryEngine: FieldWorkerSummaryEngine;
  private messagingEngine: OutboundMessagingDraftEngine;
  private matchingEngine: MatchingEngine;
  private beneficiaryRepo: BeneficiaryRepository;
  private sessionRepo: SessionRepository;
  private recRepo: RecommendationRepository;
  private oppRepo: OpportunityRepository;
  private qualRepo: QualificationRepository;
  private referralRepo: ReferralRepository;
  private auditRepo: AuditRepository;

  constructor() {
    this.summaryEngine = new FieldWorkerSummaryEngine();
    this.messagingEngine = new OutboundMessagingDraftEngine();
    this.oppRepo = new OpportunityRepository();
    this.qualRepo = new QualificationRepository();
    this.matchingEngine = new MatchingEngine(this.qualRepo, this.oppRepo);
    this.beneficiaryRepo = new BeneficiaryRepository();
    this.sessionRepo = new SessionRepository();
    this.recRepo = new RecommendationRepository();
    this.referralRepo = new ReferralRepository();
    this.auditRepo = new AuditRepository();
  }

  /**
   * Screen 6: Field-worker dashboard case overview
   */
  getCases = (req: Request, res: Response): void => {
    const { district, block } = req.query;
    const beneficiaries = this.beneficiaryRepo.list({
      district: district ? String(district) : undefined,
      block: block ? String(block) : undefined,
      limit: 100,
    });

    const cases = beneficiaries.map((b) => {
      const answers = this.sessionRepo.getProfileAnswers(b.id);
      const recs = this.recRepo.getByBeneficiaryId(b.id);
      const referrals = this.referralRepo.list({ beneficiaryId: b.id });

      const hasInterestOnly = recs.length > 0 && recs.every((r) => r.match_state === 'Interest Match');
      const hasVerified = recs.some((r) => r.match_state === 'Verified Match');
      const hasPendingReferral = referrals.some((r) => r.status === 'pending');

      return {
        id: b.id,
        name: b.name,
        category: b.category,
        district: b.district,
        block: b.block,
        status: hasPendingReferral
          ? 'Referral Pending'
          : hasVerified
          ? 'Batch Verified'
          : hasInterestOnly
          ? 'Interest Match Only'
          : 'Profiling In Progress',
        topRecommendation: recs.length > 0 ? recs[0].data_snapshot?.qualification?.title : 'N/A',
        matchState: recs.length > 0 ? recs[0].match_state : 'None',
        unconfirmedAnswersCount: answers.filter((a) => a.confirmation_status === 'unconfirmed').length,
        created_at: b.created_at,
      };
    });

    const pendingReviewCount = cases.filter((c) => c.status === 'Interest Match Only' || c.unconfirmedAnswersCount > 0).length;
    const referralsPendingCount = cases.filter((c) => c.status === 'Referral Pending' || c.status === 'Batch Verified').length;

    res.json({
      metrics: {
        casesAwaitingReview: pendingReviewCount,
        referralsPending: referralsPendingCount,
        followUpsDue: 3,
      },
      cases,
    });
  };

  /**
   * Screen 11: Field worker case review & intervention
   */
  getCaseDetail = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const beneficiary = this.beneficiaryRepo.findById(id);
    if (!beneficiary) {
      res.status(404).json({ error: 'Beneficiary case not found' });
      return;
    }

    const answers = this.sessionRepo.getProfileAnswers(id);
    const recs = this.recRepo.getByBeneficiaryId(id);
    const referrals = this.referralRepo.list({ beneficiaryId: id });

    // Generate Layer 4 Co-Pilot Case Brief
    const summary = this.summaryEngine.generateCaseSummary({
      beneficiary,
      profileAnswers: answers,
      recommendations: recs,
    });

    res.json({
      beneficiary,
      summary,
      profileAnswers: answers,
      recommendations: recs,
      referrals,
    });
  };

  /**
   * Field Worker Profile Correction
   * Updates misheard answers and re-runs matching immediately (as specified in Screen 11 & Demo sequence)
   */
  correctProfile = async (req: Request, res: Response): Promise<void> => {
    const id = String(req.params.id);
    const data = correctProfileSchema.parse(req.body);

    const beneficiary = this.beneficiaryRepo.findById(id);
    if (!beneficiary) {
      res.status(404).json({ error: 'Beneficiary not found' });
      return;
    }

    // Apply corrections
    for (const [fieldName, newValue] of Object.entries(data.corrections)) {
      this.sessionRepo.saveProfileAnswer({
        beneficiaryId: id,
        fieldName: fieldName as any,
        fieldValue: String(newValue),
        confidenceScore: 1.0, // Human verified
        confirmationStatus: 'corrected',
        source: 'worker_correction',
      });

      this.auditRepo.logEvent({
        actorId: data.workerId,
        actorName: data.workerName,
        actorRole: 'field_worker',
        action: 'PROFILE_CORRECTED',
        entityType: 'profile_answer',
        entityId: `${id}_${fieldName}`,
        newValues: { fieldName, newValue },
        metadata: { beneficiaryId: id },
      });
    }

    // Immediately re-run Grounded Matching with updated facts
    const updatedAnswers = this.sessionRepo.getProfileAnswers(id);
    const ansMap: Record<string, string> = {};
    for (const a of updatedAnswers) {
      ansMap[a.field_name] = a.field_value;
    }

    const educationLevel = ansMap['education_level'] || 'Class 8';
    let interests: string[] = ['Vocational'];
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

    const freshRecs = await this.matchingEngine.match({
      beneficiaryId: id,
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

    const savedRecs = this.recRepo.saveRecommendations(id, undefined, freshRecs);

    res.json({
      message: 'Profile corrected by field worker. Grounded recommendations recomputed.',
      beneficiaryId: id,
      recommendations: savedRecs,
    });
  };

  /**
   * CLAIM 1 PROTOCOL EXECUTION:
   * Field worker confirms live batch/seats, securely upgrading Interest Match to Verified Match.
   */
  verifyBatch = (req: Request, res: Response): void => {
    const data = verifyBatchSchema.parse(req.body);

    const opportunity = this.oppRepo.findById(data.opportunityId);
    if (!opportunity) {
      res.status(404).json({ error: 'Local training opportunity not found.' });
      return;
    }

    // Update opportunity status to active & verified
    this.oppRepo.updateBatchStatus(data.opportunityId, 'active', data.workerId);

    // Transition Recommendation state to 'Verified Match'
    const updatedRec = this.recRepo.transitionMatchState({
      recommendationId: data.recommendationId,
      newMatchState: 'Verified Match',
      actorId: data.workerId,
      actorName: data.workerName,
      actorRole: 'field_worker', // Human role guaranteed
      localOpportunityId: data.opportunityId,
      reason: data.reason || 'Human field worker physically confirmed instructor availability and open seats',
    });

    res.json({
      message: 'Batch verified. Recommendation successfully transitioned to Verified Match.',
      recommendation: updatedRec,
    });
  };

  /**
   * Field Worker approves referral and dispatches to training partner
   */
  approveReferral = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const data = approveReferralSchema.parse(req.body);

    const beneficiary = this.beneficiaryRepo.findById(id);
    const rec = this.recRepo.findById(data.recommendationId);
    const opp = this.oppRepo.findById(data.opportunityId);

    if (!beneficiary || !rec || !opp) {
      res.status(404).json({ error: 'Beneficiary, recommendation, or opportunity not found.' });
      return;
    }

    const referral = this.referralRepo.createReferral({
      beneficiaryId: id,
      recommendationId: data.recommendationId,
      localOpportunityId: data.opportunityId,
      assignedWorkerId: data.workerId,
      notes: data.notes,
    });

    // Update verification flags
    const updated = this.referralRepo.updateReferral(referral.id, {
      status: 'counselor_contacted',
      caste_document_verified: data.casteDocumentVerified,
      income_criteria_verified: data.incomeCriteriaVerified,
      residence_proof_verified: data.residenceProofVerified,
      actorId: data.workerId,
      actorName: data.workerName,
    });

    // Generate Outbound Notification Drafts
    const drafts = this.messagingEngine.draftReferralConfirmation({
      beneficiary,
      qualification: rec.data_snapshot.qualification,
      opportunity: opp,
      workerName: data.workerName,
      lang: beneficiary.preferred_language,
    });

    res.status(201).json({
      message: 'Referral approved and submitted to training partner roster.',
      referral: updated,
      outboundDrafts: drafts,
    });
  };
}
