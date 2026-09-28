import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
import { Consent } from '../types/index.js';

export interface CreateConsentInput {
  beneficiaryId: string;
  purpose: string;
  noticeVersion?: string;
  audioConsentRecorded?: boolean;
  voiceRetentionChoice?: 'do_not_keep' | 'keep_for_quality';
  dpdpAffirmativeConsent?: boolean;
}

export class ConsentRepository {
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async recordConsent(input: CreateConsentInput): Promise<Consent> {
    const id = `cns_${uuidv4()}`;

    const consent = await this.prisma.consent.create({
      data: {
        id,
        beneficiary_id: input.beneficiaryId,
        purpose: input.purpose,
        notice_version: input.noticeVersion || '1.0',
        audio_consent_recorded: input.audioConsentRecorded !== false,
        voice_retention_choice: input.voiceRetentionChoice || 'do_not_keep',
        dpdp_affirmative_consent: input.dpdpAffirmativeConsent !== false,
      },
    });

    return {
      id: consent.id,
      beneficiary_id: consent.beneficiary_id,
      purpose: consent.purpose,
      notice_version: consent.notice_version,
      audio_consent_recorded: consent.audio_consent_recorded,
      voice_retention_choice: consent.voice_retention_choice as 'do_not_keep' | 'keep_for_quality',
      dpdp_affirmative_consent: consent.dpdp_affirmative_consent,
      timestamp: consent.timestamp.toISOString(),
    };
  }

  async getByBeneficiaryId(beneficiaryId: string): Promise<Consent[]> {
    const rows = await this.prisma.consent.findMany({
      where: { beneficiary_id: beneficiaryId },
      orderBy: { timestamp: 'desc' },
    });

    return rows.map((r) => ({
      id: r.id,
      beneficiary_id: r.beneficiary_id,
      purpose: r.purpose,
      notice_version: r.notice_version,
      audio_consent_recorded: r.audio_consent_recorded,
      voice_retention_choice: r.voice_retention_choice as 'do_not_keep' | 'keep_for_quality',
      dpdp_affirmative_consent: r.dpdp_affirmative_consent,
      timestamp: r.timestamp.toISOString(),
    }));
  }
}
