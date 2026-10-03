// Audio stays in memory. The main thread sends only completed speech turns.
class VoiceCapture extends AudioWorkletProcessor {
  process(inputs) {
    const samples = inputs[0]?.[0];
    if (samples) this.port.postMessage(samples.slice());
    return true;
  }
}
registerProcessor('voice-capture', VoiceCapture);
