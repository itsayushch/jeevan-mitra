import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, ShieldCheck, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function ConsentScreen() {
  const navigate = useNavigate();
  const [hasAgreed, setHasAgreed] = useState(false);

  const handleStart = () => {
    if (hasAgreed) {
      navigate('/beneficiary/interview');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 pt-10">
      <div className="max-w-2xl w-full glass-panel rounded-3xl p-10 shadow-2xl relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-teal-500/20 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10">
          <div className="text-center mb-10">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-teal-400 to-emerald-600 mb-6 shadow-lg shadow-teal-500/30">
              <ShieldCheck className="text-white w-10 h-10" />
            </div>
            <h1 className="text-4xl font-extrabold text-white mb-4">DPDP Consent</h1>
            <p className="text-lg text-slate-300 max-w-lg mx-auto">
              Before we begin your voice interview, please review how we handle your data.
            </p>
          </div>

          <div className="space-y-4 mb-10">
            <div className="glass-card p-5 rounded-2xl flex items-start gap-4">
              <div className="mt-1 bg-teal-500/20 p-2 rounded-full text-teal-400">
                <Mic size={20} />
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg mb-1">Voice Recording</h3>
                <p className="text-slate-400">Your voice will be recorded securely to understand your preferences and skills.</p>
              </div>
            </div>

            <div className="glass-card p-5 rounded-2xl flex items-start gap-4">
              <div className="mt-1 bg-indigo-500/20 p-2 rounded-full text-indigo-400">
                <CheckCircle2 size={20} />
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg mb-1">Data Privacy</h3>
                <p className="text-slate-400">Your information is solely used for matching you with PM-AJAY skilling opportunities and will never be sold.</p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-700/50 mb-8">
            <label className="flex items-center gap-4 cursor-pointer group">
              <div className="relative flex items-center justify-center">
                <input 
                  type="checkbox" 
                  className="w-6 h-6 peer appearance-none rounded border-2 border-slate-500 checked:bg-teal-500 checked:border-teal-500 transition-colors"
                  checked={hasAgreed}
                  onChange={(e) => setHasAgreed(e.target.checked)}
                />
                <CheckCircle2 size={16} className="absolute text-white opacity-0 peer-checked:opacity-100 pointer-events-none transition-opacity" />
              </div>
              <span className="text-slate-300 group-hover:text-white transition-colors">
                I have read the notice and consent to the processing of my voice and profile data for livelihood matching.
              </span>
            </label>
          </div>

          <div className="flex gap-4">
            <button 
              onClick={() => navigate('/')} 
              className="flex-1 py-4 px-6 rounded-xl font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all duration-200"
            >
              Cancel
            </button>
            <button 
              onClick={handleStart}
              disabled={!hasAgreed}
              className={`flex-1 flex items-center justify-center gap-2 py-4 px-6 rounded-xl font-bold transition-all duration-300 ${
                hasAgreed 
                ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-lg shadow-teal-500/25 hover:shadow-teal-500/40 hover:-translate-y-1' 
                : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
              }`}
            >
              Start Interview
              <ArrowRight size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
