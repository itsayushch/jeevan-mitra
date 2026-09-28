import { SessionRepository } from '../../repositories/sessionRepository.js';
import { BeneficiaryRepository } from '../../repositories/beneficiaryRepository.js';
import { INTERVIEW_QUESTIONS } from './prompts.js';
import { getSpeechAdapter, ISpeechAdapter } from './speechAdapter.js';
import { InterviewTurn, InterviewSession, LanguageCode } from '../../types/index.js';
import { logger } from '../../utils/logger.js';

export interface ProcessTurnInput {
  sessionId: string;
  userSpeechOrText: string;
  isAudio?: boolean;
}

export interface TurnResponse {
  sessionId: string;
  completed: boolean;
  currentQuestionIndex: number;
  spokenReply: string;
  audioReplyUrl?: string;
  transcriptRecognized: string;
  confidence: number;
  clarificationPromptNeeded: boolean;
  nextQuestion?: {
    index: number;
    questionId: string;
    text: string;
  };
}

export class DialogueManager {
  private sessionRepo: SessionRepository;
  private beneficiaryRepo: BeneficiaryRepository;
  private speechAdapter: ISpeechAdapter;

  constructor(sessionRepo?: SessionRepository, beneficiaryRepo?: BeneficiaryRepository) {
    this.sessionRepo = sessionRepo || new SessionRepository();
    this.beneficiaryRepo = beneficiaryRepo || new BeneficiaryRepository();
    this.speechAdapter = getSpeechAdapter();
  }

  /**
   * Start a new structured 8-question interview session
   */
  async startInterview(beneficiaryId: string, channel: any = 'web_app', lang: LanguageCode = 'hi'): Promise<{
    session: InterviewSession;
    firstQuestion: {
      index: number;
      questionId: string;
      text: string;
      audioUrl?: string;
    };
  }> {
    const session = await this.sessionRepo.createSession({
      beneficiaryId,
      channel,
      language: lang,
    });

    const firstQ = INTERVIEW_QUESTIONS[0];
    const text = firstQ.text[lang as LanguageCode] || firstQ.text['hi'];
    const synthesis = await this.speechAdapter.synthesize(text, lang);

    await this.sessionRepo.updateSession(session.id, {
      current_question_index: 0,
      last_question: text,
      status: 'in_progress',
    });

    const updatedSession = await this.sessionRepo.getSession(session.id);

    return {
      session: updatedSession!,
      firstQuestion: {
        index: 0,
        questionId: firstQ.id,
        text,
        audioUrl: synthesis.audioUrl,
      },
    };
  }

  /**
   * Process a single turn of voice/text response from the beneficiary
   */
  async processTurn(input: ProcessTurnInput): Promise<TurnResponse> {
    const session = await this.sessionRepo.getSession(input.sessionId);
    if (!session) {
      throw new Error(`Session ${input.sessionId} not found.`);
    }

    const lang = session.language as LanguageCode;
    const currentIndex = session.current_question_index;
    const currentQDef = INTERVIEW_QUESTIONS[currentIndex] || INTERVIEW_QUESTIONS[0];

    // Transcribe or extract text
    const transcription = await this.speechAdapter.transcribe(input.userSpeechOrText, lang);

    // Guardrail Check: Check if user input is too ambiguous or "skip" / "don't know"
    const lower = transcription.text.toLowerCase().trim();
    const isSkip = lower.includes('skip') || lower.includes('छोड़ो') || lower.includes('आगे बढ़ो');
    const isUncertain = transcription.isAmbiguous || lower.includes('पता नहीं') || lower.includes('malum nahi') || lower.length < 3;

    // Check if we need to issue an empathetic clarification re-prompt
    // Only re-prompt once per question to avoid frustrating user
    const lastTurnWasClarification = session.transcript_history.length > 0 &&
      session.transcript_history[session.transcript_history.length - 1].clarification_needed;

    let clarificationNeeded = isUncertain && !isSkip && !lastTurnWasClarification;
    let spokenReplyText = '';
    let nextIndex = currentIndex;

    if (clarificationNeeded) {
      spokenReplyText = currentQDef.clarificationPrompt[lang] || currentQDef.clarificationPrompt['hi'];
      // Keep question index unchanged so they can answer again
    } else {
      // Progress to next question
      nextIndex = currentIndex + 1;
      if (nextIndex < INTERVIEW_QUESTIONS.length) {
        const nextQ = INTERVIEW_QUESTIONS[nextIndex];
        spokenReplyText = nextQ.text[lang] || nextQ.text['hi'];
      } else {
        spokenReplyText = lang === 'en'
          ? 'Thank you! We have noted all your answers. Please review your profile.'
          : 'धन्यवाद! हमने आपकी सभी बातें नोट कर ली हैं। आइए आपके उत्तरों की पुष्टि कर लें।';
      }
    }

    // Synthesize spoken reply
    const synthesis = await this.speechAdapter.synthesize(spokenReplyText, lang);

    // Save turn into session history
    const turn: InterviewTurn = {
      turn_number: session.transcript_history.length + 1,
      question_id: currentQDef.id,
      question_text: currentQDef.text[lang] || currentQDef.text['hi'],
      transcript: transcription.text,
      confidence: transcription.confidence,
      clarification_needed: clarificationNeeded,
      timestamp: new Date().toISOString(),
    };

    await this.sessionRepo.appendTurn(session.id, turn);

    const isCompleted = nextIndex >= INTERVIEW_QUESTIONS.length;
    await this.sessionRepo.updateSession(session.id, {
      current_question_index: nextIndex,
      last_question: spokenReplyText,
      status: isCompleted ? 'profile_extracted' : 'in_progress',
    });

    return {
      sessionId: session.id,
      completed: isCompleted,
      currentQuestionIndex: nextIndex,
      spokenReply: spokenReplyText,
      audioReplyUrl: synthesis.audioUrl,
      transcriptRecognized: transcription.text,
      confidence: transcription.confidence,
      clarificationPromptNeeded: clarificationNeeded,
      nextQuestion: !isCompleted && nextIndex < INTERVIEW_QUESTIONS.length
        ? {
            index: nextIndex,
            questionId: INTERVIEW_QUESTIONS[nextIndex].id,
            text: INTERVIEW_QUESTIONS[nextIndex].text[lang] || INTERVIEW_QUESTIONS[nextIndex].text['hi'],
          }
        : undefined,
    };
  }
}
