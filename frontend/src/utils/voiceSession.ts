import { api } from '../lib/api';

export type VoiceState = 'paused' | 'listening' | 'thinking' | 'speaking' | 'connecting';

export function wavBlob(chunks: Float32Array[], sampleRate: number): Blob {
  const count = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const buffer = new ArrayBuffer(44 + count * 2);
  const view = new DataView(buffer);
  const word = (offset: number, value: string) => [...value].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  word(0, 'RIFF'); view.setUint32(4, 36 + count * 2, true); word(8, 'WAVE');
  word(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  word(36, 'data'); view.setUint32(40, count * 2, true);
  let offset = 44;
  for (const chunk of chunks) for (const sample of chunk) {
    const value = Math.max(-1, Math.min(1, sample));
    view.setInt16(offset, value * (value < 0 ? 32768 : 32767), true); offset += 2;
  }
  return new Blob([buffer], { type: 'audio/wav' });
}

export class VoiceSession {
  active = false;
  state: VoiceState = 'paused';
  slow = false;
  private stream?: MediaStream;
  private context?: AudioContext;
  private node?: AudioWorkletNode;
  private audio?: HTMLAudioElement;
  private releaseSpeech?: () => void;
  private speechVersion = 0;
  private chunks: Float32Array[] = [];
  private preRoll: Float32Array[] = [];
  private speakingMs = 0;
  private quietMs = 0;
  private durationMs = 0;
  private capturing = false;
  private generation = 0;
  constructor(
    private language: string,
    private onState: (state: VoiceState) => void,
    private onTurn: (text: string) => Promise<void>,
    private onError: (message: string) => void,
  ) {}
  setState(state: VoiceState) { this.state = state; this.onState(state); }
  async start() {
    const generation = ++this.generation;
    this.setState('connecting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: {echoCancellation: true, noiseSuppression: true, autoGainControl: true} });
      if (generation !== this.generation) { stream.getTracks().forEach(track => track.stop()); return; }
      this.stream = stream;
      this.context = new AudioContext({sampleRate: 16000});
      await this.context.audioWorklet.addModule('/voice-capture.js');
      if (generation !== this.generation) return;
      this.node = new AudioWorkletNode(this.context, 'voice-capture');
      this.context.createMediaStreamSource(stream).connect(this.node);
      this.node.connect(this.context.destination); // Worklet has silent output.
      this.node.port.onmessage = event => this.capture(event.data);
      await this.context.resume();
      this.active = true;
      this.setState('listening');
    } catch {
      this.pause();
      throw new Error('Microphone unavailable. Allow microphone access and use HTTPS or localhost.');
    }
  }
  private resetCapture() {
    this.chunks = []; this.preRoll = []; this.speakingMs = 0;
    this.quietMs = 0; this.durationMs = 0; this.capturing = false;
  }
  private capture(samples: Float32Array) {
    if (!this.active || !['listening', 'speaking'].includes(this.state)) return;
    const rate = this.context?.sampleRate || 16000;
    const ms = samples.length / rate * 1000;
    const rms = Math.sqrt(samples.reduce((sum, n) => sum + n * n, 0) / samples.length);
    this.preRoll.push(samples);
    while (this.preRoll.length * ms > 400) this.preRoll.shift();
    const threshold = this.state === 'speaking' ? 0.065 : 0.018;
    this.speakingMs = rms > threshold ? this.speakingMs + ms : 0;
    if (!this.capturing && this.speakingMs > (this.state === 'speaking' ? 300 : 120)) {
      this.interrupt();
      this.capturing = true; this.chunks = [...this.preRoll];
    } else if (this.capturing) this.chunks.push(samples);
    if (!this.capturing) return;
    this.durationMs += ms;
    this.quietMs = rms < 0.018 ? this.quietMs + ms : 0;
    if (this.quietMs > 1300 || this.durationMs > 25000) {
      const blob = wavBlob(this.chunks, rate);
      this.resetCapture(); this.setState('thinking');
      const generation = this.generation;
      void api.transcribeVoice(blob, this.language).then(async text => {
        if (this.active && generation === this.generation) await this.onTurn(text);
      }).catch(() => {
        if (generation === this.generation) this.onError(this.language === 'hi' ? 'आवाज़ समझ नहीं आई। कृपया फिर बोलें।' : 'I could not hear that clearly. Please try again.');
      }).finally(() => {
        if (this.active && this.state === 'thinking') this.setState('listening');
      });
    }
  }
  interrupt() {
    this.speechVersion++;
    this.audio?.pause(); this.audio = undefined;
    window.speechSynthesis?.cancel(); this.releaseSpeech?.(); this.releaseSpeech = undefined;
    if (this.active) this.setState('listening');
  }
  async say(text: string, deviceOnly = false): Promise<boolean> {
    if (!this.active) return false;
    this.interrupt(); this.resetCapture();
    const version = this.speechVersion;
    this.setState('thinking');
    let blob: Blob | null = null;
    if (!deviceOnly) {
      try { blob = await api.voiceAudio(text, this.language, this.slow); } catch { /* Try matching device voice. */ }
    }
    if (!this.active || version !== this.speechVersion) return false;
    this.setState('speaking');
    let completed = false;
    await new Promise<void>((resolve) => {
      let url: string | undefined;
      const finish = () => { if (url) URL.revokeObjectURL(url); this.releaseSpeech = undefined; resolve(); };
      this.releaseSpeech = finish;
      if (blob) {
        url = URL.createObjectURL(blob); this.audio = new Audio(url);
        this.audio.onended = () => { completed = true; finish(); };
        this.audio.onerror = () => { this.onError('Audio playback failed. Tap Repeat to try again.'); finish(); };
        void this.audio.play().catch(() => { this.onError('Tap Repeat to allow audio playback.'); finish(); });
      } else {
        if (!('speechSynthesis' in window)) { finish(); this.onError('No speech playback available on this device.'); return; }
        const voices = window.speechSynthesis.getVoices();
        const voice = voices.find(v => v.lang.startsWith(this.language));
        if (voices.length && !voice) { finish(); this.onError('No matching device voice. Configure cloud speech or install a voice for this language.'); return; }
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.language + '-IN'; utterance.rate = this.slow ? 0.75 : 0.95;
        if (voice) utterance.voice = voice;
        utterance.onend = () => { completed = true; finish(); };
        utterance.onerror = () => { finish(); if (this.active && version === this.speechVersion) this.onError('Speech stopped. Tap Repeat to hear the message.'); };
        window.speechSynthesis.speak(utterance);
      }
    });
    if (this.active && version === this.speechVersion) { this.resetCapture(); this.setState('listening'); }
    return completed && version === this.speechVersion;
  }
  pause() {
    this.active = false; this.generation++; this.interrupt();
    this.node?.disconnect(); this.node = undefined;
    this.stream?.getTracks().forEach(track => track.stop()); this.stream = undefined;
    void this.context?.close(); this.context = undefined;
    this.resetCapture(); this.setState('paused');
  }
}
