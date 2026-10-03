const ts = require('typescript');
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const compiled = ts.transpileModule(fs.readFileSync('src/utils/voiceSession.ts','utf8'),
  {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
class StreamingSpeech {
  constructor(){ this.done = new Promise(resolve=>this.resolve=resolve); }
  append(){} end(){this.resolve(true);} cancel(){this.resolve(false);}
}
const sandbox = {exports:{},require:name=>name.includes('streamingSpeech')?{StreamingSpeech}:{api:{}},
  ArrayBuffer,DataView,Float32Array,Math,Promise,Map,setTimeout,clearTimeout,setInterval,clearInterval,performance,WebSocket:{OPEN:1}};
vm.runInNewContext(compiled,sandbox);
const {VoiceSession,pcmFrame} = sandbox.exports;
const tick = () => new Promise(resolve=>setImmediate(resolve));
(async()=>{
  const messages=[],turns=[],errors=[];
  const voice=new VoiceSession('en',()=>{},async text=>turns.push(text),error=>errors.push(error));
  voice.active=true; voice.ready=true;
  voice.context={sampleRate:16000,close:async()=>{}};
  voice.socket={readyState:1,bufferedAmount:0,send:value=>messages.push(value),close(){}};
  voice.setState('listening');
  const silence=new Float32Array(1024),speech=new Float32Array(1024).fill(0.1);
  for(let i=0;i<30;i++)voice.capture(silence);
  assert.equal(messages.length,0,'Silence must never be sent');
  for(let i=0;i<8;i++)voice.capture(speech);
  assert(messages.some(item=>item instanceof ArrayBuffer),'PCM must stream before silence ends');
  assert.equal(await voice.say('An old reply'),false,'A reply cannot reset microphone capture');
  for(let i=0;i<10;i++)voice.capture(silence);
  const commands=()=>messages.filter(x=>typeof x==='string').map(JSON.parse);
  const id=commands().find(x=>x.type==='turn_end').id;
  voice.receive({type:'transcript',id,text:'My answer'}); await tick();
  assert.deepEqual(turns,['My answer']);
  const playing=voice.say('Please confirm the details.');
  const old=voice.speechId;
  voice.receive({type:'speech_start',id:old,mime:'audio/mpeg'});
  voice.setState('speaking');
  for(let i=0;i<4;i++)voice.capture(speech);
  assert.equal(await playing,false,'Interrupted summaries must not count as fully heard');
  voice.receive({type:'speech_end',id:old});
  assert.equal(voice.capturing,true,'Late audio must not terminate a new answer');
  const count=messages.length;
  voice.pause();
  for(let i=0;i<30;i++)voice.capture(speech);
  assert.equal(messages.length,count+1,'Pause sends only interrupt then discards input');
  const view=new DataView(pcmFrame(new Float32Array([0,-1,1]),9));
  assert.equal(view.getUint32(0,true),9); assert.equal(view.getInt16(6,true),-32768);
  assert.equal(errors.length,0);
  const quietVoice=new VoiceSession('en',()=>{},async()=>{},()=>{});
  quietVoice.active=true; quietVoice.ready=true; quietVoice.socket={readyState:1,bufferedAmount:0,send(){},close(){}};
  quietVoice.context={sampleRate:16000,close:async()=>{}};
  for(let i=0;i<5;i++)quietVoice.capture(new Float32Array(512).fill(0.003),0.95);
  assert.equal(quietVoice.capturing,true,'Neural speech probability must recognize low-volume voices');
  quietVoice.finishTurn();
  assert.equal(quietVoice.state,'recognizing','Manual finish must submit without waiting indefinitely');
  quietVoice.interrupt();
  assert.equal(quietVoice.state,'recognizing','An interrupt must not pretend pending recognition is idle');
  quietVoice.pause();
  console.log('PASS: silence, streaming PCM, endpointing, stale replies, interruption guard, pause.');
})().catch(error=>{console.error(error);process.exitCode=1;});
