import { useRef, useState } from 'react';
import Link from 'next/link';
import { Menu, X, Sprout, LayoutDashboard, Route, Mic, BriefcaseBusiness, GraduationCap, TrendingUp, HandCoins, Users, ShieldCheck, ChartNoAxesCombined, PanelLeftClose } from 'lucide-react';
import { LanguagePicker } from './LanguagePicker';
import { pathForSection } from '../lib/routes';
import type { Language } from '../types';

interface NavigationProps {
  currentTab: string;
  language: Language;
  onSelectLanguage: (language: Language) => void;
  viewMode: 'kiosk' | 'full';
  onToggleViewMode: () => void;
}
const items = [
  { id: 'home', label: 'Overview', hi: 'होम', icon: LayoutDashboard },
  { id: 'journey', label: 'My journey', hi: 'मेरी यात्रा', icon: Route },
  { id: 'voice-ask', label: 'AI Assistant', hi: 'एआई सहायक', icon: Mic },
  { id: 'jobs-map', label: 'Local opportunities', hi: 'स्थानीय अवसर', icon: BriefcaseBusiness },
  { id: 'training-quiz', label: 'Skill training', hi: 'कौशल प्रशिक्षण', icon: GraduationCap },
  { id: 'career-pathways', label: 'Career pathways', hi: 'करियर के रास्ते', icon: TrendingUp },
  { id: 'financial-grants', label: 'Financial support', hi: 'आर्थिक सहायता', icon: HandCoins },
  { id: 'community-mentors', label: 'Community & mentors', hi: 'समुदाय और मार्गदर्शक', icon: Users },
];

export function Navigation({ currentTab, language, onSelectLanguage, viewMode, onToggleViewMode }: NavigationProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const closeMenu = () => {
    setMenuOpen(false);
    if (window.matchMedia('(max-width: 640px)').matches) menuButton.current?.focus();
  };
  return <aside className="sidebar" onKeyDown={event => {
    if (event.key === 'Escape' && menuOpen) { setMenuOpen(false); menuButton.current?.focus(); }
  }}>
    <Link className="brand" href="/" onClick={closeMenu} aria-label="JeevanMitra home"><span className="brand-mark"><Sprout size={25}/></span><span>Jeevan<span className="brand-green">Mitra</span><small>YOUR LIVELIHOOD COMPANION</small></span></Link>
    <LanguagePicker mobile language={language} onChange={onSelectLanguage} />
    <button ref={menuButton} className="mobile-menu-toggle" aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen} aria-controls="navigation-panel" onClick={() => setMenuOpen(open => !open)}>{menuOpen ? <X size={23}/> : <Menu size={23}/>}</button>
    <div id="navigation-panel" className={`navigation-panel ${menuOpen ? 'is-open' : ''}`}>
      <div className="sidebar-label">YOUR NEXT CHAPTER</div>
      <nav aria-label="Main navigation" className="primary-nav">{items.map(({ id, label, hi, icon: Icon }) => <Link key={id} href={pathForSection(id)} onClick={closeMenu} className={currentTab === id ? 'nav-item active' : 'nav-item'} aria-current={currentTab === id ? 'page' : undefined}><Icon size={19}/><span>{language === 'hi' ? hi : label}</span>{currentTab === id && <span className="active-dot"/>}</Link>)}</nav>
      <div className="staff-nav"><div className="sidebar-label">FOR FACILITATORS</div><Link className={`nav-item ${currentTab === 'field-worker' ? 'active' : ''}`} href="/field-worker" onClick={closeMenu} aria-current={currentTab === 'field-worker' ? 'page' : undefined}><ShieldCheck size={19}/>Field worker portal</Link><Link className={`nav-item ${currentTab === 'district-planner' ? 'active' : ''}`} href="/district-planner" onClick={closeMenu} aria-current={currentTab === 'district-planner' ? 'page' : undefined}><ChartNoAxesCombined size={19}/>District planning</Link></div>
      <div className="sidebar-bottom"><div className="sidebar-help"><span className="help-icon"><Mic size={20}/></span><strong>A little guidance goes a long way.</strong><p>Ask a question, in your own words.</p><Link href="/voice-assistant" onClick={closeMenu}>Let’s talk <span aria-hidden="true">↗</span></Link></div>
        <LanguagePicker language={language} onChange={onSelectLanguage} />
        {currentTab === 'journey' && <button className="view-toggle" onClick={onToggleViewMode}><PanelLeftClose size={16}/>{viewMode === 'full' ? 'Compact journey view' : 'Expand journey view'}</button>}
      </div>
    </div>
  </aside>;
}
