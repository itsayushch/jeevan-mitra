import { Beneficiary, ProfileAnswer, Recommendation } from '../../types/index.js';

export interface FieldWorkerCaseSummary {
  caseId: string;
  beneficiaryName: string;
  districtAndBlock: string;
  threeLineBrief: string[];
  lowConfidenceFlags: Array<{
    field: string;
    value: string;
    confidence: number;
    recommendedVerification: string;
  }>;
  suggestedAction: string;
  recommendedPathwayPreview?: {
    tradeName: string;
    matchState: string;
    centreName?: string;
  };
}

export class FieldWorkerSummaryEngine {
  generateCaseSummary(params: {
    beneficiary: Beneficiary;
    profileAnswers: ProfileAnswer[];
    recommendations?: Recommendation[];
  }): FieldWorkerCaseSummary {
    const { beneficiary, profileAnswers, recommendations } = params;

    const answerMap: Record<string, ProfileAnswer> = {};
    for (const a of profileAnswers) {
      answerMap[a.field_name] = a;
    }

    const edu = answerMap['education_level']?.field_value || 'Not provided';
    const currWork = answerMap['current_work']?.field_value || 'Unemployed/Casual';
    const mobility = answerMap['mobility_radius_km']?.field_value || '10';
    const interests = answerMap['interests']?.field_value || 'Vocational';
    const pref = answerMap['work_preference']?.field_value || 'both';

    // 1. Generate 3-line case brief
    const line1 = `Candidate: ${beneficiary.name} (${beneficiary.gender}, ~${beneficiary.age || 22}y, SC) residing in ${beneficiary.block}, ${beneficiary.district}. Education: ${edu}.`;
    const line2 = `Background & Interests: Engaged in ${currWork}; keen on ${interests}. Mobility limit: ${mobility} km daily; preference: ${pref}.`;
    const line3 = recommendations && recommendations.length > 0
      ? `Top recommendation: ${recommendations[0].data_snapshot?.qualification?.title || 'Vocational Pathway'} (${recommendations[0].match_state}). Score: ${recommendations[0].score}/100.`
      : `Interview completed; awaiting grounded recommendation matching run.`;

    // 2. Identify low confidence flags
    const lowConfidenceFlags: FieldWorkerCaseSummary['lowConfidenceFlags'] = [];
    for (const ans of profileAnswers) {
      if (ans.confidence_score < 0.75 || ans.confirmation_status === 'unconfirmed') {
        let recommendedVerif = `Verify ${ans.field_name} during house visit or phone call`;
        if (ans.field_name === 'education_level') {
          recommendedVerif = 'Check 8th/10th marksheet or school certificate';
        } else if (ans.field_name === 'mobility_radius_km') {
          recommendedVerif = 'Confirm whether candidate can commute by bus or needs hostel';
        }

        lowConfidenceFlags.push({
          field: ans.field_name,
          value: ans.field_value,
          confidence: Math.round(ans.confidence_score * 100),
          recommendedVerification: recommendedVerif,
        });
      }
    }

    // 3. Suggested action for field worker
    let suggestedAction = 'Review transcript, verify low-confidence fields, and approve referral.';
    if (recommendations && recommendations.length > 0 && recommendations[0].match_state === 'Interest Match') {
      suggestedAction = 'Check if a mobile training unit or adjacent block batch can be sanctioned to convert Interest Match to Verified Match.';
    }

    return {
      caseId: beneficiary.id,
      beneficiaryName: beneficiary.name,
      districtAndBlock: `${beneficiary.district} / ${beneficiary.block}`,
      threeLineBrief: [line1, line2, line3],
      lowConfidenceFlags,
      suggestedAction,
      recommendedPathwayPreview: recommendations && recommendations.length > 0
        ? {
            tradeName: recommendations[0].data_snapshot?.qualification?.title,
            matchState: recommendations[0].match_state,
            centreName: recommendations[0].data_snapshot?.opportunity?.centre_or_employer_name,
          }
        : undefined,
    };
  }
}
