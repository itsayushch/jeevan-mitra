import { useEffect, useRef, useState } from 'react';
import { AudioLines, ArrowRight, Keyboard, LoaderCircle, Mic, Pause, Send, Volume2, CheckCheck } from 'lucide-react';
import type { Language } from '../../types';
import { api } from '../../lib/api';
import { EMPTY_PROFILE, normalizeProfile, PROFILE_FIELDS, type Profile } from '../../lib/interview';
import { speakText, stopSpeaking } from '../../utils/speech';
import { useVoiceInput } from '../../hooks/useVoiceInput';

type Message = { role: 'assistant' | 'user'; text: string };
interface Props {
  language: Language; interviewId?: string; firstQuestion?: string;
  history?: { speaker: string; text: string }[];
  initialProfile?: Profile;
  onReview?: (profile: Profile) => void;
}

export function AskQuestionVoice({ language, interviewId, firstQuestion, history = [], initialProfile = EMPTY_PROFILE, onReview }: Props) {
  const hi = language === 'hi';
  const initialQuestion = firstQuestion || (hi ? 'आप किस जिले में रहते हैं?' : 'Which district do you live in?');
  const [question, setQuestion] = useState(initialQuestion);
  const [messages, setMessages] = useState<Message[]>(() => history.length ? history.map(turn => ({ role: turn.speaker === 'user' ? 'user' : 'assistant', text: turn.text })) : [{ role: 'assistant', text: initialQuestion }]);
  const [profile, setProfile] = useState(initialProfile);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [thinking, setThinking] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [live, setLive] = useState(false);
  const [finished, setFinished] = useState(false);
  const [pendingText, setPendingText] = useState('');
  const [showTranscript, setShowTranscript] = useState(false);
  const active = useRef(false);
  const mounted = useRef(true);
  const inFlight = useRef(false);
  const log = useRef<HTMLDivElement>(null);
  const voice = useVoiceInput(language, text => { void submit(text, 'voice'); }, interviewId, question);
  const pauseRef = useRef<() => void>(() => {});

  function pause() {
    active.current = false; setLive(false); voice.stop(); stopSpeaking(); setSpeaking(false);
  }
  pauseRef.current = pause;
  useEffect(() => {
    mounted.current = true;
    const onHidden = () => { if (document.hidden) pauseRef.current(); };
    document.addEventListener('visibilitychange', onHidden);
    return () => { mounted.current = false; active.current = false; stopSpeaking(); document.removeEventListener('visibilitychange', onHidden); };
  }, []);
  useEffect(() => { log.current?.scrollTo({ top: log.current.scrollHeight, behavior: 'smooth' }); }, [messages, showTranscript]);
  useEffect(() => { if (voice.error) { active.current = false; setLive(false); } }, [voice.error]);

  function readQuestion(text: string, continueListening = false) {
    voice.stop(); stopSpeaking(); setSpeaking(true);
    speakText(text, language, () => {
      if (mounted.current) setSpeaking(false);
    });
    // Full duplex: listen during the question so a real answer can interrupt it.
    if (continueListening && active.current && !inFlight.current) {
      if (!voice.start(text)) { active.current = false; setLive(false); }
    }
  }
  function startLive() {
    if (thinking || finished) return;
    setError(''); voice.clearError(); active.current = true; setLive(true);
    readQuestion(question, true);
  }
  async function submit(text: string, source: 'voice' | 'text') {
    if (!text.trim() || inFlight.current || finished || !interviewId) return;
    if (source === 'text') pause();
    else { voice.stop(); stopSpeaking(); setSpeaking(false); }
    inFlight.current = true; setThinking(true); setPendingText(text); setError(''); voice.clearError();
    try {
      const result = await api.submitTurn(interviewId, text.trim(), 'user', 'voice', source);
      if (!mounted.current) return;
      const next = result.next_question || (hi ? 'अपनी जानकारी जाँचें।' : 'Let’s review your answers.');
      const nextProfile = normalizeProfile(result.inferred_profile || {});
      setProfile(nextProfile); setInput(''); setQuestion(next);
      setMessages(previous => [...previous, { role: 'user', text }, { role: 'assistant', text: next }]);
      inFlight.current = false; setThinking(false); setPendingText('');
      if (result.is_final) { setFinished(true); active.current = false; setLive(false); readQuestion(next); }
      else if (active.current) readQuestion(next, true);
    } catch (err) {
      if (!mounted.current) return;
      pause(); setInput(text); setError(err instanceof Error ? err.message : 'Could not save your answer. Please retry.');
    } finally {
      inFlight.current = false;
      if (mounted.current) { setThinking(false); setPendingText(''); }
    }
  }
  const status = finished ? (hi ? 'जानकारी तैयार है' : 'Ready to review') : (thinking || voice.transcribing) ? (hi ? 'उत्तर समझ रहे हैं' : 'Understanding your answer') : speaking ? (hi ? 'मित्र बोल रहा है' : 'Mitra is speaking') : voice.listening ? (hi ? 'आपकी बात सुन रहे हैं' : 'Listening to you') : (hi ? 'आपकी गति से' : 'At your pace');
  const collected = PROFILE_FIELDS.filter(field => { const value = profile[field.key]; return Array.isArray(value) ? value.length : value != null && value !== ''; }).length;

  return <section className="live-interview" aria-label={hi ? 'लाइव साक्षात्कार' : 'Live interview'}>
    <header className="interview-heading"><div><span className="eyebrow">{hi ? 'आपका साथी, जीवनमित्र' : 'YOUR COMPANION, JEEVANMITRA'}</span><h2>{hi ? 'आइए, आपके बारे में बात करें।' : 'A conversation about you.'}</h2><p>{hi ? 'एक बार में एक सवाल। अपनी भाषा में, अपनी गति से।' : 'One question at a time. In your words, at your pace.'}</p></div><span className={`live-badge ${live ? 'on' : ''}`}><span />{live ? (hi ? 'लाइव' : 'LIVE VOICE') : (hi ? 'साक्षात्कार' : 'YOUR INTERVIEW')}</span></header>
    <div className={`conversation-stage ${speaking ? 'speaking' : voice.listening ? 'listening' : (thinking || voice.transcribing) ? 'thinking' : ''}`}>
      <div className="stage-topline"><span>{hi ? 'वर्तमान सवाल' : 'CURRENT QUESTION'}</span><span>{hi ? `${collected} जानकारियाँ मिलीं` : `${collected} details collected`}</span></div>
      <div className="mitra-orbit" aria-hidden="true"><div className="orbit-halo"/><div className="mitra-orb">{(thinking || voice.transcribing) ? <LoaderCircle className="spin" size={40}/> : finished ? <CheckCheck size={42}/> : <AudioLines size={44}/>}</div></div>
      <div className="voice-state" role="status"><span />{status}</div>
      <h3>{question}</h3>
      <p className="stage-caption">{finished ? (hi ? 'सुझाव पाने से पहले हर उत्तर जाँच सकते हैं।' : 'You’ll review every answer before we find your pathways.') : (hi ? 'माइक चालू है तो मित्र के बोलते समय भी अपना उत्तर बोल सकते हैं। या नीचे टाइप करें।' : speaking ? 'Your mic is listening. You can speak while Mitra talks.' : voice.listening ? 'Take your time. You can answer naturally and include more than one detail.' : 'Start live voice to talk, or type your answer below.')}</p>
      {(voice.transcript || pendingText) && <p className="live-caption" aria-live="polite">“{voice.transcript || pendingText}”</p>}
      <div className="voice-actions">{finished ? <button className="primary-button" onClick={() => { pause(); onReview?.(profile); }}>{hi ? 'मेरे उत्तर जाँचें' : 'Review my answers'}<ArrowRight size={18}/></button> : <><button className={`primary-button ${live ? 'pause-button' : ''}`} onClick={live ? pause : startLive} disabled={thinking || !voice.supported}>{live ? <Pause size={18}/> : <Mic size={18}/>}{live ? (hi ? 'रोकें' : 'Pause conversation') : (hi ? 'लाइव आवाज़ शुरू करें' : 'Start live voice')}</button><button className="icon-button" disabled={thinking} onClick={() => { pause(); readQuestion(question); }} aria-label={hi ? 'सवाल फिर सुनें' : 'Hear this question again'}><Volume2 size={20}/></button></>}</div>
    </div>
    {(error || voice.error) && <div role="alert" className="inline-error">{error || voice.error}</div>}
    {!finished && <form className="answer-composer" onSubmit={event => { event.preventDefault(); void submit(input, 'text'); }}><Keyboard size={20} aria-hidden="true"/><label className="sr-only" htmlFor="interview-answer">{hi ? 'अपना उत्तर टाइप करें' : 'Type your answer'}</label><input id="interview-answer" value={input} maxLength={4000} onFocus={() => { if (voice.transcript) setInput(voice.transcript); pause(); }} onChange={event => setInput(event.target.value)} disabled={thinking} placeholder={hi ? 'अपना उत्तर यहाँ टाइप करें…' : 'You can always type your answer here…'}/><button className="composer-send" type="submit" disabled={thinking || !input.trim()} aria-label={hi ? 'उत्तर भेजें' : 'Send answer'}>{(thinking || voice.transcribing) ? <LoaderCircle className="spin" size={19}/> : <Send size={19}/>}</button></form>}
    <div className="interview-footnote"><span>{hi ? 'माइक केवल लाइव आवाज़ शुरू करने पर चालू होता है।' : 'Your mic is active only during live voice.'}</span><button className="text-button" onClick={() => setShowTranscript(value => !value)} aria-expanded={showTranscript}>{showTranscript ? (hi ? 'बातचीत छिपाएँ' : 'Hide conversation') : (hi ? 'बातचीत देखें' : 'View conversation')}<span>{messages.filter(message => message.role === 'user').length}</span></button></div>
    {showTranscript && <div className="interview-log" ref={log} role="log" aria-label={hi ? 'बातचीत' : 'Conversation transcript'}>{messages.map((message, index) => <div className={`log-message ${message.role}`} key={index}><span>{message.role === 'assistant' ? 'JeevanMitra' : hi ? 'आप' : 'You'}</span><p>{message.text}</p></div>)}</div>}
  </section>;
}
