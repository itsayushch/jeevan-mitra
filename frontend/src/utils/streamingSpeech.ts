/** MPEG streaming playback. Completion means the user heard the entire prompt. */
export class StreamingSpeech {
  private audio = new Audio();
  private media?: MediaSource;
  private source?: SourceBuffer;
  private queue: ArrayBuffer[] = [];
  private chunks: ArrayBuffer[] = [];
  private ended = false;
  private stopped = false;
  private url = '';
  private timer: ReturnType<typeof setTimeout>;
  private resolve!: (completed: boolean) => void;
  readonly done: Promise<boolean>;
  constructor(private mime: string, private onPlaying: () => void, private onError: (message: string) => void) {
    this.done = new Promise(resolve => { this.resolve = resolve; });
    this.timer = setTimeout(() => this.fail(), 60000);
    this.audio.onended = () => this.finish(true);
    this.audio.onerror = () => this.fail();
    this.audio.onplaying = () => { if (!this.stopped) this.onPlaying(); };
    if (typeof MediaSource !== 'undefined' && MediaSource.isTypeSupported(mime)) {
      this.media = new MediaSource();
      this.url = URL.createObjectURL(this.media);
      this.audio.src = this.url;
      this.media.addEventListener('sourceopen', () => {
        if (this.stopped || !this.media) return;
        try {
          this.source = this.media.addSourceBuffer(mime);
          this.source.addEventListener('updateend', () => this.pump());
          this.source.addEventListener('error', () => this.fail());
          this.pump();
        } catch { this.fail(); }
      }, {once: true});
      void this.audio.play().catch(() => this.fail());
    }
  }
  append(bytes: ArrayBuffer) {
    if (this.stopped) return;
    if (this.media) { this.queue.push(bytes); this.pump(); }
    else this.chunks.push(bytes);
  }
  end() {
    if (this.stopped) return;
    this.ended = true;
    if (this.media) this.pump();
    else {
      if (!this.chunks.length) { this.fail(); return; }
      this.url = URL.createObjectURL(new Blob(this.chunks, {type: this.mime}));
      this.audio.src = this.url;
      this.chunks = [];
      void this.audio.play().catch(() => this.fail());
    }
  }
  private pump() {
    if (this.stopped || !this.source || this.source.updating || this.media?.readyState !== 'open') return;
    try {
      const bytes = this.queue.shift();
      if (bytes) this.source.appendBuffer(bytes);
      else if (this.ended) this.media.endOfStream();
    } catch { this.fail(); }
  }
  private fail() { if (!this.stopped) this.onError('Speech playback failed. Tap Repeat to retry.'); this.finish(false); }
  cancel() { this.finish(false); }
  private finish(completed: boolean) {
    if (this.stopped) return;
    this.stopped = true;
    clearTimeout(this.timer);
    this.audio.onended = this.audio.onerror = this.audio.onplaying = null;
    this.audio.pause(); this.audio.removeAttribute('src'); this.audio.load();
    if (this.url) URL.revokeObjectURL(this.url);
    this.queue = []; this.chunks = [];
    this.resolve(completed);
  }
}
