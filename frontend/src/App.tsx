import { Routes, Route, Link } from 'react-router-dom';
import ConsentScreen from './components/Beneficiary/ConsentScreen';
import VoiceInterview from './components/Beneficiary/VoiceInterview';
import { Mic, ShieldCheck, BarChart3, ArrowRight, Sparkles } from 'lucide-react';

function Home() {
  return (
    <div className="max-w-6xl mx-auto p-8 pt-20 space-y-16">
      <header className="text-center space-y-6 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-panel text-brand-100 text-sm font-medium mb-4">
          <Sparkles size={16} className="text-teal-400" />
          <span>Next-Generation Skilling AI</span>
        </div>
        <h1 className="text-6xl font-extrabold tracking-tight mb-2 text-white">
          JeevanMitra <span className="text-gradient">2.0</span>
        </h1>
        <p className="text-slate-300 text-xl leading-relaxed">
          A Verification-First, Multi-Layer Generative AI System for PM-AJAY Livelihood Matching.
          Bridging the gap between rural ambition and verified opportunities.
        </p>
      </header>

      <div className="grid md:grid-cols-3 gap-8 mt-12">
        <Link to="/beneficiary/consent" className="block p-8 rounded-2xl glass-card group">
          <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center mb-6 shadow-lg">
            <Mic className="text-white" size={28} />
          </div>
          <h2 className="text-2xl font-bold mb-3 text-white group-hover:text-teal-300 transition-colors">Beneficiary Flow</h2>
          <p className="text-slate-400 mb-6 leading-relaxed">
            Multi-dialect voice interview, AI profile extraction, and grounded PM-AJAY recommendations.
          </p>
          <div className="flex items-center text-teal-400 font-medium">
            <span>Start Interview</span>
            <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link to="/field-worker" className="block p-8 rounded-2xl glass-card group">
          <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-600 flex items-center justify-center mb-6 shadow-lg">
            <ShieldCheck className="text-white" size={28} />
          </div>
          <h2 className="text-2xl font-bold mb-3 text-white group-hover:text-indigo-300 transition-colors">Field Worker Portal</h2>
          <p className="text-slate-400 mb-6 leading-relaxed">
            Review flagged cases, correct transcripts, verify batch availability, and authorize matches.
          </p>
          <div className="flex items-center text-indigo-400 font-medium">
            <span>Open Portal</span>
            <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link to="/district-planner" className="block p-8 rounded-2xl glass-card group">
          <div className="h-14 w-14 rounded-xl bg-gradient-to-br from-rose-400 to-orange-600 flex items-center justify-center mb-6 shadow-lg">
            <BarChart3 className="text-white" size={28} />
          </div>
          <h2 className="text-2xl font-bold mb-3 text-white group-hover:text-rose-300 transition-colors">Planning Console</h2>
          <p className="text-slate-400 mb-6 leading-relaxed">
            Real-time supply-gap matrices, drift monitoring, and AI-generated district narrative briefs.
          </p>
          <div className="flex items-center text-rose-400 font-medium">
            <span>View Analytics</span>
            <ArrowRight size={18} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>
      </div>
      
      <div className="mt-20 text-center text-slate-500 text-sm">
        <p>Built for the Ministry of Social Justice and Empowerment (MoSJE)</p>
      </div>
    </div>
  );
}

function FieldWorkerPortal() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <Link to="/" className="text-indigo-400 hover:text-indigo-300 mb-8 inline-flex items-center transition-colors">
        &larr; <span className="ml-2">Back to Dashboard</span>
      </Link>
      <header className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-2">Field Worker Portal</h1>
        <p className="text-slate-400">Secure verification and match authorization environment.</p>
      </header>
      <div className="glass-panel p-8 rounded-2xl">
        <div className="flex items-center justify-center h-64 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
          <p>Case Review Dashboard (Pending Integration)</p>
        </div>
      </div>
    </div>
  );
}

function DistrictPlannerConsole() {
  return (
    <div className="p-8 max-w-5xl mx-auto">
      <Link to="/" className="text-rose-400 hover:text-rose-300 mb-8 inline-flex items-center transition-colors">
        &larr; <span className="ml-2">Back to Dashboard</span>
      </Link>
      <header className="mb-10">
        <h1 className="text-4xl font-bold text-white mb-2">District Planning Console</h1>
        <p className="text-slate-400">Aggregated insights and real-time gap analysis.</p>
      </header>
      <div className="glass-panel p-8 rounded-2xl">
        <div className="flex items-center justify-center h-64 text-slate-500 border-2 border-dashed border-slate-700 rounded-xl">
          <p>Demand vs Supply Metrics (Pending Integration)</p>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-teal-500/30">
      <div className="fixed inset-0 z-[-1] bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-[#0f172a] to-[#0f172a]"></div>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/beneficiary/consent" element={<ConsentScreen />} />
        <Route path="/beneficiary/interview" element={<VoiceInterview />} />
        <Route path="/field-worker" element={<FieldWorkerPortal />} />
        <Route path="/district-planner" element={<DistrictPlannerConsole />} />
      </Routes>
    </div>
  );
}

export default App;
