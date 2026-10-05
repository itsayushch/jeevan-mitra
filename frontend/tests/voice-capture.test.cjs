const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');
const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src/utils/speechCapture.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
function setup(options = {}) {
  let now = 0, volume = 128, next = 0, stopped = 0, closed = 0, complete = 0, resolvePermission;
  const frames = new Map(), errors = [], recordings = [];
  const stream = { getTracks: () => [{ stop: () => stopped++ }] };
  class AudioContext {
    state = 'running';
    resume() { return Promise.resolve(); }
    close() { this.state = 'closed'; closed++; return Promise.resolve(); }
    createMediaStreamSource() { return { connect() {}, disconnect() {} }; }
    createAnalyser() { return { fftSize: 2048, getByteTimeDomainData(samples) { samples.fill(volume); } }; }
  }
  class MediaRecorder {
    static isTypeSupported() { return true; }
    state = 'inactive'; mimeType = 'audio/webm;codecs=opus';
    start() { this.state = 'recording'; }
    stop() {
      this.state = 'inactive';
      queueMicrotask(() => {
        this.ondataavailable?.({ data: new Blob(['last audio chunk']) });
        this.onstop?.();
      });
    }
  }
  const env = { exports: {}, Error, Blob, Uint8Array, AudioContext, MediaRecorder,
    window: { isSecureContext: options.secure !== false },
    navigator: { mediaDevices: { getUserMedia: () => options.pending ? new Promise(r => resolvePermission = r)
      : options.denied ? Promise.reject(Object.assign(new Error(), { name: 'NotAllowedError' })) : Promise.resolve(stream) } },
    performance: { now: () => now }, setTimeout: () => 1, clearTimeout() {},
    requestAnimationFrame: cb => { frames.set(++next, cb); return next; }, cancelAnimationFrame: id => frames.delete(id) };
  vm.runInNewContext(code, env);
  return { exports: env.exports, stats: () => ({ stopped, closed, complete, errors, recordings }),
    start(record = false) { return env.exports.startSpeechCapture(() => complete++, e => errors.push(e.message), record ? audio => {
      assert.equal(stopped, 1, 'Release mic before returning audio');
      assert.equal(closed, 1, 'Close audio context before returning audio');
      recordings.push(audio);
    } : undefined); },
    tick(t, v) { now = t; volume = v; const callbacks = [...frames.values()]; frames.clear(); callbacks.forEach(cb => cb()); },
    resolvePermission() { resolvePermission(stream); } };
}
test('silence and a brief sound never fill a demo answer', async () => {
  const env = setup(); env.start(); await flush();
  env.tick(0,128); env.tick(5000,128); env.tick(6000,133); env.tick(6050,128); env.tick(9000,128);
  assert.equal(env.stats().complete,0);
});
test('speech must be followed by a full pause before microphone shutdown', async () => {
  const env = setup(); env.start(); await flush();
  [0,100,200,300].forEach(t=>env.tick(t,133)); env.tick(1499,128); await flush(); assert.equal(env.stats().complete,0);
  env.tick(1500,128); await flush(); assert.equal(env.stats().complete,1); assert.equal(env.stats().stopped,1);
});
test('recording includes the final chunk and returns audio after releasing mic', async () => {
  const env = setup(); env.start(true); await flush();
  [0,100,200,300].forEach(t=>env.tick(t,133)); env.tick(2100,128); await flush();
  assert.equal(await env.stats().recordings[0].text(),'last audio chunk'); assert.equal(env.stats().complete,1);
});

test('a short word with a brief gap between its sounds is captured after a pause', async () => {
  const env = setup(); env.start(true); await flush();
  env.tick(0,130); env.tick(35,130); env.tick(55,128); env.tick(90,130); env.tick(125,130);
  env.tick(1924,128); await flush(); assert.equal(env.stats().complete,0);
  env.tick(1925,128); await flush(); assert.equal(env.stats().recordings.length,1);
});

test('a single transient sound does not submit a recorded answer', async () => {
  const env = setup(); env.start(true); await flush();
  env.tick(0,133); env.tick(30,128); env.tick(2000,128); await flush();
  assert.equal(env.stats().recordings.length,0);
});
test('cancelling a recording never submits its audio', async () => {
  const env = setup(); const cancel = env.start(true); await flush(); cancel(); await flush();
  assert.equal(env.stats().recordings.length,0); assert.equal(env.stats().complete,0); assert.equal(env.stats().stopped,1);
});
test('permission resolved after cancellation releases the microphone', async () => {
  const env = setup({pending:true}); const cancel=env.start(true); await flush(); cancel();env.resolvePermission();await flush();
  assert.equal(env.stats().stopped,1);assert.equal(env.stats().complete,0);
});
test('permission denial and insecure origin give specific errors', async () => {
  const denied=setup({denied:true});denied.start();await flush();assert.match(denied.stats().errors[0],/permission was denied/);
  const insecure=setup({secure:false});insecure.start();await flush();assert.match(insecure.stats().errors[0],/HTTPS or localhost/);
});
