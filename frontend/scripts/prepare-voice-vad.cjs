// Serve detection assets from this app so voice startup has no CDN dependency.
const fs = require('node:fs');
const path = require('node:path');
const target = path.resolve(__dirname, '../public/voice-vad');
fs.mkdirSync(target, {recursive:true});
for (const [packageName, files] of [
  ['@ricky0123/vad-web', ['silero_vad_v5.onnx', 'vad.worklet.bundle.min.js']],
  ['onnxruntime-web', ['ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs']],
]) {
  const source = path.dirname(require.resolve(packageName));
  for (const name of files) fs.copyFileSync(path.join(source, name), path.join(target, name));
}
