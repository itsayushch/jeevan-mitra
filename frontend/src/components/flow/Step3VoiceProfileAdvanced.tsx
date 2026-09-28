import React, { useState } from 'react';
import { Mic, Volume2, ArrowRight, MapPin, Sparkles } from 'lucide-react';
import type { Language, BeneficiaryProfile } from '../../types';
import { ElderGuideAvatar, BeneficiaryAvatar } from '../common/GraphicAssets';
import { SoundFX, speakText } from '../../utils/speech';

interface Step3Props {
  language: Language;
  profile: BeneficiaryProfile;
  onUpdateProfile: (updates: Partial<BeneficiaryProfile>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step3VoiceProfileAdvanced: React.FC<Step3Props> = ({
  language,
  profile,
  onUpdateProfile,
  onNext,
  onPrev,
}) => {
  const [isGuideSpeaking, setIsGuideSpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);

  const guidePrompt = language === 'hi'
    ? 'आपके परिवार के पारंपरिक कौशल या पुश्तैनी काम क्या हैं?'
    : "What are your family's traditional skills or trades?";

  const handlePlayGuide = () => {
    SoundFX.playChime('question');
    setIsGuideSpeaking(true);
    speakText(guidePrompt, language, () => setIsGuideSpeaking(false));
  };

  const handleUserSpeakToggle = () => {
    SoundFX.playChime('start');
    setIsUserSpeaking(true);
    setTimeout(() => {
      setIsUserSpeaking(false);
      SoundFX.playChime('success');
      onUpdateProfile({
        familyTrades: ['Farming', 'Pottery', 'Mushroom Cultivation']
      });
    }, 2000);
  };

  return (
    <div className="flex flex-col justify-between min-h-[580px] p-5 text-slate-800">
      {/* Top Elder Guide Section */}
      <div className="w-full flex items-start gap-3 pt-2">
        <ElderGuideAvatar size="md" isSpeaking={isGuideSpeaking} />

        {/* Speech Bubble */}
        <div className="relative flex-1 bg-white border border-amber-200 rounded-2xl p-3.5 shadow-sm">
          <div className="absolute -left-2 top-4 w-3 h-3 bg-white border-l border-b border-amber-200 rotate-45"></div>
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-bold text-slate-800 leading-snug">
              "{guidePrompt}"
            </p>
            <button
              onClick={handlePlayGuide}
              disabled={isGuideSpeaking}
              className="p-1 rounded-lg text-emerald-700 hover:bg-emerald-50 shrink-0 transition-colors"
              title="Hear guide speaking"
            >
              <Volume2 className="w-4 h-4" />
            </button>
          </div>
          <span className="text-[10px] text-amber-700 font-semibold tracking-wide uppercase mt-1 block">
            Tradition & Local Capacity Discovery
          </span>
        </div>
      </div>

      {/* Center Section: Family Trades & User Response */}
      <div className="flex flex-col gap-4 my-3">
        {/* Family Trades Tag Box */}
        <div className="bg-white/80 backdrop-blur-xs rounded-2xl p-4 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">
              Family Trades:
            </span>
            <span className="text-[11px] font-semibold text-emerald-700">
              Farming, Pottery
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {profile.familyTrades.map((trade, i) => (
              <span
                key={i}
                className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold px-3 py-1.5 rounded-xl shadow-2xs flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                {trade}
              </span>
            ))}
          </div>
        </div>

        {/* User Speaks Interactive Pill */}
        <div className="flex items-center justify-between bg-white rounded-2xl p-3.5 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3">
            <BeneficiaryAvatar size="md" />
            <div>
              <p className="text-xs font-extrabold text-slate-900">
                {isUserSpeaking ? 'Beneficiary Speaking...' : 'User speaks.'}
              </p>
              <p className="text-[11px] font-medium text-slate-500">
                "Our family does farm work & seasonal crafts."
              </p>
            </div>
          </div>

          <button
            onClick={handleUserSpeakToggle}
            className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
              isUserSpeaking
                ? 'bg-rose-600 text-white animate-pulse'
                : 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
            }`}
            title="Record response"
          >
            <Mic className="w-5 h-5" />
          </button>
        </div>

        {/* Local Opportunities Card with Map Graphic */}
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/90 rounded-2xl p-3.5 shadow-xs flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-900 flex items-center justify-center shrink-0">
            <MapPin className="w-5 h-5 text-amber-700" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-bold text-amber-800 uppercase tracking-wider">
                Geographic Cluster Fit
              </span>
              <Sparkles className="w-3 h-3 text-amber-600" />
            </div>
            <p className="text-xs font-extrabold text-slate-900">
              Local Opportunities: Mushroom Farming
            </p>
            <p className="text-[11px] font-medium text-slate-600">
              Active cluster in Chhajlet block within 5 km.
            </p>
          </div>
        </div>
      </div>

      {/* Stepper Progress & Navigation */}
      <div className="w-full">
        {/* Progress Stepper with 4 dots */}
        <div className="flex items-center justify-center gap-2 mb-4">
          <span className="w-3 h-3 rounded-full bg-emerald-600"></span>
          <span className="w-8 h-1.5 rounded-full bg-emerald-600"></span>
          <span className="w-3.5 h-3.5 rounded-full bg-emerald-600 ring-2 ring-emerald-300"></span>
          <span className="w-8 h-1.5 rounded-full bg-slate-200"></span>
          <span className="w-3 h-3 rounded-full bg-slate-200"></span>
        </div>

        <div className="flex items-center gap-2">
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
            <span>Run AI Analysis</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
