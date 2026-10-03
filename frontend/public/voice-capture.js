// Batch 64 ms at 16 kHz; transferable buffers keep work off the UI thread.
class VoiceCapture extends AudioWorkletProcessor {
  constructor() { super(); this.buffer = new Float32Array(1024); this.offset = 0; }
  process(inputs) {
    const samples = inputs[0]?.[0];
    if (samples) for (const sample of samples) {
      this.buffer[this.offset++] = sample;
      if (this.offset === this.buffer.length) {
        this.port.postMessage(this.buffer, [this.buffer.buffer]);
        this.buffer = new Float32Array(1024); this.offset = 0;
      }
    }
    return true;
  }
}
registerProcessor('voice-capture', VoiceCapture);
