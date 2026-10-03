// Browser workflow check with mocked audio devices and backend. No paid API calls.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({headless: true, channel: process.env.PLAYWRIGHT_CHANNEL || 'msedge',args:['--autoplay-policy=no-user-gesture-required']});
  try {
    const page = await browser.newPage({viewport: {width: 1280, height: 900}});
    await page.addInitScript(() => {
      // Credentials saved before switching from a remote DB must be renewed.
      sessionStorage.setItem('jm_session_token', 'old-remote-token');
      sessionStorage.setItem('jm_session_id', 'old-remote-session');
      sessionStorage.setItem('jm_voice_interview', 'old-remote-interview');
      navigator.mediaDevices.getUserMedia = async () => {
        window.voiceTestContext=new AudioContext({sampleRate:16000});
        await window.voiceTestContext.resume();
        window.voiceTestDestination=window.voiceTestContext.createMediaStreamDestination();
        return window.voiceTestDestination.stream;
      };
      // Exercise the WebSocket protocol while keeping this workflow test offline.
      window.MediaSource = undefined;
      window.Audio = class {
        play(){ setTimeout(()=>{this.onplaying?.(); this.onended?.();},15); return Promise.resolve(); }
        pause(){} load(){} removeAttribute(){}
      };
      window.WebSocket = class {
        static OPEN=1; readyState=1;
        constructor(){setTimeout(()=>this.onopen?.(),0);}
        send(raw){
          if(typeof raw!=='string')return;
          const data=JSON.parse(raw);
          if(data.type==='auth') setTimeout(()=>this.onmessage?.({data:JSON.stringify({type:'ready'})}),0);
          if(data.type==='turn_end') setTimeout(()=>this.onmessage?.({data:JSON.stringify({type:'transcript',id:data.id,text:'Actually I can travel three kilometres.'})}),0);
          if(data.type==='speak') setTimeout(()=>{
            this.onmessage?.({data:JSON.stringify({type:'speech_start',id:data.id,mime:'audio/mpeg'})});
            const bytes=new ArrayBuffer(8); new DataView(bytes).setUint32(0,data.id,true);
            this.onmessage?.({data:bytes});
            this.onmessage?.({data:JSON.stringify({type:'speech_end',id:data.id})});
          },0);
        }
        close(){}
      };
      window.speechSynthesis.speak = utterance => setTimeout(() => utterance.onend?.(), 15);
      window.speechSynthesis.cancel = () => {};
      window.speechSynthesis.getVoices = () => [];
    });
    const profile = {district: 'Malda', block: 'English Bazar', education: 'Class 10', interests: ['Repair'], mobility: 5, self_employment_or_wage_preference: 'wage'};
    let status = 'collecting', confirmations = 0, referrals = 0, turns = 0, sessions = 0;
    await page.route('**/api/v1/**', async route => {
      const url = new URL(route.request().url());
      let body = {}, code = 200;
      if (url.pathname.endsWith('/consents/old-remote-session')) {code=403; body={detail:'Consent history does not belong to caller'};}
      else if (url.pathname.endsWith('/sessions')) {sessions++; body = {session_id: 's1', session_token: 'token', expires_at: '2099-01-01'}; code = 201;}
      else if (url.pathname.endsWith('/consents')) code = 201;
      else if (url.pathname.endsWith('/interviews/start')) {body = {interview_id: 'i1', language: 'en'}; code = 201;}
      else if (url.pathname.endsWith('/voice/speak')) {await route.fulfill({status:204}); return;}
      else if (url.pathname.endsWith('/turns')) {
        turns++; status='awaiting_confirmation';
        if(turns===1) await new Promise(resolve=>setTimeout(resolve,5000));
        else profile.mobility=3;
        body={inferred_profile:profile,is_final:true,next_question:'Please confirm.'};
      }
      else if (url.pathname.endsWith('/confirm-profile')) {confirmations++; status='ready_for_matching'; body={status};}
      else if (url.pathname.endsWith('/interviews/i1')) body={status, language:'en',last_question:'What work do you do?',fields:Object.fromEntries(Object.entries(profile).map(([key,value])=>[key,{value}]))};
      else if (url.pathname.endsWith('/recommendations/generate')) body={recommendations:[{recommendation_id:'r1',qualification:{title:'Machine repair',nsqf_level:3},why_recommended:['Matches your interest in repair.'],local_availability:{status:'unknown'},caveat:'Admission is not guaranteed.'}]};
      else if (url.pathname.endsWith('/referrals/me')) body=[{id:'case1',interview_id:'i1',status:'new'}];
      else if (url.pathname.endsWith('/referrals')) {referrals++; body={referral_id:'case1'}; code=201;}
      else throw new Error('Unexpected API request '+url.pathname);
      await route.fulfill({status:code,contentType:'application/json',body:JSON.stringify(body)});
    });
    await page.goto(process.env.VOICE_TEST_URL || 'http://localhost:3100/voice-assistant');
    await page.getByRole('combobox', {name:'Conversation language'}).selectOption('en');
    await page.getByRole('button', {name:'Agree & start',exact:true}).click();
    await page.getByRole('button',{name:'Use keyboard',exact:true}).click();
    async function send(text) {
      await page.getByText('I’m listening',{exact:true}).waitFor();
      await page.getByRole('textbox',{name:'Your answer'}).fill(text);
      await page.getByRole('button',{name:'Send',exact:true}).click();
    }
    await send('I studied class 10 and want machine repair work.');
    // Barge in during the pending HTTP interview request. The answer must queue.
    await page.evaluate(async bytes=>{
      const audio=await window.voiceTestContext.decodeAudioData(new Uint8Array(bytes).buffer);
      const source=window.voiceTestContext.createBufferSource();source.buffer=audio;
      source.connect(window.voiceTestDestination);
      await new Promise(resolve=>{source.onended=resolve;source.start();});
    },[...fs.readFileSync('scripts/fixtures/voice-answer.mp3')]);
    await page.getByText('Check what I heard',{exact:true}).waitFor();
    await page.getByText(/You can travel 3 kilometres/).waitFor();
    assert.equal(confirmations,0);
    await send('yes');
    await page.getByText('Ready to explore',{exact:true}).waitFor();
    await send('yes');
    await page.getByRole('heading',{name:'Machine repair',exact:true}).waitFor();
    await send('help');
    await page.getByText('Your permission',{exact:true}).waitFor();
    assert.equal(referrals,0);
    await send('yes');
    await page.getByText('Your next step is recorded',{exact:true}).waitFor();
    await send('status');
    await page.getByText('Your request is waiting for review.',{exact:true}).waitFor();
    assert.equal(confirmations,1); assert.equal(referrals,1); assert.equal(turns,2); assert.equal(sessions,1);
    await page.getByRole('button',{name:'Pause',exact:true}).click();
    await page.getByText('Ready when you are',{exact:true}).waitFor();
    fs.mkdirSync('output',{recursive:true});
    await page.screenshot({path:'output/voice-agent-desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'output/voice-agent-mobile.png',fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth),true);
    console.log('PASS: stale session renewal, neural VAD, queued interruption during Groq request, confirmation, referral consent, pause, mobile overflow. Cloud audio and API mocked.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error); process.exitCode=1;});
