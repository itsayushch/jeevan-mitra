import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, Volume2, RotateCcw, SkipForward } from 'lucide-react';

export default function VoiceInterview() {
  const navigate = useNavigate();
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("I used to repair bicycles and small machines in my village.");
  
  const toggleRecording = () => {
    setIsRecording(!isRecording);
  };

  return (
    <div className="min-h-screen bg-[#fdfbf4] flex flex-col items-center p-4 pt-12 md:pt-20 font-sans text-slate-800">
      <div className="w-full max-w-[400px] flex flex-col items-center">
        
        <p className="text-sm font-semibold text-slate-500 mb-6 uppercase tracking-wider">3. Voice Interview</p>

        {/* Main Card */}
        <div className="w-full bg-white rounded-3xl p-6 shadow-sm border border-slate-100 flex flex-col items-center min-h-[500px] relative">
          
          <div className="w-full flex justify-between items-center mb-8">
            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mr-4">
              <div className="bg-emerald-500 h-full w-[37%]"></div>
            </div>
            <span className="text-xs font-semibold text-slate-400 whitespace-nowrap">3 of 8</span>
          </div>

          <h2 className="text-2xl font-bold text-slate-900 text-center mb-10 px-2 leading-snug">
            What work have you done before, even small jobs?
          </h2>

          {/* Big Mic Button */}
          <button 
            onClick={toggleRecording}
            className={`w-28 h-28 rounded-full flex items-center justify-center mb-10 transition-all shadow-xl ${
              isRecording 
                ? 'bg-rose-500 text-white shadow-rose-500/40 animate-pulse scale-105' 
                : 'bg-emerald-700 text-white shadow-emerald-700/30'
            }`}
          >
            {isRecording ? <MicOff className="w-12 h-12" /> : <Mic className="w-12 h-12" />}
          </button>

          {/* Editable Transcript */}
          <div className="w-full text-left mb-6">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Editable recognized transcript</label>
            <textarea 
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-slate-700 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 min-h-[80px]"
            />
          </div>

          <div className="mt-auto w-full flex gap-3">
            <button className="flex-1 flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-4 rounded-full transition-colors">
              <RotateCcw className="w-4 h-4" />
              Replay
            </button>
            <button className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-6 rounded-full transition-colors">
              Skip
              <SkipForward className="w-4 h-4" />
            </button>
          </div>
          
        </div>

        {/* Temporary Navigation for Demo Purposes */}
        <button 
          onClick={() => navigate('/field-worker')}
          className="mt-8 text-emerald-700 font-semibold text-sm underline"
        >
          (Demo: View Field Worker Dashboard)
        </button>

      </div>
    </div>
  );
}
