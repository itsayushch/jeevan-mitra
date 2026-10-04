import { SupportedLocale, isLocaleEnabled } from './locales';

export type VoiceCapabilityState = 'supported' | 'unsupported' | 'fallback';

export type VoiceCapability = {
  locale: SupportedLocale;
  stt: VoiceCapabilityState;
  tts: VoiceCapabilityState;
  message?: string;
};

export const VOICE_CAPABILITIES: Record<SupportedLocale, VoiceCapability> = {
  en: {
    locale: 'en',
    stt: 'supported',
    tts: 'supported',
  },
  hi: {
    locale: 'hi',
    stt: 'supported',
    tts: 'supported',
  },
  bn: {
    locale: 'bn',
    stt: 'unsupported',
    tts: 'unsupported',
    message: 'Voice input/output is currently available in Hindi and English.',
  },
  mr: {
    locale: 'mr',
    stt: 'unsupported',
    tts: 'unsupported',
    message: 'Voice input/output is currently available in Hindi and English.',
  },
  ta: {
    locale: 'ta',
    stt: 'unsupported',
    tts: 'unsupported',
    message: 'Voice input/output is currently available in Hindi and English.',
  },
};

export function getVoiceCapability(locale: SupportedLocale): VoiceCapability {
  if (VOICE_CAPABILITIES[locale]) {
    return VOICE_CAPABILITIES[locale];
  }
  return {
    locale,
    stt: 'unsupported',
    tts: 'unsupported',
    message: 'Voice interaction is not available for this locale.',
  };
}

export function isSpeechRecognitionSupported(locale: SupportedLocale): boolean {
  if (typeof window === 'undefined') return false;
  const SpeechRec =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!SpeechRec) return false;
  const cap = getVoiceCapability(locale);
  return cap.stt === 'supported';
}

export function isSpeechSynthesisSupported(locale: SupportedLocale): boolean {
  if (typeof window === 'undefined') return false;
  if (!('speechSynthesis' in window)) return false;
  const cap = getVoiceCapability(locale);
  return cap.tts === 'supported';
}
