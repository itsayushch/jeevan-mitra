import { Beneficiary, Qualification, LocalOpportunity, LanguageCode } from '../../types/index.js';

export interface DraftNotification {
  channel: 'sms' | 'whatsapp';
  recipientPhone: string;
  templateName: string;
  messageText: string;
  requiresWorkerApproval: boolean;
}

export class OutboundMessagingDraftEngine {
  draftReferralConfirmation(params: {
    beneficiary: Beneficiary;
    qualification: Qualification;
    opportunity: LocalOpportunity;
    workerName: string;
    lang?: LanguageCode;
  }): {
    smsDraft: DraftNotification;
    whatsappDraft: DraftNotification;
  } {
    const { beneficiary, qualification, opportunity, workerName, lang = 'hi' } = params;
    const phone = beneficiary.phone || 'N/A';

    let smsText = '';
    let waText = '';

    if (lang === 'hi') {
      smsText = `PM-AJAY सूचना: नमस्ते ${beneficiary.name}! आपका नामांकन "${qualification.title}" हेतु ${opportunity.centre_or_employer_name} में अग्रसारित किया गया है। बैच तिथि: ${opportunity.batch_start_date}। समन्वयक: ${workerName}।`;
      waText = `*PM-AJAY आजीविका मित्र (सत्यापित)*\n\nनमस्ते ${beneficiary.name} जी,\n\nआपकी काउंसिलिंग के आधार पर आपके प्रशिक्षण बैच की पुष्टि हो गई है:\n• *कोर्स:* ${qualification.title} (NSQF L${qualification.nsqf_level})\n• *केंद्र:* ${opportunity.centre_or_employer_name}\n• *पता:* ${opportunity.address}\n• *बैच प्रारंभ:* ${opportunity.batch_start_date}\n• *सुविधाएं:* निःशुल्क टूल-किट, वजीफा एवं हॉस्टल\n\nकिसी भी सहायता के लिए अपने ग्राम समन्वयक ${workerName} से संपर्क करें।`;
    } else {
      smsText = `PM-AJAY Notice: Hello ${beneficiary.name}, your nomination for "${qualification.title}" at ${opportunity.centre_or_employer_name} is approved. Batch starts: ${opportunity.batch_start_date}. Coordinator: ${workerName}.`;
      waText = `*PM-AJAY Livelihood Assistant (Verified)*\n\nDear ${beneficiary.name},\n\nYour training referral is verified:\n• Course: ${qualification.title} (NSQF Level ${qualification.nsqf_level})\n• Centre: ${opportunity.centre_or_employer_name}\n• Address: ${opportunity.address}\n• Batch Starts: ${opportunity.batch_start_date}\n• Entitlements: Free toolkit, stipend, and hostel\n\nFor assistance, contact coordinator ${workerName}.`;
    }

    return {
      smsDraft: {
        channel: 'sms',
        recipientPhone: phone,
        templateName: 'pmajay_referral_confirmation_sms',
        messageText: smsText,
        requiresWorkerApproval: true,
      },
      whatsappDraft: {
        channel: 'whatsapp',
        recipientPhone: phone,
        templateName: 'pmajay_referral_confirmation_wa',
        messageText: waText,
        requiresWorkerApproval: true,
      },
    };
  }
}
