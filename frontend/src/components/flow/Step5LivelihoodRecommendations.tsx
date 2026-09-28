import React from 'react';
import { ArrowLeft, ChevronRight, Sparkles, Store, SunMedium, Scissors, CheckCircle2 } from 'lucide-react';
import type { Language } from '../../types';
import { SoundFX } from '../../utils/speech';

interface Step5Props {
  language: Language;
  onSelectCourse: (courseId: string) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step5LivelihoodRecommendations: React.FC<Step5Props> = ({
  language,
  onSelectCourse,
  onNext,
  onPrev,
}) => {

  const handleCardClick = (id: string) => {
    SoundFX.playChime('click');
    onSelectCourse(id);
    onNext();
  };

  return (
    <div className="flex flex-col justify-between min-h-[580px] p-5 text-slate-800">
      {/* Top Header */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={onPrev}
            className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              {language === 'hi' ? 'आजीविका सिफारिशें' : 'Livelihood Recommendations.'}
            </h2>
            <p className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              <span>Verified Match Protocol (Problem ID 26097)</span>
            </p>
          </div>
        </div>

        {/* Section 1: Self-Employment Path */}
        <div className="mb-5">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-xs font-black uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-2.5 py-0.5 rounded-lg border border-emerald-300">
              Self-Employment Path
            </span>
            <span className="text-[10px] font-semibold text-slate-400">Micro-Enterprise / Subsidy</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Card 1: Mushroom Cultivation */}
            <div className="bg-white rounded-3xl p-3.5 border-2 border-emerald-500/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
              <div className="flex flex-col items-center text-center">
                {/* Custom Mushroom Icon Graphic */}
                <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-2xl mb-2 shadow-2xs">
                  🍄
                </div>
                <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                  Mushroom cultivation
                </h3>
                <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full mb-3">
                  Verified Batch
                </span>
              </div>

              <button
                onClick={() => handleCardClick('mushroom-cultivation')}
                className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
              >
                <span>View Course</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Card 2: Small Retail Shop */}
            <div className="bg-white rounded-3xl p-3.5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
              <div className="flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-2xl bg-teal-50 border border-teal-200 text-teal-700 flex items-center justify-center mb-2 shadow-2xs">
                  <Store className="w-7 h-7" />
                </div>
                <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                  Small retail shop
                </h3>
                <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full mb-3">
                  High Demand
                </span>
              </div>

              <button
                onClick={() => handleCardClick('small-retail-shop')}
                className="w-full bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
              >
                <span>View Course</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Section 2: Wage Employment Path */}
        <div>
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-xs font-black uppercase tracking-wider text-teal-800 bg-teal-100/80 px-2.5 py-0.5 rounded-lg border border-teal-300">
              Wage Employment Path
            </span>
            <span className="text-[10px] font-semibold text-slate-400">Guaranteed Placements</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {/* Card 1: Solar Technician */}
            <div className="bg-white rounded-3xl p-3.5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
              <div className="flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mb-2 shadow-2xs">
                  <SunMedium className="w-7 h-7" />
                </div>
                <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                  Solar Technician
                </h3>
                <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full mb-3">
                  PM Surya Ghar
                </span>
              </div>

              <button
                onClick={() => handleCardClick('solar-technician')}
                className="w-full bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
              >
                <span>View Course</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Card 2: Apparel Maker */}
            <div className="bg-white rounded-3xl p-3.5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
              <div className="flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-700 flex items-center justify-center mb-2 shadow-2xs">
                  <Scissors className="w-7 h-7" />
                </div>
                <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                  Apparel Maker
                </h3>
                <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full mb-3">
                  Textile Cluster
                </span>
              </div>

              <button
                onClick={() => handleCardClick('apparel-maker')}
                className="w-full bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
              >
                <span>View Course</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Footer info */}
      <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500 font-medium">
        <span className="flex items-center gap-1 text-emerald-700 font-bold">
          <CheckCircle2 className="w-3.5 h-3.5" /> 4 Verified Courses Found
        </span>
        <span>Tap any course to inspect</span>
      </div>
    </div>
  );
};
