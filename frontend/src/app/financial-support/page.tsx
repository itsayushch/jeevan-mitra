"use client";
import { FinancialAidGrants } from '../../components/modules/FinancialAidGrants';
import { useAppSettings } from '../../components/AppShell';
export default function Page() { const { language } = useAppSettings(); return <div className="module-content"><FinancialAidGrants language={language} /></div>; }
