export type Profile = {
  district: string;
  block: string;
  education: string;
  interests: string[];
  traditional_or_existing_skills: string[];
  mobility: number | null;
  self_employment_or_wage_preference: string;
  current_work: string;
  access_needs: string;
};

export const EMPTY_PROFILE: Profile = {
  district: '', block: '', education: '', interests: [], traditional_or_existing_skills: [],
  mobility: null, self_employment_or_wage_preference: '', current_work: '', access_needs: '',
};

export const PROFILE_FIELDS: { key: keyof Profile; en: string; hi: string; optional?: boolean }[] = [
  { key: 'district', en: 'District', hi: 'जिला' },
  { key: 'block', en: 'Block', hi: 'ब्लॉक' },
  { key: 'education', en: 'Education', hi: 'शिक्षा' },
  { key: 'interests', en: 'Interests', hi: 'रुचियाँ' },
  { key: 'traditional_or_existing_skills', en: 'Existing skills', hi: 'मौजूदा कौशल', optional: true },
  { key: 'current_work', en: 'Current work', hi: 'वर्तमान काम', optional: true },
  { key: 'mobility', en: 'Travel radius', hi: 'यात्रा की सीमा' },
  { key: 'self_employment_or_wage_preference', en: 'Work preference', hi: 'काम की पसंद' },
  { key: 'access_needs', en: 'Accessibility needs', hi: 'पहुँच संबंधी ज़रूरतें', optional: true },
];

export function normalizeProfile(raw: Record<string, unknown>): Profile {
  const string = (key: string) => typeof raw[key] === 'string' ? raw[key] as string : '';
  const list = (key: string) => Array.isArray(raw[key]) ? (raw[key] as unknown[]).filter((v): v is string => typeof v === 'string') : [];
  return {
    district: string('district'), block: string('block'), education: string('education'),
    interests: list('interests'), traditional_or_existing_skills: list('traditional_or_existing_skills'),
    mobility: raw.mobility != null && Number.isFinite(Number(raw.mobility)) ? Number(raw.mobility) : null,
    self_employment_or_wage_preference: string('self_employment_or_wage_preference'),
    current_work: string('current_work'), access_needs: string('access_needs'),
  };
}

export function profileFromFields(fields: Record<string, { value: unknown }>) {
  return normalizeProfile(Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value])));
}

export function displayAnswer(profile: Profile, key: keyof Profile, hi = false): string {
  const value = profile[key];
  if (Array.isArray(value)) return value.join(', ');
  if (key === 'mobility') return value == null ? '' : `${value} ${hi ? 'किमी' : 'km'}`;
  if (key === 'self_employment_or_wage_preference') {
    return ({ wage: hi ? 'नौकरी' : 'A job', self_employment: hi ? 'स्वरोजगार' : 'Self-employment', both: hi ? 'दोनों के लिए तैयार' : 'Open to both' } as Record<string, string>)[String(value)] || '';
  }
  return value == null ? '' : String(value);
}

export function missingProfileFields(profile: Profile) {
  return PROFILE_FIELDS.filter(field => !field.optional && !displayAnswer(profile, field.key));
}
