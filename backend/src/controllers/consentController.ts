import { Request, Response } from 'express';
import { z } from 'zod';
import { ConsentRepository } from '../repositories/consentRepository.js';
import { AuditRepository } from '../repositories/auditRepository.js';

export const recordConsentSchema = z.object({
  beneficiaryId: z.string(),
  purpose: z.string().default('PM-AJAY GIA Livelihood Matching and Skilling Recommendations'),
  noticeVersion: z.string().default('1.0'),
  audioConsentRecorded: z.boolean().default(true),
  voiceRetentionChoice: z.enum(['do_not_keep', 'keep_for_quality']).default('do_not_keep'),
  dpdpAffirmativeConsent: z.boolean().default(true),
});

export class ConsentController {
  private consentRepo: ConsentRepository;
  private auditRepo: AuditRepository;

  constructor() {
    this.consentRepo = new ConsentRepository();
    this.auditRepo = new AuditRepository();
  }

  record = (req: Request, res: Response): void => {
    const data = recordConsentSchema.parse(req.body);
    const consent = this.consentRepo.recordConsent(data);

    this.auditRepo.logEvent({
      actorId: data.beneficiaryId,
      actorName: 'Beneficiary',
      actorRole: 'beneficiary',
      action: 'CONSENT_RECORDED',
      entityType: 'consent',
      entityId: consent.id,
      newValues: {
        voiceRetentionChoice: data.voiceRetentionChoice,
        dpdpConsent: data.dpdpAffirmativeConsent,
        noticeVersion: data.noticeVersion,
      },
    });

    res.status(201).json({
      message: 'Consent recorded in compliance with DPDP Act principles.',
      consent,
    });
  };

  getByBeneficiary = (req: Request, res: Response): void => {
    const beneficiaryId = String(req.params.beneficiaryId);
    const consents = this.consentRepo.getByBeneficiaryId(beneficiaryId);
    res.json({
      beneficiaryId,
      consents,
    });
  };
}
