"use client";

import { createContext, useContext, useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import type { Language } from '../types';
import { Navigation } from './Navigation';
import { sectionForPath } from '../lib/routes';

type AppSettings = {
  language: Language;
  setLanguage: (language: Language) => void;
  viewMode: 'kiosk' | 'full';
};
const AppSettingsContext = createContext<AppSettings | null>(null);

export function useAppSettings() {
  const settings = useContext(AppSettingsContext);
  if (!settings) throw new Error('App settings must be used within AppShell');
  return settings;
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const currentTab = sectionForPath(pathname);
  const [language, setLanguage] = useState<Language>('en');
  const [viewMode, setViewMode] = useState<'kiosk' | 'full'>('full');

  useEffect(() => {
    const saved = window.localStorage.getItem('jeevanmitra-language');
    if (saved && ['en', 'hi', 'ta', 'bn', 'te'].includes(saved)) setLanguage(saved as Language);
  }, []);
  const chooseLanguage = (value: Language) => {
    setLanguage(value);
    window.localStorage.setItem('jeevanmitra-language', value);
  };

  return <AppSettingsContext.Provider value={{ language, setLanguage: chooseLanguage, viewMode }}>
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <Navigation currentTab={currentTab} language={language} onSelectLanguage={chooseLanguage} viewMode={viewMode} onToggleViewMode={() => setViewMode(previous => previous === 'kiosk' ? 'full' : 'kiosk')} />
      <div className="workspace">
        {/* <header className="workspace-header"><span>PM-AJAY <span className="header-divider">/</span> Livelihood & skilling</span></header> */}
        <main id="main-content" className={`workspace-main ${currentTab === 'voice-ask' ? 'chat-workspace' : ''}`} tabIndex={-1}>
          {children}
        </main>
        <footer className="workspace-footer"><span>JeevanMitra · A step towards a better tomorrow.</span><span>Designed for PM-AJAY • Grant-in-Aid</span></footer>
      </div>
    </div>
  </AppSettingsContext.Provider>;
}
