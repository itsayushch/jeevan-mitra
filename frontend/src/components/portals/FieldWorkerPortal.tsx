import React, { useState, useEffect } from 'react';
import { CheckCircle2, ArrowLeft } from 'lucide-react';
import { SoundFX, speakText } from '../../utils/speech';
import { api } from '../../lib/api';
import { OutcomeSimulator } from './OutcomeSimulator';

interface FieldWorkerPortalProps {
  onBack: () => void;
}

export const FieldWorkerPortal: React.FC<FieldWorkerPortalProps> = ({ onBack }) => {
  const [approved, setApproved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState<any[]>([]);
  const [selectedCase, setSelectedCase] = useState<any>(null);
  const [verified, setVerified] = useState(false);
  const [referralId, setReferralId] = useState<string | null>(null);
  
  // Form checks
  const [casteVerified, setCasteVerified] = useState(false);
  const [residenceVerified, setResidenceVerified] = useState(false);
  const [batchConfirmed, setBatchConfirmed] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getWorkerCases();
        setCases(data.cases || []);
        if (data.cases && data.cases.length > 0) {
          const caseData = await api.getWorkerCaseDetails(data.cases[0].beneficiary_id);
          setSelectedCase(caseData);
        }
      } catch (err) {
        console.error('Failed to load cases:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleVerify = async () => {
    if (!selectedCase) return;
    try {
      const opportunity = selectedCase.recommendations?.[0];
      if (!opportunity) return;
      await api.verifyOpportunity(opportunity.local_opportunity_id, {
        batch_status: 'active',
        available_seats: 5,
        notes: 'Verified physically in the village.'
      });
      setVerified(true);
      SoundFX.playChime('success');
    } catch (err) {
      console.error('Failed to verify:', err);
      alert('Verification failed');
    }
  };

  const handleApprove = async () => {
    if (!verified || !casteVerified || !residenceVerified || !batchConfirmed) {
      alert("Please complete all verification steps first.");
      return;
    }
    try {
      const opportunity = selectedCase.recommendations?.[0];
      const res = await api.approveReferral(selectedCase.beneficiary_id, {
        recommendation_id: opportunity.recommendation_id,
        local_opportunity_id: opportunity.local_opportunity_id,
        notes: 'All documents checked',
        caste_document_verified: casteVerified,
        income_criteria_verified: true,
        residence_proof_verified: residenceVerified
      });
      if (res.referral_id) {
          setReferralId(res.referral_id);
      }
      SoundFX.playChime('success');
      setApproved(true);
      speakText('Case referral approved and logged under PM-AJAY GIA verification protocol.', 'en');
    } catch (err: any) {
      console.error('Failed to approve:', err);
      alert(err.message || 'Failed to approve');
    }
  };

  if (loading) return <div className="p-6">Loading cases...</div>;

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
            Review profiles and confirm local opportunities
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-emerald-50 p-4 rounded-2xl border border-emerald-200 relative">
          <p className="text-xs font-bold text-emerald-800 mb-1">Cases Awaiting Review</p>
          <p className="text-2xl font-black text-emerald-900">{cases.length}</p>
          <div className="absolute top-4 right-4 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
        </div>
      </div>

      {selectedCase ? (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-black text-slate-900">
                Case Review: #{selectedCase.beneficiary_id.substring(0,8)}
              </h2>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl mb-4 text-xs space-y-1 border border-slate-100">
              <p className="text-slate-500">
                Extracted Profile: 
              </p>
              <pre className="text-xs font-medium text-slate-700 bg-white p-2.5 rounded-xl border border-slate-200 overflow-auto max-h-40">
                {JSON.stringify(selectedCase.profile, null, 2)}
              </pre>
            </div>

            <h3 className="font-extrabold text-xs text-slate-800 uppercase tracking-wider mb-3">
              Field Verification Checks:
            </h3>

            <div className="space-y-2 mb-6 text-xs font-medium text-slate-700">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={casteVerified} onChange={(e) => setCasteVerified(e.target.checked)} className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" />
                <span>SC Caste Certificate / Self-Declaration Verified</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={residenceVerified} onChange={(e) => setResidenceVerified(e.target.checked)} className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" />
                <span>Aadhaar Biometric & Residence Proof Attached</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={batchConfirmed} onChange={(e) => setBatchConfirmed(e.target.checked)} className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4" />
                <span>Local Batch Availability Confirmed</span>
              </label>
            </div>

            {!verified ? (
              <button
                onClick={handleVerify}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-2xl text-xs shadow-md transition-colors mb-3"
              >
                1. Verify Opportunity Availability
              </button>
            ) : approved ? (
              <div className="bg-emerald-50 border-2 border-emerald-500 rounded-2xl p-3.5 text-center text-xs font-bold text-emerald-900 flex items-center justify-center gap-2 animate-fadeIn">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>Referral Approved & Enrolment Packet Dispatched!</span>
              </div>
            ) : (
              <button
                onClick={handleApprove}
                className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 px-4 rounded-2xl text-xs shadow-md transition-colors"
              >
                2. Approve Verified Match
              </button>
            )}
          </div>

          <div className="space-y-4">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
              <h3 className="text-sm font-black text-slate-900 mb-3">
                Recommendation: {selectedCase.recommendations?.[0]?.qualification_name || "None"}
              </h3>
              <div className="space-y-3 text-xs">
                <p>Status: {selectedCase.recommendations?.[0]?.match_state || "No match"}</p>
                <p>Confidence: {selectedCase.recommendations?.[0]?.match_score ? (selectedCase.recommendations[0].match_score * 100).toFixed(0) + '%' : 'N/A'}</p>
                <p>Opportunity ID: {selectedCase.recommendations?.[0]?.local_opportunity_id}</p>
              </div>
            </div>

            <div className="bg-indigo-50 border border-indigo-100 p-5 rounded-3xl text-xs text-indigo-950">
              <p className="font-extrabold mb-1">Human-in-the-Loop Protocol Note:</p>
              <p className="text-slate-600 leading-relaxed">
                No beneficiary is enrolled into skilling without field verification of distance, caste certificate, and batch schedule.
              </p>
            </div>
            {referralId && <OutcomeSimulator referralId={referralId} />}
          </div>
        </div>
      ) : (
        <div className="p-4 text-center text-slate-500">No cases found</div>
      )}
    </div>
  );
};
