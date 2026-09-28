"use client";
import { useRouter } from 'next/navigation';
import { FieldWorkerPortal } from '../../components/portals/FieldWorkerPortal';
export default function Page() { const router = useRouter(); return <div className="module-content"><FieldWorkerPortal onBack={() => router.push('/')} /></div>; }
