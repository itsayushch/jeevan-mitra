import { Request, Response } from 'express';
import { z } from 'zod';
import { DialogueManager } from '../ai-layers/layer1-intake/dialogueManager.js';
import { ExtractionEngine } from '../ai-layers/layer2-extraction/extractionEngine.js';
import { generateProfileConfirmation } from '../ai-layers/layer2-extraction/validation.js';
import { SessionRepository } from '../repositories/sessionRepository.js';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';
import { AuditRepository } from '../repositories/auditRepository.js';

export const startInterviewSchema = z.object({
  beneficiaryId: z.string(),
  channel: z.enum(['web_app', 'kiosk', 'whatsapp', 'ivr']).default('web_app'),
  language: z.enum(['hi', 'bho', 'awa', 'en', 'bn', 'ta', 'te']).default('hi'),
});

export const processTurnSchema = z.object({
  sessionId: z.string(),
  speechOrText: z.string().min(1, 'Speech or text response required'),
  isAudio: z.boolean().default(false),
});

export const confirmProfileSchema = z.object({
  sessionId: z.string(),
  beneficiaryId: z.string(),
  confirmedFields: z.record(z.string(), z.any()), // Map of field_name -> { value: any, confirmed: boolean }
});

export class InterviewController {
  private dialogueManager: DialogueManager;
  private extractionEngine: ExtractionEngine;
  private sessionRepo: SessionRepository;
  private beneficiaryRepo: BeneficiaryRepository;
  private auditRepo: AuditRepository;

  constructor() {
    this.sessionRepo = new SessionRepository();
    this.beneficiaryRepo = new BeneficiaryRepository();
    this.dialogueManager = new DialogueManager(this.sessionRepo, this.beneficiaryRepo);
    this.extractionEngine = new ExtractionEngine();
    this.auditRepo = new AuditRepository();
  }

  start = async (req: Request, res: Response): Promise<void> => {
    const data = startInterviewSchema.parse(req.body);
    const result = await this.dialogueManager.startInterview(
      data.beneficiaryId,
      data.channel,
      data.language
    );

    this.auditRepo.logEvent({
      actorId: data.beneficiaryId,
      actorName: 'Beneficiary',
      actorRole: 'beneficiary',
      action: 'INTERVIEW_STARTED',
      entityType: 'interview_session',
      entityId: result.session.id,
      metadata: { channel: data.channel, language: data.language },
    });

    res.status(201).json(result);
  };

  processTurn = async (req: Request, res: Response): Promise<void> => {
    const data = processTurnSchema.parse(req.body);
    const result = await this.dialogueManager.processTurn({
      sessionId: data.sessionId,
      userSpeechOrText: data.speechOrText,
      isAudio: data.isAudio,
    });

    res.json(result);
  };

  extractProfile = (req: Request, res: Response): void => {
    const sessionId = String(req.params.sessionId);
    const session = this.sessionRepo.getSession(sessionId);
    if (!session) {
      res.status(404).json({ error: 'Session not found' });
      return;
    }

    const beneficiary = this.beneficiaryRepo.findById(session.beneficiary_id);
    const profile = this.extractionEngine.extractProfile(
      session.transcript_history,
      beneficiary?.district || 'Moradabad',
      beneficiary?.block || 'Moradabad Rural'
    );

    const readback = generateProfileConfirmation(profile, session.language);

    res.json({
      sessionId,
      beneficiaryId: session.beneficiary_id,
      profile,
      readback,
    });
  };

  confirmProfile = (req: Request, res: Response): void => {
    const data = confirmProfileSchema.parse(req.body);
    const session = this.sessionRepo.getSession(data.sessionId);
    if (!session) {
      res.status(404).json({ error: 'Session not found' });
      return;
    }

    // Save profile answers into persistent DB
    const savedAnswers = [];
    for (const [fieldName, fieldData] of Object.entries(data.confirmedFields)) {
      const dataObj = fieldData as any;
      const valStr = typeof dataObj === 'object' && dataObj !== null
        ? (Array.isArray(dataObj.value) ? JSON.stringify(dataObj.value) : String(dataObj.value))
        : String(fieldData);

      const confidence = typeof dataObj === 'object' && dataObj !== null && dataObj.confidence !== undefined
        ? Number(dataObj.confidence)
        : 1.0;

      const confirmed = typeof dataObj === 'object' && dataObj !== null && dataObj.confirmed !== undefined
        ? (dataObj.confirmed ? 'confirmed' : 'unconfirmed')
        : 'confirmed';

      const ans = this.sessionRepo.saveProfileAnswer({
        beneficiaryId: data.beneficiaryId,
        sessionId: data.sessionId,
        fieldName: fieldName as any,
        fieldValue: valStr,
        confidenceScore: confidence,
        confirmationStatus: confirmed as any,
        source: 'voice_extraction',
      });
      savedAnswers.push(ans);
    }

    this.sessionRepo.updateSession(data.sessionId, { status: 'confirmed' });

    this.auditRepo.logEvent({
      actorId: data.beneficiaryId,
      actorName: 'Beneficiary',
      actorRole: 'beneficiary',
      action: 'PROFILE_CONFIRMED',
      entityType: 'interview_session',
      entityId: data.sessionId,
      metadata: { answerCount: savedAnswers.length },
    });

    res.json({
      message: 'Beneficiary profile confirmed and validated.',
      savedAnswers,
    });
  };

  getSession = (req: Request, res: Response): void => {
    const id = String(req.params.id);
    const session = this.sessionRepo.getSession(id);
    if (!session) {
      res.status(404).json({ error: 'Session not found' });
      return;
    }
    const answers = this.sessionRepo.getProfileAnswers(session.beneficiary_id);
    res.json({
      session,
      profileAnswers: answers,
    });
  };
}
