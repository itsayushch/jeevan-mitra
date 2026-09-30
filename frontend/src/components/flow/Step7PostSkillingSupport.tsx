import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Banknote,
  Briefcase,
  Handshake,
  ChevronRight,
  CheckCircle2,
  RotateCcw,
  Clock,
  PhoneCall,
  XCircle,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import type { Language } from '../../types';
import { mentorsData } from '../../data/mockData';
import { SoundFX } from '../../utils/speech';
import { api, BeneficiaryReferralDisplay } from '../../lib/api';

interface Step7Props {
  language: Language;
  onNavigateModule: (moduleKey: string) => void;
  onRestart: () => void;
  onPrev: () => void;
}

export const Step7PostSkillingSupport: React.FC<Step7Props> = ({
  language,
  onNavigateModule,
  onRestart,
  onPrev,
}) => {
  const topMentor = mentorsData[0]; // Sunita Devi
  const isHindi = language === 'hi';

  const [referrals, setReferrals] = useState<BeneficiaryReferralDisplay[]>([
    {
      id: 'ref_mor_101',
      case_id: 'case_moradabad_8291',
      opportunity_title: 'Mushroom Cultivation Batch #4 (PM-AJAY GIA)',
      provider_name: 'Krishi Vigyan Kendra Chhajlet',
      district: 'Moradabad',
      status: 'CONTACTED',
      display_status: {
        title: isHindi ? 'परामर्शदाता ने संपर्क किया' : 'Field Worker Contacted You',
        description: isHindi
          ? 'क्षेत्रीय कार्यकर्ता ने आपके साथ बैच की जानकारी साझा करने के लिए संपर्क किया है।'
          : 'Your assigned field worker has initiated contact to discuss batch timing and travel arrangements.',
      },
      created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);
  const [supportRequested, setSupportRequested] = useState<Record<string, boolean>>({});
  const [declined, setDeclined] = useState<Record<string, boolean>>({});
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  useEffect(() => {
    async function loadBeneficiaryReferrals() {
      try {
        const res = await api.getMyReferrals();
        if (res?.referrals && res.referrals.length > 0) {
          setReferrals(res.referrals);
        }
      } catch {
        // Fallback to sample data for demo/unauthenticated mode
      }
    }
    loadBeneficiaryReferrals();
  }, [language]);

  const handleStepClick = (moduleKey: string) => {
    SoundFX.playChime('click');
    onNavigateModule(moduleKey);
  };

  const handleRequestSupport = async (refId: string) => {
    setLoadingAction(refId);
    try {
      await api.requestReferralSupport(refId, 'Beneficiary requested follow-up call');
      setSupportRequested((prev) => ({ ...prev, [refId]: true }));
      SoundFX.playChime('success');
    } catch {
      setSupportRequested((prev) => ({ ...prev, [refId]: true }));
      SoundFX.playChime('success');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleDecline = async (refId: string) => {
    if (!window.confirm(isHindi ? 'क्या आप इस रेफरल को रद्द करना चाहते हैं?' : 'Are you sure you want to decline this referral?')) {
      return;
    }
    setLoadingAction(refId);
    try {
      await api.declineReferral(refId, 'Beneficiary opted out via portal');
      setDeclined((prev) => ({ ...prev, [refId]: true }));
      SoundFX.playChime('click');
    } catch {
      setDeclined((prev) => ({ ...prev, [refId]: true }));
      SoundFX.playChime('click');
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="flex flex-col justify-between min-h-[580px] p-5 text-slate-800">
      <div>
        {/* Top Header */}
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={onPrev}
            className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              {isHindi ? 'प्रशिक्षण उपरांत एवं रेफरल सहयोग' : 'Post-Skilling & Referral Support.'}
            </h2>
            <p className="text-[11px] font-semibold text-emerald-700">
              {isHindi ? 'सत्यापित प्रशिक्षण एवं आजीविका प्रगति' : 'Track your verified batch & field-worker referral'}
            </p>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* BENEFICIARY SAFE REFERRAL TIMELINE (SPRINT 5) */}
        {/* ========================================================================= */}
        {referrals.length > 0 && (
          <div className="mb-5 space-y-3">
            <h3 className="text-xs font-black uppercase text-slate-700 tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>{isHindi ? 'सक्रिय रेफरल एवं स्थिति' : 'Your Active Referral Status'}</span>
            </h3>

            {referrals.map((ref) => {
              const isSupportSent = supportRequested[ref.id];
              const isDeclined = declined[ref.id] || ref.status === 'BENEFICIARY_DECLINED';

              return (
                <div
                  key={ref.id}
                  className="bg-white rounded-3xl p-4 border border-emerald-200 shadow-xs relative overflow-hidden"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100 font-bold inline-block mb-1">
                        {ref.opportunity_title}
                      </span>
                      <h4 className="text-xs font-black text-slate-900">{ref.provider_name}</h4>
                      <p className="text-[10px] text-slate-500 font-medium">District: {ref.district}</p>
                    </div>

                    <span
                      className={`text-[10px] font-black uppercase px-2.5 py-1 rounded-full border shrink-0 ${
                        isDeclined
                          ? 'bg-slate-100 text-slate-600 border-slate-200'
                          : 'bg-emerald-100 text-emerald-900 border-emerald-300'
                      }`}
                    >
                      {isDeclined
                        ? isHindi
                          ? 'रद्द किया गया'
                          : 'Declined'
                        : ref.display_status?.title || ref.status}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100 mb-3 leading-relaxed">
                    {isDeclined
                      ? isHindi
                        ? 'आपने इस रेफरल को अस्वीकार कर दिया है।'
                        : 'You have declined this referral.'
                      : ref.display_status?.description ||
                        'Your case is actively being processed by local field workers.'}
                  </p>

                  {/* Beneficiary Action Buttons */}
                  {!isDeclined && (
                    <div className="flex items-center gap-2 pt-1 border-t border-slate-100">
                      <button
                        onClick={() => handleRequestSupport(ref.id)}
                        disabled={isSupportSent || loadingAction === ref.id}
                        className={`text-[11px] font-bold py-1.5 px-3 rounded-xl flex items-center gap-1.5 transition-all ${
                          isSupportSent
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-2xs'
                        }`}
                      >
                        <PhoneCall className="w-3 h-3" />
                        <span>
                          {isSupportSent
                            ? isHindi
                              ? 'कॉल अनुरोध भेजा गया'
                              : 'Callback Requested'
                            : isHindi
                            ? 'सहायता / कॉल अनुरोध'
                            : 'Request Worker Call'}
                        </span>
                      </button>

                      <button
                        onClick={() => handleDecline(ref.id)}
                        disabled={loadingAction === ref.id}
                        className="text-[11px] font-bold py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-700 border border-slate-200 transition-colors flex items-center gap-1"
                      >
                        <XCircle className="w-3 h-3" />
                        <span>{isHindi ? 'आवश्यकता नहीं' : 'Not Interested'}</span>
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Vertical Connected Pathway Steps */}
        <div className="relative pl-6 space-y-4 my-3">
          <div className="absolute left-[29px] top-6 bottom-6 w-0.5 bg-gradient-to-b from-emerald-500 via-teal-500 to-amber-500"></div>

          {/* Step 1: Connect with Financial Consultant */}
          <div
            onClick={() => handleStepClick('financial-grants')}
            className="relative bg-white rounded-3xl p-4 border border-slate-200/90 shadow-sm hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="absolute -left-9 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-emerald-100 border-2 border-emerald-600 text-emerald-800 flex items-center justify-center text-xs font-black shadow-xs">
              1
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
                  <Banknote className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xs font-extrabold text-slate-900 group-hover:text-emerald-700 transition-colors">
                    {isHindi ? 'वित्तीय सलाहकार से जुड़ें' : 'Connect with Financial Consultant'}
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    {isHindi ? 'मुद्रा ऋण एवं पीएम-अजय अनुदान' : 'MUDRA loans & PM-AJAY capital grants'}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 group-hover:translate-x-0.5 transition-all" />
            </div>
          </div>

          {/* Step 2: View Local Job Openings */}
          <div
            onClick={() => handleStepClick('jobs-map')}
            className="relative bg-white rounded-3xl p-4 border border-slate-200/90 shadow-sm hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="absolute -left-9 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-teal-100 border-2 border-teal-600 text-teal-800 flex items-center justify-center text-xs font-black shadow-xs">
              2
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
                  <Briefcase className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xs font-extrabold text-slate-900 group-hover:text-teal-700 transition-colors">
                    {isHindi ? 'स्थानीय रोजगार अवसर देखें' : 'View Local Job Openings'}
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    {isHindi ? '5 किमी के दायरे में सत्यापित नियोजक' : 'Verified employers within 5 km radius'}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600 group-hover:translate-x-0.5 transition-all" />
            </div>
          </div>

          {/* Step 3: Enterprise Mentorship */}
          <div
            onClick={() => handleStepClick('community-mentors')}
            className="relative bg-white rounded-3xl p-4 border border-slate-200/90 shadow-sm hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="absolute -left-9 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-amber-100 border-2 border-amber-600 text-amber-800 flex items-center justify-center text-xs font-black shadow-xs">
              3
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
                  <Handshake className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xs font-extrabold text-slate-900 group-hover:text-amber-700 transition-colors">
                    {isHindi ? 'उद्यमिता मार्गदर्शन' : 'Enterprise Mentorship'}
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    {isHindi ? 'अनुभवी उद्यमियों से सीधा मार्गदर्शन' : '1-on-1 guidance with veteran entrepreneurs'}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 group-hover:translate-x-0.5 transition-all" />
            </div>
          </div>
        </div>

        {/* Assigned Verified Mentor Spotlight */}
        <div className="bg-gradient-to-tr from-amber-50 to-orange-50 border border-amber-200 rounded-3xl p-4 shadow-2xs mt-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-white border border-amber-300 flex items-center justify-center text-2xl shadow-xs shrink-0">
              {topMentor.avatar}
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-extrabold text-slate-900">{topMentor.name}</h4>
                <span className="text-[10px] font-bold text-amber-800 bg-amber-200/60 px-2 py-0.5 rounded-full">
                  ★ {topMentor.rating}
                </span>
              </div>
              <p className="text-[11px] font-semibold text-slate-600">{topMentor.role}</p>
              <p className="text-[10px] text-slate-400">
                {isHindi ? 'ध्वनि परामर्श के लिए उपलब्ध' : 'Available for Voice Consultation'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Restart or Explore More */}
      <div className="pt-4 flex items-center gap-2">
        <button
          onClick={onRestart}
          className="px-4 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>{isHindi ? 'प्रारंभ करें' : 'Start Over'}</span>
        </button>

        <button
          onClick={() => handleStepClick('jobs-map')}
          className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white rounded-2xl py-3 px-4 font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-emerald-700/20 transition-all uppercase tracking-wider"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>{isHindi ? 'स्थानीय नक्शा देखें' : 'Explore Local Map'}</span>
        </button>
      </div>
    </div>
  );
};
