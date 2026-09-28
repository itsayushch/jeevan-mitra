"use client";
import { CareerPathways } from '../../components/modules/CareerPathways';
import { useAppSettings } from '../../components/AppShell';
export default function Page() { const { language } = useAppSettings(); return <div className="module-content"><CareerPathways language={language} /></div>; }
