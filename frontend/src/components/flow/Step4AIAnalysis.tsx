import React, { useState, useEffect } from 'react';
import { ArrowRight, Sparkles, CheckCircle2, TrendingUp, Layers } from 'lucide-react';
import type { Language, BeneficiaryProfile } from '../../types';
import { BrainNeuralGraphic } from '../common/GraphicAssets';
import { SoundFX } from '../../utils/speech';

interface Step4Props {
  language: Language;
  profile: BeneficiaryProfile;
  onNext: () => void;
  onPrev: () => void;
}

export const Step4AIAnalysis: React.FC<Step4Props> = ({
  language,
  profile,
  onNext,
  onPrev,
}) => {
  const [analyzing, setAnalyzing] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnalyzing(false);
      SoundFX.playChime('success');
    }, 1400);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex flex-col justify-between min-h-[580px] p-5 text-slate-800">
      {/* Header with Brain Graphic */}
      <div className="flex flex-col items-center pt-1">
        <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-50 border border-teal-200/80 px-3 py-1 rounded-full mb-3">
          <Sparkles className="w-3.5 h-3.5 text-teal-600 animate-spin" />
          <span>Six-Layer AI Matching Engine</span>
        </div>

        <h2 className="text-xl font-black text-slate-900 tracking-tight text-center">
          {language === 'hi' ? 'एआई कौशल विश्लेषण' : 'AI Analysis.'}
        </h2>

        {/* Central Brain Neural Graphic */}
        <div className="my-2">
          <BrainNeuralGraphic className="w-28 h-28" />
        </div>

        {analyzing ? (
          <div className="flex items-center gap-2 text-xs font-semibold text-teal-700 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-teal-600"></span>
            <span>Synthesizing NQR Qualification & District Gaps...</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>AI Verified Profile Generated</span>
          </div>
        )}
      </div>

      {/* Output Section */}
      <div className="w-full bg-white rounded-3xl p-4 shadow-sm border border-slate-200/80 my-3">
        <div className="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-2.5">
          Output:
        </div>

        {/* 1. Skill Profile with Gaps (Low, Med, High) */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-extrabold text-slate-800 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
              Skill Profile:
            </span>
            <span className="text-[10px] font-semibold text-slate-400">
              Visual chart with gaps (Low, Med, High)
            </span>
          </div>

          <div className="space-y-2">
            {profile.skills.slice(0, 3).map((skill, i) => {
              const badgeBg =
                skill.level === 'High'
                  ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                  : skill.level === 'Med'
                  ? 'bg-amber-100 text-amber-800 border-amber-300'
                  : 'bg-rose-100 text-rose-800 border-rose-300';

              const barColor =
                skill.level === 'High'
                  ? 'bg-emerald-500'
                  : skill.level === 'Med'
                  ? 'bg-amber-500'
                  : 'bg-rose-400';

              return (
                <div key={i} className="text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-slate-700">{skill.name}</span>
                    <span
                      className={`text-[10px] font-extrabold px-2 py-0.5 rounded-md border ${badgeBg}`}
                    >
                      {skill.level}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${barColor}`}
                      style={{ width: `${skill.score}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 2. NSQF Pathway Mapping (Visual flow to skill levels 1-10) */}
        <div className="pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-extrabold text-slate-800 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-teal-600" />
              NSQF Pathway Mapping:
            </span>
            <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-md">
              Levels 1-10
            </span>
          </div>

          {/* Visual flow indicator */}
          <div className="bg-slate-50 rounded-2xl p-2.5 border border-slate-100 flex items-center justify-between">
            <div className="text-center">
              <span className="text-[9px] font-bold text-slate-400 block uppercase">Current</span>
              <span className="text-xs font-black text-slate-700">Level 2</span>
            </div>
            
            {/* Arrow with connecting steps */}
            <div className="flex-1 mx-2 flex items-center justify-center">
              <div className="w-full h-1 bg-gradient-to-r from-slate-300 via-emerald-400 to-emerald-600 rounded-full relative">
                <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] font-bold text-emerald-800 bg-emerald-100 px-1.5 rounded-full border border-emerald-300">
                  Target: L4
                </span>
              </div>
            </div>

            <div className="text-center">
              <span className="text-[9px] font-bold text-emerald-600 block uppercase">Certified</span>
              <span className="text-xs font-black text-emerald-700">Level 4</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center gap-2 pt-2">
        <button
          onClick={onPrev}
          className="px-4 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold text-xs transition-colors"
        >
          Back
        </button>

        <button
          onClick={() => {
            SoundFX.playChime('click');
            onNext();
          }}
          className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white rounded-2xl py-3 px-4 font-bold text-sm flex items-center justify-center gap-2 shadow-md shadow-emerald-700/20 transition-all"
        >
          <span>View Livelihood Matches</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
