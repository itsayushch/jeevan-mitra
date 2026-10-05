// Detect a spoken utterance followed by a pause. Recording is optional for demo login.
export class SpeechPauseDetector {
  private startedAt: number | null = null;
  private lastSoundAt: number | null = null;
  private heardSpeech = false;
  constructor(private pauseMs = 1200, private threshold = 0.018, private minimumSpeechMs = 200, private soundGapMs = 180) {}

  update(level: number, now: number): boolean {
    if (level >= this.threshold) {
      this.startedAt ??= now;
      this.lastSoundAt = now;
      if (now - this.startedAt >= this.minimumSpeechMs) this.heardSpeech = true;
    } else if (this.lastSoundAt === null || now - this.lastSoundAt > this.soundGapMs) {
      // Brief gaps between consonants/vowels belong to the same word.
      this.startedAt = null;
    }
    return this.heardSpeech && this.lastSoundAt !== null && now - this.lastSoundAt >= this.pauseMs;
  }
}

export function startSpeechCapture(onComplete: () => void, onError: (error: Error) => void, onAudio?: (audio: Blob) => void): () => void {
  let cancelled = false;
  let finishing = false;
  let stream: MediaStream | undefined;
  let context: AudioContext | undefined;
  let source: MediaStreamAudioSourceNode | undefined;
  let frame = 0;
  let timeout: ReturnType<typeof setTimeout> | undefined;
  let recorder: MediaRecorder | undefined;
  const chunks: Blob[] = [];

  const cleanup = async () => {
    cancelAnimationFrame(frame);
    clearTimeout(timeout);
    if (recorder && recorder.state !== 'inactive') recorder.stop();
    stream?.getTracks().forEach(track => track.stop());
    source?.disconnect();
    if (context && context.state !== 'closed') await context.close().catch(() => {});
  };
  const finish = async (error?: Error) => {
    if (cancelled || finishing) return;
    finishing = true;
    if (!error && recorder && recorder.state !== 'inactive') {
      await new Promise<void>(resolve => { recorder!.onstop = () => resolve(); recorder!.stop(); });
    }
    await cleanup();
    if (!cancelled) {
      if (error) onError(error);
      else {
        if (onAudio) onAudio(new Blob(chunks, { type: recorder?.mimeType || 'audio/webm' }));
        onComplete();
      }
    }
  };

  void (async () => {
    try {
      if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        throw new Error('Microphone access requires HTTPS or localhost. You can still type your answer.');
      }
      // Resume during the button gesture, before waiting for microphone permission.
      context = new AudioContext();
      await context.resume();
      if (cancelled) return;
      const captured = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      if (cancelled) {
        captured.getTracks().forEach(track => track.stop());
        return;
      }
      stream = captured;
      if (onAudio) {
        const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'].find(type => MediaRecorder.isTypeSupported(type));
        recorder = new MediaRecorder(stream, mimeType ? { mimeType, audioBitsPerSecond: 64000 } : undefined);
        recorder.ondataavailable = event => { if (!cancelled && event.data.size) chunks.push(event.data); };
        recorder.onerror = () => void finish(new Error('Microphone recording failed. Please try again or type your answer.'));
        recorder.start(250);
      }
      source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 2048;
      source.connect(analyser);
      const samples = new Uint8Array(analyser.fftSize);
      // Give conversational answers room for breaths and brief thinking pauses.
      const detector = onAudio ? new SpeechPauseDetector(1800, 0.009, 80) : new SpeechPauseDetector();
      timeout = setTimeout(() => void finish(new Error('No speech detected. Check the microphone, then try again or type your answer.')), 60000);
      const listen = () => {
        if (cancelled || finishing) return;
        analyser.getByteTimeDomainData(samples);
        let energy = 0;
        for (const sample of samples) energy += ((sample - 128) / 128) ** 2;
        if (detector.update(Math.sqrt(energy / samples.length), performance.now())) {
          void finish();
        } else frame = requestAnimationFrame(listen);
      };
      frame = requestAnimationFrame(listen);
    } catch (error) {
      const name = error instanceof Error ? error.name : '';
      const message = name === 'NotAllowedError'
        ? 'Microphone permission was denied. Allow microphone access, then tap the mic again or type your answer.'
        : name === 'NotFoundError'
          ? 'No microphone was found. Connect a microphone or type your answer.'
          : name === 'NotReadableError'
            ? 'The microphone is unavailable or in use. Try again or type your answer.'
            : error instanceof Error ? error.message : 'Unable to open the microphone. Please try again or type your answer.';
      await finish(new Error(message));
    }
  })();

  return () => {
    cancelled = true;
    void cleanup();
  };
}
