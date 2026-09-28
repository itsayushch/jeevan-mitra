"use client";
import { CommunityMentorship } from '../../components/modules/CommunityMentorship';
import { useAppSettings } from '../../components/AppShell';
export default function Page() { const { language } = useAppSettings(); return <div className="module-content"><CommunityMentorship language={language} /></div>; }
