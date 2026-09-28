import { Request, Response } from 'express';
import { z } from 'zod';
import { ReferralRepository } from '../repositories/referralRepository.js';
import { OutcomeRepository } from '../repositories/outcomeRepository.js';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';

export const updateReferralSchema = z.object({
  status: z
    .enum([
      'pending',
      'counselor_contacted',
      'documents_verified',
      'enrolled',
      'rejected',
      'ineligible',
    ])
    .optional(),
  notes: z.string().optional(),
  caste_document_verified: z.boolean().optional(),
  income_criteria_verified: z.boolean().optional(),
  residence_proof_verified: z.boolean().optional(),
  sms_sent: z.boolean().optional(),
  whatsapp_sent: z.boolean().optional(),
  next_follow_up: z.string().optional(),
  workerId: z.string().default('worker_vle_01'),
  workerName: z.string().default('Ramesh Kumar (VLE)'),
});

export const recordOutcomeSchema = z.object({
  beneficiaryId: z.string(),
  referralId: z.string().optional(),
  enrolmentStatus: z.enum(['enrolled', 'completed', 'dropped_out']).default('enrolled'),
  completionStatus: z.enum(['in_progress', 'passed', 'failed', 'dropped_out']).default('in_progress'),
  dropoutReason: z.string().optional(),
  employmentStatus: z
    .enum(['unemployed', 'wage_employed', 'self_employed', 'enterprise_started'])
    .default('unemployed'),
  employerOrEnterpriseName: z.string().optional(),
  monthlyIncomeInr: z.number().default(0),
  toolkitReceived: z.boolean().default(false),
  seedGrantApplied: z.boolean().default(false),
  followUpDate: z.string().optional(),
  notes: z.string().optional(),
  workerId: z.string().default('worker_vle_01'),
});

export class ReferralController {
  private referralRepo: ReferralRepository;
  private outcomeRepo: OutcomeRepository;
  private beneficiaryRepo: BeneficiaryRepository;

  constructor() {
    this.referralRepo = new ReferralRepository();
    this.outcomeRepo = new OutcomeRepository();
    this.beneficiaryRepo = new BeneficiaryRepository();
  }

  listReferrals = (req: Request, res: Response): void => {
    const { status, workerId, beneficiaryId } = req.query;
    const referrals = this.referralRepo.list({
      status: status as any,
      assignedWorkerId: workerId ? String(workerId) : undefined,
      beneficiaryId: beneficiaryId ? String(beneficiaryId) : undefined,
    });
    res.json({ count: referrals.length, referrals });
  };

  getReferralById = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const ref = this.referralRepo.findById(id);
    if (!ref) {
      res.status(404).json({ error: 'Referral not found' });
      return;
    }
    res.json(ref);
  };

  updateReferral = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const data = updateReferralSchema.parse(req.body);

    const updated = this.referralRepo.updateReferral(id, {
      status: data.status,
      notes: data.notes,
      caste_document_verified: data.caste_document_verified,
      income_criteria_verified: data.income_criteria_verified,
      residence_proof_verified: data.residence_proof_verified,
      sms_sent: data.sms_sent,
      whatsapp_sent: data.whatsapp_sent,
      next_follow_up: data.next_follow_up,
      actorId: data.workerId,
      actorName: data.workerName,
    });

    if (!updated) {
      res.status(404).json({ error: 'Referral not found' });
      return;
    }

    res.json(updated);
  };

  recordOutcome = (req: Request, res: Response): void => {
    const data = recordOutcomeSchema.parse(req.body);
    const outcome = this.outcomeRepo.createOutcome({
      beneficiaryId: data.beneficiaryId,
      referralId: data.referralId,
      enrolmentStatus: data.enrolmentStatus,
      completionStatus: data.completionStatus,
      dropoutReason: data.dropoutReason,
      employmentStatus: data.employmentStatus,
      employerOrEnterpriseName: data.employerOrEnterpriseName,
      monthlyIncomeInr: data.monthlyIncomeInr,
      toolkitReceived: data.toolkitReceived,
      seedGrantApplied: data.seedGrantApplied,
      followUpDate: data.followUpDate,
      notes: data.notes,
      recordedByWorkerId: data.workerId,
    });

    res.status(201).json(outcome);
  };

  /**
   * Screen 9: Beneficiary Progress Tracker
   */
  getBeneficiaryProgressTracker = (req: Request, res: Response): void => {
    const beneficiaryId = String(req.params.beneficiaryId);
    const beneficiary = this.beneficiaryRepo.findById(beneficiaryId);
    if (!beneficiary) {
      res.status(404).json({ error: 'Beneficiary not found' });
      return;
    }

    const referrals = this.referralRepo.list({ beneficiaryId });
    const outcomes = this.outcomeRepo.findByBeneficiaryId(beneficiaryId);

    const latestReferral = referrals.length > 0 ? referrals[0] : null;
    const latestOutcome = outcomes.length > 0 ? outcomes[0] : null;

    // Build 5-step milestone timeline
    const timeline = [
      {
        step: 1,
        title: 'Voice Counseling Complete',
        status: 'completed',
        details: 'Initial interview conducted; skills & aspiration profile mapped.',
      },
      {
        step: 2,
        title: 'Field-Worker Verified',
        status: latestReferral ? 'completed' : 'pending',
        details: latestReferral
          ? `Verified by ${latestReferral.assigned_worker_id}`
          : 'Awaiting local VLE/worker verification',
      },
      {
        step: 3,
        title: 'Batch Enrolment',
        status:
          latestReferral &&
          (latestReferral.status === 'enrolled' ||
            latestOutcome?.enrolment_status === 'enrolled' ||
            latestOutcome?.enrolment_status === 'completed')
            ? 'completed'
            : latestReferral
            ? 'in_progress'
            : 'pending',
        details: 'Seat allocated in PM-AJAY GIA training partner batch.',
      },
      {
        step: 4,
        title: 'Skilling & Assessment',
        status:
          latestOutcome?.completion_status === 'passed'
            ? 'completed'
            : latestOutcome?.completion_status === 'in_progress'
            ? 'in_progress'
            : 'pending',
        details: 'Classroom & practical training with NCVET/NSQF assessment.',
      },
      {
        step: 5,
        title: 'Tool Kit & Enterprise Linkage',
        status:
          latestOutcome?.toolkit_received || latestOutcome?.seed_grant_applied
            ? 'completed'
            : 'pending',
        details: 'Tool kit distribution and enterprise seed grant assistance.',
      },
    ];

    res.json({
      applicationId: `PMAJAY-2026-${beneficiaryId.slice(-4).toUpperCase()}`,
      beneficiaryName: beneficiary.name,
      district: beneficiary.district,
      block: beneficiary.block,
      preferredLanguage: beneficiary.preferred_language,
      currentStep: timeline.filter((t) => t.status === 'completed').length + 1,
      timeline,
      audioUpdateScript: `नमस्ते ${beneficiary.name}! आपका आवेदन चरण 3 (बैच नामांकन) में है। किसी भी सहायता हेतु अपने ग्राम समन्वयक से संपर्क करें।`,
    });
  };
}
