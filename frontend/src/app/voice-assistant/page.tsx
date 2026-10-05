"use client";
import { FlowContainer } from '../../components/flow/FlowContainer';
import { useAppSettings } from '../../components/AppShell';
import { useRouter } from 'next/navigation';
import { pathForSection } from '../../lib/routes';

export default function Page() {
  const { language, setLanguage } = useAppSettings();
  const router = useRouter();

  return (
    <FlowContainer
      mode="assistant"
      language={language}
      onSelectLanguage={setLanguage}
      onNavigateModule={key => router.push(pathForSection(key))}
    />
  );
}
