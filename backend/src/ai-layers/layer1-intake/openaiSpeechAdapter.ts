import OpenAI from 'openai';
import { ISpeechAdapter, TranscriptionResult, SynthesisResult } from './speechAdapter.js';
import { LanguageCode } from '../../types/index.js';
import { logger } from '../../utils/logger.js';
import { env } from '../../config/env.js';
import { toFile } from 'openai';

export class OpenAISpeechAdapter implements ISpeechAdapter {
  private openai: OpenAI;

  constructor() {
    this.openai = new OpenAI({
      apiKey: env.OPENAI_API_KEY,
    });
  }

  async transcribe(audioData: string | Buffer, preferredLang: LanguageCode): Promise<TranscriptionResult> {
    logger.info('OpenAISpeechAdapter: Transcribing audio input', { preferredLang });

    if (typeof audioData === 'string' && !audioData.startsWith('data:audio')) {
      // It's already text (fallback mode)
      return {
        text: audioData,
        confidence: 0.9,
        languageDetected: preferredLang,
        isAmbiguous: audioData.length < 4,
      };
    }

    try {
      let buffer: Buffer;
      let mimeType = 'audio/webm'; // Default assumption for web captures

      if (typeof audioData === 'string') {
        const matches = audioData.match(/^data:(audio\/[a-zA-Z0-9+-]+);base64,(.+)$/);
        if (matches && matches.length === 3) {
          mimeType = matches[1];
          buffer = Buffer.from(matches[2], 'base64');
        } else {
          throw new Error('Invalid base64 audio data');
        }
      } else {
        buffer = audioData;
      }

      // Convert buffer to OpenAI File object
      // Whisper expects a file with an extension, like .webm, .mp3, .wav
      const ext = mimeType.split('/')[1]?.split(';')[0] || 'webm';
      const file = await toFile(buffer, `speech.${ext}`, { type: mimeType });

      const response = await this.openai.audio.transcriptions.create({
        file,
        model: 'whisper-1',
        language: preferredLang,
        response_format: 'verbose_json',
      });

      const text = response.text || '';
      
      // Calculate a rough confidence / ambiguity metric based on length or whisper metadata if available
      // Whisper verbose JSON gives segment probabilities, but we can approximate it:
      const confidence = 0.85; // Default high confidence for successful whisper parsing
      const isAmbiguous = text.trim().length < 4;

      return {
        text,
        confidence,
        languageDetected: preferredLang,
        isAmbiguous,
      };

    } catch (error: any) {
      logger.error('OpenAISpeechAdapter: Transcription failed', error);
      throw error;
    }
  }

  async synthesize(text: string, lang: LanguageCode, gender: 'male' | 'female' = 'female'): Promise<SynthesisResult> {
    logger.info('OpenAISpeechAdapter: Synthesizing speech output', { lang, gender });

    try {
      const voice = gender === 'female' ? 'nova' : 'echo';

      const response = await this.openai.audio.speech.create({
        model: 'tts-1',
        voice,
        input: text,
      });

      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      const audioBase64 = `data:audio/mp3;base64,${buffer.toString('base64')}`;

      // Estimate duration based on text length (very rough)
      const durationSeconds = Math.max(1, Math.round(text.length / 15));

      return {
        audioBase64,
        mimeType: 'audio/mp3',
        durationSeconds,
      };
    } catch (error: any) {
      logger.error('OpenAISpeechAdapter: Synthesis failed', error);
      throw error;
    }
  }
}
