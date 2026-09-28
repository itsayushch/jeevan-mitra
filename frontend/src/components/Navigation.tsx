import React from 'react';
import { Mic, Smartphone, Monitor, Globe, Shield, BarChart3, Compass } from 'lucide-react';
import type { Language } from '../types';

interface NavigationProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  viewMode: 'kiosk' | 'full';
  onToggleViewMode: () => void;
}

export const Navigation: React.FC<NavigationProps> = ({
  currentTab,
  onSelectTab,
  language,
  onSelectLanguage,
  viewMode,
  onToggleViewMode,
}) => {
  const languages: { code: Language; label: string; native: string }[] = [
    { code: 'hi', label: 'Hindi', native: 'हिन्दी' },
    { code: 'en', label: 'English', native: 'English' },
    { code: 'ta', label: 'Tamil', native: 'தமிழ்' },
    { code: 'bn', label: 'Bengali', native: 'বাংলা' },
    { code: 'te', label: 'Telugu', native: 'తెలుగు' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#fdfbf4]/95 backdrop-blur-md border-b border-amber-900/10 shadow-sm px-4 py-2.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Brand / Emblem */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => onSelectTab('journey')}>
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-700 to-teal-600 flex items-center justify-center text-white shadow-md shadow-emerald-700/20">
            <Mic className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-slate-900 tracking-tight text-lg">PM-AJAY</span>
              <span className="bg-emerald-100 text-emerald-800 text-[11px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                SAHAYAK
              </span>
            </div>
            <p className="text-[11px] font-medium text-slate-500">
              {language === 'hi' ? 'आजीविका एवं कौशल मार्गदर्शन' : 'Voice-Led Livelihood & Skilling Guide'}
            </p>
          </div>
        </div>

        {/* Primary View / Module Switcher */}
        <nav className="flex items-center bg-white/80 p-1 rounded-2xl border border-slate-200/80 shadow-xs overflow-x-auto max-w-full">
          <button
            onClick={() => onSelectTab('journey')}
            className={`px-3.5 py-1.5 rounded-xl text-xs md:text-sm font-bold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'journey'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>7-Step Flow</span>
          </button>

          <button
            onClick={() => onSelectTab('voice-ask')}
            className={`px-3 py-1.5 rounded-xl text-xs md:text-sm font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'voice-ask'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Mic className="w-4 h-4" />
            <span>Voice Assistant</span>
          </button>

          <button
            onClick={() => onSelectTab('jobs-map')}
            className={`px-3 py-1.5 rounded-xl text-xs md:text-sm font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'jobs-map'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>Jobs Map</span>
          </button>

          <button
            onClick={() => onSelectTab('training-quiz')}
            className={`px-3 py-1.5 rounded-xl text-xs md:text-sm font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'training-quiz'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>Skill Quiz</span>
          </button>

          <button
            onClick={() => onSelectTab('career-pathways')}
            className={`px-3 py-1.5 rounded-xl text-xs md:text-sm font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'career-pathways'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>NSQF Pathways</span>
          </button>

          <button
            onClick={() => onSelectTab('financial-grants')}
            className={`px-3 py-1.5 rounded-xl text-xs md:text-sm font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'financial-grants'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>Grants & MUDRA</span>
          </button>

          <button
            onClick={() => onSelectTab('community-mentors')}
            className={`px-3 py-1.5 rounded-xl text-xs md:text-sm font-semibold flex items-center gap-1.5 transition-all whitespace-nowrap ${
              currentTab === 'community-mentors'
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <span>Mentors</span>
          </button>
        </nav>

        {/* Right Action Tools: Language, Kiosk/Full Toggle, Worker/Planner */}
        <div className="flex items-center gap-2">
          {/* Language Selector */}
          <div className="relative group">
            <button className="flex items-center gap-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-semibold px-2.5 py-1.5 rounded-xl hover:bg-slate-50 transition-colors">
              <Globe className="w-3.5 h-3.5 text-emerald-600" />
              <span>{languages.find((l) => l.code === language)?.native || 'English'}</span>
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-white rounded-xl shadow-lg border border-slate-100 py-1 hidden group-hover:block z-50">
              {languages.map((l) => (
                <button
                  key={l.code}
                  onClick={() => onSelectLanguage(l.code)}
                  className={`w-full text-left px-3 py-1.5 text-xs font-medium flex items-center justify-between hover:bg-emerald-50 ${
                    language === l.code ? 'text-emerald-700 font-bold bg-emerald-50/50' : 'text-slate-700'
                  }`}
                >
                  <span>{l.native}</span>
                  <span className="text-[10px] text-slate-400">{l.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* View Mode Toggle (Kiosk Phone Frame vs Wide Screen) */}
          <button
            onClick={onToggleViewMode}
            title={viewMode === 'kiosk' ? 'Switch to Full Screen View' : 'Switch to Phone / Kiosk View'}
            className="flex items-center gap-1 text-xs font-semibold bg-white border border-slate-200 text-slate-700 px-2.5 py-1.5 rounded-xl hover:bg-slate-50 transition-colors"
          >
            {viewMode === 'kiosk' ? (
              <>
                <Monitor className="w-3.5 h-3.5 text-teal-600" />
                <span className="hidden sm:inline">Full</span>
              </>
            ) : (
              <>
                <Smartphone className="w-3.5 h-3.5 text-teal-600" />
                <span className="hidden sm:inline">Kiosk</span>
              </>
            )}
          </button>

          {/* Field Worker Portal quick link */}
          <button
            onClick={() => onSelectTab('field-worker')}
            className={`p-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1 transition-colors ${
              currentTab === 'field-worker'
                ? 'bg-amber-100 border-amber-300 text-amber-900'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
            title="Field-Worker Verification Portal"
          >
            <Shield className="w-3.5 h-3.5 text-amber-700" />
            <span className="hidden md:inline">Worker</span>
          </button>

          {/* District Planner quick link */}
          <button
            onClick={() => onSelectTab('district-planner')}
            className={`p-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1 transition-colors ${
              currentTab === 'district-planner'
                ? 'bg-indigo-100 border-indigo-300 text-indigo-900'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
            title="District GIA Planning Console"
          >
            <BarChart3 className="w-3.5 h-3.5 text-indigo-700" />
            <span className="hidden md:inline">District</span>
          </button>
        </div>
      </div>
    </header>
  );
};
