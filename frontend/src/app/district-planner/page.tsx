"use client";
import { useRouter } from 'next/navigation';
import { DistrictPlannerConsole } from '../../components/portals/DistrictPlannerConsole';
export default function Page() { const router = useRouter(); return <div className="module-content"><DistrictPlannerConsole onBack={() => router.push('/')} /></div>; }
