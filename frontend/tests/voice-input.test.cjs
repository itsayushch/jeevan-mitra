const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const path = require('node:path');
const transpile = file => ts.transpileModule(fs.readFileSync(path.join(__dirname,file),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
const turns={exports:{}};vm.runInNewContext(transpile('../src/utils/voiceTurn.ts'),turns);
const flush=async()=>{for(let i=0;i<20;i++)await Promise.resolve()};
function setup() {
  const captures=[], timers=new Map(), answers=[];let cleanup,resolveTranscript,nextTimer=0;
  const react={useState: initial=>[initial,()=>{}],useRef: value=>({current:value}),useEffect: action=>{cleanup=action()}};
  const requireMock=name=>{
    if(name==='react')return react;
    if(name.includes('voiceCapabilities'))return {getVoiceCapability:()=>({stt:'supported'})};
    if(name.includes('speechCapture'))return {startSpeechCapture:(complete,error,audio)=>{const capture={complete,error,audio,cancelled:false};captures.push(capture);return ()=>{capture.cancelled=true}}};
    if(name.includes('voiceTurn'))return turns.exports;
    if(name.includes('/api'))return {api:{transcribeAnswer:()=>new Promise(resolve=>resolveTranscript=resolve)}};
    throw new Error(name);
  };
  const context={exports:{},require:requireMock,Error,AbortController,MediaRecorder:function(){},window:{isSecureContext:true,speechSynthesis:{speaking:true}},navigator:{mediaDevices:{getUserMedia(){}}},setTimeout:cb=>{timers.set(++nextTimer,cb);return nextTimer},clearTimeout:id=>timers.delete(id)};
  vm.runInNewContext(transpile('../src/hooks/useVoiceInput.ts'),context);
  const hook=context.exports.useVoiceInput('en',text=>answers.push(text),'int_test','Which district do you live in?');
  return {hook,captures,answers,cleanup:()=>cleanup(),async transcribe(text){const c=captures.at(-1);c.audio({});c.complete();resolveTranscript(text);await flush()},resolvePending(text){resolveTranscript(text)},runTimers(){const callbacks=[...timers.values()];timers.clear();callbacks.forEach(cb=>cb())}};
}
test('microphone starts while assistant speech is playing',()=>{const env=setup();assert.equal(env.hook.start(),true);assert.equal(env.captures.length,1)});
test('assistant echo is ignored and microphone restarts without an answer',async()=>{const env=setup();env.hook.start();await env.transcribe('Which district do you live in?');assert.deepEqual(env.answers,[]);env.runTimers();assert.equal(env.captures.length,2)});
test('real interruption is delivered once after removing captured question',async()=>{const env=setup();env.hook.start();await env.transcribe('Which district do you live in? Moradabad.');assert.deepEqual(env.answers,['Moradabad'])});

test('both is delivered as a short answer even when the spoken question contains both',async()=>{
  const env=setup();env.hook.start('Would you prefer a job, self-employment, or both?');
  await env.transcribe('both');assert.deepEqual(env.answers,['both']);
});
test('pausing prevents a late transcription from submitting an answer',async()=>{const env=setup();env.hook.start();const c=env.captures[0];c.audio({});env.hook.stop();assert.equal(c.cancelled,true);env.resolvePending('Moradabad');await flush();env.cleanup();assert.deepEqual(env.answers,[])});
