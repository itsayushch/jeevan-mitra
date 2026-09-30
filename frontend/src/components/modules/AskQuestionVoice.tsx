import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Keyboard, Mic, RotateCcw, Square, Volume2, Waves, Edit2, Play, Pause } from 'lucide-react';
import type { Language } from '../../types';
import { speakText, stopSpeaking } from '../../utils/speech';

type Turn = { question: string; answer: string; language: Language; sources?: string[] };

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
  const [reviewingTranscript, setReviewingTranscript] = useState(false);
  
  const speechHandled = useRef(false);
  const conversationEnd = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    return () => {
      stopSpeaking();
    };
  }, []);

  useEffect(() => { if (turns.length) conversationEnd.current?.scrollIntoView({ block: 'end' }); }, [turns.length]);

  const playAnswer = (answer: string, answerLanguage: Language, index: number) => {
    if (!('speechSynthesis' in window)) { setStatus(hi ? 'ऑडियो उपलब्ध नहीं है।' : 'Audio playback is unavailable.'); return; }
    stopSpeaking();
    setSpeakingIndex(index);
    speakText(answer, answerLanguage === 'hi' ? 'hi' : 'en', () => setSpeakingIndex(null));
  };

  const answerQuestion = async (question: string) => {
    const clean = question.trim();
    if (!clean) return;
    
    stopSpeaking();
    setSpeakingIndex(null);
    setReviewingTranscript(false);
    setStatus(hi ? 'जवाब ढूंढा जा रहा है...' : 'Finding answer in course material...');

    // Simulate backend call strictly grounded in course content
    setTimeout(() => {
      const answer = hi 
        ? 'इलेक्ट्रिक वायर को छूने से पहले हमेशा मेन पावर स्विच बंद करें। (यह जानकारी कोर्स से ली गई है)' 
        : 'Always switch off the main power before touching any electrical wire. (Sourced from course material)';
        
      setTurns(previous => [...previous, { question: clean, answer, language, sources: ['Electrical Safety Basics'] }]);
      setTranscript(''); setDraft(''); setStatus(''); setTyping(false);
    }, 1000);
  };

  const toggleListening = () => {
    if (listening) {
      setListening(false);
      if (transcript) {
        setReviewingTranscript(true);
        setDraft(transcript);
      }
      return;
    }
    
    stopSpeaking(); 
    setSpeakingIndex(null); 
    setStatus(''); 
    setTranscript(''); 
    speechHandled.current = false;
    setListening(true);
    
    setStatus(hi ? 'रिकॉर्डिंग...' : 'Recording...');
    
    setTimeout(() => {
      if (!speechHandled.current) {
        speechHandled.current = true;
        setListening(false);
        const demoQuestion = hi ? 'खराब तार की जांच कैसे करें?' : 'How should I check a damaged wire?';
        setTranscript(demoQuestion);
        setDraft(demoQuestion);
        setReviewingTranscript(true);
        setStatus('');
      }
    }, 3000);
  };

  const reset = () => { 
    stopSpeaking(); 
    setListening(false); 
    setSpeakingIndex(null); 
    setTurns([]); 
    setTranscript(''); 
    setDraft(''); 
    setStatus(''); 
    setTyping(false);
    setReviewingTranscript(false);
  };

  return <section className={`voice-experience ${turns.length ? 'has-conversation' : ''}`}>
    <header className="voice-header bg-white p-4 rounded-t-2xl border-b border-slate-100 flex justify-between items-center">
      <div>
        <h2 className="font-black text-slate-900">{hi ? 'कोर्स असिस्टेंट (वैकल्पिक)' : 'Course Assistant (Optional)'}</h2>
        <p className="text-xs text-slate-500">{hi ? 'सिर्फ कोर्स से जुड़े सवाल पूछें' : 'Ask questions based on this course only'}</p>
      </div>
      {turns.length > 0 && (
        <button type="button" className="text-slate-400 hover:text-slate-700 p-2" onClick={reset}>
          <RotateCcw size={16}/>
        </button>
      )}
    </header>

    <div className="bg-slate-50 p-4 min-h-[300px] flex flex-col justify-end rounded-b-2xl border-x border-b border-slate-200">
      {turns.length > 0 ? (
        <div className="space-y-4 mb-4 overflow-y-auto max-h-[400px] pr-2">
          {turns.map((turn, index) => (
            <div key={index} className="space-y-3">
              <div className="flex justify-end">
                <div className="bg-emerald-100 text-emerald-900 text-sm p-3 rounded-2xl rounded-tr-sm max-w-[85%]">
                  {turn.question}
                </div>
              </div>
              
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 text-slate-800 text-sm p-4 rounded-2xl rounded-tl-sm max-w-[90%] shadow-sm">
                  <p className="mb-2">{turn.answer}</p>
                  
                  {turn.sources && (
                    <div className="text-[10px] text-slate-400 bg-slate-50 p-2 rounded-lg mb-3">
                      Source: {turn.sources.join(', ')}
                    </div>
                  )}

                  <div className="flex gap-2">
                    <button 
                      type="button" 
                      className="flex items-center gap-1.5 text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 py-1.5 px-3 rounded-lg transition-colors"
                      onClick={() => {
                        if (speakingIndex === index) {
                          stopSpeaking();
                          setSpeakingIndex(null);
                        } else {
                          playAnswer(turn.answer, turn.language, index);
                        }
                      }}
                    >
                      {speakingIndex === index ? (
                        <><Pause size={14}/> Stop</>
                      ) : (
                        <><Volume2 size={14}/> Listen</>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={conversationEnd} />
        </div>
      ) : (
        <div className="text-center py-10 opacity-60">
          <Waves className="w-12 h-12 mx-auto text-emerald-600 mb-3" />
          <p className="text-sm font-medium text-slate-600">
            {hi ? 'माइक दबाएं और सवाल पूछें' : 'Tap mic to ask a question'}
          </p>
        </div>
      )}

      {reviewingTranscript && (
        <div className="bg-white p-3 rounded-xl border border-emerald-200 shadow-sm mb-3">
          <p className="text-xs font-bold text-slate-500 mb-1">{hi ? 'आपका सवाल:' : 'Your question:'}</p>
          <input 
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 p-2 text-sm rounded-lg mb-2"
          />
          <div className="flex gap-2">
            <button 
              onClick={() => answerQuestion(draft)}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold py-2 rounded-lg"
            >
              {hi ? 'पूछें' : 'Ask'}
            </button>
            <button 
              onClick={() => setReviewingTranscript(false)}
              className="px-3 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-bold rounded-lg"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {status && !reviewingTranscript && (
        <div className="text-xs text-center text-slate-500 mb-3 animate-pulse">{status}</div>
      )}

      {!reviewingTranscript && (
        <div className="flex items-center gap-2 bg-white p-2 rounded-2xl shadow-sm border border-slate-200">
          <button 
            type="button" 
            className={`p-3 rounded-xl transition-colors ${listening ? 'bg-rose-100 text-rose-600' : 'bg-emerald-100 text-emerald-700'}`}
            onClick={toggleListening}
          >
            {listening ? <Square size={20} fill="currentColor"/> : <Mic size={20}/>}
          </button>
          
          <form className="flex-1 flex gap-2" onSubmit={event => { event.preventDefault(); answerQuestion(draft); }}>
            <input 
              value={draft} 
              onChange={event => setDraft(event.target.value)} 
              className="flex-1 text-sm px-2 outline-none"
              placeholder={hi ? 'अपना सवाल लिखें...' : 'Type your question...'}
            />
            <button 
              type="submit" 
              disabled={!draft.trim()} 
              className="p-3 bg-emerald-600 disabled:bg-slate-200 text-white disabled:text-slate-400 rounded-xl transition-colors"
            >
              <ArrowUp size={20}/>
            </button>
          </form>
        </div>
      )}
      
      <p className="text-[10px] text-center text-slate-400 mt-3 px-4">
        {hi ? 'AI गलतियां कर सकता है। कृपया अहम जानकारी की पुष्टि फील्ड वर्कर से करें।' : 'AI can make mistakes. Confirm important info with a field worker.'}
      </p>
    </div>
  </section>;
}
