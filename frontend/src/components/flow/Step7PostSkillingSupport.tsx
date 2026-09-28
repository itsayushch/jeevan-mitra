import React from 'react';
import { ArrowLeft, Banknote, Briefcase, Handshake, ChevronRight, CheckCircle2, RotateCcw } from 'lucide-react';
import type { Language } from '../../types';
import { mentorsData } from '../../data/mockData';
import { SoundFX } from '../../utils/speech';

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

  const handleStepClick = (moduleKey: string) => {
    SoundFX.playChime('click');
    onNavigateModule(moduleKey);
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
              {language === 'hi' ? 'प्रशिक्षण उपरांत सहयोग' : 'Post-Skilling & Support.'}
            </h2>
            <p className="text-[11px] font-semibold text-emerald-700">
              End-to-End Livelihood Guarantee Framework
            </p>
          </div>
        </div>

        {/* Vertical Connected Pathway Steps */}
        <div className="relative pl-6 space-y-4 my-3">
          {/* Vertical Connecting Line */}
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
                    Connect with Financial Consultant
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    MUDRA loans & PM-AJAY capital grants
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
                    View Local Job Openings
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    Verified employers within 5 km radius
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
                    Enterprise Mentorship
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    1-on-1 guidance with veteran entrepreneurs
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
              <p className="text-[10px] text-slate-400">Available for Voice Consultation</p>
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
          <span>Start Over</span>
        </button>

        <button
          onClick={() => handleStepClick('jobs-map')}
          className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white rounded-2xl py-3 px-4 font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-emerald-700/20 transition-all uppercase tracking-wider"
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>Explore Local Map</span>
        </button>
      </div>
    </div>
  );
};
