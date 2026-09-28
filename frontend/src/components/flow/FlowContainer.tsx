import React, { useState } from 'react';
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

  const updateProfile = (updates: Partial<BeneficiaryProfile>) => {
    setProfile((prev) => ({ ...prev, ...updates }));
  };

  const stepTitles = [
    'Welcome & Login',
    'Voice Profile (Basic)',
    'Voice Profile (Advanced)',
    'AI Analysis',
    'Livelihood Recommendations',
    'Skill Training Details',
    'Post-Skilling & Support',
  ];

  return (
    <div className="w-full flex flex-col items-center">
      {/* Top Flow Stepper Progress Bar */}
      <div className="w-full max-w-[440px] px-4 pt-3 pb-1">
        <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 mb-1.5">
          <span className="text-emerald-700 uppercase tracking-wider">
            Step {currentStep} of 7: {stepTitles[currentStep - 1]}
          </span>
          <span className="font-semibold text-slate-400">
            {Math.round((currentStep / 7) * 100)}%
          </span>
        </div>

        {/* Stepper Dots & Line */}
        <div className="flex items-center gap-1.5 w-full">
          {stepTitles.map((_, idx) => {
            const stepNum = idx + 1;
            const isActive = stepNum === currentStep;
            const isCompleted = stepNum < currentStep;

            return (
              <button
                key={stepNum}
                onClick={() => setCurrentStep(stepNum)}
                title={stepTitles[idx]}
                className={`h-2 flex-1 rounded-full transition-all duration-300 ${
                  isActive
                    ? 'bg-emerald-600 ring-2 ring-emerald-300 ring-offset-1'
                    : isCompleted
                    ? 'bg-emerald-500'
                    : 'bg-slate-200 hover:bg-slate-300'
                }`}
              />
            );
          })}
        </div>
      </div>

      {/* Main Step Canvas Frame */}
      <div className="w-full max-w-[440px] bg-[#fbf9f1] border border-amber-900/10 rounded-[36px] shadow-xl overflow-hidden my-3">
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
            onRestart={() => setCurrentStep(1)}
            onPrev={() => setCurrentStep(6)}
          />
        )}
      </div>
    </div>
  );
};
