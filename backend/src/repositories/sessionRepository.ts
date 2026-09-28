import { v4 as uuidv4 } from 'uuid';
import Database from 'better-sqlite3';
import { getDatabase } from '../database/connection.js';
import {
  InterviewSession,
  InterviewTurn,
  ProfileAnswer,
  Channel,
  LanguageCode,
  ConfirmationStatus,
  AnswerSource,
} from '../types/index.js';

export class SessionRepository {
  private db: Database.Database;

  constructor(customDb?: Database.Database) {
    this.db = customDb || getDatabase();
  }

  createSession(input: {
    beneficiaryId: string;
    channel?: Channel;
    language?: LanguageCode;
  }): InterviewSession {
    const id = `ses_${uuidv4()}`;
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      INSERT INTO interview_sessions (
        id, beneficiary_id, channel, status, current_question_index,
        last_question, language, transcript_history, created_at, updated_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      id,
      input.beneficiaryId,
      input.channel || 'web_app',
      'in_progress',
      0,
      null,
      input.language || 'hi',
      JSON.stringify([]),
      now,
      now
    );

    return this.getSession(id)!;
  }

  getSession(id: string): InterviewSession | null {
    const stmt = this.db.prepare(`SELECT * FROM interview_sessions WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;

    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      channel: row.channel,
      status: row.status,
      current_question_index: row.current_question_index,
      last_question: row.last_question || undefined,
      language: row.language,
      transcript_history: JSON.parse(row.transcript_history || '[]'),
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }

  updateSession(
    id: string,
    updates: {
      status?: InterviewSession['status'];
      current_question_index?: number;
      last_question?: string;
    }
  ): InterviewSession | null {
    const session = this.getSession(id);
    if (!session) return null;

    const now = new Date().toISOString();
    const newStatus = updates.status || session.status;
    const newIndex =
      updates.current_question_index !== undefined
        ? updates.current_question_index
        : session.current_question_index;
    const newLastQuestion =
      updates.last_question !== undefined ? updates.last_question : session.last_question;

    const stmt = this.db.prepare(`
      UPDATE interview_sessions
      SET status = ?, current_question_index = ?, last_question = ?, updated_at = ?
      WHERE id = ?
    `);

    stmt.run(newStatus, newIndex, newLastQuestion || null, now, id);
    return this.getSession(id);
  }

  appendTurn(id: string, turn: InterviewTurn): InterviewSession | null {
    const session = this.getSession(id);
    if (!session) return null;

    const history = [...session.transcript_history, turn];
    const now = new Date().toISOString();

    const stmt = this.db.prepare(`
      UPDATE interview_sessions
      SET transcript_history = ?, updated_at = ?
      WHERE id = ?
    `);

    stmt.run(JSON.stringify(history), now, id);
    return this.getSession(id);
  }

  saveProfileAnswer(input: {
    beneficiaryId: string;
    sessionId?: string;
    fieldName: ProfileAnswer['field_name'];
    fieldValue: string;
    confidenceScore?: number;
    confirmationStatus?: ConfirmationStatus;
    source?: AnswerSource;
  }): ProfileAnswer {
    const id = `ans_${uuidv4()}`;
    const now = new Date().toISOString();

    // Check if an unconfirmed/confirmed answer for this field already exists, update or insert
    const existing = this.db
      .prepare(`SELECT id FROM profile_answers WHERE beneficiary_id = ? AND field_name = ?`)
      .get(input.beneficiaryId, input.fieldName) as any;

    if (existing) {
      const stmt = this.db.prepare(`
        UPDATE profile_answers
        SET session_id = ?, field_value = ?, confidence_score = ?,
            confirmation_status = ?, source = ?, updated_at = ?
        WHERE id = ?
      `);
      stmt.run(
        input.sessionId || null,
        input.fieldValue,
        input.confidenceScore ?? 1.0,
        input.confirmationStatus || 'unconfirmed',
        input.source || 'voice_extraction',
        now,
        existing.id
      );
      return this.getAnswerById(existing.id)!;
    } else {
      const stmt = this.db.prepare(`
        INSERT INTO profile_answers (
          id, beneficiary_id, session_id, field_name, field_value,
          confidence_score, confirmation_status, source, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
      stmt.run(
        id,
        input.beneficiaryId,
        input.sessionId || null,
        input.fieldName,
        input.fieldValue,
        input.confidenceScore ?? 1.0,
        input.confirmationStatus || 'unconfirmed',
        input.source || 'voice_extraction',
        now,
        now
      );
      return this.getAnswerById(id)!;
    }
  }

  getAnswerById(id: string): ProfileAnswer | null {
    const stmt = this.db.prepare(`SELECT * FROM profile_answers WHERE id = ?`);
    const row = stmt.get(id) as any;
    if (!row) return null;
    return this.mapAnswerRow(row);
  }

  getProfileAnswers(beneficiaryId: string): ProfileAnswer[] {
    const stmt = this.db.prepare(`
      SELECT * FROM profile_answers
      WHERE beneficiary_id = ?
      ORDER BY created_at ASC
    `);
    const rows = stmt.all(beneficiaryId) as any[];
    return rows.map(this.mapAnswerRow);
  }

  updateProfileAnswerStatus(
    id: string,
    updates: {
      status: ConfirmationStatus;
      newValue?: string;
      source?: AnswerSource;
    }
  ): ProfileAnswer | null {
    const now = new Date().toISOString();
    let query = `UPDATE profile_answers SET confirmation_status = ?, updated_at = ?`;
    const params: any[] = [updates.status, now];

    if (updates.newValue !== undefined) {
      query += `, field_value = ?`;
      params.push(updates.newValue);
    }
    if (updates.source !== undefined) {
      query += `, source = ?`;
      params.push(updates.source);
    }

    query += ` WHERE id = ?`;
    params.push(id);

    const stmt = this.db.prepare(query);
    stmt.run(...params);
    return this.getAnswerById(id);
  }

  private mapAnswerRow(row: any): ProfileAnswer {
    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      session_id: row.session_id || undefined,
      field_name: row.field_name,
      field_value: row.field_value,
      confidence_score: row.confidence_score,
      confirmation_status: row.confirmation_status,
      source: row.source,
      created_at: row.created_at,
      updated_at: row.updated_at,
    };
  }
}
