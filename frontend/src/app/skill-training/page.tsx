"use client";
import { SkillTrainingModule } from '../../components/modules/SkillTrainingModule';
import { useAppSettings } from '../../components/AppShell';
export default function Page() { const { language } = useAppSettings(); return <div className="module-content"><SkillTrainingModule language={language} /></div>; }
