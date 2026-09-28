"use client";
import { AskQuestionVoice } from '../../components/modules/AskQuestionVoice';
import { useAppSettings } from '../../components/AppShell';
export default function Page() { const { language } = useAppSettings(); return <AskQuestionVoice language={language} />; }
