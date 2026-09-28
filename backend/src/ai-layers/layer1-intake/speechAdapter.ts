import { LanguageCode } from '../../types/index.js';
import { logger } from '../../utils/logger.js';

export interface TranscriptionResult {
  text: string;
  confidence: number;
  languageDetected: LanguageCode;
  isAmbiguous: boolean;
}

export interface SynthesisResult {
  audioBase64?: string;
  audioUrl?: string;
  mimeType: string;
  durationSeconds: number;
}

export interface ISpeechAdapter {
  transcribe(audioData: string | Buffer, preferredLang: LanguageCode): Promise<TranscriptionResult>;
  synthesize(text: string, lang: LanguageCode, gender?: 'male' | 'female'): Promise<SynthesisResult>;
}

/**
 * High-performance deterministic mock/synthetic speech adapter.
 * Ensures tests and zero-dependency deployments operate seamlessly without cloud billings.
 */
export class MockSpeechAdapter implements ISpeechAdapter {
  async transcribe(audioData: string | Buffer, preferredLang: LanguageCode): Promise<TranscriptionResult> {
    logger.debug('MockSpeechAdapter: Transcribing audio input', { preferredLang });

    // If audioData is already a text string (e.g. from simulator or text fallback), use it
    let recognizedText = typeof audioData === 'string' && !audioData.startsWith('data:')
      ? audioData
      : 'Main 10th pass hoon aur gaadi ya tractor repair ka kaam seekhna chahta hoon';

    let confidence = 0.92;
    let isAmbiguous = false;

    // Check if input is short or ambiguous
    if (recognizedText.trim().length < 4 || recognizedText.toLowerCase().includes('pata nahi')) {
      confidence = 0.55;
      isAmbiguous = true;
    }

    return {
      text: recognizedText,
      confidence,
      languageDetected: preferredLang,
      isAmbiguous,
    };
  }

  async synthesize(text: string, lang: LanguageCode, gender: 'male' | 'female' = 'female'): Promise<SynthesisResult> {
    logger.debug('MockSpeechAdapter: Synthesizing speech output', { lang, gender, textSnippet: text.slice(0, 40) });

    // Generates a mock standard data URL representation of audio
    const durationSeconds = Math.max(2, Math.round(text.length / 18));
    return {
      audioUrl: `/api/static/audio/mock-synthesized-${lang}-${gender}.mp3`,
      audioBase64: 'data:audio/mp3;base64,//uQZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAACcAA=',
      mimeType: 'audio/mpeg',
      durationSeconds,
    };
  }
}

/**
 * Factory to obtain the active Speech Adapter based on configuration
 */
export function getSpeechAdapter(): ISpeechAdapter {
  return new MockSpeechAdapter();
}
