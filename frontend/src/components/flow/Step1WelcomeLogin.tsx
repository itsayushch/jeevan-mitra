import React, { useState } from 'react';
import { Mic, Volume2, Sparkles, CheckCircle2 } from 'lucide-react';
import type { Language } from '../../types';
import { FingerprintIcon, WaveformVisualizer } from '../common/GraphicAssets';
import { SoundFX, speakText } from '../../utils/speech';

interface Step1Props {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  onNext: () => void;
}

export const Step1WelcomeLogin: React.FC<Step1Props> = ({
  language,
  onSelectLanguage,
  onNext,
}) => {
  const [isScanning, setIsScanning] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const langCircles: { code: Language; char: string; name: string; bg: string; text: string }[] = [
    { code: 'hi', char: 'ह', name: 'Hindi', bg: 'bg-emerald-100 hover:bg-emerald-200 border-emerald-300', text: 'text-emerald-800' },
    { code: 'ta', char: 'த', name: 'Tamil', bg: 'bg-amber-100 hover:bg-amber-200 border-amber-300', text: 'text-amber-800' },
    { code: 'bn', char: 'বা', name: 'Bengali', bg: 'bg-yellow-100 hover:bg-yellow-200 border-yellow-300', text: 'text-yellow-800' },
    { code: 'te', char: 'తె', name: 'Telugu', bg: 'bg-teal-100 hover:bg-teal-200 border-teal-300', text: 'text-teal-800' },
    { code: 'en', char: 'A', name: 'English', bg: 'bg-indigo-100 hover:bg-indigo-200 border-indigo-300', text: 'text-indigo-800' },
  ];

  const handleLanguageClick = (langCode: Language) => {
    SoundFX.playChime('click');
    onSelectLanguage(langCode);
  };

  const handlePlayIntro = () => {
    SoundFX.playChime('question');
    setIsSpeaking(true);
    const msg = language === 'hi' 
      ? 'पीएम-अजय सहायक में आपका स्वागत है। यहां आप बोलकर अपने लिए सही कौशल प्रशिक्षण और रोजगार खोज सकते हैं।'
      : 'Welcome to PM-AJAY Sahayak. Speak or touch to discover skilling courses and local livelihoods suited for you.';
    speakText(msg, language, () => setIsSpeaking(false));
  };

  const handleStartTouch = () => {
    SoundFX.playChime('start');
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
      onNext();
    }, 1200);
  };

  return (
    <div className="flex flex-col items-center justify-between min-h-[580px] p-5 text-slate-800">
      {/* Header with Title & Mic */}
      <div className="w-full flex flex-col items-center text-center pt-2">
        <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full text-xs font-bold text-emerald-800 mb-3 shadow-xs">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600 animate-spin" />
          <span>MoSJE PM-AJAY GIA Component</span>
        </div>

        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-700 flex items-center justify-center text-white shadow-lg shadow-emerald-700/25">
            <Mic className="w-6 h-6 animate-pulse" />
          </div>
          <div className="text-left">
            <h1 className="text-2xl font-black tracking-tight text-slate-900 leading-tight">
              PM-AJAY
            </h1>
            <p className="text-sm font-bold text-emerald-700 tracking-wider uppercase">
              SAHAYAK
            </p>
          </div>
        </div>

        {/* Ambient Waveform */}
        <div className="w-full max-w-[280px] my-2">
          <WaveformVisualizer active={isSpeaking} barCount={16} color="bg-emerald-500/70" />
        </div>
      </div>

      {/* Select Language Section */}
      <div className="w-full max-w-[340px] bg-white/90 backdrop-blur-xs rounded-3xl p-5 shadow-sm border border-slate-100 flex flex-col items-center my-3">
        <div className="flex items-center justify-between w-full mb-3 px-1">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Select Language
          </span>
          <button
            onClick={handlePlayIntro}
            disabled={isSpeaking}
            className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full transition-colors"
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>{isSpeaking ? 'Playing...' : 'Audio Guide'}</span>
          </button>
        </div>

        {/* Language Circles */}
        <div className="flex items-center justify-center gap-3 w-full py-1">
          {langCircles.map((l) => {
            const isSelected = language === l.code;
            return (
              <button
                key={l.code}
                onClick={() => handleLanguageClick(l.code)}
                className={`flex flex-col items-center gap-1 group transition-all transform active:scale-95 ${
                  isSelected ? 'scale-105' : 'opacity-85 hover:opacity-100'
                }`}
              >
                <div
                  className={`w-12 h-12 rounded-full border-2 flex items-center justify-center font-bold text-lg shadow-sm transition-all ${
                    l.bg
                  } ${l.text} ${
                    isSelected ? 'ring-3 ring-emerald-600 ring-offset-2 font-black' : ''
                  }`}
                >
                  {l.char}
                </div>
                <span
                  className={`text-[11px] font-semibold ${
                    isSelected ? 'text-emerald-800 font-bold' : 'text-slate-500'
                  }`}
                >
                  {l.name}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Fingerprint / Touch Start Button */}
      <div className="w-full max-w-[340px] flex flex-col items-center">
        <button
          onClick={handleStartTouch}
          disabled={isScanning}
          className={`relative w-28 h-28 rounded-3xl flex flex-col items-center justify-center transition-all duration-300 shadow-xl border-2 ${
            isScanning
              ? 'bg-emerald-600 text-white border-emerald-400 scale-95 shadow-emerald-500/50'
              : 'bg-white text-emerald-700 border-emerald-200 hover:border-emerald-500 hover:shadow-emerald-600/20'
          }`}
        >
          {isScanning ? (
            <div className="flex flex-col items-center gap-1">
              <CheckCircle2 className="w-10 h-10 animate-bounce" />
              <span className="text-[10px] font-bold tracking-wide">VERIFYING...</span>
            </div>
          ) : (
            <>
              <FingerprintIcon className="w-14 h-14 text-emerald-600 group-hover:scale-105 transition-transform" />
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
            </>
          )}
        </button>

        <p className="mt-3 text-base font-bold text-slate-800 text-center">
          {language === 'hi' ? 'अपनी यात्रा शुरू करें।' : 'Start your journey.'}
        </p>
        <p className="text-xs font-medium text-slate-500 text-center">
          {language === 'hi' ? 'बोलें या स्क्रीन पर स्पर्श करें।' : 'Speak or select.'}
        </p>
      </div>

      {/* Kiosk Footer Graphic */}
      <div className="w-full max-w-[340px] pt-4 mt-2 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-400 font-medium">
        <div className="flex items-center gap-1.5 text-slate-600">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Village Kiosk Mode</span>
        </div>
        <span>Gram Panchayat / VLE Ready</span>
      </div>
    </div>
  );
};
