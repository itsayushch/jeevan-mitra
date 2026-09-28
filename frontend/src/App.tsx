import { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import type { Language } from './types';
import { Navigation } from './components/Navigation';
import { FlowContainer } from './components/flow/FlowContainer';
import { AskQuestionVoice } from './components/modules/AskQuestionVoice';
import { JobPlacementMap } from './components/modules/JobPlacementMap';
import { SkillTrainingModule } from './components/modules/SkillTrainingModule';
import { CareerPathways } from './components/modules/CareerPathways';
import { FinancialAidGrants } from './components/modules/FinancialAidGrants';
import { CommunityMentorship } from './components/modules/CommunityMentorship';
import { FieldWorkerPortal } from './components/portals/FieldWorkerPortal';
import { DistrictPlannerConsole } from './components/portals/DistrictPlannerConsole';

function MainApp() {
  const [currentTab, setCurrentTab] = useState<string>('journey');
  const [language, setLanguage] = useState<Language>('hi');
  const [viewMode, setViewMode] = useState<'kiosk' | 'full'>('kiosk');

  const handleSelectTab = (tab: string) => {
    setCurrentTab(tab);
  };

  const handleToggleViewMode = () => {
    setViewMode((prev) => (prev === 'kiosk' ? 'full' : 'kiosk'));
  };

  return (
    <div className="min-h-screen bg-[#f7f5ed] flex flex-col font-sans text-slate-800 selection:bg-emerald-200">
      {/* Universal Top Navigation Header */}
      <Navigation
        currentTab={currentTab}
        onSelectTab={handleSelectTab}
        language={language}
        onSelectLanguage={setLanguage}
        viewMode={viewMode}
        onToggleViewMode={handleToggleViewMode}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full py-4 px-2 md:px-4 flex flex-col items-center">
        {/* Render Selected View */}
        {currentTab === 'journey' && (
          <div className={viewMode === 'full' ? 'w-full max-w-5xl' : 'w-full'}>
            <FlowContainer
              language={language}
              onSelectLanguage={setLanguage}
              onNavigateModule={handleSelectTab}
            />
          </div>
        )}

        {currentTab === 'voice-ask' && (
          <div className={viewMode === 'full' ? 'w-full max-w-4xl' : 'w-full'}>
            <AskQuestionVoice language={language} />
          </div>
        )}

        {currentTab === 'jobs-map' && (
          <div className={viewMode === 'full' ? 'w-full max-w-4xl' : 'w-full'}>
            <JobPlacementMap language={language} />
          </div>
        )}

        {currentTab === 'training-quiz' && (
          <div className={viewMode === 'full' ? 'w-full max-w-4xl' : 'w-full'}>
            <SkillTrainingModule language={language} />
          </div>
        )}

        {currentTab === 'career-pathways' && (
          <div className={viewMode === 'full' ? 'w-full max-w-4xl' : 'w-full'}>
            <CareerPathways language={language} />
          </div>
        )}

        {currentTab === 'financial-grants' && (
          <div className={viewMode === 'full' ? 'w-full max-w-4xl' : 'w-full'}>
            <FinancialAidGrants language={language} />
          </div>
        )}

        {currentTab === 'community-mentors' && (
          <div className={viewMode === 'full' ? 'w-full max-w-4xl' : 'w-full'}>
            <CommunityMentorship language={language} />
          </div>
        )}

        {currentTab === 'field-worker' && (
          <FieldWorkerPortal onBack={() => setCurrentTab('journey')} />
        )}

        {currentTab === 'district-planner' && (
          <DistrictPlannerConsole onBack={() => setCurrentTab('journey')} />
        )}
      </main>

      {/* Global Accessibility Footer */}
      <footer className="py-3 px-4 border-t border-amber-900/10 text-center text-xs text-slate-500 font-medium bg-[#fdfbf4]/80">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Ministry of Social Justice and Empowerment (MoSJE) • PM-AJAY Grant-in-Aid
          </span>
          <span className="text-[11px] text-emerald-800 font-bold bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
            JeevanMitra 2.0 Verification Architecture Active
          </span>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();

  return (
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/field-worker" element={<FieldWorkerPortal onBack={() => navigate('/')} />} />
      <Route path="/district-planner" element={<DistrictPlannerConsole onBack={() => navigate('/')} />} />
      <Route path="*" element={<MainApp />} />
    </Routes>
  );
}
