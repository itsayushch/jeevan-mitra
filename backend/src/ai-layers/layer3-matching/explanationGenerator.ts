import { Qualification, LocalOpportunity, MatchState, LanguageCode, ScoreBreakdown } from '../../types/index.js';

export interface GroundedExplanation {
  explanationText: string;
  audioExplanationScript: string;
  tradeoffSummary: string;
  skillGapSummary: string;
}

export class ExplanationGenerator {
  generateExplanation(params: {
    qualification: Qualification;
    opportunity?: LocalOpportunity | null;
    matchState: MatchState;
    scoreBreakdown: ScoreBreakdown;
    beneficiaryInterest: string[];
    beneficiarySkills: string[];
    lang?: LanguageCode;
  }): GroundedExplanation {
    const { qualification, opportunity, matchState, beneficiaryInterest, lang = 'hi' } = params;

    let explanationText = '';
    let audioExplanationScript = '';
    let tradeoffSummary = '';
    let skillGapSummary = '';

    const isVerified = matchState === 'Verified Match' && Boolean(opportunity);

    if (lang === 'hi') {
      if (isVerified && opportunity) {
        explanationText = `आपकी रुचि ${qualification.sector} और हुनर के आधार पर "${qualification.title}" का कोर्स आपके लिए सबसे उपयुक्त है। यह NSQF स्तर ${qualification.nsqf_level} का कोर्स है (अवधि: ${qualification.duration_hours} घंटे)। अच्छी बात यह है कि ${opportunity.centre_or_employer_name} (${opportunity.block}) में इसका नया बैच स्वीकृत है, जिसमें SC वर्ग के लिए सीटें उपलब्ध हैं।`;
        audioExplanationScript = `नमस्ते! आपकी पसंद के अनुसार ${qualification.title} का प्रशिक्षण आपके लिए बहुत अच्छा रहेगा। यह ${qualification.duration_hours} घंटे का सरकारी मान्यता प्राप्त कोर्स है। आपके नजदीकी केंद्र ${opportunity.centre_or_employer_name} में इसका नया बैच शुरू हो रहा है। आप इसके लिए सीधे आवेदन कर सकते हैं।`;
      } else {
        explanationText = `आपकी रुचि ${qualification.sector} के क्षेत्र में "${qualification.title}" (NSQF स्तर ${qualification.nsqf_level}, ${qualification.duration_hours} घंटे) से मेल खाती है। ध्यान दें: वर्तमान में आपके ब्लॉक में इस कोर्स का स्थानीय बैच जिला टीम द्वारा अभी सत्यापित नहीं हुआ है। हमारे फील्ड वर्कर जल्द ही इसकी उपलब्धता की जांच करेंगे।`;
        audioExplanationScript = `आपकी पसंद के अनुसार ${qualification.title} का कोर्स NQR रजिस्टर में मौजूद है। लेकिन अभी आपके गांव के पास इसका कोई नया बैच कन्फर्म नहीं है। इसलिए पहले फील्ड वर्कर इसकी जांच करेंगे, तब तक आप अन्य विकल्प भी देख सकते हैं।`;
      }

      tradeoffSummary =
        qualification.work_type === 'wage'
          ? `कंपनी में नियमित वेतन, लेकिन प्रतिदिन केंद्र या कार्यस्थल जाना होगा (${qualification.physical_intensity} शारीरिक श्रम)।`
          : qualification.work_type === 'self_employment'
          ? `घर या गांव से खुद की दुकान/काम शुरू करने की सुविधा, टूलकिट और सहायता उपलब्ध।`
          : `नौकरी और स्वरोजगार दोनों के बेहतर अवसर, स्थानीय बाजार में सतत मांग।`;

      skillGapSummary = `प्रारंभिक स्तर (Level ${qualification.nsqf_level}) से प्रमाणित कारीगर बनने के लिए ${Math.round(qualification.duration_hours / 30)} सप्ताह का व्यावहारिक अभ्यास जरूरी है।`;
    } else {
      if (isVerified && opportunity) {
        explanationText = `Based on your interest in ${qualification.sector}, "${qualification.title}" (NSQF Level ${qualification.nsqf_level}, ${qualification.duration_hours} hrs) is an excellent pathway. A verified live batch is currently open at ${opportunity.centre_or_employer_name} (${opportunity.block}) with reserved SC seats.`;
        audioExplanationScript = `Based on your answers, ${qualification.title} matches your profile. A confirmed batch is starting soon at ${opportunity.centre_or_employer_name}. You can request enrolment immediately.`;
      } else {
        explanationText = `"${qualification.title}" (NSQF Level ${qualification.nsqf_level}, ${qualification.duration_hours} hrs) aligns with your profile per official NQR standards. Note: A live local batch is not yet verified in your immediate block. A field counselor will investigate availability before enrolment.`;
        audioExplanationScript = `${qualification.title} fits your career aspirations, but local batch availability is currently unconfirmed in your block. A field worker will review this case.`;
      }

      tradeoffSummary =
        qualification.work_type === 'wage'
          ? `Steady contract wages with employer; requires daily commute (${qualification.physical_intensity} physical intensity).`
          : qualification.work_type === 'self_employment'
          ? `Home-based enterprise with government toolkit support; lower initial overhead.`
          : `Flexible pathway: can take up contractual roles or launch a micro-enterprise.`;

      skillGapSummary = `Requires ~${Math.round(qualification.duration_hours / 30)} weeks of hands-on practical training to achieve Level ${qualification.nsqf_level} industry certification.`;
    }

    return {
      explanationText,
      audioExplanationScript,
      tradeoffSummary,
      skillGapSummary,
    };
  }
}
