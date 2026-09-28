import { ExtractedBeneficiaryProfile, LanguageCode } from '../../types/index.js';

export interface ConfirmationReadback {
  spokenSummary: string;
  fieldsForReview: Array<{
    field: string;
    label: string;
    currentValue: string;
    isLowConfidence: boolean;
    confidence: number;
  }>;
}

export function generateProfileConfirmation(
  profile: ExtractedBeneficiaryProfile,
  lang: LanguageCode = 'hi'
): ConfirmationReadback {
  const fieldsForReview = [
    {
      field: 'district_and_block',
      label: lang === 'hi' ? 'जिला और ब्लॉक' : 'District & Block',
      currentValue: `${profile.district.value}, ${profile.block.value}`,
      isLowConfidence: !profile.district.confirmed || !profile.block.confirmed,
      confidence: Math.min(profile.district.confidence, profile.block.confidence),
    },
    {
      field: 'education_level',
      label: lang === 'hi' ? 'शिक्षा स्तर' : 'Education Level',
      currentValue: profile.education_level.value,
      isLowConfidence: !profile.education_level.confirmed,
      confidence: profile.education_level.confidence,
    },
    {
      field: 'interests',
      label: lang === 'hi' ? 'रुचि / पसंद' : 'Interests',
      currentValue: profile.interests.value.join(', '),
      isLowConfidence: !profile.interests.confirmed,
      confidence: profile.interests.confidence,
    },
    {
      field: 'mobility_radius_km',
      label: lang === 'hi' ? 'दूरी (आवागमन)' : 'Travel Radius',
      currentValue: `${profile.mobility_radius_km.value} km`,
      isLowConfidence: !profile.mobility_radius_km.confirmed,
      confidence: profile.mobility_radius_km.confidence,
    },
    {
      field: 'work_preference',
      label: lang === 'hi' ? 'काम की प्राथमिकता' : 'Work Preference',
      currentValue:
        profile.work_preference.value === 'self_employment'
          ? (lang === 'hi' ? 'खुद का स्वरोजगार' : 'Self-Employment')
          : profile.work_preference.value === 'wage'
          ? (lang === 'hi' ? 'कंपनी में नौकरी' : 'Wage Employment')
          : (lang === 'hi' ? 'दोनों चलेगा' : 'Both'),
      isLowConfidence: !profile.work_preference.confirmed,
      confidence: profile.work_preference.confidence,
    },
  ];

  let spokenSummary = '';
  if (lang === 'hi') {
    const prefStr =
      profile.work_preference.value === 'self_employment'
        ? 'खुद का स्वरोजगार'
        : profile.work_preference.value === 'wage'
        ? 'नौकरी'
        : 'काम';
    spokenSummary = `आपने बताया कि आप ${profile.block.value} के निवासी हैं, ${profile.education_level.value} तक पढ़े हैं, आपकी रुचि ${profile.interests.value[0] || 'हुनर'} में है, आप ${profile.mobility_radius_km.value} किमी तक जा सकते हैं और ${prefStr} चाहते हैं। क्या यह जानकारी सही है?`;
  } else {
    spokenSummary = `You confirmed: residing in ${profile.block.value}, education ${profile.education_level.value}, interest in ${profile.interests.value[0] || 'vocational skills'}, travel up to ${profile.mobility_radius_km.value} km, preferring ${profile.work_preference.value}. Is this correct?`;
  }

  return {
    spokenSummary,
    fieldsForReview,
  };
}
