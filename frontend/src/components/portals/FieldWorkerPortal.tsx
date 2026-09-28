import React, { useState } from 'react';
import { CheckCircle2, ArrowLeft } from 'lucide-react';
import { SoundFX, speakText } from '../../utils/speech';

interface FieldWorkerPortalProps {
  onBack: () => void;
}

export const FieldWorkerPortal: React.FC<FieldWorkerPortalProps> = ({ onBack }) => {
  const [approved, setApproved] = useState(false);
  const [edu, setEdu] = useState('Class 10 Pass');
  const [mobility, setMobility] = useState('Max 5 km');
  const [aspiration, setAspiration] = useState('Mushroom Cultivation & Agri');

  const handleApprove = () => {
    SoundFX.playChime('success');
    setApproved(true);
    speakText('Case referral approved and logged under PM-AJAY GIA verification protocol.', 'en');
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4 md:p-6 text-slate-800">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors border border-slate-200"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-900">
            Field-Worker Verification Portal
          </h1>
          <p className="text-xs font-semibold text-emerald-700">
            Claim 1: Verified Match Protocol (Outside LLM Verification)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-emerald-50 p-4 rounded-2xl border border-emerald-200 relative">
          <p className="text-xs font-bold text-emerald-800 mb-1">Cases Awaiting Review</p>
          <p className="text-2xl font-black text-emerald-900">12</p>
          <div className="absolute top-4 right-4 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <p className="text-xs font-bold text-slate-500 mb-1">Verified Batches</p>
          <p className="text-2xl font-black text-slate-900">8</p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <p className="text-xs font-bold text-slate-500 mb-1">Referrals Pending</p>
          <p className="text-2xl font-black text-slate-900">5</p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <p className="text-xs font-bold text-slate-500 mb-1">Follow-ups Due</p>
          <p className="text-2xl font-black text-slate-900">3</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Case Review Card */}
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-black text-slate-900">
              Case Review: #AJAY-8291
            </h2>
            <span className="text-[10px] font-bold bg-amber-100 text-amber-900 px-2.5 py-1 rounded-full">
              Voice Conf: 91%
            </span>
          </div>

          <div className="bg-slate-50 p-4 rounded-2xl mb-4 text-xs space-y-1 border border-slate-100">
            <p className="text-slate-500">
              Beneficiary: <strong className="text-slate-900">Rajesh Kumar</strong> (SC | Village: Chhajlet)
            </p>
            <p className="text-slate-500">Recorded Intent:</p>
            <p className="text-xs font-medium italic text-slate-700 bg-white p-2.5 rounded-xl border border-slate-200">
              "10th pass, family farming background, interested in Mushroom cultivation & local enterprise within 5 km."
            </p>
          </div>

          <h3 className="font-extrabold text-xs text-slate-800 uppercase tracking-wider mb-3">
            Field Verification Fields:
          </h3>

          <div className="space-y-3 mb-5 text-xs">
            <div className="flex items-center gap-3">
              <label className="w-24 text-slate-500 font-semibold">Education:</label>
              <input
                type="text"
                value={edu}
                onChange={(e) => setEdu(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-800 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="flex items-center gap-3">
              <label className="w-24 text-slate-500 font-semibold">Mobility:</label>
              <input
                type="text"
                value={mobility}
                onChange={(e) => setMobility(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-800 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div className="flex items-center gap-3">
              <label className="w-24 text-slate-500 font-semibold">Aspiration:</label>
              <input
                type="text"
                value={aspiration}
                onChange={(e) => setAspiration(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-800 focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="space-y-2 mb-6 text-xs font-medium text-slate-700">
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" />
              <span>SC Caste Certificate / Self-Declaration Verified</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" />
              <span>Aadhaar Biometric & Residence Proof Attached</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" defaultChecked className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" />
              <span>Local Batch Availability Confirmed (Chhajlet Center)</span>
            </label>
          </div>

          {approved ? (
            <div className="bg-emerald-50 border-2 border-emerald-500 rounded-2xl p-3.5 text-center text-xs font-bold text-emerald-900 flex items-center justify-center gap-2 animate-fadeIn">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>Referral Approved & Enrolment Packet Dispatched!</span>
            </div>
          ) : (
            <div className="flex gap-3">
              <button
                onClick={handleApprove}
                className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 px-4 rounded-2xl text-xs shadow-md transition-colors"
              >
                Approve Verified Match
              </button>
              <button
                onClick={() => SoundFX.playChime('click')}
                className="bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold py-3 px-4 rounded-2xl text-xs transition-colors"
              >
                Flag Review
              </button>
            </div>
          )}
        </div>

        {/* Local Centre Capacity Card */}
        <div className="space-y-4">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <h3 className="text-sm font-black text-slate-900 mb-3">
              Nearest Training Capacity (Chhajlet Centre)
            </h3>
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <p className="font-black text-slate-800">Mushroom Cultivation Batch #4</p>
                  <p className="text-[10px] text-slate-500">Starts: 15 Oct • 25 Seats</p>
                </div>
                <span className="text-[10px] font-extrabold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  18 / 25 Filled
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                <div>
                  <p className="font-black text-slate-800">Retail Operations Batch #2</p>
                  <p className="text-[10px] text-slate-500">Starts: 20 Oct • 30 Seats</p>
                </div>
                <span className="text-[10px] font-extrabold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                  28 / 30 Filled
                </span>
              </div>
            </div>
          </div>

          <div className="bg-indigo-50 border border-indigo-100 p-5 rounded-3xl text-xs text-indigo-950">
            <p className="font-extrabold mb-1">Human-in-the-Loop Protocol Note:</p>
            <p className="text-slate-600 leading-relaxed">
              No beneficiary is enrolled into skilling without field verification of distance, caste certificate, and batch schedule.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
