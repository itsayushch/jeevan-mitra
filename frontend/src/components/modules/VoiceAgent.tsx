'use client';
import { useEffect, useRef, useState } from 'react';
import { Mic, Pause, Play, RotateCcw, Volume2, Keyboard, PhoneOff, Waves } from 'lucide-react';
import { api, type ConversationProfile, type RecommendationItem } from '../../lib/api';
import { VoiceSession, type VoiceState } from '../../utils/voiceSession';
import type { Language } from '../../types';
import styles from './VoiceAgent.module.css';

type Phase = 'interview' | 'review' | 'offer' | 'options' | 'referral' | 'done';
const YES = /^(yes|yes please|yes correct|correct|that is correct|confirm|okay|ok|हाँ|हां|हाँ सही है|सही है|जी|जी हाँ|जी हां|ठीक है)[.!।\s]*$/i;
const NO = /^(no|no thanks|नहीं|नही)[.!।\s]*$/i;
const KEY = 'jm_voice_interview';

export function VoiceAgent({language, onLanguage}: {language: Language; onLanguage: (language: Language) => void}) {
  const hi = language === 'hi';
  const [state, setState] = useState<VoiceState>('paused');
  const [started, setStarted] = useState(false);
  const [caption, setCaption] = useState('');
  const [error, setError] = useState('');
  const [draft, setDraft] = useState('');
  const [typing, setTyping] = useState(false);
  const [options, setOptions] = useState<RecommendationItem[]>([]);
  const [index, setIndex] = useState(0);
  const [phaseView, setPhaseView] = useState<Phase>('interview');
  const engine = useRef<VoiceSession | null>(null);
  const phase = useRef<Phase>('interview');
  const interview = useRef('');
  const profile = useRef<ConversationProfile>({});
  const choices = useRef<RecommendationItem[]>([]);
  const choiceIndex = useRef(0);
  const lastSpeech = useRef('');
  const heardPrompt = useRef(false);
  const processing = useRef(false);
  const mounted = useRef(true);
  const handler = useRef<(text: string) => Promise<void>>(async () => {});
  const t = (en: string, hindi: string) => hi ? hindi : en;
  const move = (value: Phase) => { phase.current = value; setPhaseView(value); heardPrompt.current = false; };
  async function say(text: string) {
    lastSpeech.current = text; setCaption(text); heardPrompt.current = false;
    const completed = await engine.current?.say(text);
    if (completed) heardPrompt.current = true;
  }
  const reviewText = () => {
    const p = profile.current;
    const work = p.self_employment_or_wage_preference === 'wage' ? t('a job', 'नौकरी') : p.self_employment_or_wage_preference === 'self_employment' ? t('self-employment', 'स्वरोजगार') : t('either kind of work', 'दोनों तरह का काम');
    return t(`You live in ${p.block}, ${p.district}. Your education is ${p.education}. You want to learn ${(p.interests || []).join(', ')}. You can travel ${p.mobility} kilometres and prefer ${work}. Your current work is ${p.current_work || 'not specified'}. Existing skills: ${(p.traditional_or_existing_skills || []).join(', ') || 'not specified'}. Access needs: ${p.access_needs || 'not specified'}. Is this correct? Say yes, or tell me what to change.`,
      `आप ${p.district} के ${p.block} में रहते हैं। आपकी पढ़ाई ${p.education} है। आपकी रुचि ${(p.interests || []).join(', ')} में है। आप ${p.mobility} किलोमीटर जा सकते हैं और ${work} पसंद करते हैं। आपका वर्तमान काम ${p.current_work || 'नहीं बताया'} है। मौजूदा कौशल ${(p.traditional_or_existing_skills || []).join(', ') || 'नहीं बताए'} हैं। सहायता की ज़रूरत ${p.access_needs || 'नहीं बताई'} है। क्या यह सही है? हाँ कहें या बदलाव बताएं।`);
  };
  async function describeOption() {
    const rec = choices.current[choiceIndex.current];
    if (!rec) { await say(t('No matching pathways were found. Say help to request a counselor.', 'अभी कोई उपयुक्त विकल्प नहीं मिला। सलाहकार के लिए मदद कहें।')); return; }
    const availability = rec.local_availability.status === 'verified_open'
      ? t('A local opportunity is verified. Admission still needs confirmation.', 'स्थानीय अवसर सत्यापित है। प्रवेश की पुष्टि अभी बाकी है।')
      : t('A local batch has not been confirmed.', 'स्थानीय बैच की पुष्टि नहीं हुई है।');
    await say(t(`Option ${choiceIndex.current + 1}: ${rec.qualification.title}. ${rec.why_recommended.slice(0, 1).join(' ')} ${availability} Say next for another option, or help to talk to a counselor.`,
      `विकल्प ${choiceIndex.current + 1}: ${rec.qualification.title}। ${availability} अगला विकल्प सुनने के लिए अगला, या सलाहकार के लिए मदद कहें।`));
  }
  async function handle(text: string) {
    if (processing.current) return;
    processing.current = true; setError(''); setDraft('');
    try {
      const input = text.trim();
      if (/^(stop|pause|रुको|रुकिए|बंद करो|बंद)[.!।\s]*$/i.test(input)) { engine.current?.pause(); return; }
      if (/^(repeat|again|दोबारा|फिर से|दोबारा बताओ)[.!।\s]*$/i.test(input)) { await say(lastSpeech.current); return; }
      if (/^(slow|slower|speak slowly|धीरे|धीरे बोलो)[.!।\s]*$/i.test(input)) { if (engine.current) engine.current.slow = true; await say(lastSpeech.current); return; }
      if (/^(status|my status|request status|स्थिति|मेरी स्थिति)[.!।\s]*$/i.test(input)) {
        if (['review', 'offer', 'referral'].includes(phase.current)) { await say(lastSpeech.current); return; }
        const requests = await api.getMyReferrals();
        const request = requests.find(item => item.interview_id === interview.current);
        const names: Record<string, string> = {new: t('waiting for review', 'समीक्षा की प्रतीक्षा में'), assigned: t('assigned to a counselor', 'सलाहकार को सौंपा गया'), contacted: t('contacted', 'संपर्क किया गया'), enrolled: t('enrolled', 'नामांकन हो गया'), in_progress: t('in progress', 'प्रगति पर'), completed: t('completed', 'पूरा हो गया'), dropped_out: t('discontinued', 'बंद हुआ'), documents_verified: t('documents verified', 'दस्तावेज़ सत्यापित')};
        await say(request ? t(`Your request is ${names[request.status] || request.status}.`, `आपका अनुरोध ${names[request.status] || request.status} है।`) : t('No counselor request is recorded for this interview. Say help to request support.', 'इस बातचीत के लिए सलाहकार अनुरोध दर्ज नहीं है। सहायता के लिए मदद कहें।'));
        return;
      }
      if (/^(help|counselor|मदद|सहायता|सलाहकार)[.!।\s]*$/i.test(input)) {
        move('referral');
        await say(t('May I share your profile with a counselor and send a help request? Say yes to send, or no to cancel.', 'क्या मैं आपकी जानकारी सलाहकार के साथ साझा करके मदद का अनुरोध भेजूँ? भेजने के लिए हाँ, या रद्द करने के लिए नहीं कहें।')); return;
      }
      if (['review', 'offer', 'referral'].includes(phase.current) && YES.test(input) && !heardPrompt.current) {
        await say(lastSpeech.current); return;
      }
      if (phase.current === 'referral') {
        if (NO.test(input)) { move(choices.current.length ? 'options' : 'interview'); await say(t('Cancelled. We can continue. Tell me what you would like to do.', 'रद्द कर दिया। हम आगे बात कर सकते हैं। बताइए।')); return; }
        if (!YES.test(input)) { await say(lastSpeech.current); return; }
        const prior = sessionStorage.getItem(`${KEY}_referral_${interview.current}`);
        if (!prior) {
          await api.recordConsent('counselor_referral', true, language);
          const response = await api.createReferral(interview.current, 'user_requested_human_help', choices.current[choiceIndex.current]?.recommendation_id, `voice-help-${interview.current}`);
          sessionStorage.setItem(`${KEY}_referral_${interview.current}`, response.referral_id);
        }
        move('done'); await say(t('Your request has been recorded. A counselor can review your case. You can pause the conversation now.', 'आपका अनुरोध दर्ज हो गया है। सलाहकार आपकी जानकारी देख सकेंगे। आप अब बातचीत रोक सकते हैं।')); return;
      }
      if (phase.current === 'review' && YES.test(input)) {
        await api.confirmProfile(interview.current, {...profile.current, language});
        move('offer'); await say(t('Your profile is confirmed. Shall I find training pathways for you?', 'आपकी जानकारी की पुष्टि हो गई है। क्या मैं आपके लिए प्रशिक्षण के विकल्प खोजूँ?')); return;
      }
      if (phase.current === 'offer') {
        if (NO.test(input)) { engine.current?.pause(); return; }
        if (YES.test(input)) {
          const result = await api.generateRecommendations(interview.current);
          choices.current = result.recommendations; setOptions(result.recommendations);
          choiceIndex.current = 0; setIndex(0); move('options'); await describeOption(); return;
        }
      }
      if (phase.current === 'options') {
        if (/next|another|अगला|अगली/i.test(input)) { choiceIndex.current = (choiceIndex.current + 1) % Math.max(1, choices.current.length); setIndex(choiceIndex.current); await describeOption(); return; }
        if (/detail|explain|why|विवरण|क्यों|समझा/i.test(input)) {
          const rec = choices.current[choiceIndex.current];
          if (rec) await say(`${rec.qualification.title}. ${rec.why_recommended.join(' ')} ${rec.caveat}`);
          return;
        }
        if (!/change|correct|edit|बदल|सुधार/i.test(input)) { await describeOption(); return; }
      }
      if (phase.current === 'done') { await say(lastSpeech.current); return; }
      engine.current?.setState('thinking');
      const result = await api.submitTurn(interview.current, input, 'user', language, 'voice');
      profile.current = result.inferred_profile || {};
      if (result.is_final) { move('review'); await say(reviewText()); }
      else { move('interview'); await say(result.next_question || t('Please tell me more.', 'कृपया और बताएं।')); }
    } catch {
      setError(t('The connection or AI service is unavailable. Your saved answers are safe. Pause and resume to reload the last question.', 'कनेक्शन या AI सेवा उपलब्ध नहीं है। आपकी सुरक्षित जानकारी मौजूद है। रोकें और फिर शुरू करें।'));
      engine.current?.pause();
    } finally { processing.current = false; }
  }
  handler.current = handle;
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; engine.current?.pause(); };
  }, []);
  useEffect(() => {
    engine.current?.pause();
    setStarted(false); setCaption(''); setOptions([]);
  }, [language]);
  async function begin() {
    if (processing.current) return;
    processing.current = true; setError('');
    const voice = new VoiceSession(language, value => { if (mounted.current) setState(value); }, text => handler.current(text), message => { if (mounted.current) setError(message); });
    engine.current?.pause(); engine.current = voice;
    try {
      await voice.start();
      if (!voice.active || !mounted.current) return;
      voice.setState('thinking');
      if (!api.getSessionToken()) await api.createAnonymousSession();
      await api.recordConsent('ai_processing', true, language);
      await api.recordConsent('profile_storage', true, language);
      const saved = sessionStorage.getItem(KEY);
      if (saved) {
        const session = await api.getInterview(saved);
        if (session.language !== language) throw new Error('Language changed; start a new conversation.');
        interview.current = saved;
        profile.current = Object.fromEntries(Object.entries(session.fields).map(([key, item]) => [key, item.value])) as ConversationProfile;
        setStarted(true);
        if (sessionStorage.getItem(`${KEY}_referral_${saved}`)) { move('done'); await say(t('Your counselor request is already recorded.', 'आपका सलाहकार अनुरोध पहले ही दर्ज है।')); }
        else if (session.status === 'awaiting_confirmation') { move('review'); await say(reviewText()); }
        else if (session.status === 'ready_for_matching') { move('offer'); await say(t('Your profile is confirmed. Shall I find your training options?', 'आपकी जानकारी की पुष्टि हो चुकी है। क्या प्रशिक्षण के विकल्प खोजूँ?')); }
        else { move('interview'); await say(session.last_question); }
      } else {
        const session = await api.startInterview(language, 'voice_web');
        interview.current = session.interview_id; sessionStorage.setItem(KEY, session.interview_id); setStarted(true);
        move('interview'); await say(t('Hello, I am JeevanMitra. You can say repeat, speak slowly, or pause at any time. What work do you currently do?', 'नमस्ते, मैं जीवनमित्र हूँ। आप कभी भी दोबारा, धीरे बोलो, या रुको कह सकते हैं। आप अभी क्या काम करते हैं?'));
      }
    } catch (e) { voice.pause(); setError(e instanceof Error ? e.message : 'Could not start voice.'); }
    finally { processing.current = false; }
  }
  const status = {paused: t('Ready when you are', 'जब आप तैयार हों'), connecting: t('Connecting your microphone', 'माइक जोड़ रहे हैं'), listening: t('I’m listening', 'मैं सुन रहा हूँ'), thinking: t('One moment…', 'एक क्षण…'), speaking: t('JeevanMitra is speaking', 'जीवनमित्र बोल रहा है')}[state];
  const active = state !== 'paused';
  return <section className={styles.page} aria-label="JeevanMitra voice assistant">
    <header className={styles.header}><span><Waves size={18}/> JEEVANMITRA</span><span>{hi ? 'आवाज़ से आपका अगला कदम' : 'Your next step, through conversation'}</span></header>
    {!started && <div className={styles.welcome}><h1>{t('Let’s talk about your future.', 'आइए आपके भविष्य की बात करें।')}</h1><p>{t('Speak in your own words. I’ll help you explore training and work.', 'अपने शब्दों में बोलें। मैं प्रशिक्षण और काम के विकल्प खोजने में मदद करूँगा।')}</p><select aria-label="Conversation language" value={language === 'hi' ? 'hi' : 'en'} disabled={active} onChange={e => onLanguage(e.target.value as Language)}><option value="hi">हिन्दी / Hinglish</option><option value="en">English</option></select></div>}
    {started && <p className={styles.progress}>{({interview: t('Getting to know you', 'आपको समझ रहे हैं'), review: t('Check what I heard', 'जानकारी की पुष्टि'), offer: t('Ready to explore', 'विकल्प खोजें'), options: t('Your pathways', 'आपके विकल्प'), referral: t('Your permission', 'आपकी अनुमति'), done: t('Your next step is recorded', 'आपका अगला कदम दर्ज है')})[phaseView]}</p>}
    <div className={`${styles.stage} ${state === 'listening' || state === 'speaking' ? styles.live : ''}`}><div className={styles.halo}/><button className={styles.orb} disabled={state === 'connecting' || state === 'thinking'} onClick={() => active ? engine.current?.interrupt() : void begin()} aria-label={active ? t('Interrupt and speak', 'रोककर बोलें') : t('Agree and start voice', 'सहमत होकर बातचीत शुरू करें')}><Mic size={54} strokeWidth={1.4}/></button></div>
    <h2 className={styles.status} role="status">{status}</h2>
    <p className={styles.caption}>{caption || t('One tap to begin. No forms to fill in.', 'शुरू करने के लिए एक बार दबाएँ। कोई फ़ॉर्म नहीं भरना है।')}</p>
    {options[index] && phaseView === 'options' && <article className={styles.card}><small>{index + 1} / {options.length} · NSQF {options[index].qualification.nsqf_level}</small><h3>{options[index].qualification.title}</h3><p>{options[index].local_availability.status === 'verified_open' ? t('Local opportunity verified', 'स्थानीय अवसर सत्यापित') : t('Local batch not confirmed', 'स्थानीय बैच की पुष्टि बाकी')}</p></article>}
    {error && <p className={styles.error} role="alert">{error}</p>}
    <div className={styles.controls}>
      <button onClick={() => active ? engine.current?.pause() : void begin()} disabled={state === 'connecting'}>{active ? <Pause size={19}/> : <Play size={19}/>} {active ? t('Pause', 'रोकें') : started ? t('Resume', 'जारी रखें') : t('Agree & start', 'सहमत हैं · शुरू करें')}</button>
      {started && <button disabled={!active || state === 'thinking'} onClick={() => void say(lastSpeech.current)}><RotateCcw size={19}/>{t('Repeat', 'दोबारा')}</button>}
      {started && <button onClick={() => { engine.current?.pause(); setCaption(t('Conversation paused. You can resume from here.', 'बातचीत रुक गई है। यहीं से जारी कर सकते हैं।')); }}><PhoneOff size={19}/>{t('End', 'समाप्त')}</button>}
    </div>
    {!started && <p className={styles.consent}>{t('By starting, you agree to AI processing of your voice and storage of your answers for livelihood guidance. Audio is not stored by this application. Sharing with a counselor needs your separate permission.', 'शुरू करने पर आप आजीविका मार्गदर्शन के लिए आवाज़ का AI द्वारा उपयोग और उत्तर सुरक्षित रखने की सहमति देते हैं। यह ऐप ऑडियो सुरक्षित नहीं रखता। सलाहकार से साझा करने के लिए अलग अनुमति ली जाएगी।')}</p>}
    {!started && <button className={styles.textButton} onClick={() => { const u = new SpeechSynthesisUtterance(t('Starting gives permission to process your speech with AI and store your answers for guidance. Your audio is not saved by this app. Sharing with a counselor requires separate permission.', 'शुरू करने पर आवाज़ का AI द्वारा उपयोग और उत्तर सुरक्षित रखने की अनुमति मिलती है। ऐप ऑडियो सुरक्षित नहीं रखता। सलाहकार से साझा करने के लिए अलग अनुमति ली जाएगी।')); u.lang = hi ? 'hi-IN' : 'en-IN'; window.speechSynthesis?.speak(u); }}><Volume2 size={16}/>{t('Hear this notice', 'यह सूचना सुनें')}</button>}
    {started && <><p className={styles.hint}>{t('Try “repeat”, “speak slowly”, “help”, or “pause”.', '“दोबारा”, “धीरे बोलो”, “मदद”, या “रुको” कहें।')}</p><button className={styles.textButton} onClick={() => setTyping(!typing)}><Keyboard size={16}/>{t('Use keyboard', 'लिखकर बताएं')}</button>{typing && <form className={styles.form} onSubmit={e => { e.preventDefault(); if (draft.trim() && !processing.current) { engine.current?.interrupt(); void handle(draft); } }}><input aria-label="Your answer" value={draft} onChange={e => setDraft(e.target.value)} disabled={!active}/><button disabled={!active || !draft.trim() || state === 'thinking'}>{t('Send', 'भेजें')}</button></form>}</>}
    {state === 'paused' && <button className={styles.textButton} onClick={() => { sessionStorage.removeItem(KEY); interview.current = ''; profile.current = {}; choices.current = []; setOptions([]); setStarted(false); setCaption(''); setError(''); move('interview'); }}>{t('Start a new conversation', 'नई बातचीत शुरू करें')}</button>}
  </section>;
}
