import React, { useState } from 'react';
import { Mic, Volume2, ArrowRight, Check, GraduationCap, Briefcase } from 'lucide-react';
import type { Language, BeneficiaryProfile } from '../../types';
import { ElderGuideAvatar, WaveformVisualizer } from '../common/GraphicAssets';
import { SoundFX, speakText } from '../../utils/speech';

interface Step2Props {
  language: Language;
  profile: BeneficiaryProfile;
  onUpdateProfile: (updates: Partial<BeneficiaryProfile>) => void;
  onNext: () => void;
  onPrev: () => void;
}

export const Step2VoiceProfileBasic: React.FC<Step2Props> = ({
  language,
  profile,
  onUpdateProfile,
  onNext,
  onPrev,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isGuideSpeaking, setIsGuideSpeaking] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState<string>('');

  const promptText = language === 'hi' 
    ? 'अपनी पढ़ाई और रुचि के बारे में बताएं।' 
    : 'Tell me about your studies and what work you like.';

  const handlePlayGuide = () => {
    SoundFX.playChime('question');
    setIsGuideSpeaking(true);
    speakText(promptText, language, () => setIsGuideSpeaking(false));
  };

  const handleStartSpeaking = () => {
    SoundFX.playChime('start');
    setIsRecording(true);
    setLiveTranscript('');

    // Simulate speech recognition transcription
    setTimeout(() => {
      setLiveTranscript(
        language === 'hi'
          ? 'मैंने 10वीं पास की है और मुझे कृषि और व्यवसाय में काम करना पसंद है।'
          : 'I have passed 10th class and I want to start an agri-business or farm enterprise.'
      );
      onUpdateProfile({
        education: '10th Pass',
        aspiration: 'Agri-Business & Farming'
      });
      setIsRecording(false);
      SoundFX.playChime('success');
    }, 2200);
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
              "{promptText}"
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
            JeevanMitra voice guide
          </span>
        </div>
      </div>

      {/* Center Waveform & Big Mic Button */}
      <div className="flex flex-col items-center justify-center my-6">
        <div className="w-full max-w-[260px] mb-2">
          <WaveformVisualizer active={isRecording || isGuideSpeaking} barCount={18} color="bg-emerald-600" />
        </div>

        {/* Big Mic Button with Pulsing Wave Rings */}
        <div className="relative">
          {isRecording && (
            <>
              <span className="absolute -inset-4 rounded-full bg-rose-400/30 animate-ping"></span>
              <span className="absolute -inset-8 rounded-full bg-rose-300/20 animate-pulse"></span>
            </>
          )}
          <button
            onClick={handleStartSpeaking}
            className={`w-28 h-28 rounded-full flex flex-col items-center justify-center transition-all duration-300 shadow-2xl relative z-10 ${
              isRecording
                ? 'bg-rose-600 text-white scale-105 shadow-rose-600/40 ring-4 ring-rose-300'
                : 'bg-emerald-700 text-white hover:bg-emerald-800 shadow-emerald-700/35 hover:scale-102'
            }`}
          >
            <Mic className={`w-12 h-12 ${isRecording ? 'animate-bounce' : ''}`} />
            <span className="text-[10px] font-bold uppercase tracking-wider mt-1">
              {isRecording ? 'Listening...' : 'Tap to Talk'}
            </span>
          </button>
        </div>

        <p className="mt-3 text-xs font-semibold text-slate-500">
          {isRecording ? 'Listening to your voice...' : 'Press button and speak naturally'}
        </p>

        {/* Live speech feedback pill */}
        {liveTranscript && (
          <div className="mt-3 bg-emerald-50 border border-emerald-200 px-3.5 py-2 rounded-xl text-center max-w-[320px] animate-fadeIn">
            <span className="text-[11px] text-emerald-800 font-medium">
              "{liveTranscript}"
            </span>
          </div>
        )}
      </div>

      {/* Bottom Profile Extraction Badges */}
      <div className="w-full">
        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
          <span>Voice Extracted Profile</span>
          <span className="text-emerald-700 flex items-center gap-1">
            <Check className="w-3 h-3" /> Sample profile
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2.5 mb-4">
          {/* Badge 1: Education */}
          <div className="bg-white rounded-2xl p-3 border border-slate-200/80 shadow-xs flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center shrink-0">
              <GraduationCap className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase">Educ</p>
              <p className="text-xs font-extrabold text-slate-900">{profile.education || '10th'}</p>
            </div>
          </div>

          {/* Badge 2: Aspiration */}
          <div className="bg-white rounded-2xl p-3 border border-slate-200/80 shadow-xs flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center shrink-0">
              <Briefcase className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase">Aspir</p>
              <p className="text-xs font-extrabold text-slate-900 truncate max-w-[100px]" title={profile.aspiration}>
                {profile.aspiration || 'Agri-Business'}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation Actions */}
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
            <span>Next: Family Skills</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
