"use client";
import { JobPlacementMap } from '../../components/modules/JobPlacementMap';
import { useAppSettings } from '../../components/AppShell';
export default function Page() { const { language } = useAppSettings(); return <div className="module-content"><JobPlacementMap language={language} /></div>; }
