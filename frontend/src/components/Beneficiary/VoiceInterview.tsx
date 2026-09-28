import React, { useState, useEffect, useRef } from 'react';
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
    const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition;
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
    <div className="max-w-3xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-[700px]">
      <div className="flex items-center justify-between border-b pb-4 mb-4">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center">
          <Volume2 className="w-6 h-6 mr-2 text-blue-600" />
          Voice Interview
        </h2>
        {isCompleted && (
          <span className="flex items-center text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm font-medium">
            <CheckCircle className="w-4 h-4 mr-1" />
            Interview Complete
          </span>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-4 p-4 bg-gray-50 rounded-xl mb-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex items-end space-x-2 max-w-[80%] ${msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.sender === 'user' ? 'bg-blue-600' : 'bg-green-600'}`}>
                {msg.sender === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
              </div>
              <div className={`p-4 rounded-2xl ${msg.sender === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'}`}>
                {msg.text}
              </div>
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="flex justify-start">
            <div className="flex items-end space-x-2">
              <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="p-4 bg-white border border-gray-200 rounded-2xl rounded-bl-none text-gray-500 flex items-center shadow-sm">
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Thinking...
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t flex justify-center">
        <button
          onClick={toggleRecording}
          disabled={isCompleted || isProcessing}
          className={`flex items-center justify-center space-x-3 w-64 py-4 px-6 rounded-full font-bold text-lg transition-all shadow-md ${
            isRecording 
              ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse shadow-red-200' 
              : isCompleted || isProcessing
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-200'
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
  );
}
