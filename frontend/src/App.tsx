import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import ConsentScreen from './components/Beneficiary/ConsentScreen';
import VoiceInterview from './components/Beneficiary/VoiceInterview';
import { Mic, ShieldCheck, MapPin, Briefcase, GraduationCap, ArrowRight, Volume2 } from 'lucide-react';

function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#fdfbf4] flex flex-col items-center p-4 pt-12 md:pt-20 font-sans text-slate-800">
      <div className="w-full max-w-[400px] flex flex-col items-center">
        {/* Branding header */}
        <div className="w-16 h-16 bg-emerald-700 rounded-2xl flex items-center justify-center mb-6 shadow-md shadow-emerald-700/20">
          <Mic className="text-white w-8 h-8" />
        </div>
        
        <h1 className="text-3xl font-bold text-slate-900 text-center mb-2">
          नमस्ते और स्वागत है!
        </h1>
        <h2 className="text-xl font-medium text-slate-700 text-center mb-8">
          JeevanMitra Livelihood Assistant
        </h2>

        {/* Main Card */}
        <div className="w-full bg-white rounded-3xl p-6 shadow-sm border border-slate-100 mb-6">
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-600 mb-2">Choose your language to start.</label>
            <select className="w-full bg-slate-50 border border-slate-200 text-slate-800 text-lg rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none font-medium">
              <option>Hindi (हिन्दी)</option>
              <option>English</option>
              <option>Tamil (தமிழ்)</option>
            </select>
          </div>

          <button 
            onClick={() => navigate('/beneficiary/consent')}
            className="w-full bg-emerald-700 hover:bg-emerald-800 text-white rounded-full py-4 px-6 font-bold text-lg flex items-center justify-center gap-3 transition-colors shadow-lg shadow-emerald-700/30"
          >
            <Mic className="w-6 h-6" />
            Start speaking
            <Volume2 className="w-5 h-5 ml-2 opacity-80" />
          </button>
        </div>

        {/* Assisted Mode Options */}
        <div className="w-full bg-white rounded-3xl p-6 shadow-sm border border-slate-100">
          <h3 className="text-sm font-semibold text-slate-600 mb-4">Assisted mode options</h3>
          
          <Link to="/field-worker" className="flex items-center gap-3 w-full p-3 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-200">
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="font-medium text-slate-700">Take with a helper</span>
          </Link>
          
          <div className="w-full h-px bg-slate-100 my-2"></div>
          
          <Link to="/district-planner" className="flex items-center gap-3 w-full p-3 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-200">
            <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-700">
              <MapPin className="w-5 h-5" />
            </div>
            <span className="font-medium text-slate-700">District Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  );
}

function FieldWorkerPortal() {
  return (
    <div className="min-h-screen bg-[#fdfbf4] p-4">
      <div className="max-w-[1000px] mx-auto">
        <div className="flex items-center gap-4 mb-8 pt-4">
          <Link to="/" className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center text-slate-600 hover:bg-slate-50">&larr;</Link>
          <h1 className="text-2xl font-bold text-slate-900">Field-Worker Dashboard</h1>
        </div>
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <p className="text-sm font-semibold text-slate-500 mb-1">Cases awaiting review</p>
            <p className="text-3xl font-bold text-slate-900">21</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <p className="text-sm font-semibold text-slate-500 mb-1">Referrals pending</p>
            <p className="text-3xl font-bold text-slate-900">15</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <p className="text-sm font-semibold text-slate-500 mb-1">Follow-ups due</p>
            <p className="text-3xl font-bold text-slate-900">20</p>
          </div>
        </div>
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 min-h-[400px]">
          <p className="text-slate-500">Case list table goes here...</p>
        </div>
      </div>
    </div>
  );
}

function DistrictPlannerConsole() {
  return (
    <div className="min-h-screen bg-[#fdfbf4] p-4">
      <div className="max-w-[1000px] mx-auto">
        <div className="flex items-center gap-4 mb-8 pt-4">
          <Link to="/" className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center text-slate-600 hover:bg-slate-50">&larr;</Link>
          <h1 className="text-2xl font-bold text-slate-900">District Dashboard</h1>
        </div>
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 min-h-[400px]">
          <p className="text-slate-500">Trade Aspiration vs Training Supply Matrix goes here...</p>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen text-slate-800 font-sans selection:bg-emerald-200">
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
