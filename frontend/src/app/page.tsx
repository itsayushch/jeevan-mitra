"use client";
import { useRouter } from 'next/navigation';
import { Overview } from '../components/Overview';
import { useAppSettings } from '../components/AppShell';
import { pathForSection } from '../lib/routes';
export default function Page() { const router = useRouter(); const { language } = useAppSettings(); return <Overview language={language} onNavigate={section => router.push(pathForSection(section))} />; }
