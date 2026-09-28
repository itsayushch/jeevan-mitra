import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Mic, MicOff, CheckCircle, Volume2, User, Bot, Loader2 } from 'lucide-react';

interface TurnResponse {
  completed: boolean;
  spokenReply: string;
  transcriptRecognized: string;
  nextQuestion?: { text: string };
}

export default function VoiceInterview() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [messages, setMessages] = useState<{ sender: 'bot' | 'user', text: string }[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  
  const recognitionRef = useRef<any>(null);
  const synthesisRef = useRef<SpeechSynthesis>(window.speechSynthesis);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'hi-IN'; // Hindi language

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        handleUserSpeech(transcript);
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    } else {
      console.warn("Speech Recognition API not supported in this browser.");
    }
  }, []);

  // Start Interview on mount
  useEffect(() => {
    startInterview();
  }, []);

  const speakText = (text: string) => {
    if (!text) return;
    synthesisRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'hi-IN';
    synthesisRef.current.speak(utterance);
  };

  const startInterview = async () => {
    try {
      setIsProcessing(true);
      // Hardcoded dummy beneficiary ID for demo purposes
      const beneficiaryId = `ben_${Math.random().toString(36).substr(2, 9)}`;
      
      const res = await axios.post('/api/interview/start', {
        beneficiaryId,
        channel: 'web_app',
        language: 'hi'
      });
      
      setSessionId(res.data.session.id);
      
      const firstQ = res.data.firstQuestion?.text || "नमस्ते, क्या हम शुरू करें?";
      setMessages([{ sender: 'bot', text: firstQ }]);
      speakText(firstQ);
    } catch (error) {
      console.error("Failed to start interview", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUserSpeech = async (transcript: string) => {
    setMessages(prev => [...prev, { sender: 'user', text: transcript }]);
    
    if (!sessionId) return;
    
    try {
      setIsProcessing(true);
      const res = await axios.post('/api/interview/turn', {
        sessionId,
        speechOrText: transcript,
        isAudio: false
      });
      
      const data: TurnResponse = res.data;
      
      const botReply = data.spokenReply + (data.nextQuestion ? ` ${data.nextQuestion.text}` : "");
      
      if (botReply) {
        setMessages(prev => [...prev, { sender: 'bot', text: botReply }]);
        speakText(botReply);
      }
      
      if (data.completed) {
        setIsCompleted(true);
        // Wait a bit and navigate to confirmation screen
        setTimeout(() => {
          navigate(`/beneficiary/confirm/${sessionId}`);
        }, 5000);
      }
    } catch (error) {
      console.error("Failed to process turn", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      recognitionRef.current?.stop();
    } else {
      // Cancel any ongoing speech so mic can pick up clearly
      synthesisRef.current.cancel();
      try {
        recognitionRef.current?.start();
        setIsRecording(true);
      } catch (err) {
        console.error(err);
      }
    }
  };

  return (
    <div className="min-h-screen p-4 flex flex-col items-center justify-center">
      <div className="w-full max-w-4xl flex flex-col h-[85vh] glass-panel rounded-3xl overflow-hidden relative shadow-2xl">
        
        {/* Decorative background glow */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
          <div className="absolute top-0 right-0 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 flex flex-col h-full">
          <div className="flex items-center justify-between p-6 border-b border-slate-700/50 bg-slate-900/40 backdrop-blur-md">
            <h2 className="text-2xl font-bold text-white flex items-center">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center mr-4 shadow-lg shadow-teal-500/20">
                <Volume2 className="w-5 h-5 text-white" />
              </div>
              AI Voice Interview
            </h2>
            {isCompleted && (
              <span className="flex items-center text-teal-400 bg-teal-500/10 border border-teal-500/20 px-4 py-2 rounded-full text-sm font-semibold shadow-sm">
                <CheckCircle className="w-4 h-4 mr-2" />
                Interview Complete
              </span>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex items-end space-x-3 max-w-[85%] ${msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ${msg.sender === 'user' ? 'bg-gradient-to-br from-indigo-500 to-purple-600 shadow-indigo-500/20' : 'bg-gradient-to-br from-teal-500 to-emerald-600 shadow-teal-500/20'}`}>
                    {msg.sender === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
                  </div>
                  <div className={`p-5 text-[15px] leading-relaxed shadow-lg backdrop-blur-md ${
                    msg.sender === 'user' 
                      ? 'bg-indigo-600/90 text-white rounded-2xl rounded-br-sm border border-indigo-500/30' 
                      : 'bg-slate-800/80 text-slate-200 rounded-2xl rounded-bl-sm border border-slate-700'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="flex items-end space-x-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="p-5 bg-slate-800/80 backdrop-blur-md border border-slate-700 rounded-2xl rounded-bl-sm text-slate-400 flex items-center shadow-lg">
                    <Loader2 className="w-5 h-5 animate-spin mr-3 text-teal-400" />
                    Analyzing response...
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-6 border-t border-slate-700/50 bg-slate-900/40 backdrop-blur-md flex justify-center">
            <button
              onClick={toggleRecording}
              disabled={isCompleted || isProcessing}
              className={`flex items-center justify-center space-x-3 w-72 py-5 px-8 rounded-full font-bold text-lg transition-all duration-300 shadow-2xl ${
                isRecording 
                  ? 'bg-rose-500 text-white hover:bg-rose-600 animate-pulse shadow-rose-500/40 hover:-translate-y-1' 
                  : isCompleted || isProcessing
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                    : 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white hover:shadow-teal-500/40 shadow-teal-500/20 hover:-translate-y-1'
              }`}
            >
              {isRecording ? (
                <>
                  <MicOff className="w-6 h-6" />
                  <span>Stop Speaking</span>
                </>
              ) : (
                <>
                  <Mic className="w-6 h-6" />
                  <span>Tap to Speak</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
