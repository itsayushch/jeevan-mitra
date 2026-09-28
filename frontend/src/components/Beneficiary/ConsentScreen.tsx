import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Volume2, Shield } from 'lucide-react';

export default function ConsentScreen() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#fdfbf4] flex flex-col items-center p-4 pt-12 md:pt-20 font-sans text-slate-800">
      <div className="w-full max-w-[400px] flex flex-col items-center">
        
        <p className="text-sm font-semibold text-slate-500 mb-6 uppercase tracking-wider">2. Consent</p>

        {/* Main Card */}
        <div className="w-full bg-white rounded-3xl p-8 shadow-sm border border-slate-100 flex flex-col items-center">
          
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-6 text-emerald-700">
            <Shield className="w-8 h-8" />
          </div>

          <h1 className="text-2xl font-bold text-slate-900 text-center mb-1">
            आपके डेटा की सुरक्षा.
          </h1>
          <h2 className="text-lg font-medium text-slate-700 text-center mb-6">
            Our commitment to privacy.
          </h2>

          <p className="text-center text-slate-600 mb-6 text-sm">
            Plain-language privacy notice to local government, privacy notice. Your voice data is safe and only used for recommendations.
          </p>

          <button className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-3 px-6 rounded-full transition-colors mb-8">
            <Volume2 className="w-5 h-5" />
            Play explanation
          </button>

          <div className="w-full mb-8">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Recording preference</label>
            <select className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none font-medium">
              <option>Only for guidance</option>
              <option>Record to improve accuracy</option>
              <option>Do not record</option>
            </select>
          </div>

          <div className="w-full flex flex-col gap-3">
            <button 
              onClick={() => navigate('/beneficiary/interview')}
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white rounded-full py-4 font-bold text-lg transition-colors shadow-md shadow-emerald-700/20"
            >
              Agree and Continue
            </button>
            <button 
              onClick={() => navigate('/')}
              className="w-full bg-transparent hover:bg-emerald-50 text-emerald-700 rounded-full py-4 font-bold text-lg transition-colors"
            >
              Request help
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
