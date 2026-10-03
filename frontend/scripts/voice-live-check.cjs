// Live cloud speech/Groq check against an isolated backend, with synthetic mic input.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
(async()=>{
  const backend=process.env.VOICE_TEST_BACKEND || 'http://127.0.0.1:4100';
  const hi=process.env.VOICE_TEST_LANGUAGE==='hi';
  const browser=await chromium.launch({headless:true,channel:'msedge',args:['--autoplay-policy=no-user-gesture-required']});
  try {
    const page=await browser.newPage();
    await page.addInitScript(({backend})=>{
      const NativeWebSocket=window.WebSocket;
      window.WebSocket=class extends NativeWebSocket {
        constructor(url,...rest){
          super(url.includes('/voice/stream')?backend.replace('http','ws')+'/api/v1/voice/stream':url,...rest);
          this.addEventListener('message',event=>{if(typeof event.data==='string'){
            const data=JSON.parse(event.data);window.voiceProtocol.push({direction:'in',type:data.type,id:data.id,message:data.message});
          }});
        }
        send(data){if(typeof data==='string'){
          const value=JSON.parse(data);window.voiceProtocol.push({direction:'out',type:value.type,id:value.id});
        }return super.send(data);}
      };
      navigator.mediaDevices.getUserMedia=async()=>{
        window.voiceTestContext=new AudioContext({sampleRate:16000});
        await window.voiceTestContext.resume();
        window.voiceTestDestination=window.voiceTestContext.createMediaStreamDestination();
        return window.voiceTestDestination.stream;
      };
      window.voiceEvents=[];
      window.voiceProtocol=[];
      const originalPlay=HTMLMediaElement.prototype.play;
      HTMLMediaElement.prototype.play=function(){
        this.addEventListener('playing',()=>window.voiceEvents.push({type:'playing',time:performance.now()}));
        this.addEventListener('ended',()=>window.voiceEvents.push({type:'ended',time:performance.now()}));
        return originalPlay.call(this);
      };
    },{backend});
    await page.route('**/api/v1/**', async route=>{
      const url=new URL(route.request().url());
      const response=await route.fetch({url:backend+url.pathname+url.search});
      await route.fulfill({response});
    });
    await page.goto(process.env.VOICE_TEST_URL || 'http://localhost:3100/voice-assistant');
    await page.getByRole('combobox',{name:'Conversation language'}).selectOption(hi?'hi':'en');
    await page.getByRole('button',{name:hi?'सहमत हैं · शुरू करें':'Agree & start',exact:true}).click();
    await page.waitForFunction(()=>window.voiceEvents.some(x=>x.type==='ended') || document.querySelector('[role=alert]'),{},{timeout:30000});
    await page.getByText(hi?'मैं सुन रहा हूँ':'I’m listening',{exact:true}).waitFor({timeout:30000});
    const greeting=await page.evaluate(()=>({events:window.voiceEvents,protocol:window.voiceProtocol,
      errors:[...document.querySelectorAll('[role=alert]')].map(x=>x.textContent)}));
    assert(greeting.events.some(x=>x.type==='ended'),'Real greeting must play completely: '+JSON.stringify(greeting));
    const start=Date.now();
    await page.evaluate(async({backend,hi,gain})=>{
      const response=await fetch(backend+'/api/v1/voice/speak',{
        method:'POST',headers:{'Content-Type':'application/json','X-Session-Token':sessionStorage.getItem('jm_session_token')},
        body:JSON.stringify({text:hi?'मैं सिलाई का काम करता हूँ और मुरादाबाद में रहता हूँ।':'I work as a tailor and live in Moradabad.',language:hi?'hi':'en'})
      });
      if(!response.ok)throw new Error('Synthetic speech generation failed');
      const context=new AudioContext();
      const decoded=await context.decodeAudioData(await response.arrayBuffer());
      const offline=new OfflineAudioContext(1,Math.ceil(decoded.duration*16000),16000);
      const source=offline.createBufferSource(); source.buffer=decoded; source.connect(offline.destination); source.start();
      const rendered=await offline.startRendering();
      await context.close();
      window.voiceEvents=[];
      const mic=window.voiceTestContext.createBufferSource();mic.buffer=rendered;
      const volume=window.voiceTestContext.createGain();volume.gain.value=gain;
      mic.connect(volume);volume.connect(window.voiceTestDestination);
      await new Promise(resolve=>{mic.onended=()=>{window.voiceSpeechEndedAt=performance.now();resolve();};mic.start();});
    },{backend,hi,gain:Number(process.env.VOICE_TEST_GAIN || 1)});
    try { await page.waitForFunction(()=>window.voiceEvents.some(x=>x.type==='ended'),{},{timeout:45000}); }
    catch(error){
      console.log(await page.evaluate(()=>({protocol:window.voiceProtocol,events:window.voiceEvents,
        errors:[...document.querySelectorAll('[role=alert]')].map(x=>x.textContent),status:document.querySelector('[role=status]')?.textContent})));
      throw error;
    }
    const result=await page.evaluate(()=>({
      responseAudioSeconds:Math.round((window.voiceEvents.find(x=>x.type==='playing').time-window.voiceSpeechEndedAt)/10)/100,
      errors:[...document.querySelectorAll('[role=alert]')].map(x=>x.textContent),
      caption:document.querySelector('section[aria-label="JeevanMitra voice assistant"]')?.innerText
    }));
    assert.equal(result.errors.length,0,JSON.stringify(result.errors));
    assert(!result.caption.includes(hi?'आप अभी क्या काम करते हैं?':'What work do you currently do?'),'Interviewer must advance');
    await page.getByRole('button',{name:hi?'रोकें':'Pause',exact:true}).click();
    console.log(JSON.stringify({pass:true,language:hi?'hi':'en',syntheticMic:true,cloudServices:true,responseAudioSeconds:result.responseAudioSeconds,totalCheckSeconds:(Date.now()-start)/1000}));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
