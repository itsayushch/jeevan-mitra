import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
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
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  recordConsent(input: CreateConsentInput): Consent {
    const id = `cns_${uuidv4()}`;
    const timestamp = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO consents (
        id, beneficiary_id, purpose, notice_version,
        audio_consent_recorded, voice_retention_choice,
        dpdp_affirmative_consent, timestamp
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.beneficiaryId,
      input.purpose,
      input.noticeVersion || '1.0',
      input.audioConsentRecorded !== false ? 1 : 0,
      input.voiceRetentionChoice || 'do_not_keep',
      input.dpdpAffirmativeConsent !== false ? 1 : 0,
      timestamp
    );

    return {
      id,
      beneficiary_id: input.beneficiaryId,
      purpose: input.purpose,
      notice_version: input.noticeVersion || '1.0',
      audio_consent_recorded: input.audioConsentRecorded !== false,
      voice_retention_choice: input.voiceRetentionChoice || 'do_not_keep',
      dpdp_affirmative_consent: input.dpdpAffirmativeConsent !== false,
      timestamp,
    };
  }

  getByBeneficiaryId(beneficiaryId: string): Consent[] {
    const stmt = this.db.prepare(`
      SELECT * FROM consents
      WHERE beneficiary_id = ?
      ORDER BY timestamp DESC
    `);
    const rows = stmt.all(beneficiaryId) as any[];
    return rows.map((r) => ({
      id: r.id,
      beneficiary_id: r.beneficiary_id,
      purpose: r.purpose,
      notice_version: r.notice_version,
      audio_consent_recorded: Boolean(r.audio_consent_recorded),
      voice_retention_choice: r.voice_retention_choice,
      dpdp_affirmative_consent: Boolean(r.dpdp_affirmative_consent),
      timestamp: r.timestamp,
    }));
  }
}
