import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { getDb } from '../database/connection.js';
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
  private prisma: PrismaClient;

  constructor(customPrisma?: PrismaClient) {
    this.prisma = customPrisma || getDb();
  }

  async createSession(input: {
    beneficiaryId: string;
    channel?: Channel;
    language?: LanguageCode;
  }): Promise<InterviewSession> {
    const id = `ses_${uuidv4()}`;

    const session = await this.prisma.interviewSession.create({
      data: {
        id,
        beneficiary_id: input.beneficiaryId,
        channel: input.channel || 'web_app',
        status: 'in_progress',
        current_question_index: 0,
        last_question: null,
        language: input.language || 'hi',
        transcript_history: JSON.stringify([]),
      },
    });

    return this.getSession(id) as Promise<InterviewSession>;
  }

  async getSession(id: string): Promise<InterviewSession | null> {
    const row = await this.prisma.interviewSession.findUnique({ where: { id } });
    if (!row) return null;

    return {
      id: row.id,
      beneficiary_id: row.beneficiary_id,
      channel: row.channel as Channel,
      status: row.status as any,
      current_question_index: row.current_question_index,
      last_question: row.last_question || undefined,
      language: row.language as LanguageCode,
      transcript_history: JSON.parse(row.transcript_history || '[]'),
      created_at: row.created_at.toISOString(),
      updated_at: row.updated_at.toISOString(),
    };
  }

  async updateSession(
    id: string,
    updates: {
      status?: InterviewSession['status'];
      current_question_index?: number;
      last_question?: string;
    }
  ): Promise<InterviewSession | null> {
    const session = await this.getSession(id);
    if (!session) return null;

    const data: any = {};
    if (updates.status !== undefined) data.status = updates.status;
    if (updates.current_question_index !== undefined) data.current_question_index = updates.current_question_index;
    if (updates.last_question !== undefined) data.last_question = updates.last_question;

    await this.prisma.interviewSession.update({
      where: { id },
      data,
    });
    return this.getSession(id);
  }

  async appendTurn(id: string, turn: InterviewTurn): Promise<InterviewSession | null> {
    const session = await this.getSession(id);
    if (!session) return null;

    const history = [...session.transcript_history, turn];

    await this.prisma.interviewSession.update({
      where: { id },
      data: { transcript_history: JSON.stringify(history) },
    });
    return this.getSession(id);
  }

  async saveProfileAnswer(input: {
    beneficiaryId: string;
    sessionId?: string;
    fieldName: ProfileAnswer['field_name'];
    fieldValue: string;
    confidenceScore?: number;
    confirmationStatus?: ConfirmationStatus;
    source?: AnswerSource;
  }): Promise<ProfileAnswer> {
    const id = `ans_${uuidv4()}`;

    // Check if an unconfirmed/confirmed answer for this field already exists, update or insert
    const existing = await this.prisma.profileAnswer.findFirst({
      where: {
        beneficiary_id: input.beneficiaryId,
        field_name: input.fieldName,
      },
    });

    if (existing) {
      const updated = await this.prisma.profileAnswer.update({
        where: { id: existing.id },
        data: {
          session_id: input.sessionId || null,
          field_value: input.fieldValue,
          confidence_score: input.confidenceScore ?? 1.0,
          confirmation_status: input.confirmationStatus || 'unconfirmed',
          source: input.source || 'voice_extraction',
        },
      });
      return this.mapAnswerRow(updated);
    } else {
      const created = await this.prisma.profileAnswer.create({
        data: {
          id,
          beneficiary_id: input.beneficiaryId,
          session_id: input.sessionId || null,
          field_name: input.fieldName,
          field_value: input.fieldValue,
          confidence_score: input.confidenceScore ?? 1.0,
          confirmation_status: input.confirmationStatus || 'unconfirmed',
          source: input.source || 'voice_extraction',
        },
      });
      return this.mapAnswerRow(created);
    }
  }

  async getAnswerById(id: string): Promise<ProfileAnswer | null> {
    const row = await this.prisma.profileAnswer.findUnique({ where: { id } });
    if (!row) return null;
    return this.mapAnswerRow(row);
  }

  async getProfileAnswers(beneficiaryId: string): Promise<ProfileAnswer[]> {
    const rows = await this.prisma.profileAnswer.findMany({
      where: { beneficiary_id: beneficiaryId },
      orderBy: { created_at: 'asc' },
    });
    return rows.map(this.mapAnswerRow);
  }

  async updateProfileAnswerStatus(
    id: string,
    updates: {
      status: ConfirmationStatus;
      newValue?: string;
      source?: AnswerSource;
    }
  ): Promise<ProfileAnswer | null> {
    const data: any = { confirmation_status: updates.status };

    if (updates.newValue !== undefined) data.field_value = updates.newValue;
    if (updates.source !== undefined) data.source = updates.source;

    await this.prisma.profileAnswer.update({
      where: { id },
      data,
    });
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
      confirmation_status: row.confirmation_status as any,
      source: row.source as any,
      created_at: row.created_at.toISOString(),
      updated_at: row.updated_at.toISOString(),
    };
  }
}
