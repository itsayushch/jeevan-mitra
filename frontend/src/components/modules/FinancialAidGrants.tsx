import React, { useState } from 'react';
import { Handshake, Mic, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react';
import type { Language, FinancialScheme } from '../../types';
import { financialSchemesData } from '../../data/mockData';
import { SoundFX, speakText } from '../../utils/speech';

interface FinancialAidGrantsProps {
  language: Language;
}

export const FinancialAidGrants: React.FC<FinancialAidGrantsProps> = ({ language }) => {
  const [selectedScheme, setSelectedScheme] = useState<FinancialScheme>(financialSchemesData[0]);
  const [isApplyingVoice, setIsApplyingVoice] = useState(false);
  const [applicationSubmitted, setApplicationSubmitted] = useState(false);

  const handleApplyVoice = () => {
    SoundFX.playChime('start');
    setIsApplyingVoice(true);

    setTimeout(() => {
      setIsApplyingVoice(false);
      setApplicationSubmitted(true);
      SoundFX.playChime('success');

      const msg = language === 'hi'
        ? `${selectedScheme.title} के लिए आपका वॉयस आवेदन स्वीकार कर लिया गया है।`
        : `Your voice application for ${selectedScheme.title} has been logged for district verification.`;
      speakText(msg, language);
    }, 2000);
  };

  return (
    <div className="module-page financial-page">
      <div>
        {/* Header */}
        <div className="module-header mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
              Capital Subsidy & Micro-Credit
            </span>
            <span className="text-[11px] font-bold text-slate-400">
              MoSJE PM-AJAY GIA
            </span>
          </div>

          <h2 className="text-lg font-black text-slate-900 tracking-tight leading-tight">
            FINANCIAL SUPPORT SCHEMES
          </h2>
          <p className="text-xs font-semibold text-slate-500">
            {language === 'hi'
              ? 'मुद्रा ऋण और अनुसूचित जाति के लिए शत-प्रतिशत सहायता अनुदान'
              : 'Institutional credit and direct enterprise seed capital grants'}
          </p>
        </div>

        {/* Scheme Cards */}
        <div className="scheme-grid mb-4">
          {financialSchemesData.map((scheme) => {
            const isSelected = selectedScheme.id === scheme.id;
            return (
              <div
                key={scheme.id}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    setSelectedScheme(scheme);
                    setApplicationSubmitted(false);
                  }
                }}
                onClick={() => {
                  SoundFX.playChime('click');
                  setSelectedScheme(scheme);
                  setApplicationSubmitted(false);
                }}
                className={`financial-scheme w-full text-left bg-white rounded-3xl p-4 border transition-all cursor-pointer ${
                  isSelected
                    ? 'border-emerald-500 shadow-md ring-1 ring-emerald-400'
                    : 'border-slate-200/90 hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2.5">
                    <div className="w-10 h-10 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center font-black text-xs shrink-0">
                      {scheme.id.includes('mudra') ? 'MUDRA' : 'GRANT'}
                    </div>
                    <div>
                      <h3 className="text-xs font-black text-slate-900 leading-snug">
                        {scheme.title}
                      </h3>
                      <span className="text-[10px] font-bold text-emerald-700">
                        {scheme.maxAmount}
                      </span>
                    </div>
                  </div>

                  <span className="text-[9px] font-bold text-amber-800 bg-amber-100/80 px-2 py-0.5 rounded-full shrink-0">
                    {scheme.badge}
                  </span>
                </div>

                <p className="text-[11px] text-slate-600 font-medium mb-2.5 line-clamp-2">
                  {scheme.description}
                </p>

                {/* Eligibility checklist preview */}
                <div className="bg-slate-50 rounded-2xl p-2.5 border border-slate-100 text-[10px] space-y-1">
                  <span className="font-extrabold text-slate-700 block uppercase">
                    Eligibility Checklist:
                  </span>
                  {scheme.eligibility.slice(0, 2).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-slate-600 font-medium">
                      <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span className="truncate">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Handshake Graphic / Partnership Banner */}
        <div className="dbt-banner bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-3xl p-3.5 flex items-center justify-between gap-3 shadow-2xs mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center shrink-0">
              <Handshake className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-black text-slate-900">
                Direct Benefit Transfer (DBT)
              </p>
              <p className="text-[10px] text-slate-600 font-medium">
                Sanctioned grants credited directly to Aadhaar-seeded bank account.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Action / Apply Now (Voice) */}
      <div className="financial-actions">
        {applicationSubmitted ? (
          <div className="bg-emerald-50 border border-emerald-300 rounded-3xl p-3.5 text-center animate-fadeIn">
            <div className="flex items-center justify-center gap-1.5 text-emerald-800 font-black text-xs mb-1">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Application Submitted! Ref #MUDRA-4910</span>
            </div>
            <p className="text-[11px] text-slate-600 mb-2">
              Forwarded to District Welfare Officer for sanction.
            </p>
            <button
              onClick={() => setApplicationSubmitted(false)}
              className="text-xs font-bold text-emerald-700 hover:underline"
            >
              Apply for another scheme
            </button>
          </div>
        ) : (
          <button
            onClick={handleApplyVoice}
            disabled={isApplyingVoice}
            className={`w-full rounded-3xl py-4 px-6 font-black text-sm flex items-center justify-center gap-2.5 transition-all duration-300 shadow-xl uppercase tracking-wider ${
              isApplyingVoice
                ? 'bg-rose-600 text-white animate-pulse'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-emerald-700/30'
            }`}
          >
            <Mic className={`w-5 h-5 ${isApplyingVoice ? 'animate-bounce' : ''}`} />
            <span>
              {isApplyingVoice
                ? 'Recording Application...'
                : `Apply Now (Voice)`}
            </span>
          </button>
        )}

        <div className="flex items-center justify-center gap-1 text-[11px] text-slate-400 font-semibold mt-2.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Zero Collateral Required for SC Micro-Units</span>
        </div>
      </div>
    </div>
  );
};
