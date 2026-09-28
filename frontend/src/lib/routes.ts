export const sectionPaths = {
  home: '/',
  journey: '/journey',
  'voice-ask': '/voice-assistant',
  'jobs-map': '/opportunities',
  'training-quiz': '/skill-training',
  'career-pathways': '/career-pathways',
  'financial-grants': '/financial-support',
  'community-mentors': '/community',
  'field-worker': '/field-worker',
  'district-planner': '/district-planner',
} as const;

export type Section = keyof typeof sectionPaths;

export function pathForSection(section: string): string {
  return sectionPaths[section as Section] ?? '/';
}

export function sectionForPath(pathname: string): Section {
  return (Object.entries(sectionPaths).find(([, path]) => path === pathname)?.[0] ?? 'home') as Section;
}
