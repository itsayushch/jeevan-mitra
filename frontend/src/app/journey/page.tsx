"use client";
import { useRouter } from 'next/navigation';
import { FlowContainer } from '../../components/flow/FlowContainer';
import { useAppSettings } from '../../components/AppShell';
import { pathForSection } from '../../lib/routes';
export default function Page() { const router = useRouter(); const { language, setLanguage, viewMode } = useAppSettings(); return <div className={viewMode === 'kiosk' ? 'journey-compact' : ''}><FlowContainer mode="journey" language={language} onSelectLanguage={setLanguage} onNavigateModule={section => router.push(pathForSection(section))} /></div>; }
