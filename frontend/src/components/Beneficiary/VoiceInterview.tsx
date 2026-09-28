import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Mic, MicOff, RotateCcw, SkipForward, Loader2 } from 'lucide-react';

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
  const [isProcessing, setIsProcessing] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [currentQuestion, setCurrentQuestion] = useState("");
  
  const recognitionRef = useRef<any>(null);
  const synthesisRef = useRef<SpeechSynthesis>(window.speechSynthesis);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'hi-IN';

      recognitionRef.current.onresult = (event: any) => {
        const text = event.results[0][0].transcript;
        setTranscript(text);
        // Automatically send the spoken text after recognized
        handleUserSubmit(text);
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
  }, [sessionId]);

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
      const beneficiaryId = `ben_${Math.random().toString(36).substr(2, 9)}`;
      
      const res = await axios.post('/api/interview/start', {
        beneficiaryId,
        channel: 'web_app',
        language: 'hi'
      });
      
      setSessionId(res.data.session.id);
      
      const firstQ = res.data.firstQuestion?.text || "नमस्ते, क्या हम शुरू करें?";
      setCurrentQuestion(firstQ);
      speakText(firstQ);
    } catch (error) {
      console.error("Failed to start interview", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUserSubmit = async (textToSend: string) => {
    if (!sessionId || !textToSend.trim()) return;
    
    try {
      setIsProcessing(true);
      const res = await axios.post('/api/interview/turn', {
        sessionId,
        speechOrText: textToSend,
        isAudio: false
      });
      
      const data: TurnResponse = res.data;
      
      const botReply = data.spokenReply + (data.nextQuestion ? ` ${data.nextQuestion.text}` : "");
      
      if (botReply) {
        setCurrentQuestion(botReply);
        setTranscript(""); // Clear transcript for next answer
        speakText(botReply);
      }
      
      if (data.completed) {
        setIsCompleted(true);
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
      synthesisRef.current.cancel();
      try {
        recognitionRef.current?.start();
        setIsRecording(true);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleReplay = () => {
    speakText(currentQuestion);
  };

  const handleSkip = () => {
    handleUserSubmit("I want to skip this question.");
  };

  const handleManualSubmit = () => {
    handleUserSubmit(transcript);
  };

  return (
    <div className="min-h-screen bg-[#fdfbf4] flex flex-col items-center p-4 pt-12 md:pt-20 font-sans text-slate-800">
      <div className="w-full max-w-[400px] flex flex-col items-center">
        
        <p className="text-sm font-semibold text-slate-500 mb-6 uppercase tracking-wider">3. Voice Interview</p>

        {/* Main Card */}
        <div className="w-full bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex flex-col items-center min-h-[500px] relative">
          
          <div className="w-full flex justify-between items-center mb-8">
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mr-4">
              <div className="bg-emerald-500 h-full w-[37%] transition-all duration-500"></div>
            </div>
            <span className="text-xs font-semibold text-slate-400 whitespace-nowrap">3 of 8</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10 px-2 leading-snug min-h-[80px]">
            {isProcessing ? (
              <span className="flex items-center justify-center text-emerald-600 animate-pulse">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Thinking...
              </span>
            ) : currentQuestion ? currentQuestion : "Loading..."}
          </h2>

          {/* Big Mic Button */}
          <button 
            onClick={toggleRecording}
            disabled={isProcessing || isCompleted}
            className={`w-28 h-28 rounded-full flex items-center justify-center mb-10 transition-all shadow-xl ${
              isRecording 
                ? 'bg-rose-500 text-white shadow-rose-500/40 animate-pulse scale-105' 
                : isProcessing || isCompleted
                  ? 'bg-slate-300 text-slate-500 shadow-none cursor-not-allowed'
                  : 'bg-emerald-700 text-white shadow-emerald-700/30 hover:bg-emerald-800'
            }`}
          >
            {isRecording ? <MicOff className="w-12 h-12" /> : <Mic className="w-12 h-12" />}
          </button>

          {/* Editable Transcript */}
          <div className="w-full text-left mb-6">
            <div className="flex justify-between items-end mb-2">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">Editable recognized transcript</label>
            </div>
            <textarea 
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              disabled={isProcessing}
              placeholder="What you say will appear here..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-slate-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 min-h-[80px]"
            />
            {transcript.trim() && !isProcessing && (
              <button 
                onClick={handleManualSubmit}
                className="w-full mt-2 bg-slate-800 hover:bg-slate-900 text-white font-medium py-2 rounded-lg transition-colors"
              >
                Send Answer
              </button>
            )}
          </div>

          <div className="mt-auto w-full flex gap-3">
            <button 
              onClick={handleReplay}
              disabled={isProcessing || isCompleted}
              className="flex-1 flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-full transition-colors disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              Replay
            </button>
            <button 
              onClick={handleSkip}
              disabled={isProcessing || isCompleted}
              className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-6 rounded-full transition-colors disabled:opacity-50"
            >
              Skip
              <SkipForward className="w-4 h-4" />
            </button>
          </div>
          
        </div>

      </div>
    </div>
  );
}
