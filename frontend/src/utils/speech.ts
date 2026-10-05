// Web Speech API and Web Audio synthesizer utilities for PM-AJAY SAHAYAK
import type { SupportedLocale } from '../lib/i18n/locales';
import { getVoiceCapability } from '../lib/i18n/voiceCapabilities';

export class SoundFX {
  private static ctx: AudioContext | null = null;

  private static getContext(): AudioContext {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    return this.ctx;
  }

  static playChime(type: 'start' | 'success' | 'click' | 'question') {
    try {
      const ctx = this.getContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;

      if (type === 'start') {
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.exponentialRampToValueAtTime(880, now + 0.15);
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
        osc.start(now);
        osc.stop(now + 0.3);
      } else if (type === 'success') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(523.25, now);
        osc.frequency.setValueAtTime(659.25, now + 0.1);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
        osc.start(now);
        osc.stop(now + 0.45);
      } else if (type === 'question') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, now);
        osc.frequency.exponentialRampToValueAtTime(739.99, now + 0.2);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      } else {
        osc.frequency.setValueAtTime(600, now);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
        osc.start(now);
        osc.stop(now + 0.08);
      }
    } catch {
      // Audio not permitted yet or not supported
    }
  }
}

let currentAudio: HTMLAudioElement | null = null;
let speechGeneration = 0;
let speechTimeout: ReturnType<typeof setTimeout> | null = null;
let speechPaused = false;
let timerAction: (() => void) | null = null;
let timerRemaining = 0;
let timerStarted = 0;
let resumeAction: (() => void) | null = null;
function armSpeechTimer(action: () => void, milliseconds: number) {
  if (speechTimeout) clearTimeout(speechTimeout);
  speechTimeout = null;
  timerAction = action; timerRemaining = milliseconds; timerStarted = Date.now();
  if (!speechPaused) speechTimeout = setTimeout(action, milliseconds);
}
export function pauseSpeaking() {
  if (speechPaused) return;
  speechPaused = true;
  if (speechTimeout) {
    clearTimeout(speechTimeout); speechTimeout = null;
    timerRemaining = Math.max(0, timerRemaining - (Date.now() - timerStarted));
  }
  currentAudio?.pause();
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.pause();
}
export function resumeSpeaking() {
  if (!speechPaused) return;
  speechPaused = false;
  if (timerAction) armSpeechTimer(timerAction, timerRemaining);
  resumeAction?.();
}
export function speakText(
  text: string,
  lang: SupportedLocale = 'en',
  onEnd?: () => void,
  onStart?: () => void
): boolean {
  stopSpeaking();
  const generation = speechGeneration;
  let ended = false;
  let fallbackStarted = false;
  const finish = () => {
    if (ended || generation !== speechGeneration) return;
    ended = true;
    if (speechTimeout) clearTimeout(speechTimeout);
    speechTimeout = null;
    timerAction = null; resumeAction = null;
    onEnd?.();
  };
  if (typeof window === 'undefined' || getVoiceCapability(lang).tts !== 'supported') {
    onStart?.(); finish();
    return false;
  }
  const fallback = () => {
    if (fallbackStarted || ended || generation !== speechGeneration) return;
    if (speechPaused) { resumeAction = fallback; return; }
    fallbackStarted = true;
    if (speechTimeout) clearTimeout(speechTimeout);
    if (currentAudio) {
      currentAudio.onended = null; currentAudio.onerror = null; currentAudio.onplaying = null;
      currentAudio.pause(); currentAudio = null;
    }
    if (!('speechSynthesis' in window)) { finish(); return; }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = `${lang}-IN`;
    utterance.rate = .95;
    utterance.onstart = () => {
      if (generation !== speechGeneration) return;
      if (speechPaused) window.speechSynthesis.pause();
      else onStart?.();
    };
    utterance.onend = finish;
    utterance.onerror = finish;
    resumeAction = () => window.speechSynthesis.resume();
    armSpeechTimer(() => { window.speechSynthesis.cancel(); finish(); }, 60000);
    window.speechSynthesis.resume();
    window.speechSynthesis.speak(utterance);
  };
  try {
    currentAudio = new Audio(`/api/v1/tts/generate?text=${encodeURIComponent(text)}&lang=${lang}`);
    currentAudio.onplaying = () => {
      if (generation !== speechGeneration) return;
      if (speechPaused) { currentAudio?.pause(); return; }
      armSpeechTimer(() => { currentAudio?.pause(); finish(); }, 60000);
      onStart?.();
    };
    currentAudio.onended = finish;
    currentAudio.onerror = fallback;
    resumeAction = () => { void currentAudio?.play().catch(fallback); };
    armSpeechTimer(fallback, 8000);
    void currentAudio.play().catch(fallback);
    return true;
  } catch { fallback(); return false; }
}

export function stopSpeaking() {
  speechGeneration++;
  if (speechTimeout) clearTimeout(speechTimeout);
  speechTimeout = null;
  speechPaused = false; timerAction = null; resumeAction = null;
  if (currentAudio) {
    currentAudio.onended = null; currentAudio.onerror = null; currentAudio.onplaying = null;
    currentAudio.pause();
    currentAudio.src = '';
    currentAudio = null;
  }
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}
