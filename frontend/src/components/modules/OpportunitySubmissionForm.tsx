"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Type, Send, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import { useAppSettings } from '../AppShell';
import { opportunitiesApi } from '../../lib/api/opportunities';
import { getVoiceCapability } from '../../lib/i18n/voiceCapabilities';
import { SoundFX } from '../../utils/speech';

interface OpportunitySubmissionFormProps {
  onSubmitted?: () => void;
}

export const OpportunitySubmissionForm: React.FC<OpportunitySubmissionFormProps> = ({
  onSubmitted
}) => {
  const { t, language } = useAppSettings();
  const [activeTab, setActiveTab] = useState<'voice' | 'text'>('text');
  const [text, setText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedSuccess, setSubmittedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const voiceCap = getVoiceCapability(language);
  const isSttSupported = voiceCap.stt === 'supported';

  // Cleanup speech recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {
          // ignore
        }
      }
    };
  }, []);

  const handleTabChange = (newTab: 'voice' | 'text') => {
    if (activeTab === 'voice' && isRecording) {
      stopRecording();
    }
    setErrorMessage(null);
    setActiveTab(newTab);
  };

  const startRecording = () => {
    if (!isSttSupported) {
      setErrorMessage(t('voice.sttUnsupported'));
      return;
    }

    const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRec) {
      setErrorMessage(t('voice.micUnavailable'));
      return;
    }

    try {
      const recognition = new SpeechRec();
      const localeTags: Record<string, string> = {
        hi: 'hi-IN',
        en: 'en-IN',
        bn: 'bn-IN',
        mr: 'mr-IN',
        ta: 'ta-IN'
      };
      recognition.lang = localeTags[language] || 'en-IN';
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setIsRecording(true);
        setErrorMessage(null);
        SoundFX.playChime('start');
      };

      recognition.onresult = (event: any) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript + ' ';
        }
        setText(prev => {
          // Append or set text
          const trimmed = transcript.trim();
          return trimmed;
        });
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
        if (event.error !== 'no-speech') {
          setErrorMessage(t('voice.micUnavailable'));
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setIsRecording(false);
      setErrorMessage(t('voice.micUnavailable'));
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
    }
    setIsRecording(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmed = text.trim();
    if (trimmed.length < 3) {
      setErrorMessage(t('opportunities.emptySubmission'));
      return;
    }
    if (trimmed.length > 1500) {
      setErrorMessage(t('opportunities.submissionTooLong', { max: 1500 }));
      return;
    }

    if (isRecording) {
      stopRecording();
    }

    setIsSubmitting(true);
    try {
      await opportunitiesApi.submitOpportunity({
        input_mode: activeTab,
        text: trimmed,
        locale: language
      });

      SoundFX.playChime('success');
      setSubmittedSuccess(true);
      setText('');
      if (onSubmitted) onSubmitted();
    } catch (err: any) {
      console.error('Submission failed:', err);
      setErrorMessage(err.message || 'Failed to submit opportunity.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submittedSuccess) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center space-y-4">
        <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-emerald-900">
          {t('opportunities.submissionSuccess')}
        </h3>
        <p className="text-sm text-emerald-700 max-w-md mx-auto">
          Your information has been logged in our verification queue. It will be validated against accredited training providers before appearing as an active opportunity.
        </p>
        <button
          type="button"
          onClick={() => setSubmittedSuccess(false)}
          className="mt-2 inline-flex items-center px-4 py-2 border border-emerald-600 text-emerald-800 rounded-xl text-sm font-semibold hover:bg-emerald-100 transition-colors"
        >
          Submit another opportunity
        </button>
      </div>
    );
  }

  const charCount = text.length;
  const isTooLong = charCount > 1500;
  const isTooShort = text.trim().length < 3;
  const canSubmit = !isTooShort && !isTooLong && !isSubmitting;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <div>
        <h3 className="text-base font-bold text-slate-900">
          Share a Local Opportunity or Need
        </h3>
        <p className="text-xs text-slate-500 mt-0.5">
          Know about a training batch, workshop vacancy, or need? Submit it below for field staff verification.
        </p>
      </div>

      {/* Mode Tabs (Accessible Tablist) */}
      <div
        role="tablist"
        aria-label="Submission Input Mode"
        className="flex items-center gap-2 border-b border-slate-100 pb-2"
      >
        <button
          type="button"
          role="tab"
          id="tab-voice"
          aria-selected={activeTab === 'voice'}
          aria-controls="panel-voice"
          tabIndex={activeTab === 'voice' ? 0 : -1}
          onClick={() => handleTabChange('voice')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'voice'
              ? 'bg-emerald-700 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Mic className="w-3.5 h-3.5" />
          <span>{t('opportunities.inputModeVoice')}</span>
        </button>

        <button
          type="button"
          role="tab"
          id="tab-text"
          aria-selected={activeTab === 'text'}
          aria-controls="panel-text"
          tabIndex={activeTab === 'text' ? 0 : -1}
          onClick={() => handleTabChange('text')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'text'
              ? 'bg-emerald-700 text-white shadow-xs'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <Type className="w-3.5 h-3.5" />
          <span>{t('opportunities.inputModeText')}</span>
        </button>
      </div>

      {/* Voice Mode Panel */}
      {activeTab === 'voice' && (
        <div
          role="tabpanel"
          id="panel-voice"
          aria-labelledby="tab-voice"
          className="space-y-3"
        >
          {!isSttSupported ? (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2.5 text-xs text-amber-900">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">{t('voice.sttUnsupported')}</p>
                <button
                  type="button"
                  onClick={() => handleTabChange('text')}
                  className="mt-1 font-bold underline text-amber-800"
                >
                  Switch to text input
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-4 bg-slate-50 border border-dashed border-slate-200 rounded-xl space-y-3">
              <button
                type="button"
                onClick={isRecording ? stopRecording : startRecording}
                className={`w-14 h-14 rounded-full flex items-center justify-center text-white shadow-md transition-all ${
                  isRecording
                    ? 'bg-red-600 animate-pulse hover:bg-red-700 ring-4 ring-red-200'
                    : 'bg-emerald-700 hover:bg-emerald-800'
                }`}
                aria-label={isRecording ? t('voice.stopRecording') : t('voice.tapToSpeak')}
              >
                {isRecording ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
              </button>
              <p className="text-xs font-semibold text-slate-700">
                {isRecording ? t('voice.recording') : t('voice.tapToSpeak')}
              </p>
              {isRecording && (
                <button
                  type="button"
                  onClick={stopRecording}
                  className="text-xs text-red-600 font-bold hover:underline"
                >
                  {t('voice.stopRecording')}
                </button>
              )}
            </div>
          )}

          {/* Transcript review / edit area */}
          <div>
            <label htmlFor="voice-transcript" className="block text-xs font-semibold text-slate-700 mb-1">
              {t('voice.reviewTranscript')}
            </label>
            <textarea
              id="voice-transcript"
              rows={3}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t('opportunities.promptLabel')}
              className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-600 bg-white"
            />
          </div>
        </div>
      )}

      {/* Text Mode Panel */}
      {activeTab === 'text' && (
        <div
          role="tabpanel"
          id="panel-text"
          aria-labelledby="tab-text"
          className="space-y-2"
        >
          <label htmlFor="text-submission" className="block text-xs font-semibold text-slate-700">
            {t('opportunities.promptLabel')}
          </label>
          <textarea
            id="text-submission"
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. There is a solar panel installation training batch starting at PMKK Moradabad next Monday with 15 seats."
            className="w-full text-xs p-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-600 bg-white"
          />
        </div>
      )}

      {/* Error Message */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-2.5 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Character Count & Submit Actions */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-100">
        <span
          className={`text-[11px] font-medium ${
            isTooLong ? 'text-red-600 font-bold' : 'text-slate-500'
          }`}
        >
          {t('opportunities.charCount', { current: charCount, max: 1500 })}
        </span>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
            canSubmit
              ? 'bg-emerald-700 text-white hover:bg-emerald-800 shadow-xs cursor-pointer'
              : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200'
          }`}
        >
          {isSubmitting ? (
            <span>{t('opportunities.submitting')}</span>
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
              <span>{t('opportunities.submitInformation')}</span>
            </>
          )}
        </button>
      </div>

      {/* Verification Invariant Banner */}
      <div className="bg-slate-50 rounded-xl p-2.5 flex items-start gap-2 text-[11px] text-slate-500 border border-slate-100">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
        <span>
          Verification invariant: All submissions are reviewed by field staff before being added to verified opportunities.
        </span>
      </div>
    </div>
  );
};
