const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');
function load(file, globals = {}) {
  const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../src', file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const context = { exports: {}, ...globals }; vm.runInNewContext(code, context); return context.exports;
}
function storage(entries) {
  const map = new Map(Object.entries(entries));
  return { get length() { return map.size; }, key: index => [...map.keys()][index], getItem: key => map.get(key) || null,
    setItem: (key, value) => map.set(key, value), removeItem: key => map.delete(key) };
}
test('finish clears app credentials and help state but preserves unrelated storage and backend records', () => {
  const sessionStorage = storage({ jm_session_token: 'secret', jm_session_id: 'session', jm_jwt_token: 'jwt', jm_worker_key: 'worker', jm_officer_key: 'officer', 'jeevanmitra:help:interview': 'case', unrelated: 'keep' });
  const localStorage = storage({ jm_jwt_token: 'jwt', 'jeevanmitra.locale': 'hi', unrelated: 'keep' });
  let requests = 0;
  const { api } = load('lib/api.ts', { window: { sessionStorage, localStorage }, fetch: () => { requests++; } });
  assert.equal(api.getSessionToken(), 'secret');
  api.clearKioskSession();
  assert.equal(api.getSessionToken(), null); assert.equal(api.getSessionId(), null);
  assert.equal(api.getJwtToken(), null); assert.equal(api.getOfficerKey(), null);
  assert.equal(sessionStorage.length, 1); assert.equal(localStorage.length, 1);
  assert.equal(sessionStorage.getItem('unrelated'), 'keep'); assert.equal(requests, 0);
});
test('take-home URL includes only public course IDs and selected language, never private answers or tokens', () => {
  const { courseShareUrl, sharedCourseIds } = load('lib/courseShare.ts', { URL });
  const rec = { qualification_id: 'nqr_10422', recommendation_id: 'secret-rec', qualification: { title: 'Sewing', official_url: 'https://www.nqr.gov.in/qualifications/10422' }, profile: { phone: '9876543210' } };
  const url = new URL(courseShareUrl('https://example.org', [rec, rec], 'hi'));
  assert.equal(url.pathname, '/take-home'); assert.equal(url.searchParams.get('courses'), 'nqr_10422');
  assert.equal(url.searchParams.get('lang'), 'hi'); assert.equal([...url.searchParams].length, 2);
  assert.equal(url.toString().includes('secret'), false); assert.equal(url.toString().includes('9876543210'), false);
  assert.deepEqual(Array.from(sharedCourseIds('nqr_10422,../../../secret,nqr_10422,nqr_14080')), ['nqr_10422', 'nqr_14080']);
});
function speechHarness() {
  let now = 0; let timerId = 0; const timers = new Map(); const audios = []; const utterances = [];
  const synth = { pauses: 0, resumes: 0, cancels: 0, pause() { this.pauses++; }, resume() { this.resumes++; }, cancel() { this.cancels++; }, speak(u) { utterances.push(u); u.onstart?.(); } };
  class Audio { constructor() { audios.push(this); this.paused = true; } play() { this.paused = false; this.onplaying?.(); return Promise.resolve(); } pause() { this.paused = true; } }
  const exports = load('utils/speech.ts', { window: { speechSynthesis: synth }, Audio, SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    require: () => ({ getVoiceCapability: () => ({ tts: 'supported' }) }), Date: { now: () => now },
    setTimeout: (action, ms) => { const id = ++timerId; timers.set(id, { action, deadline: now + ms }); return id; }, clearTimeout: id => timers.delete(id) });
  function advance(ms) { now += ms; for (const [id, timer] of [...timers]) { if (timer.deadline <= now && timers.has(id)) { timers.delete(id); timer.action(); } } }
  return { ...exports, audios, synth, utterances, advance };
}
test('pausing narration suspends timeout and resuming continues audio rather than skipping a course', () => {
  const h = speechHarness(); let ended = 0;
  h.speakText('Course one', 'en', () => ended++);
  h.pauseSpeaking(); h.advance(120000);
  assert.equal(ended, 0); assert.equal(h.audios[0].paused, true);
  h.resumeSpeaking(); assert.equal(h.audios[0].paused, false);
  h.audios[0].onended(); assert.equal(ended, 1);
});
test('fallback speech can pause/resume and stop invalidates stale completion callbacks', () => {
  const h = speechHarness(); let ended = 0;
  h.speakText('Course one', 'hi', () => ended++); h.audios[0].onerror();
  assert.equal(h.utterances.length, 1);
  h.pauseSpeaking(); h.advance(120000); assert.equal(ended, 0);
  h.resumeSpeaking(); assert.ok(h.synth.resumes > 1);
  const oldEnd = h.utterances[0].onend; h.stopSpeaking(); oldEnd();
  assert.equal(ended, 0);
});
