import { useRef, useState } from 'react';
import Link from 'next/link';
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
} from 'lucide-react';
import { LanguagePicker } from './LanguagePicker';
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
  { id: 'home', key: 'nav.overview', icon: LayoutDashboard },
  { id: 'journey', key: 'nav.journey', icon: Route },
  { id: 'voice-ask', key: 'nav.aiAssistant', icon: Mic },
  { id: 'jobs-map', key: 'nav.localOpportunities', icon: BriefcaseBusiness },
  { id: 'training-quiz', key: 'nav.skillTraining', icon: GraduationCap },
  { id: 'career-pathways', key: 'nav.careerPathways', icon: TrendingUp },
  { id: 'financial-grants', key: 'nav.financialSupport', icon: HandCoins },
  { id: 'community-mentors', key: 'nav.communityMentors', icon: Users },
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
        <div className="sidebar-label">YOUR NEXT CHAPTER</div>
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

        <div className="staff-nav">
          <div className="sidebar-label">{t('nav.facilitators')}</div>
          <Link
            className={`nav-item ${currentTab === 'field-worker' ? 'active' : ''}`}
            href="/field-worker"
            onClick={closeMenu}
            aria-current={currentTab === 'field-worker' ? 'page' : undefined}
          >
            <ShieldCheck size={19} />
            {t('nav.fieldWorkerPortal')}
          </Link>
          <Link
            className={`nav-item ${currentTab === 'district-planner' ? 'active' : ''}`}
            href="/district-planner"
            onClick={closeMenu}
            aria-current={currentTab === 'district-planner' ? 'page' : undefined}
          >
            <ChartNoAxesCombined size={19} />
            {t('nav.districtPlanning')}
          </Link>
        </div>

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <span className="help-icon">
              <Mic size={20} />
            </span>
            <strong>{t('nav.guidanceTitle')}</strong>
            <p>{t('nav.guidanceSubtitle')}</p>
            <Link href="/voice-assistant" onClick={closeMenu}>
              {t('nav.letsTalk')} <span aria-hidden="true">↗</span>
            </Link>
          </div>

          <LanguagePicker language={language} onChange={onSelectLanguage} />

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
