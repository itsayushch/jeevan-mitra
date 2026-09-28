import { Request, Response } from 'express';
import { z } from 'zod';
import { DialogueManager } from '../ai-layers/layer1-intake/dialogueManager.js';
import { MatchingEngine } from '../ai-layers/layer3-matching/matchingEngine.js';
import { BeneficiaryRepository } from '../repositories/beneficiaryRepository.js';
import { RecommendationRepository } from '../repositories/recommendationRepository.js';
import { SessionRepository } from '../repositories/sessionRepository.js';

export const whatsappVoiceSchema = z.object({
  fromPhone: z.string(),
  beneficiaryName: z.string().default('Rajesh Kumar'),
  voiceNoteTranscript: z.string(),
  dialect: z.enum(['hi', 'awa', 'bho', 'en']).default('awa'),
  district: z.string().default('Moradabad'),
  block: z.string().default('Chhajlet'),
});

export const ivrCallSchema = z.object({
  callerNumber: z.string(),
  dtmfDigit: z.string().optional(),
  speechInput: z.string().optional(),
  currentStep: z.number().default(1),
  language: z.enum(['hi', 'awa', 'bho', 'en']).default('hi'),
});

export class ChannelController {
  private beneficiaryRepo: BeneficiaryRepository;
  private sessionRepo: SessionRepository;
  private matchingEngine: MatchingEngine;
  private recRepo: RecommendationRepository;

  constructor() {
    this.beneficiaryRepo = new BeneficiaryRepository();
    this.sessionRepo = new SessionRepository();
    this.matchingEngine = new MatchingEngine();
    this.recRepo = new RecommendationRepository();
  }

  /**
   * Screen 10: WhatsApp voice note interface simulator & webhook
   */
  handleWhatsAppVoice = async (req: Request, res: Response): Promise<void> => {
    const data = whatsappVoiceSchema.parse(req.body);

    // Look up or auto-register beneficiary for this WhatsApp phone
    let beneficiary = this.beneficiaryRepo.findByPhone(data.fromPhone);
    if (!beneficiary) {
      beneficiary = this.beneficiaryRepo.create({
        name: data.beneficiaryName,
        phone: data.fromPhone,
        preferred_language: data.dialect,
        district: data.district,
        block: data.block,
        contact_preference: 'whatsapp',
      });
    }

    // Process matching based on voice note input
    const recs = await this.matchingEngine.match({
      beneficiaryId: beneficiary.id,
      district: beneficiary.district,
      block: beneficiary.block,
      educationLevel: 'Class 8',
      interests: [data.voiceNoteTranscript],
      skills: ['Manual Precision Work'],
      mobilityRadiusKm: 10,
      accessibilityNeeds: 'None',
      workPreference: 'both',
      preferredLanguage: data.dialect,
    });

    const topRec = recs[0];

    const replyAudioText =
      data.dialect === 'awa'
        ? `नमस्ते! आपकी बात सुनिके हमने आपके खातिर ${topRec.data_snapshot.qualification.title} का प्रशिक्षण चुना है। ई ${topRec.data_snapshot.qualification.duration_hours} घंटा क सरकारी कोर्स है।`
        : `नमस्ते! आपकी पसंद के अनुसार हमने ${topRec.data_snapshot.qualification.title} का चयन किया है।`;

    res.json({
      status: 'success',
      channel: 'whatsapp',
      incomingVoiceNote: {
        from: data.fromPhone,
        transcriptHeard: data.voiceNoteTranscript,
        detectedDialect: data.dialect,
      },
      outgoingBotResponse: {
        audioNoteUrl: `/api/static/audio/wa-response-${data.dialect}.mp3`,
        audioTranscript: replyAudioText,
        actionPills: [
          `1. View ${topRec.data_snapshot.qualification.title} Centres Near Me`,
          `2. Connect with ${data.district} Field Coordinator`,
          `3. Hear Detailed Explanation in Hindi`,
        ],
        attachment: {
          title: 'Livelihood-Summary-Card.pdf',
          qualification: topRec.data_snapshot.qualification.title,
          matchState: topRec.match_state,
          verifiedBatch: topRec.data_snapshot.opportunity?.centre_or_employer_name || 'Verification Pending',
        },
      },
    });
  };

  /**
   * IVR Telephony call simulator with DTMF keypad fallback
   */
  handleIvrCall = (req: Request, res: Response): void => {
    const data = ivrCallSchema.parse(req.body);

    let promptText = '';
    let nextStep = data.currentStep + 1;
    let completed = false;

    if (data.currentStep === 1) {
      promptText =
        'पीएम-अजय आजीविका सेवा में आपका स्वागत है। हिंदी के लिए 1 दबाएं, अवधी खातिर 2 दबाएं, भोजपुरी बदे 3 दबाएं।';
    } else if (data.currentStep === 2) {
      promptText =
        'अपनी पढ़ाई का स्तर बताएं। 5वीं पास के लिए 1, 8वीं पास के लिए 2, 10वीं पास के लिए 3 दबाएं, या बोलकर बताएं।';
    } else if (data.currentStep === 3) {
      promptText =
        'आप क्या काम सीखना चाहते हैं? सोलर बिजली के लिए 1, सिलाई के लिए 2, गाड़ी रिपेयर के लिए 3 दबाएं।';
    } else {
      promptText =
        'धन्यवाद! आपके उत्तर दर्ज कर लिए गए हैं। आपके नंबर पर प्रशिक्षण केंद्र की जानकारी का एसएमएस भेज दिया गया है।';
      completed = true;
      nextStep = data.currentStep;
    }

    res.json({
      channel: 'ivr',
      caller: data.callerNumber,
      currentStep: data.currentStep,
      nextStep,
      completed,
      twimlOrVoiceXml: `<Response><Say voice="alice" language="hi-IN">${promptText}</Say><Gather numDigits="1" action="/api/channels/ivr/simulate" method="POST"/></Response>`,
      spokenPrompt: promptText,
    });
  };
}
