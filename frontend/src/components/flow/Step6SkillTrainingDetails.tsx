import React, { useState } from 'react';
import { ArrowLeft, Mic, Calendar, MapPin, Users, CheckCircle2, Volume2, Sparkles } from 'lucide-react';
import type { Language } from '../../types';
import { MushroomHeroArt } from '../common/GraphicAssets';
import { SoundFX, speakText } from '../../utils/speech';

interface Step6Props {
  language: Language;
  onNext: () => void;
  onPrev: () => void;
  onOpenTrainingModule?: () => void;
}

export const Step6SkillTrainingDetails: React.FC<Step6Props> = ({
  language,
  onNext,
  onPrev,
  onOpenTrainingModule,
}) => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [registered, setRegistered] = useState(false);

  const handleRegisterVoice = () => {
    SoundFX.playChime('start');
    setIsRegistering(true);

    setTimeout(() => {
      setIsRegistering(false);
      setRegistered(true);
      SoundFX.playChime('success');

      const msg = language === 'hi'
        ? 'मशरूम प्रशिक्षण के लिए आपका पंजीकरण दर्ज कर लिया गया है। फील्ड वर्कर जल्द आपसे संपर्क करेंगे।'
        : 'Your interest for Mushroom Cultivation Course has been registered. A field worker will confirm the batch.';
      speakText(msg, language);
    }, 1800);
  };

  return (
    <div className="flex flex-col justify-between min-h-[580px] p-5 text-slate-800">
      <div>
        {/* Top Header */}
        <div className="flex items-center gap-3 mb-3">
          <button
            onClick={onPrev}
            className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              {language === 'hi' ? 'कौशल प्रशिक्षण विवरण' : 'Skill Training Details.'}
            </h2>
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">
              NCVET NSQF Level 4 Qualification
            </span>
          </div>
        </div>

        {/* Hero Artwork Banner */}
        <div className="mb-4">
          <MushroomHeroArt className="w-full h-36" />
        </div>

        {/* Course Details Card */}
        <div className="bg-white rounded-3xl p-5 border border-slate-200/80 shadow-sm mb-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="text-lg font-black text-slate-900 leading-tight">
                Mushroom Cultivation Course
              </h3>
              <p className="text-xs font-semibold text-emerald-700">
                MoSJE PM-AJAY GIA Component (Code: AGR/Q7803)
              </p>
            </div>
            <span className="bg-emerald-100 text-emerald-800 font-extrabold text-[10px] px-2.5 py-1 rounded-full uppercase">
              100% Free
            </span>
          </div>

          <div className="space-y-3 pt-2 border-t border-slate-100 text-xs">
            {/* Duration */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
                <Calendar className="w-4 h-4" />
              </div>
              <div>
                <span className="text-slate-400 font-semibold block text-[10px] uppercase">
                  Duration:
                </span>
                <span className="font-extrabold text-slate-900 text-sm">3 Months</span>
              </div>
            </div>

            {/* Location */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
                <MapPin className="w-4 h-4" />
              </div>
              <div>
                <span className="text-slate-400 font-semibold block text-[10px] uppercase">
                  Location:
                </span>
                <span className="font-extrabold text-slate-900 text-sm">
                  Nearest Skilling Center (4.2 km)
                </span>
              </div>
            </div>

            {/* Mode */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
                <Users className="w-4 h-4" />
              </div>
              <div>
                <span className="text-slate-400 font-semibold block text-[10px] uppercase">
                  Mode:
                </span>
                <span className="font-extrabold text-slate-900 text-sm">
                  Voice / In-person
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick link to interactive training lessons */}
        {onOpenTrainingModule && (
          <button
            onClick={onOpenTrainingModule}
            className="w-full mb-3 bg-amber-50 hover:bg-amber-100 text-amber-900 text-xs font-bold py-2.5 px-4 rounded-2xl border border-amber-200 flex items-center justify-center gap-2 transition-colors"
          >
            <Volume2 className="w-4 h-4 text-amber-700" />
            <span>Preview Audio Lessons & Quiz Now</span>
          </button>
        )}
      </div>

      {/* Primary Action Button: REGISTER INTEREST (voice) */}
      <div className="pt-2">
        {registered ? (
          <div className="bg-emerald-50 border-2 border-emerald-500 rounded-3xl p-4 text-center animate-fadeIn mb-3">
            <div className="flex items-center justify-center gap-2 text-emerald-800 font-black text-sm mb-1">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>Interest Registered!</span>
            </div>
            <p className="text-xs font-medium text-emerald-700 mb-3">
              Case Ref #AJAY-8291 created for Moradabad Block.
            </p>
            <button
              onClick={onNext}
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-extrabold py-3 px-4 rounded-2xl text-xs uppercase tracking-wider shadow-md transition-all"
            >
              Continue to Post-Skilling & Support →
            </button>
          </div>
        ) : (
          <button
            onClick={handleRegisterVoice}
            disabled={isRegistering}
            className={`w-full rounded-3xl py-4 px-6 font-black text-sm flex items-center justify-center gap-3 transition-all duration-300 shadow-xl uppercase tracking-wider ${
              isRegistering
                ? 'bg-rose-600 text-white animate-pulse'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-emerald-700/30 active:scale-98'
            }`}
          >
            <Mic className={`w-5 h-5 ${isRegistering ? 'animate-bounce' : ''}`} />
            <span>
              {isRegistering
                ? 'Recording your voice interest...'
                : 'REGISTER INTEREST (voice)'}
            </span>
          </button>
        )}

        <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold px-2 mt-3">
          <span className="flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            ₹1,500/mo DBT Stipend
          </span>
          <button onClick={onNext} className="text-emerald-700 hover:underline font-bold">
            Skip to Support →
          </button>
        </div>
      </div>
    </div>
  );
};
