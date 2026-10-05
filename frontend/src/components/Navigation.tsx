import { useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Menu,
  X,
  Sprout,
  LayoutDashboard,
  Route,
  Mic,
  BriefcaseBusiness,
  GraduationCap,
  TrendingUp,
  HandCoins,
  Users,
  ShieldCheck,
  ChartNoAxesCombined,
  PanelLeftClose,
  LogOut,
} from 'lucide-react';
import { LanguagePicker } from './LanguagePicker';
import { api } from '../lib/api';
import { pathForSection } from '../lib/routes';
import type { SupportedLocale } from '../lib/i18n/locales';
import { useAppSettings } from './AppShell';

interface NavigationProps {
  currentTab: string;
  language: SupportedLocale;
  onSelectLanguage: (language: SupportedLocale) => void;
  viewMode: 'kiosk' | 'full';
  onToggleViewMode: () => void;
}

const navItems = [
  { id: 'voice-ask', key: 'nav.aiAssistant', icon: Mic },
  { id: 'journey', key: 'nav.journey', icon: Route },
];

export function Navigation({
  currentTab,
  language,
  onSelectLanguage,
  viewMode,
  onToggleViewMode,
}: NavigationProps) {
  const { t } = useAppSettings();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const router = useRouter();

  const handleLogout = () => {
    api.setJwtToken('');
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem('jm_worker_key');
      window.sessionStorage.removeItem('jm_officer_key');
    }
    api.setWorkerKey('');
    api.setOfficerKey('');
    closeMenu();
    router.push('/');
  };

  const closeMenu = () => {
    setMenuOpen(false);
    if (window.matchMedia('(max-width: 640px)').matches) menuButton.current?.focus();
  };

  return (
    <aside
      className="sidebar"
      onKeyDown={(event) => {
        if (event.key === 'Escape' && menuOpen) {
          setMenuOpen(false);
          menuButton.current?.focus();
        }
      }}
    >
      <Link
        className="brand"
        href="/"
        onClick={closeMenu}
        aria-label={`${t('app.title')} home`}
      >
        <span className="brand-mark">
          <Sprout size={25} />
        </span>
        <span>
          Jeevan<span className="brand-green">Mitra</span>
          <small>{t('app.subtitle')}</small>
        </span>
      </Link>

      <LanguagePicker mobile language={language} onChange={onSelectLanguage} />

      <button
        ref={menuButton}
        className="mobile-menu-toggle"
        aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
        aria-expanded={menuOpen}
        aria-controls="navigation-panel"
        onClick={() => setMenuOpen((open) => !open)}
      >
        {menuOpen ? <X size={23} /> : <Menu size={23} />}
      </button>

      <div id="navigation-panel" className={`navigation-panel ${menuOpen ? 'is-open' : ''}`}>
        <div className="sidebar-label">{language === 'hi' ? 'मुख्य मेनू' : 'MAIN MENU'}</div>
        <nav aria-label="Main navigation" className="primary-nav">
          {navItems.map(({ id, key, icon: Icon }) => (
            <Link
              key={id}
              href={pathForSection(id)}
              onClick={closeMenu}
              className={currentTab === id ? 'nav-item active' : 'nav-item'}
              aria-current={currentTab === id ? 'page' : undefined}
            >
              <Icon size={19} />
              <span>{t(key)}</span>
              {currentTab === id && <span className="active-dot" />}
            </Link>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <LanguagePicker language={language} onChange={onSelectLanguage} />

          {api.getJwtToken() && (
            <button className="view-toggle" onClick={handleLogout}>
              <LogOut size={16} />
              Sign out
            </button>
          )}

          {currentTab === 'journey' && (
            <button className="view-toggle" onClick={onToggleViewMode}>
              <PanelLeftClose size={16} />
              {viewMode === 'full' ? t('nav.compactView') : t('nav.expandView')}
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}
