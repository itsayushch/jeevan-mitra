"use client";
import { VoiceAgent } from '../../components/modules/VoiceAgent';
import { useAppSettings } from '../../components/AppShell';
export default function Page() {
  const { language, setLanguage } = useAppSettings();
  return <VoiceAgent language={language} onLanguage={setLanguage} />;
}
