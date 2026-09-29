import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Mic, Square, Volume2 } from 'lucide-react';
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
  const active = useRef(false);
  const recognition = useRef<Recognition | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const mounted = useRef(true);
  const greeting = hi ? 'अपनी पढ़ाई, रुचि और जहाँ रहते हैं उसके बारे में बताएं।' : 'Tell me about your education, the work you would like to learn, and where you live.';
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; recognition.current?.abort(); stopSpeaking(); }; }, []);
  useEffect(() => { recognition.current?.abort(); setListening(false); stopSpeaking(); }, [language]);
  useEffect(() => { if (turns.length) end.current?.scrollIntoView({ block: 'nearest' }); }, [turns]);
  async function send() {
    const text = draft.trim();
    if (!text || active.current) return;
    active.current = true; setBusy(true); setError(''); stopSpeaking();
    recognition.current?.abort(); setListening(false);
    try {
      const result = await api.submitTurn(interviewId, text, 'user', language, 'conversational');
      if (!mounted.current) return;
      setTurns(old => [...old, { user: text, answer: result.next_question || '' }]);
      setProfile(result.inferred_profile || {}); setReady(!!result.is_final);
      setProvider(result.extraction_provider || 'guided'); setDraft('');
    } catch (e) {
      if (mounted.current) setError(e instanceof Error ? e.message : 'Please try again.');
    } finally { active.current = false; if (mounted.current) setBusy(false); }
  }
  function microphone() {
    if (listening) { recognition.current?.stop(); return; }
    const browser = window as unknown as { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
    const Constructor = browser.SpeechRecognition || browser.webkitSpeechRecognition;
    if (!Constructor) { setError(hi ? 'इस ब्राउज़र में आवाज़ उपलब्ध नहीं है। नीचे लिखें।' : 'Voice input is unavailable in this browser. Please type below.'); return; }
    stopSpeaking(); setError('');
    const instance = new Constructor(); recognition.current = instance;
    instance.lang = ({ en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN', bn: 'bn-IN', te: 'te-IN' })[language];
    instance.continuous = false; instance.interimResults = true;
    instance.onresult = event => {
      if (mounted.current) setDraft(Array.from(event.results).map(result => result[0].transcript).join(' '));
    };
    instance.onerror = event => {
      if (!mounted.current || event.error === 'aborted') return;
      setError(event.error === 'not-allowed'
        ? (hi ? 'माइक्रोफ़ोन की अनुमति नहीं मिली। नीचे लिख सकते हैं।' : 'Microphone permission was denied. You can type below.')
        : (hi ? 'आवाज़ नहीं मिल सकी। फिर कोशिश करें या नीचे लिखें।' : 'The browser could not transcribe your voice. Try again or type below.'));
      setListening(false);
    };
    instance.onend = () => { if (mounted.current) setListening(false); };
    try { instance.start(); setListening(true); } catch { setListening(false); setError('Could not start the microphone. Please type below.'); }
  }
  const hasConversation = turns.length > 0;
  return <section className={`voice-experience ${hasConversation ? 'has-conversation' : ''}`} aria-label={hi ? 'एआई सहायक' : 'AI Assistant'}>
    <header className="voice-header"><div><span className="voice-eyebrow">JEEVANMITRA</span><h2>{hasConversation ? (hi ? 'आइए बात करें' : 'Let’s find your next step.') : (hi ? 'अपनी आवाज़ से पूछें' : 'Ask with your voice')}</h2><p>{hasConversation ? (hi ? 'बोलें या लिखें। सुझावों से पहले जानकारी की पुष्टि करेंगे।' : 'Speak or type. You will review your details before getting matches.') : (hi ? 'स्वाभाविक रूप से बोलें। हम सुनने के लिए यहाँ हैं।' : 'Speak naturally. We’re here to listen.')}</p></div></header>
    {provider === 'guided' && <p role="status" className="voice-note">{hi ? 'सरल प्रश्नों वाला मोड सक्रिय है। जो जानकारी समझ नहीं आई, उसे जाँच में भरें।' : 'Guided mode is active. You can fill in anything we miss during review.'}</p>}
    
    {hasConversation ? (
      <div className="voice-conversation" role="log" aria-live="polite">
        <div className="voice-assistant-message"><div className="voice-assistant-copy"><p>{greeting}</p></div></div>
        {turns.map((turn, index) => <div className="voice-exchange" key={index}><div className="voice-user-message"><span>{hi ? 'आप' : 'You'}</span><p>{turn.user}</p></div><div className="voice-assistant-message"><div className="voice-assistant-copy"><span>{hi ? 'सहायक' : 'Assistant'}</span><p>{turn.answer}</p><button type="button" className="voice-replay" onClick={() => speakText(turn.answer, hi ? 'hi' : 'en')}><Volume2 size={16}/>{hi ? 'सुनें' : 'Listen'}</button></div></div></div>)}
        {busy && <p role="status">{hi ? 'आपकी जानकारी समझ रहे हैं…' : 'Understanding your answer…'}</p>}<div ref={end}/>
      </div>
    ) : (
      <div className="voice-stage">
        <div className="voice-visual">
          <div className="voice-rings" aria-hidden="true"><span/><span/><span/></div>
          <div className={`voice-orb ${listening ? 'is-listening' : ''} ${busy ? 'is-speaking' : ''}`}>
            <button type="button" onClick={microphone} aria-label={listening ? (hi ? 'सुनना बंद करें' : 'Stop listening') : (hi ? 'बोलना शुरू करें' : 'Start speaking')} aria-pressed={listening}>{listening ? <Square size={35} fill="currentColor"/> : <Mic size={43} strokeWidth={1.8}/>}</button>
          </div>
        </div>
        <div className="voice-wave" aria-hidden="true">{Array.from({length:19},(_,index)=><span key={index} style={{height: `${8 + ((index * 7) % 17)}px`, animationDelay: `${index * 55}ms`}}/>)}</div>
        <h2 aria-live="polite">{listening ? (hi ? 'सुन रहे हैं…' : 'Listening…') : busy ? (hi ? 'आपकी जानकारी समझ रहे हैं…' : 'Understanding…') : (hi ? 'बोलने के लिए माइक्रोफ़ोन दबाएँ' : 'Tap the microphone to speak')}</h2>
        <p className="voice-stage-hint">{listening ? (hi ? 'अपना जवाब बोलें।' : 'Speak your answer.') : (hi ? 'कोई फॉर्म नहीं भरना है' : 'No forms to fill in')}</p>
      </div>
    )}

    <div className="voice-composer-wrap">
      {error && <p role="alert" className="voice-composer-feedback has-error">{error}</p>}
      {listening && hasConversation && <p role="status">{hi ? 'सुन रहे हैं…' : 'Listening…'}</p>}
      <form className="voice-composer" onSubmit={e => { e.preventDefault(); void send(); }}>
        <input value={draft} maxLength={4000} disabled={busy} onChange={e => setDraft(e.target.value)} aria-label={hi ? 'अपना जवाब लिखें' : 'Your answer'} placeholder={hi ? 'यहाँ बोलें या लिखें…' : 'Speak or type your answer…'}/>
        <button type="button" className="voice-composer-mic" disabled={busy} onClick={microphone} aria-pressed={listening} aria-label={listening ? 'Stop listening' : 'Start microphone'}>{listening ? <Square size={19}/> : <Mic size={21}/>}</button>
        <button type="submit" className="voice-composer-send" disabled={busy || listening || !draft.trim()} aria-label="Send answer"><ArrowUp size={20}/></button>
      </form>
      <p className="voice-note">{hi ? 'बोले गए शब्द जाँचें और भेजें।' : 'Check the transcribed words, then press send.'}</p>
      <button className={ready ? 'primary-button' : 'voice-type-toggle'} disabled={busy || listening} onClick={() => onReview(profile)}>{ready ? (hi ? 'जानकारी जाँचें और पुष्टि करें' : 'Review and confirm profile') : (hi ? 'फ़ॉर्म में जाँचें या भरें' : 'Review or complete with a form')}</button>
    </div>
  </section>;
}
