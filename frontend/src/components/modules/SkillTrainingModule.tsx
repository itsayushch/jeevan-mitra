import React, { useState } from 'react';
import { Play, Pause, Volume2, Mic, CheckCircle2, XCircle, Award, ChevronRight, RotateCcw } from 'lucide-react';
import type { Language } from '../../types';
import { mushroomModules, mushroomQuiz } from '../../data/mockData';
import { SoundFX, speakText, stopSpeaking } from '../../utils/speech';

interface SkillTrainingModuleProps {
  language: Language;
}

export const SkillTrainingModule: React.FC<SkillTrainingModuleProps> = ({ language }) => {
  const [activeTab, setActiveTab] = useState<'lessons' | 'quiz'>('lessons');
  const [playingLessonId, setPlayingLessonId] = useState<string | null>(null);
  
  // Quiz state
  const [quizIndex, setQuizIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isVoiceAnswering, setIsVoiceAnswering] = useState(false);
  const [quizScore, setQuizScore] = useState(0);

  const currentQuiz = mushroomQuiz[quizIndex] || mushroomQuiz[0];

  const handleTogglePlayLesson = (lessonId: string, prompt: string) => {
    if (playingLessonId === lessonId) {
      stopSpeaking();
      setPlayingLessonId(null);
    } else {
      stopSpeaking();
      SoundFX.playChime('click');
      setPlayingLessonId(lessonId);
      speakText(prompt, language, () => setPlayingLessonId(null));
    }
  };

  const handleReadAloudQuiz = () => {
    SoundFX.playChime('question');
    const questionText = language === 'hi' ? currentQuiz.questionHi : currentQuiz.question;
    const optionsText = currentQuiz.options
      .map((o) => `Option ${o.key}: ${language === 'hi' ? o.textHi : o.text}`)
      .join('. ');
    speakText(`${questionText}. ${optionsText}`, language);
  };

  const handleVoiceAnswer = () => {
    SoundFX.playChime('start');
    setIsVoiceAnswering(true);
    setTimeout(() => {
      setIsVoiceAnswering(false);
      // Pick correct answer A
      handleSelectOption('A');
      SoundFX.playChime('success');
    }, 1800);
  };

  const handleSelectOption = (key: string) => {
    setSelectedOption(key);
    setShowResult(true);
    const chosen = currentQuiz.options.find((o) => o.key === key);
    if (chosen?.isCorrect) {
      SoundFX.playChime('success');
      setQuizScore((prev) => prev + 1);
      const praise = language === 'hi' ? 'शाबाश! सही उत्तर।' : 'Excellent! That is the correct answer.';
      speakText(praise, language);
    } else {
      const correction = language === 'hi' ? 'यह गलत है। सही उत्तर ए है।' : 'Incorrect. The correct answer is Option A.';
      speakText(correction, language);
    }
  };

  const handleNextQuiz = () => {
    if (quizIndex < mushroomQuiz.length - 1) {
      setQuizIndex((prev) => prev + 1);
      setSelectedOption(null);
      setShowResult(false);
    } else {
      // Completed quiz
      SoundFX.playChime('success');
    }
  };

  return (
    <div className="module-page training-page">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
            NSQF Interactive Skilling
          </span>
          <div className="flex bg-white rounded-xl border border-slate-200 p-0.5">
            <button
              onClick={() => setActiveTab('lessons')}
              className={`text-xs font-bold px-3 py-1 rounded-lg transition-all ${
                activeTab === 'lessons'
                  ? 'bg-emerald-700 text-white'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Lessons
            </button>
            <button
              onClick={() => setActiveTab('quiz')}
              className={`text-xs font-bold px-3 py-1 rounded-lg transition-all ${
                activeTab === 'quiz'
                  ? 'bg-emerald-700 text-white'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Quiz & Test
            </button>
          </div>
        </div>

        <h2 className="text-base font-black text-slate-900 tracking-tight mb-1">
          TRAINING: MUSHROOM CULTIVATION
        </h2>
        <p className="text-xs font-bold text-emerald-700 mb-3">
          Module 2: Media Preparation
        </p>

        {/* Tab 1: Interactive Lessons */}
        {activeTab === 'lessons' && (
          <div className="lesson-grid space-y-3">
            {mushroomModules.map((module) => {
              const isPlaying = playingLessonId === module.id;
              return (
                <div
                  key={module.id}
                  className="bg-white rounded-2xl p-3.5 border border-slate-200/90 shadow-xs flex items-center justify-between gap-3 hover:border-emerald-300 transition-all"
                >
                  <div className="flex items-center gap-3">
                    {/* Visual lesson icon */}
                    <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-xl shrink-0 shadow-2xs">
                      {module.icon === 'soil' ? '🌾' : module.icon === 'water' ? '💧' : '🌡️'}
                    </div>

                    <div>
                      <h4 className="text-xs font-black text-slate-900 leading-tight">
                        {module.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 font-medium line-clamp-1 mt-0.5">
                        {module.description}
                      </p>
                      <span className="text-[10px] text-emerald-700 font-bold block mt-1">
                        ⏱ {module.duration}
                      </span>
                    </div>
                  </div>

                  {/* Play audio button */}
                  <button
                    onClick={() => handleTogglePlayLesson(module.id, module.audioPrompt)}
                    className={`w-9 h-9 rounded-full flex items-center justify-center transition-all shrink-0 shadow-sm ${
                      isPlaying
                        ? 'bg-rose-500 text-white animate-pulse'
                        : 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                    }`}
                    title={isPlaying ? 'Pause' : 'Play Audio Lesson'}
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                  </button>
                </div>
              );
            })}

            {/* Test Your Skill Banner */}
            <div className="mt-4 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-3xl p-4 flex items-center justify-between gap-3 shadow-xs">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 block">
                  Verify Learning
                </span>
                <h4 className="text-xs font-black text-slate-900">
                  Ready to test your knowledge?
                </h4>
              </div>
              <button
                onClick={() => {
                  SoundFX.playChime('click');
                  setActiveTab('quiz');
                }}
                className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-2.5 px-4 rounded-xl flex items-center gap-1.5 shadow-sm transition-all"
              >
                <span>Test Your Skill (Quiz)</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Tab 2: Voice Read-Aloud Quiz */}
        {activeTab === 'quiz' && (
          <div className="training-quiz bg-white rounded-3xl p-4 border border-slate-200/90 shadow-sm">
            {/* Progress overview */}
            <div className="mb-3">
              <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 mb-1">
                <span className="text-emerald-700">Question {quizIndex + 1} of {mushroomQuiz.length}</span>
                <span>Progress: {Math.round(((quizIndex + 1) / mushroomQuiz.length) * 100)}%</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${((quizIndex + 1) / mushroomQuiz.length) * 100}%` }}
                />
              </div>
            </div>

            {/* Question Text with Read Aloud Button */}
            <div className="bg-slate-50 rounded-2xl p-3 border border-slate-100 mb-3">
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="text-xs font-black text-slate-900 leading-snug">
                  {language === 'hi' ? currentQuiz.questionHi : currentQuiz.question}
                </p>
                <button
                  onClick={handleReadAloudQuiz}
                  className="p-1.5 rounded-lg bg-white border border-slate-200 text-emerald-700 hover:bg-emerald-50 shrink-0"
                  title="Read aloud question"
                >
                  <Volume2 className="w-4 h-4" />
                </button>
              </div>
              <span className="text-[10px] text-slate-400 font-semibold uppercase">
                Open voice read-aloud quiz
              </span>
            </div>

            {/* Radio Options A, B, C */}
            <div className="space-y-2 mb-3">
              {currentQuiz.options.map((opt) => {
                const isSelected = selectedOption === opt.key;
                const isCorrect = opt.isCorrect;

                let borderStyle = 'border-slate-200 hover:border-slate-300';
                if (showResult && isSelected) {
                  borderStyle = isCorrect
                    ? 'border-emerald-500 bg-emerald-50'
                    : 'border-rose-500 bg-rose-50';
                } else if (isSelected) {
                  borderStyle = 'border-emerald-600 bg-emerald-50';
                }

                return (
                  <button
                    key={opt.key}
                    onClick={() => handleSelectOption(opt.key)}
                    className={`w-full p-2.5 rounded-2xl border text-left flex items-start gap-2.5 transition-all text-xs ${borderStyle}`}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center font-black text-xs shrink-0 ${
                        isSelected
                          ? 'bg-emerald-700 text-white'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {opt.key}
                    </div>

                    <div className="flex-1">
                      <p className="font-bold text-slate-800 leading-tight">
                        {language === 'hi' ? opt.textHi : opt.text}
                      </p>
                    </div>

                    {showResult && isSelected && (
                      <span className="shrink-0">
                        {isCorrect ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-600" />
                        )}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Explanation card */}
            {showResult && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-2.5 mb-3 text-[11px] text-emerald-900 font-medium animate-fadeIn">
                <strong>Explanation:</strong> {currentQuiz.explanation}
              </div>
            )}

            {/* Action buttons */}
            <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={handleVoiceAnswer}
                disabled={isVoiceAnswering}
                className={`flex-1 text-xs font-bold py-2.5 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-all ${
                  isVoiceAnswering
                    ? 'bg-rose-600 text-white animate-pulse'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                <Mic className="w-3.5 h-3.5 text-emerald-700" />
                <span>{isVoiceAnswering ? 'Listening...' : 'Speak Answer'}</span>
              </button>

              {showResult && (
                <button
                  onClick={handleNextQuiz}
                  className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-2.5 px-4 rounded-xl shadow-xs transition-colors"
                >
                  {quizIndex < mushroomQuiz.length - 1 ? 'Next Question →' : 'Finish Quiz ✓'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-400 font-semibold">
        <span className="flex items-center gap-1 text-emerald-700 font-bold">
          <Award className="w-3.5 h-3.5" /> Score: {quizScore} / {mushroomQuiz.length}
        </span>
        <button
          onClick={() => {
            setQuizIndex(0);
            setSelectedOption(null);
            setShowResult(false);
            setQuizScore(0);
          }}
          className="text-slate-500 hover:text-slate-800 flex items-center gap-1"
        >
          <RotateCcw className="w-3 h-3" /> Reset
        </button>
      </div>
    </div>
  );
};
