import React, { useState } from 'react';
import { Users, Mic, Phone, Star, Sparkles, CheckCircle2, X, Radio } from 'lucide-react';
import type { Language, Mentor } from '../../types';
import { mentorsData } from '../../data/mockData';
import { WaveformVisualizer } from '../common/GraphicAssets';
import { SoundFX, speakText } from '../../utils/speech';

interface CommunityMentorshipProps {
  language: Language;
}

export const CommunityMentorship: React.FC<CommunityMentorshipProps> = ({ language }) => {
  const [selectedMentor, setSelectedMentor] = useState<Mentor | null>(null);
  const [inVoiceRoom, setInVoiceRoom] = useState(false);
  const [isMicMuted, setIsMicMuted] = useState(true);
  const activeSpeaker = 'Sunita Devi (Mentor)';
  const [callStatus, setCallStatus] = useState<string | null>(null);

  const handleConnectMentor = (mentor: Mentor) => {
    SoundFX.playChime('click');
    setSelectedMentor(mentor);
  };

  const handleStartCall = () => {
    SoundFX.playChime('start');
    setCallStatus(`Connecting to ${selectedMentor?.name}...`);
    setTimeout(() => {
      setCallStatus(`Connected with ${selectedMentor?.name}`);
      SoundFX.playChime('success');
      const intro = language === 'hi'
        ? `नमस्ते! मैं ${selectedMentor?.name} हूँ। आप मुझसे अपने काम या व्यवसाय के बारे में कोई भी प्रश्न पूछ सकते हैं।`
        : `Hello! I am ${selectedMentor?.name}. Feel free to ask me anything about starting your enterprise.`;
      speakText(intro, language);
    }, 1500);
  };

  const handleJoinVoiceRoom = () => {
    SoundFX.playChime('start');
    setInVoiceRoom(true);
  };

  return (
    <div className="w-full max-w-[460px] mx-auto bg-[#fbf9f1] border border-amber-900/10 rounded-[36px] shadow-xl p-5 text-slate-800 flex flex-col justify-between min-h-[620px]">
      <div>
        {/* Header */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
              Peer & Enterprise Support
            </span>
            <span className="text-[11px] font-bold text-slate-400">
              Gram Panchayat Network
            </span>
          </div>

          <h2 className="text-lg font-black text-slate-900 tracking-tight leading-tight">
            COMMUNITY CONNECT & MENTORS
          </h2>
          <p className="text-xs font-semibold text-slate-500">
            {language === 'hi'
              ? 'सत्यापित मार्गदर्शकों और साथी लाभार्थियों से जुड़ें'
              : 'Connect with verified local mentors and fellow entrepreneurs'}
          </p>
        </div>

        {/* Section 1: Verified Mentors */}
        <div className="mb-5">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-xs font-black uppercase tracking-wider text-slate-700">
              Verified Mentors
            </span>
            <span className="text-[10px] font-bold text-emerald-700 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> MoSJE Certified
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {mentorsData.slice(0, 2).map((mentor) => (
              <div
                key={mentor.id}
                className="bg-white rounded-3xl p-3.5 border border-slate-200/90 shadow-sm flex flex-col justify-between hover:shadow-md transition-all text-center"
              >
                <div className="flex flex-col items-center">
                  <div className="w-14 h-14 rounded-full bg-amber-50 border-2 border-amber-200 flex items-center justify-center text-3xl mb-2 shadow-2xs">
                    {mentor.avatar}
                  </div>
                  <h4 className="text-xs font-black text-slate-900 leading-tight">
                    {mentor.name}
                  </h4>
                  <p className="text-[10px] font-bold text-emerald-700 mt-0.5">
                    {mentor.role.split('&')[0]}
                  </p>
                  <p className="text-[9px] text-slate-400 mt-1 line-clamp-1">
                    {mentor.specialization}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[10px] font-bold text-amber-700 flex items-center gap-0.5">
                    <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                    {mentor.rating}
                  </span>
                  <button
                    onClick={() => handleConnectMentor(mentor)}
                    className="bg-emerald-700 hover:bg-emerald-800 text-white text-[10px] font-extrabold px-3 py-1 rounded-xl shadow-xs transition-colors"
                  >
                    Connect
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Third mentor: Community Leader */}
          <div className="mt-3 bg-white rounded-2xl p-3 border border-slate-200/90 shadow-2xs flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="text-2xl">{mentorsData[2].avatar}</span>
              <div>
                <h4 className="text-xs font-black text-slate-900">{mentorsData[2].name}</h4>
                <p className="text-[10px] font-bold text-slate-500">Community Leader & Scheme Advisor</p>
              </div>
            </div>
            <button
              onClick={() => handleConnectMentor(mentorsData[2])}
              className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-bold px-3 py-1.5 rounded-xl transition-colors"
            >
              Consult
            </button>
          </div>
        </div>

        {/* Section 2: Local Community Meetups & Voice Chat */}
        <div className="bg-gradient-to-tr from-teal-50 to-emerald-50 border border-teal-200 rounded-3xl p-4 shadow-xs">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-teal-700" />
            <span className="text-xs font-black text-slate-900">
              Community Meetups & Voice Space
            </span>
          </div>

          <p className="text-[11px] text-slate-600 font-medium leading-relaxed mb-3">
            Find local community meetups or connect with other beneficiaries with similar interests.
          </p>

          <button
            onClick={handleJoinVoiceRoom}
            className="w-full bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold py-3 px-4 rounded-2xl flex items-center justify-center gap-2 shadow-sm transition-all"
          >
            <Radio className="w-4 h-4 animate-pulse" />
            <span>Join Live Voice Chat Room</span>
          </button>
        </div>
      </div>

      {/* Voice Chat Room Modal */}
      {inVoiceRoom && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-5 max-w-sm w-full shadow-2xl border border-slate-200 animate-fadeIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                <h3 className="text-sm font-black text-slate-900">
                  Moradabad SC Enterprise Voice Room
                </h3>
              </div>
              <button
                onClick={() => setInVoiceRoom(false)}
                className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-4 flex flex-col items-center">
              <WaveformVisualizer active={!isMicMuted} barCount={16} color="bg-teal-600" />
              <p className="text-xs font-bold text-teal-800 mt-2">
                Speaking: {activeSpeaker}
              </p>
            </div>

            {/* Participants avatars */}
            <div className="grid grid-cols-4 gap-2 mb-4 text-center">
              {[
                { name: 'Sunita D.', avatar: '👩‍🌾', speaking: true },
                { name: 'Rajesh K.', avatar: '🧑‍🌾', speaking: false },
                { name: 'Amit V.', avatar: '👷‍♂️', speaking: false },
                { name: 'Pooja R.', avatar: '👩‍💼', speaking: false },
              ].map((p, idx) => (
                <div key={idx} className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-xl relative ${
                      p.speaking ? 'ring-2 ring-emerald-500 bg-emerald-50' : 'bg-slate-100'
                    }`}
                  >
                    {p.avatar}
                    {p.speaking && (
                      <span className="absolute -bottom-1 -right-1 w-3 h-3 rounded-full bg-emerald-600 border border-white"></span>
                    )}
                  </div>
                  <span className="text-[10px] font-bold text-slate-700 mt-1">{p.name}</span>
                </div>
              ))}
            </div>

            <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setIsMicMuted(!isMicMuted)}
                className={`flex-1 py-2.5 rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 transition-colors ${
                  isMicMuted
                    ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    : 'bg-emerald-600 text-white'
                }`}
              >
                <Mic className="w-3.5 h-3.5" />
                <span>{isMicMuted ? 'Unmute Mic' : 'Muted'}</span>
              </button>

              <button
                onClick={() => setInVoiceRoom(false)}
                className="bg-rose-100 hover:bg-rose-200 text-rose-800 font-bold text-xs py-2.5 px-4 rounded-xl"
              >
                Leave
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mentor Consultation Call Modal */}
      {selectedMentor && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-5 max-w-sm w-full shadow-2xl border border-slate-200 animate-fadeIn text-center">
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setSelectedMentor(null);
                  setCallStatus(null);
                }}
                className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-slate-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="w-16 h-16 rounded-full bg-amber-50 border-2 border-amber-300 flex items-center justify-center text-3xl mx-auto mb-2 shadow-xs">
              {selectedMentor.avatar}
            </div>

            <h3 className="text-base font-black text-slate-900">{selectedMentor.name}</h3>
            <p className="text-xs font-bold text-emerald-700 mb-2">{selectedMentor.role}</p>
            <p className="text-xs text-slate-600 mb-4">{selectedMentor.bio}</p>

            {callStatus ? (
              <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-3 mb-4 text-xs font-bold text-emerald-900 flex items-center justify-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping"></span>
                <span>{callStatus}</span>
              </div>
            ) : null}

            <button
              onClick={handleStartCall}
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 rounded-2xl text-xs flex items-center justify-center gap-2 shadow-md uppercase tracking-wider"
            >
              <Phone className="w-4 h-4" />
              <span>Start 1-on-1 Voice Call</span>
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-400 font-semibold">
        <span className="flex items-center gap-1 text-emerald-700 font-bold">
          <CheckCircle2 className="w-3.5 h-3.5" /> 3 Mentors Active Today
        </span>
        <span>Free under PM-AJAY</span>
      </div>
    </div>
  );
};
