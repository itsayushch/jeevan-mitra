import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Keyboard, Mic, RotateCcw, Square, Volume2, Waves } from 'lucide-react';
import type { Language } from '../../types';
import { api, type ConversationProfile } from '../../lib/api';
import { speakText, stopSpeaking } from '../../utils/speech';

type Recognition = {
  lang: string; continuous: boolean; interimResults: boolean;
  start(): void; stop(): void; abort(): void;
  onresult: ((event: { results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};
interface Props {
  language: Language;
  interviewId: string;
  onReview: (profile: ConversationProfile) => void;
}
export function AskQuestionVoice({ language, interviewId, onReview }: Props) {
  const hi = language === 'hi';
  const [turns, setTurns] = useState<{ user?: string; answer: string }[]>([]);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState('');
  const [provider, setProvider] = useState('');
  const [profile, setProfile] = useState<ConversationProfile>({});
  const [ready, setReady] = useState(false);
  const [typing, setTyping] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const active = useRef(false);
  const recognition = useRef<Recognition | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const mounted = useRef(true);
  const latestTranscript = useRef('');
  const speechHandled = useRef(false);

  useEffect(() => {
    active.current = true;
    api.pollInterview(interviewId, state => {
      if (!active.current) return;
      if (state.turns.length) {
        setTurns(state.turns);
        const last = state.turns[state.turns.length - 1];
        if (last && last.speaker === 'ai' && !speaking && active.current) {
          setSpeaking(true);
          speakText(last.text, hi ? 'hi' : 'en').finally(() => { if (mounted.current) setSpeaking(false); });
        }
      }
      setProvider(state.provider);
      setProfile(state.extracted_profile || {});
      setReady(state.status === 'ready_for_matching' || state.status === 'profile_extracted');
    }).catch(() => {});
    return () => { active.current = false; mounted.current = false; stopSpeaking(); recognition.current?.abort(); };
  }, [interviewId, hi]);

  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth' }); }, [turns, busy]);

  async function send(text = draft) {
    if (busy || !text.trim()) return;
    setBusy(true); setError(''); setDraft(''); setTyping(false);
    try {
      await api.replyInterview(interviewId, text.trim(), language);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send');
      setDraft(text);
    } finally {
      if (mounted.current) setBusy(false);
    }
  }

  function toggleListening() {
    if (listening) {
      recognition.current?.stop();
      return;
    }
    const browser = window as any;
    const Constructor = browser.SpeechRecognition || browser.webkitSpeechRecognition;
    if (!Constructor) { setError(hi ? 'वॉइस इनपुट उपलब्ध नहीं है। कृपया लिखें।' : 'Voice input is unavailable in this browser. Please type below.'); setTyping(true); return; }
    stopSpeaking(); setError(''); latestTranscript.current = ''; speechHandled.current = false;
    const instance = new Constructor(); recognition.current = instance;
    instance.lang = language === 'hi' ? 'hi-IN' : 'en-IN';
    instance.continuous = false; instance.interimResults = true;
    instance.onresult = (event: any) => {
      if (mounted.current) {
        const text = Array.from(event.results).map((result: any) => result[0].transcript).join(' ');
        latestTranscript.current = text;
        setError(text);
      }
    };
    instance.onerror = (event: any) => {
      if (!mounted.current || event.error === 'aborted') return;
      setError(event.error === 'not-allowed'
        ? (hi ? 'माइक्रोफ़ोन अनुमति अस्वीकृत। कृपया लिखें।' : 'Microphone permission was denied. You can type below.')
        : (hi ? 'ब्राउज़र आपकी आवाज़ को ट्रांसक्राइब नहीं कर सका। कृपया लिखें।' : 'The browser could not transcribe your voice. Try again or type below.'));
      setListening(false); setTyping(true);
    };
    instance.onend = () => { 
      if (mounted.current) {
        setListening(false);
        if (!speechHandled.current && latestTranscript.current) {
          speechHandled.current = true;
          const text = latestTranscript.current;
          latestTranscript.current = '';
          setError('');
          void send(text);
        } else if (!speechHandled.current) {
          setError(hi ? 'कोई आवाज़ नहीं सुनाई दी। दोबारा प्रयास करें।' : 'No speech was detected. Tap the microphone and try again.');
        }
      }
    };
    try { instance.start(); setListening(true); } catch { setListening(false); setError('Could not start the microphone. Please type below.'); setTyping(true); }
  }

  const reset = () => { recognition.current?.abort(); recognition.current = null; stopSpeaking(); setListening(false); setDraft(''); setError(''); setTyping(false); };

  const hasConversation = turns.length > 0;
  const aiTurns = turns.reduce<{user?: string, answer: string}[]>((acc, turn) => {
      if (turn.speaker === 'user') {
          acc.push({ user: turn.text, answer: '' });
      } else if (turn.speaker === 'ai' || turn.speaker === 'system') {
          if (acc.length === 0) acc.push({ answer: turn.text });
          else acc[acc.length - 1].answer += (acc[acc.length - 1].answer ? ' ' : '') + turn.text;
      }
      return acc;
  }, []);

  return <section className={`voice-experience ${hasConversation ? 'has-conversation' : ''}`} aria-label={hi ? 'एआई असिस्टेंट' : 'AI Assistant'}>
    <header className="voice-header">
      <div>
        <span className="voice-eyebrow">JEEVANMITRA</span>
        <h1>{hi ? 'एआई असिस्टेंट' : 'AI Assistant'}</h1>
        <p>{hasConversation ? (hi ? 'आगे बोलें या अपना सवाल लिखें।' : 'Keep talking, or type a follow-up.') : (hi ? 'अपने शब्दों में बोलें। हम सुन रहे हैं।' : 'Speak naturally. We’re here to listen.')}</p>
      </div>
      {hasConversation && <button type="button" className="voice-reset" aria-label={hi ? 'फिर शुरू करें' : 'Start over'} onClick={reset}><RotateCcw size={16}/><span>{hi ? 'फिर शुरू करें' : 'Start over'}</span></button>}
    </header>
    {hasConversation ? <>
      <div className="voice-conversation" role="log" aria-label={hi ? 'बातचीत' : 'Conversation'} aria-live="polite">
        {aiTurns.map((turn, index) => <div className="voice-exchange" key={index} lang={language === 'hi' ? 'hi-IN' : 'en-IN'}>
          {turn.user && <div className="voice-user-message"><span>{hi ? 'आप' : 'You'}</span><p>{turn.user}</p></div>}
          <div className="voice-assistant-message">
            <div className="voice-assistant-avatar" aria-hidden="true"><Waves size={19}/></div>
            <div className="voice-assistant-copy">
              <span>{hi ? 'एआई असिस्टेंट' : 'AI Assistant'}</span>
              <p>{turn.answer}</p>
              <button type="button" className="voice-replay" onClick={() => speakText(turn.answer, hi ? 'hi' : 'en')}><Volume2 size={16}/>{hi ? 'जवाब सुनें' : 'Listen to answer'}</button>
            </div>
          </div>
        </div>)}
        {busy && <p role="status" style={{textAlign: 'center', color: '#6b806d', fontSize: '13px'}}>{hi ? 'आपकी जानकारी समझ रहे हैं…' : 'Understanding your answer…'}</p>}
        <div ref={end} aria-hidden="true" />
      </div>
      <div className="voice-composer-wrap">
        {(listening || error) && <p className={`voice-composer-feedback ${error ? 'has-error' : ''}`} role="status">{error || (hi ? 'सुन रहे हैं…' : 'Listening…')}</p>}
        <form className="voice-composer" onSubmit={event => { event.preventDefault(); void send(draft); }}>
          <input value={draft} onChange={event => setDraft(event.target.value)} aria-label={hi ? 'अगला सवाल लिखें' : 'Type a follow-up'} placeholder={hi ? 'बोलें या टाइप करें…' : 'Speak or type a follow-up…'} disabled={busy} />
          <button type="button" className={`voice-composer-mic ${listening ? 'is-listening' : ''}`} disabled={busy} onClick={toggleListening} aria-label={listening ? (hi ? 'सुनना बंद करें' : 'Stop listening') : (hi ? 'माइक्रोफ़ोन से पूछें' : 'Ask with microphone')} aria-pressed={listening}>{listening ? <Square size={18} fill="currentColor"/> : <Mic size={21}/>}</button>
          <button type="submit" className="voice-composer-send" disabled={busy || listening || !draft.trim()} aria-label={hi ? 'भेजें' : 'Send'}><ArrowUp size={20}/></button>
        </form>
        {ready ? (
            <button className="primary-button" style={{marginTop: '15px'}} onClick={() => onReview(profile)}>{hi ? 'जानकारी जाँचें और पुष्टि करें' : 'Review and confirm profile'}</button>
        ) : (
            <p className="voice-note">{hi ? 'सामान्य मार्गदर्शन • स्थानीय उपलब्धता की पुष्टि फील्ड वर्कर से करें।' : 'General guidance · Ask a field worker to confirm local availability.'}</p>
        )}
      </div>
    </> : <>
      <div className="voice-stage">
        <div className="voice-visual">
          <div className="voice-rings" aria-hidden="true"><span/><span/><span/></div>
          <div className={`voice-orb ${listening ? 'is-listening' : ''} ${speaking ? 'is-speaking' : ''}`}>
            <button type="button" onClick={toggleListening} aria-label={listening ? (hi ? 'सुनना बंद करें' : 'Stop listening') : (hi ? 'बोलना शुरू करें' : 'Start speaking')} aria-pressed={listening}>{listening ? <Square size={35} fill="currentColor"/> : <Mic size={43} strokeWidth={1.8}/>}</button>
          </div>
        </div>
        <div className="voice-wave" aria-hidden="true">{Array.from({length:19},(_,index)=><span key={index} style={{height: `${8 + ((index * 7) % 17)}px`, animationDelay: `${index * 55}ms`}}/>)}</div>
        <h2 aria-live="polite">{listening ? (hi ? 'सुन रहे हैं…' : 'Listening…') : busy ? (hi ? 'समझ रहे हैं…' : 'Understanding…') : speaking ? (hi ? 'जवाब सुना रहे हैं…' : 'Speaking your answer…') : (hi ? 'बोलने के लिए माइक दबाएं' : 'Tap the microphone to speak')}</h2>
        <p className="voice-stage-hint">{listening ? (hi ? 'अपना सवाल बोलें। पूरा होने पर जवाब सुनाई देगा।' : 'Ask your question. Your answer will play when you finish.') : (hi ? 'कोई फ़ॉर्म भरने की ज़रूरत नहीं' : 'No forms to fill in')}</p>
        {error && <p className="voice-status has-error" role="status">{error}</p>}
      </div>
      <div className="voice-fallback"><button type="button" className="voice-type-toggle" onClick={() => setTyping(value => !value)} aria-expanded={typing}><Keyboard size={19}/>{typing ? (hi ? 'लिखना बंद करें' : 'Hide typing') : (hi ? 'लिखकर पूछें' : 'Type instead')}</button>{typing && <form className="voice-type-form" onSubmit={event => { event.preventDefault(); void send(draft); }}><input autoFocus value={draft} onChange={event => setDraft(event.target.value)} disabled={busy} aria-label={hi ? 'अपना सवाल लिखें' : 'Type your question'} placeholder={hi ? 'अपना सवाल लिखें…' : 'Type your question…'}/><button type="submit" disabled={busy || !draft.trim()} aria-label={hi ? 'सवाल भेजें' : 'Send question'}><ArrowUp size={20}/></button></form>}</div>
      <p className="voice-note">{hi ? 'सामान्य मार्गदर्शन • स्थानीय उपलब्धता की पुष्टि फील्ड वर्कर से करें।' : 'General guidance · Ask a field worker to confirm local availability.'}</p>
    </>}
  </section>;
}
