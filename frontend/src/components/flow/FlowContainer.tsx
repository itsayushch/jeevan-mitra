import React, { useEffect, useState } from 'react';
import type { Language, BeneficiaryProfile } from '../../types';
import { initialProfile } from '../../data/mockData';
import { Step1WelcomeLogin } from './Step1WelcomeLogin';
import { Step2VoiceProfileBasic } from './Step2VoiceProfileBasic';
import { Step3VoiceProfileAdvanced } from './Step3VoiceProfileAdvanced';
import { Step4AIAnalysis } from './Step4AIAnalysis';
import { Step5LivelihoodRecommendations } from './Step5LivelihoodRecommendations';
import { Step6SkillTrainingDetails } from './Step6SkillTrainingDetails';
import { Step7PostSkillingSupport } from './Step7PostSkillingSupport';

interface FlowContainerProps {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  onNavigateModule: (moduleKey: string) => void;
}

export const FlowContainer: React.FC<FlowContainerProps> = ({
  language,
  onSelectLanguage,
  onNavigateModule,
}) => {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [profile, setProfile] = useState<BeneficiaryProfile>(initialProfile);
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    try {
      const saved = window.sessionStorage.getItem('jeevanmitra-journey');
      if (saved) {
        const journey = JSON.parse(saved) as { step?: number; profile?: BeneficiaryProfile };
        if (Number.isInteger(journey.step) && journey.step! >= 1 && journey.step! <= 7) setCurrentStep(journey.step!);
        if (journey.profile) setProfile(journey.profile);
      }
    } catch {
      window.sessionStorage.removeItem('jeevanmitra-journey');
    }
    setRestored(true);
  }, []);

  useEffect(() => {
    if (restored) window.sessionStorage.setItem('jeevanmitra-journey', JSON.stringify({ step: currentStep, profile }));
  }, [currentStep, profile, restored]);

  const updateProfile = (updates: Partial<BeneficiaryProfile>) => {
    setProfile((prev) => ({ ...prev, ...updates }));
  };

  const stepTitles = [
    'Welcome & consent',
    'Your interests',
    'Your experience',
    'Understand your profile',
    'Explore your matches',
    'Training details',
    'Your next steps',
  ];

  return (
    <div className="flow-layout">
      <aside className="flow-progress" aria-label="Journey progress">
        <div className="eyebrow">ONE STEP AT A TIME</div>
        <h1>My journey</h1>
        <p>Step {currentStep} of {stepTitles.length}</p>
        <ol>{stepTitles.map((title, index) => <li key={title}><button disabled={index + 1 > currentStep} aria-current={index + 1 === currentStep ? 'step' : undefined} onClick={() => setCurrentStep(index + 1)} className={`flow-step ${index + 1 === currentStep ? 'current' : index + 1 < currentStep ? 'complete' : ''}`} title={title}><span>{index + 1 < currentStep ? '✓' : index + 1}</span>{title}</button></li>)}</ol>
      </aside>
      <div className="flow-canvas">
        {currentStep === 1 && (
          <Step1WelcomeLogin
            language={language}
            onSelectLanguage={onSelectLanguage}
            onNext={() => setCurrentStep(2)}
          />
        )}

        {currentStep === 2 && (
          <Step2VoiceProfileBasic
            language={language}
            profile={profile}
            onUpdateProfile={updateProfile}
            onNext={() => setCurrentStep(3)}
            onPrev={() => setCurrentStep(1)}
          />
        )}

        {currentStep === 3 && (
          <Step3VoiceProfileAdvanced
            language={language}
            profile={profile}
            onUpdateProfile={updateProfile}
            onNext={() => setCurrentStep(4)}
            onPrev={() => setCurrentStep(2)}
          />
        )}

        {currentStep === 4 && (
          <Step4AIAnalysis
            language={language}
            profile={profile}
            onNext={() => setCurrentStep(5)}
            onPrev={() => setCurrentStep(3)}
          />
        )}

        {currentStep === 5 && (
          <Step5LivelihoodRecommendations
            language={language}
            onSelectCourse={(_courseId) => setCurrentStep(6)}
            onNext={() => setCurrentStep(6)}
            onPrev={() => setCurrentStep(4)}
          />
        )}

        {currentStep === 6 && (
          <Step6SkillTrainingDetails
            language={language}
            onNext={() => setCurrentStep(7)}
            onPrev={() => setCurrentStep(5)}
            onOpenTrainingModule={() => onNavigateModule('training-quiz')}
          />
        )}

        {currentStep === 7 && (
          <Step7PostSkillingSupport
            language={language}
            onNavigateModule={onNavigateModule}
            onRestart={() => { setCurrentStep(1); setProfile(initialProfile); }}
            onPrev={() => setCurrentStep(6)}
          />
        )}
      </div>
    </div>
  );
};
