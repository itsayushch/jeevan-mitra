"use client";

import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import type { SupportedLocale } from '../lib/i18n/locales';
import { DEFAULT_LOCALE, LOCALES, isLocaleEnabled } from '../lib/i18n/locales';
import { translate } from '../lib/i18n';
import { Navigation } from './Navigation';
import { sectionForPath } from '../lib/routes';

type AppSettings = {
  language: SupportedLocale;
  setLanguage: (language: SupportedLocale) => void;
  viewMode: 'kiosk' | 'full';
  t: (key: string, params?: Record<string, string | number>) => string;
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
  const [language, setLanguage] = useState<SupportedLocale>(DEFAULT_LOCALE);
  const [viewMode, setViewMode] = useState<'kiosk' | 'full'>('full');

  // Precedence resolver:
  // 1. Authenticated user preference from backend profile
  // 2. Current in-memory locale state
  // 3. Persisted browser preference (jeevanmitra.locale or legacy jeevanmitra-language)
  // 4. Browser language, if supported
  // 5. English fallback
  useEffect(() => {
    let resolvedLocale: SupportedLocale = DEFAULT_LOCALE;

    // Check localStorage
    const savedLocale = window.localStorage.getItem('jeevanmitra.locale') || window.localStorage.getItem('jeevanmitra-language');
    if (savedLocale && isLocaleEnabled(savedLocale)) {
      resolvedLocale = savedLocale as SupportedLocale;
    } else if (typeof navigator !== 'undefined' && navigator.language) {
      const browserLang = navigator.language.split('-')[0];
      if (isLocaleEnabled(browserLang)) {
        resolvedLocale = browserLang as SupportedLocale;
      }
    }

    // Check if authenticated user has preferred_language
    const token = window.localStorage.getItem('jm_jwt_token');
    if (token) {
      fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept-Language': resolvedLocale,
        }
      })
      .then(res => res.ok ? res.json() : null)
      .then(user => {
        if (user && user.preferred_language && isLocaleEnabled(user.preferred_language)) {
          applyLocale(user.preferred_language as SupportedLocale);
        }
      })
      .catch(() => {
        // Fallback to resolved browser/storage locale
      });
    }

    applyLocale(resolvedLocale);
  }, []);

  const applyLocale = (val: SupportedLocale) => {
    const valid = isLocaleEnabled(val) ? val : DEFAULT_LOCALE;
    setLanguage(valid);
    document.documentElement.lang = valid;
    document.documentElement.dir = LOCALES[valid]?.direction || 'ltr';
    window.localStorage.setItem('jeevanmitra.locale', valid);
    window.localStorage.setItem('jeevanmitra-language', valid);
  };

  const chooseLanguage = (value: SupportedLocale) => {
    applyLocale(value);

    // Sync to backend if authenticated
    const token = window.localStorage.getItem('jm_jwt_token');
    if (token) {
      fetch('/api/v1/auth/me/language', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept-Language': value,
        },
        body: JSON.stringify({ preferred_language: value }),
      }).catch(err => console.warn('Could not sync preferred language to server', err));
    }
  };

  const t = useCallback((key: string, params?: Record<string, string | number>) => {
    return translate(key, language, params);
  }, [language]);

  return (
    <AppSettingsContext.Provider value={{ language, setLanguage: chooseLanguage, viewMode, t }}>
      <div className="app-shell">
        <a className="skip-link" href="#main-content">{t('app.skipToContent')}</a>
        <Navigation
          currentTab={currentTab}
          language={language}
          onSelectLanguage={chooseLanguage}
          viewMode={viewMode}
          onToggleViewMode={() => setViewMode(previous => (previous === 'kiosk' ? 'full' : 'kiosk'))}
        />
        <div className="workspace">
          <main id="main-content" className={`workspace-main ${currentTab === 'voice-ask' ? 'chat-workspace' : ''}`} tabIndex={-1}>
            {children}
          </main>
          <footer className="workspace-footer">
            <span>{t('app.footerNote')}</span>
            <span>{t('app.footerComponent')}</span>
          </footer>
        </div>
      </div>
    </AppSettingsContext.Provider>
  );
}
