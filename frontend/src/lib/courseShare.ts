import type { RecommendationItem } from './api';

export const REGISTER_URL = 'https://www.skillindiadigital.gov.in/home';

export function courseName(title: string, hi: boolean) {
  const names: Record<string, [string, string]> = {
    'Sewing Machine Operator': ['Learn sewing', 'सिलाई सीखें'],
    'Assistant Electrician (Domestic cum Industrial)': ['Learn electrical work', 'बिजली का काम सीखें'],
    'Paddy Cultivator': ['Learn paddy farming', 'धान की खेती सीखें'],
    'Pulses Cultivator': ['Learn pulses farming', 'दालों की खेती सीखें'],
    'Organic Grower': ['Learn organic farming', 'जैविक खेती सीखें'],
    'Small Poultry Farmer': ['Learn poultry farming', 'मुर्गी पालन सीखें'],
    'Quality Seed Grower': ['Learn seed growing', 'अच्छे बीज उगाना सीखें'],
  };
  return names[title]?.[hi ? 1 : 0] || title;
}

// Share catalogue IDs only: never include interview IDs, answers or credentials.
export function courseShareUrl(origin: string, courses: RecommendationItem[], language: string) {
  const ids = courses.map(course => course.qualification_id ||
    `nqr_${course.qualification.official_url.match(/\/qualifications\/(\d+)/)?.[1] || ''}`)
    .filter(id => /^nqr_\d+$/.test(id));
  if (!ids.length) throw new Error('No course link is available.');
  const url = new URL('/take-home', origin);
  url.searchParams.set('courses', [...new Set(ids)].join(','));
  url.searchParams.set('lang', language === 'hi' ? 'hi' : 'en');
  return url.toString();
}

export function sharedCourseIds(value: string) {
  return [...new Set(value.split(',').filter(id => /^nqr_\d{1,12}$/.test(id)))].slice(0, 10);
}
