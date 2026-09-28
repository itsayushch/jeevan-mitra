import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Keyboard, Mic, RotateCcw, Square, Volume2, Waves } from 'lucide-react';
import type { Language } from '../../types';
import { speakText, stopSpeaking } from '../../utils/speech';

type Turn = { question: string; answer: string; language: Language };
type SpeechResult = { results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> };
type Recognition = {
  lang: string; continuous: boolean; interimResults: boolean;
  start: () => void; stop: () => void; abort: () => void;
  onresult: ((event: SpeechResult) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};
const topics = [
  { keys: /skill|learn|training|कौशल|प्रशिक्षण|सीख/i, answer: 'Start with work you enjoy, skills you already use, and how far you can travel. A field worker should confirm the local batch and schedule before you choose a course.', answerHi: 'अपने पसंदीदा काम, पहले से आने वाले कौशल और यात्रा की सुविधा से शुरुआत करें। कोर्स चुनने से पहले फील्ड वर्कर से स्थानीय बैच और समय की पुष्टि करें।' },
  { keys: /job|work|near|काम|नौकरी|रोजगार/i, answer: 'Explore local opportunities based on the kind of work you want and how far you can travel. Ask a field worker to confirm that an opening is current before making plans.', answerHi: 'अपनी रुचि और यात्रा की दूरी के अनुसार स्थानीय काम के विकल्प देखें। योजना बनाने से पहले फील्ड वर्कर से अवसर की उपलब्धता की पुष्टि करें।' },
  { keys: /money|grant|stipend|financial|support|पैस|वजीफा|आर्थिक|सहायता/i, answer: 'Financial support depends on the scheme, course, and your eligibility. Confirm the amount, documents, and application process with the relevant office.', answerHi: 'आर्थिक सहायता योजना, कोर्स और पात्रता पर निर्भर करती है। राशि, दस्तावेज और आवेदन की प्रक्रिया संबंधित कार्यालय से पुष्टि करें।' },
];
const locales: Record<Language, string> = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN', bn: 'bn-IN', te: 'te-IN' };

export function AskQuestionVoice({ language }: { language: Language }) {
  const hi = language === 'hi';
  const [turns, setTurns] = useState<Turn[]>([]);
  const [transcript, setTranscript] = useState('');
  const [draft, setDraft] = useState('');
  const [typing, setTyping] = useState(false);
  const [listening, setListening] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);
  const [status, setStatus] = useState('');
  const recognition = useRef<Recognition | null>(null);
  const speechHandled = useRef(false);
  const latestTranscript = useRef('');
  const conversationEnd = useRef<HTMLDivElement | null>(null);
  const speaking = speakingIndex !== null;

  useEffect(() => () => { recognition.current?.abort(); recognition.current = null; stopSpeaking(); }, []);
  useEffect(() => { recognition.current?.abort(); recognition.current = null; stopSpeaking(); setListening(false); setSpeakingIndex(null); setTranscript(''); setStatus(''); latestTranscript.current = ''; }, [language]);
  useEffect(() => { if (turns.length) conversationEnd.current?.scrollIntoView({ block: 'end' }); }, [turns.length]);

  const playAnswer = (answer: string, answerLanguage: Language, index: number) => {
    if (!('speechSynthesis' in window)) { setStatus(hi ? 'ऑडियो उपलब्ध नहीं है। जवाब नीचे पढ़ सकते हैं।' : 'Audio playback is unavailable. You can read the answer below.'); return; }
    stopSpeaking();
    setSpeakingIndex(index);
    speakText(answer, answerLanguage === 'hi' ? 'hi' : 'en', () => setSpeakingIndex(null));
  };

  const answerQuestion = (question: string, fromVoice = false) => {
    const clean = question.trim();
    if (!clean) return;
    stopSpeaking();
    setSpeakingIndex(null);
    const topic = topics.find(item => item.keys.test(clean));
    const answer = topic ? (hi ? topic.answerHi : topic.answer) : (hi
      ? 'कौशल, स्थानीय काम या आर्थिक सहायता के बारे में पूछें। अपनी स्थिति के अनुसार रास्ते देखने के लिए “मेरी यात्रा” खोलें।'
      : 'Ask me about skills, local work, or financial support. For a pathway based on your situation, open My journey.');
    setTurns(previous => [...previous, { question: clean, answer, language }]);
    setTranscript(''); setDraft(''); setStatus(''); setTyping(false);
    if (fromVoice) playAnswer(answer, language, turns.length);
  };

  const toggleListening = () => {
    if (listening) {
      if (recognition.current) {
        clearTimeout(recognition.current as unknown as number);
        recognition.current = null;
      }
      setListening(false);
      return;
    }
    
    stopSpeaking(); 
    setSpeakingIndex(null); 
    setStatus(''); 
    setTranscript(''); 
    latestTranscript.current = ''; 
    speechHandled.current = false;
    setListening(true);
    
    setStatus(hi ? 'रिकॉर्डिंग... (यह एक डेमो है)' : 'Recording... (Simulated backend processing)');
    
    const timer = setTimeout(() => {
      if (!speechHandled.current) {
        speechHandled.current = true;
        setListening(false);
        const demoQuestion = hi ? 'मेरे आस-पास कौन सी नौकरियां उपलब्ध हैं?' : 'What kind of jobs are available near me?';
        setTranscript(demoQuestion);
        setTimeout(() => answerQuestion(demoQuestion, true), 1000);
      }
    }, 3000);
    recognition.current = { abort: () => clearTimeout(timer) } as any;
  };

  const reset = () => { recognition.current?.abort(); recognition.current = null; stopSpeaking(); setListening(false); setSpeakingIndex(null); setTurns([]); setTranscript(''); latestTranscript.current = ''; setDraft(''); setStatus(''); setTyping(false); };

  return <section className={`voice-experience ${turns.length ? 'has-conversation' : ''}`} aria-label={hi ? 'एआई सहायक' : 'AI Assistant'}>
    <header className="voice-header">
      <div><span className="voice-eyebrow">JEEVANMITRA</span><h1>{hi ? 'एआई सहायक' : 'AI Assistant'}</h1><p>{turns.length ? (hi ? 'आगे बोलें या अपना सवाल लिखें।' : 'Keep talking, or type a follow-up.') : (hi ? 'अपने शब्दों में बोलें। हम सुन रहे हैं।' : 'Speak naturally. We’re here to listen.')}</p></div>
      {turns.length > 0 && <button type="button" className="voice-reset" aria-label={hi ? 'फिर शुरू करें' : 'Start over'} onClick={reset}><RotateCcw size={16}/><span>{hi ? 'फिर शुरू करें' : 'Start over'}</span></button>}
    </header>
    {turns.length ? <>
      <div className="voice-conversation" role="log" aria-label={hi ? 'बातचीत' : 'Conversation'} aria-live="polite">
        {turns.map((turn, index) => <div className="voice-exchange" key={index} lang={locales[turn.language]}>
          <div className="voice-user-message"><span>{hi ? 'आप' : 'You'}</span><p>{turn.question}</p></div>
          <div className="voice-assistant-message"><div className="voice-assistant-avatar" aria-hidden="true"><Waves size={19}/></div><div className="voice-assistant-copy"><span>{hi ? 'एआई सहायक' : 'AI Assistant'}</span><p>{turn.answer}</p><button type="button" className="voice-replay" onClick={() => { if (speakingIndex === index) { stopSpeaking(); setSpeakingIndex(null); } else playAnswer(turn.answer, turn.language, index); }}><Volume2 size={16}/>{speakingIndex === index ? (hi ? 'ऑडियो रोकें' : 'Stop audio') : (hi ? 'जवाब सुनें' : 'Listen to answer')}</button></div></div>
        </div>)}
        <div ref={conversationEnd} aria-hidden="true" />
      </div>
      <div className="voice-composer-wrap">
        {(listening || transcript || status) && <p className={`voice-composer-feedback ${status ? 'has-error' : ''}`} role="status">{status || (transcript ? transcript : (hi ? 'सुन रहे हैं…' : 'Listening…'))}</p>}
        <form className="voice-composer" onSubmit={event => { event.preventDefault(); answerQuestion(draft); }}>
          <input value={draft} onChange={event => setDraft(event.target.value)} aria-label={hi ? 'अगला सवाल लिखें' : 'Type a follow-up question'} placeholder={hi ? 'अगला सवाल लिखें…' : 'Ask a follow-up…'}/>
          <button type="button" className={`voice-composer-mic ${listening ? 'is-listening' : ''}`} onClick={toggleListening} aria-label={listening ? (hi ? 'सुनना बंद करें' : 'Stop listening') : (hi ? 'माइक्रोफ़ोन से पूछें' : 'Ask with microphone')} aria-pressed={listening}>{listening ? <Square size={18} fill="currentColor"/> : <Mic size={21}/>}</button>
          <button type="submit" className="voice-composer-send" disabled={!draft.trim()} aria-label={hi ? 'सवाल भेजें' : 'Send question'}><ArrowUp size={20}/></button>
        </form>
        <p className="voice-note">{hi ? 'सामान्य मार्गदर्शन • स्थानीय उपलब्धता की पुष्टि फील्ड वर्कर से करें।' : 'General guidance · Ask a field worker to confirm local availability.'}</p>
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
        <h2 aria-live="polite">{listening ? (hi ? 'सुन रहे हैं…' : 'Listening…') : speaking ? (hi ? 'जवाब सुना रहे हैं…' : 'Speaking your answer…') : (hi ? 'बोलने के लिए माइक दबाएं' : 'Tap the microphone to speak')}</h2>
        <p className="voice-stage-hint">{listening ? (hi ? 'अपना सवाल बोलें। पूरा होने पर जवाब सुनाई देगा।' : 'Ask your question. Your answer will play when you finish.') : (hi ? 'कोई फ़ॉर्म भरने की ज़रूरत नहीं' : 'No forms to fill in')}</p>
        {transcript && <p className="voice-live-transcript" aria-live="polite">{transcript}</p>}
        {status && <p className="voice-status" role="status">{status}</p>}
      </div>
      <div className="voice-fallback"><button type="button" className="voice-type-toggle" onClick={() => setTyping(value => !value)} aria-expanded={typing}><Keyboard size={19}/>{typing ? (hi ? 'लिखना बंद करें' : 'Hide typing') : (hi ? 'लिखकर पूछें' : 'Type instead')}</button>{typing && <form className="voice-type-form" onSubmit={event => { event.preventDefault(); answerQuestion(draft); }}><input autoFocus value={draft} onChange={event => setDraft(event.target.value)} aria-label={hi ? 'अपना सवाल लिखें' : 'Type your question'} placeholder={hi ? 'अपना सवाल लिखें…' : 'Type your question…'}/><button type="submit" disabled={!draft.trim()} aria-label={hi ? 'सवाल भेजें' : 'Send question'}><ArrowUp size={20}/></button></form>}</div>
      <p className="voice-note">{hi ? 'सामान्य मार्गदर्शन • स्थानीय उपलब्धता की पुष्टि फील्ड वर्कर से करें।' : 'General guidance · Ask a field worker to confirm local availability.'}</p>
    </>}
  </section>;
}
