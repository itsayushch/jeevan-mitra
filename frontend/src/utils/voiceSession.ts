import { api } from '../lib/api';
import { StreamingSpeech } from './streamingSpeech';
import type { MicVAD } from '@ricky0123/vad-web';

export type VoiceState = 'paused' | 'listening' | 'recording' | 'recognizing' | 'thinking' | 'buffering' | 'speaking' | 'connecting';
export type MicrophoneInfo = {label: string; status: 'ready' | 'silent' | 'muted' | 'suspended' | 'stalled'};

// Generation-tagged PCM frames follow the RealtimeVoiceChat transport pattern.
export function pcmFrame(samples: Float32Array, id: number): ArrayBuffer {
  const buffer = new ArrayBuffer(4 + samples.length * 2);
  const view = new DataView(buffer);
  view.setUint32(0, id, true);
  samples.forEach((sample, i) => {
    const value = Math.max(-1, Math.min(1, sample));
    view.setInt16(4 + i * 2, value * (value < 0 ? 32768 : 32767), true);
  });
  return buffer;
}

export class VoiceSession {
  active = false;
  state: VoiceState = 'paused';
  slow = false;
  private stream?: MediaStream;
  private context?: AudioContext;
  private vad?: MicVAD;
  private inputSource?: MediaStreamAudioSourceNode;
  private inputMeter?: AnalyserNode;
  private silentOutput?: GainNode;
  private watchdog?: ReturnType<typeof setInterval>;
  private lastFrame = 0;
  private lastMeter = 0;
  private lastInput = 0;
  private inputLabel = 'Microphone';
  private inputStatus?: MicrophoneInfo['status'];
  private manualCapture = false;
  private processingTurns = 0;
  private socket?: WebSocket;
  private playback?: StreamingSpeech;
  private releaseSpeech?: (completed: boolean) => void;
  private ready = false;
  private serial = 0;
  private speechId = 0;
  private turnId = 0;
  private waitingTurns = new Map<number, ReturnType<typeof setTimeout>>();
  private speechTimer?: ReturnType<typeof setTimeout>;
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
    private onLevel: (level: number) => void = () => {},
    private options: {deviceId?: string; onMicrophone?: (info: MicrophoneInfo) => void} = {},
  ) {}
  private reportInput(status: MicrophoneInfo['status']) {
    if (status === this.inputStatus) return;
    this.inputStatus = status;
    this.options.onMicrophone?.({label: this.inputLabel, status});
  }
  private checkInput() {
    if (!this.active || !this.ready) return;
    const now = performance.now();
    const track = this.stream?.getAudioTracks()[0];
    if (track?.muted || track?.enabled === false) { this.reportInput('muted'); return; }
    if (this.context?.state === 'suspended') {
      this.reportInput('suspended');
      void this.context.resume().catch(() => {});
      return;
    }
    if (this.inputMeter) {
      const input = new Float32Array(this.inputMeter.fftSize);
      this.inputMeter.getFloatTimeDomainData(input);
      const rms = Math.sqrt(input.reduce((sum, n) => sum + n * n, 0) / input.length);
      this.onLevel(Math.min(1, rms * 35));
      if (rms > 0.0001) this.lastInput = now;
    }
    if (now - this.lastFrame > 5000) this.reportInput('stalled');
    else this.reportInput(now - this.lastInput > 10000 ? 'silent' : 'ready');
  }
  setState(state: VoiceState) { this.state = state; this.onState(state); }
  async start() {
    const generation = ++this.generation;
    this.setState('connecting');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({audio: {channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true,
        ...(this.options.deviceId ? {deviceId: {exact: this.options.deviceId}} : {})}});
      if (generation !== this.generation) { stream.getTracks().forEach(track => track.stop()); return; }
      this.stream = stream;
      this.context = new AudioContext({sampleRate: 16000});
      await this.context.resume();
      this.inputLabel = stream.getAudioTracks()[0].label || 'Microphone';
      // Keep a rendered, muted input path and meter the device independently of VAD.
      this.inputSource = this.context.createMediaStreamSource(stream);
      this.inputMeter = this.context.createAnalyser(); this.inputMeter.fftSize = 1024;
      this.silentOutput = this.context.createGain(); this.silentOutput.gain.value = 0;
      this.inputSource.connect(this.inputMeter).connect(this.silentOutput).connect(this.context.destination);
      const {MicVAD} = await import('@ricky0123/vad-web/dist/real-time-vad');
      const vad = await MicVAD.new({
        model: 'v5', startOnLoad: false, audioContext: this.context,
        baseAssetPath: '/voice-vad/', onnxWASMBasePath: '/voice-vad/',
        ortConfig: ort => { ort.env.wasm.numThreads = 1; },
        getStream: async () => stream, pauseStream: async () => {},
        onFrameProcessed: (probabilities, frame) => this.capture(frame, probabilities.isSpeech),
      });
      if (generation !== this.generation) { await vad.destroy(); return; }
      this.vad = vad;
      this.active = true;
      this.lastFrame = this.lastInput = performance.now();
      await vad.start();
      if (generation !== this.generation) { await vad.destroy(); return; }
      this.reportInput('ready');
      stream.getAudioTracks()[0].onended = () => { if (this.active) { this.onError('Microphone disconnected. Reconnect it and tap Resume.'); this.pause(); } };
      this.watchdog = setInterval(() => this.checkInput(), 100);
    } catch (cause) {
      this.pause();
      throw new Error(cause instanceof Error && cause.name === 'NotAllowedError'
        ? 'Microphone access was denied. Allow microphone access and try again.'
        : 'Could not start the microphone and speech detector. Check your input device and reload.');
    }
  }
  /** Call after session credentials and processing consent are recorded. */
  async connect() {
    const generation = this.generation;
    const url = process.env.NEXT_PUBLIC_VOICE_WS_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/v1/voice/stream`;
    const socket = new WebSocket(url);
    this.socket = socket; socket.binaryType = 'arraybuffer';
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => { socket.close(); reject(new Error('Voice connection timed out. Please resume to retry.')); }, 12000);
      const fail = () => { clearTimeout(timer); reject(new Error('Voice connection failed. Check the backend WebSocket connection.')); };
      // MicVAD resamples frames to 16 kHz even when the device uses another rate.
      socket.onopen = () => socket.send(JSON.stringify({type: 'auth', token: api.getSessionToken(), language: this.language, sample_rate: 16000}));
      socket.onerror = fail;
      socket.onclose = () => { fail(); if (this.active && generation === this.generation) { this.onError('Voice disconnected. Tap Resume to reconnect.'); this.pause(); } };
      socket.onmessage = event => {
        if (!this.active || generation !== this.generation) return;
        if (typeof event.data === 'string') {
          const data = JSON.parse(event.data);
          if (data.type === 'ready') { clearTimeout(timer); this.ready = true; this.setState('listening'); resolve(); }
          else this.receive(data);
        } else {
          const buffer = event.data as ArrayBuffer;
          if (buffer.byteLength >= 4 && new DataView(buffer).getUint32(0, true) === this.speechId) this.playback?.append(buffer.slice(4));
        }
      };
    });
  }
  private send(data: object) { if (this.ready && this.socket?.readyState === WebSocket.OPEN) this.socket.send(JSON.stringify(data)); }
  private receive(data: {type: string; id?: number; text?: string; mime?: string; message?: string}) {
    if (data.type === 'transcript' && data.id !== undefined && this.waitingTurns.has(data.id)) {
      clearTimeout(this.waitingTurns.get(data.id)); this.waitingTurns.delete(data.id);
      const generation = this.generation;
      this.processingTurns++; this.setState('thinking');
      void this.onTurn(data.text || '').catch(() => this.onError('Could not process your answer. Please repeat.')).finally(() => {
        this.processingTurns--;
        if (this.active && generation === this.generation && !this.releaseSpeech) this.settleState();
      });
    } else if (data.type === 'speech_start' && data.id === this.speechId) {
      this.setState('buffering');
      this.playback = new StreamingSpeech(data.mime || 'audio/mpeg', () => this.setState('speaking'), this.onError);
      const id = this.speechId;
      void this.playback.done.then(completed => { if (id === this.speechId) this.finishSpeech(completed); });
    } else if (data.type === 'speech_end' && data.id === this.speechId) this.playback?.end();
    else if (data.type === 'error' && (data.id === undefined || data.id === this.speechId || (data.id !== undefined && this.waitingTurns.has(data.id)))) {
      this.onError(data.message || 'Voice unavailable. Please try again.');
      if (data.id !== undefined) { clearTimeout(this.waitingTurns.get(data.id)); this.waitingTurns.delete(data.id); }
      if (data.id === this.speechId) { this.playback?.cancel(); this.finishSpeech(false); }
      if (this.active) this.settleState();
    }
  }
  private resetCapture() {
    this.preRoll = []; this.speakingMs = 0; this.quietMs = 0; this.durationMs = 0; this.capturing = false; this.manualCapture = false;
  }
  private sendSamples(samples: Float32Array) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    if (this.socket.bufferedAmount > 512000) { this.onError('The connection is too slow for live audio. Please reconnect.'); this.pause(); return; }
    this.socket.send(pcmFrame(samples, this.turnId));
  }
  private capture(samples: Float32Array, speechProbability?: number) {
    this.lastFrame = performance.now();
    const rms = Math.sqrt(samples.reduce((sum, n) => sum + n * n, 0) / samples.length);
    if (rms > 0.0001) this.lastInput = this.lastFrame;
    if (!this.inputMeter && this.lastFrame - this.lastMeter >= 100) {
      this.lastMeter = this.lastFrame; this.onLevel(Math.min(1, rms * 35));
    }
    if (!this.active || !this.ready || this.state === 'connecting') return;
    const ms = samples.length / 16000 * 1000;
    this.preRoll.push(samples);
    while (this.preRoll.length * ms > 320) this.preRoll.shift();
    const playing = this.state === 'speaking';
    const speech = speechProbability === undefined ? rms > (playing ? 0.055 : 0.015)
      : speechProbability >= (playing ? 0.8 : 0.55);
    this.speakingMs = speech ? this.speakingMs + ms : Math.max(0, this.speakingMs - ms);
    if (!this.capturing && this.speakingMs >= (playing ? 250 : 128)) {
      this.interrupt();
      this.capturing = true; this.turnId = ++this.serial;
      this.setState('recording');
      this.send({type: 'turn_start', id: this.turnId});
      this.preRoll.forEach(chunk => this.sendSamples(chunk));
    } else if (this.capturing) this.sendSamples(samples);
    if (!this.capturing) return;
    this.durationMs += ms;
    const quiet = speechProbability === undefined ? rms < 0.015 : speechProbability < 0.35;
    this.quietMs = quiet ? this.quietMs + ms : 0;
    // Allow pauses within speech while removing the previous 1.3 s fixed delay.
    if ((!this.manualCapture && this.quietMs >= (this.slow ? 1000 : 480)) || this.durationMs >= 25000) {
      const id = this.turnId;
      this.send({type: 'turn_end', id});
      this.resetCapture(); this.setState('recognizing');
      this.waitingTurns.set(id, setTimeout(() => {
        this.waitingTurns.delete(id); this.onError('Recognition timed out. Please repeat.');
        if (this.active && !this.releaseSpeech) this.settleState();
      }, 35000));
    }
  }
  private finishSpeech(completed: boolean) {
    clearTimeout(this.speechTimer);
    const release = this.releaseSpeech; this.releaseSpeech = undefined;
    release?.(completed);
    if (this.active) this.settleState();
  }
  private settleState() {
    this.setState(this.capturing ? 'recording' : this.waitingTurns.size ? 'recognizing' : this.processingTurns ? 'thinking' : 'listening');
  }
  finishTurn() {
    if (this.capturing) { this.manualCapture = false; this.quietMs = 1200; this.capture(new Float32Array(512), 0); }
  }
  startAnswer() {
    if (!this.active || !this.ready || this.capturing || this.waitingTurns.size || this.processingTurns) return;
    void this.context?.resume().catch(() => {});
    this.interrupt(); this.resetCapture();
    this.capturing = this.manualCapture = true; this.turnId = ++this.serial;
    this.send({type: 'turn_start', id: this.turnId}); this.setState('recording');
  }
  interrupt() {
    this.speechId = ++this.serial;
    this.send({type: 'interrupt', id: this.speechId});
    this.playback?.cancel(); this.playback = undefined;
    this.finishSpeech(false);
  }
  async say(text: string): Promise<boolean> {
    if (!this.active || !this.ready) return false;
    // A previous LLM reply must not reset an answer currently being recorded.
    if (this.capturing || this.waitingTurns.size) return false;
    this.interrupt(); this.resetCapture();
    const id = this.speechId;
    this.setState('buffering');
    const done = new Promise<boolean>(resolve => { this.releaseSpeech = resolve; });
    this.speechTimer = setTimeout(() => { if (id === this.speechId) { this.onError('Speech timed out. Tap Repeat to retry.'); this.interrupt(); } }, 60000);
    this.send({type: 'speak', id, text, slow: this.slow});
    return done;
  }
  pause() {
    this.active = false; this.generation++; this.interrupt();
    this.ready = false; this.socket?.close(); this.socket = undefined;
    this.waitingTurns.forEach(timer => clearTimeout(timer)); this.waitingTurns.clear();
    clearInterval(this.watchdog);
    void this.vad?.destroy().catch(() => {}); this.vad = undefined;
    this.inputSource?.disconnect(); this.inputSource = undefined;
    this.inputMeter?.disconnect(); this.inputMeter = undefined;
    this.silentOutput?.disconnect(); this.silentOutput = undefined;
    this.stream?.getTracks().forEach(track => track.stop()); this.stream = undefined;
    void this.context?.close(); this.context = undefined;
    this.resetCapture(); this.onLevel(0); this.setState('paused');
  }
}
