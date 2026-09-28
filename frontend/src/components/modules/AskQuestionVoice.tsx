import React, { useState } from 'react';
import { Mic, Play, Pause } from 'lucide-react';
import type { Language } from '../../types';
import { ElderGuideAvatar, WaveformVisualizer } from '../common/GraphicAssets';
import { voiceFAQData } from '../../data/mockData';
import { SoundFX, speakText, stopSpeaking } from '../../utils/speech';

interface AskQuestionVoiceProps {
  language: Language;
}

export const AskQuestionVoice: React.FC<AskQuestionVoiceProps> = ({ language }) => {
  const [isListening, setIsListening] = useState(false);
  const [isGuideSpeaking, setIsGuideSpeaking] = useState(false);
  const [activeFaq, setActiveFaq] = useState(voiceFAQData[0]);
  const [spokenResponse, setSpokenResponse] = useState<string>('');
  const [playbackProgress, setPlaybackProgress] = useState<number>(45);

  const handleSelectFaq = (faq: typeof voiceFAQData[0]) => {
    SoundFX.playChime('click');
    setActiveFaq(faq);
    setSpokenResponse(language === 'hi' ? faq.answerHi : faq.answer);
    
    // Speak response
    stopSpeaking();
    setIsGuideSpeaking(true);
    SoundFX.playChime('question');
    speakText(
      language === 'hi' ? faq.answerHi : faq.answer,
      language,
      () => setIsGuideSpeaking(false)
    );
  };

  const handleMicToggle = () => {
    if (isListening) {
      setIsListening(false);
      SoundFX.playChime('click');
      return;
    }

    SoundFX.playChime('start');
    setIsListening(true);
    stopSpeaking();
    setIsGuideSpeaking(false);

    // Simulate listening and answering
    setTimeout(() => {
      setIsListening(false);
      const randomFaq = voiceFAQData[Math.floor(Math.random() * voiceFAQData.length)];
      setActiveFaq(randomFaq);
      setSpokenResponse(language === 'hi' ? randomFaq.answerHi : randomFaq.answer);
      SoundFX.playChime('success');

      setIsGuideSpeaking(true);
      speakText(
        language === 'hi' ? randomFaq.answerHi : randomFaq.answer,
        language,
        () => setIsGuideSpeaking(false)
      );
    }, 2500);
  };

  const handleTogglePlayback = () => {
    if (isGuideSpeaking) {
      stopSpeaking();
      setIsGuideSpeaking(false);
    } else {
      setIsGuideSpeaking(true);
      const textToSpeak = spokenResponse || (language === 'hi' ? activeFaq.answerHi : activeFaq.answer);
      speakText(textToSpeak, language, () => setIsGuideSpeaking(false));
    }
  };

  return (
    <div className="w-full max-w-[440px] mx-auto bg-[#fbf9f1] border border-amber-900/10 rounded-[36px] shadow-xl p-5 text-slate-800 flex flex-col justify-between min-h-[620px]">
      {/* Top Header */}
      <div className="flex flex-col items-center pt-2">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-700 flex items-center justify-center text-white shadow-md">
            <Mic className="w-5 h-5 animate-pulse" />
          </div>
          <div className="text-left">
            <h1 className="text-lg font-black tracking-tight text-slate-900 leading-tight">
              PM-AJAY SAHAYAK
            </h1>
            <span className="text-[10px] font-bold text-emerald-700 tracking-wider uppercase">
              Conversational Voice Bot
            </span>
          </div>
        </div>

        <h2 className="text-base font-extrabold text-slate-800 text-center mt-2">
          {language === 'hi' ? 'किसी भी विषय पर पूछें।' : 'Ask me anything about a pathway.'}
        </h2>
      </div>

      {/* Waveform & Central Mic */}
      <div className="flex flex-col items-center justify-center my-4">
        <div className="w-full max-w-[280px]">
          <WaveformVisualizer active={isListening || isGuideSpeaking} barCount={20} color="bg-emerald-600" />
        </div>

        {/* Big Mic Button */}
        <div className="relative my-3">
          {isListening && (
            <>
              <span className="absolute -inset-4 rounded-full bg-rose-400/30 animate-ping"></span>
              <span className="absolute -inset-8 rounded-full bg-rose-300/20 animate-pulse"></span>
            </>
          )}
          <button
            onClick={handleMicToggle}
            className={`w-28 h-28 rounded-full flex flex-col items-center justify-center transition-all duration-300 shadow-2xl relative z-10 ${
              isListening
                ? 'bg-rose-600 text-white scale-105 shadow-rose-600/40 ring-4 ring-rose-300'
                : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-emerald-700/35 active:scale-95'
            }`}
          >
            <Mic className={`w-12 h-12 ${isListening ? 'animate-bounce' : ''}`} />
          </button>
        </div>

        {/* "I'm listening" badge */}
        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 shadow-2xs ${
              isListening
                ? 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse'
                : isGuideSpeaking
                ? 'bg-teal-100 text-teal-800 border border-teal-300'
                : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isListening ? 'bg-rose-500' : isGuideSpeaking ? 'bg-teal-600' : 'bg-emerald-600'
              }`}
            ></span>
            <span>
              {isListening
                ? "I'm listening..."
                : isGuideSpeaking
                ? 'Speaking answer...'
                : 'Tap to speak'}
            </span>
          </span>
        </div>
      </div>

      {/* Quick Prompt Bilingual Chips */}
      <div className="my-2">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2 px-1">
          Common Questions (Tap to Ask):
        </span>
        <div className="grid grid-cols-2 gap-2">
          {voiceFAQData.map((faq) => {
            const isSelected = activeFaq.id === faq.id;
            return (
              <button
                key={faq.id}
                onClick={() => handleSelectFaq(faq)}
                className={`p-2.5 rounded-2xl text-left border transition-all text-xs flex flex-col justify-between ${
                  isSelected
                    ? 'bg-emerald-50 border-emerald-400 text-emerald-950 font-bold shadow-xs'
                    : 'bg-white border-slate-200/90 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <span className="line-clamp-2 leading-snug">{faq.en}</span>
                <span className="text-[10px] text-emerald-700 font-semibold mt-1">
                  {faq.hi}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Elder Guide Answer Card with Audio Player Slider */}
      <div className="bg-white rounded-3xl p-3.5 border border-slate-200 shadow-sm mt-2">
        <div className="flex items-center gap-3 mb-2">
          <ElderGuideAvatar size="sm" isSpeaking={isGuideSpeaking} />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-slate-900">
                Sahayak Elder Guide
              </span>
              <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                Verified MoSJE Rule
              </span>
            </div>
            <p className="text-[11px] text-slate-600 font-medium line-clamp-2 mt-0.5">
              {spokenResponse || (language === 'hi' ? activeFaq.answerHi : activeFaq.answer)}
            </p>
          </div>
        </div>

        {/* Audio Scrubber & Controls */}
        <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
          <button
            onClick={handleTogglePlayback}
            className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center hover:bg-emerald-200 transition-colors shrink-0"
          >
            {isGuideSpeaking ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
          </button>

          {/* Timeline slider */}
          <div className="flex-1">
            <input
              type="range"
              min="0"
              max="100"
              value={playbackProgress}
              onChange={(e) => setPlaybackProgress(Number(e.target.value))}
              className="w-full accent-emerald-600 h-1.5 bg-slate-200 rounded-lg cursor-pointer"
            />
          </div>

          <span className="text-[10px] font-mono text-slate-400">0:18</span>
        </div>
      </div>
    </div>
  );
};
