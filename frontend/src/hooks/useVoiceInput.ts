import { useEffect, useRef, useState } from 'react';
import type { Language } from '../types';
import { getVoiceCapability } from '../lib/i18n/voiceCapabilities';
import { startSpeechCapture } from '../utils/speechCapture';
import { api } from '../lib/api';
import { stripAssistantEcho } from '../utils/voiceTurn';

/** Capture one real answer per speech/pause boundary using server transcription. */
export function useVoiceInput(language: Language, onAnswer: (text: string) => void, interviewId?: string, assistantQuestion = '') {
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');
  const [supported, setSupported] = useState(false);
  const startTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancel = useRef<(() => void) | null>(null);
  const request = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const callback = useRef(onAnswer);
  callback.current = onAnswer;
  const hi = language === 'hi';

  function cleanup() {
    generation.current++;
    if (startTimer.current) clearTimeout(startTimer.current);
    startTimer.current = null;
    cancel.current?.(); cancel.current = null;
    request.current?.abort(); request.current = null;
  }
  function stop() {
    cleanup(); setListening(false); setTranscribing(false);
  }
  function start(question = assistantQuestion) {
    stop(); setError(''); setTranscript('');
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setError(hi ? 'माइक के लिए localhost या HTTPS पर ऐप खोलें। अभी उत्तर टाइप कर सकते हैं।' : 'Open the app on localhost or HTTPS to use the microphone. You can type your answer below.');
      return false;
    }
    if (typeof MediaRecorder === 'undefined' || getVoiceCapability(language).stt !== 'supported' || !interviewId) {
      setError(hi ? 'इस ब्राउज़र में आवाज़ उपलब्ध नहीं है। अपना उत्तर टाइप करें।' : 'Voice recording is unavailable. You can type your answer below.');
      return false;
    }
    const current = generation.current;
    const capture = () => {
      if (generation.current !== current) return;
      setListening(true);
      cancel.current = startSpeechCapture(() => {
      if (generation.current === current) { cancel.current = null; setListening(false); }
    }, captureError => {
      if (generation.current !== current) return;
      cancel.current = null; setListening(false);
      if (captureError.message.startsWith('No speech detected')) {
        startTimer.current = setTimeout(capture, 100);
      } else setError(captureError.message);
    }, audio => {
      if (generation.current !== current) return;
      setTranscribing(true);
      const controller = new AbortController();
      request.current = controller;
      const timeout = setTimeout(() => controller.abort(), 35000);
      void api.transcribeAnswer(interviewId, audio, language, controller.signal).then(text => {
        if (generation.current !== current) return;
        request.current = null; setTranscribing(false);
        const answer = stripAssistantEcho(text, question);
        if (!answer.trim()) {
          setTranscript('');
          startTimer.current = setTimeout(capture, 100);
          return;
        }
        setTranscript('');
        callback.current(answer);
      }).catch(err => {
        if (generation.current !== current) return;
        request.current = null; setTranscribing(false);
        if (err instanceof Error && err.message.startsWith('No speech was heard')) { startTimer.current = setTimeout(capture, 100); return; }
        setError(controller.signal.aborted
          ? (hi ? 'आवाज़ समझने में समय लगा। फिर बोलें या टाइप करें।' : 'Voice transcription timed out. Try again or type your answer.')
          : err instanceof Error ? err.message : 'Could not transcribe your answer. Try again or type.');
      }).finally(() => clearTimeout(timeout));
    });
    };
    capture();
    return true;
  }
  useEffect(() => {
    // Keep the button enabled on insecure origins so it can explain what is needed.
    setSupported(typeof MediaRecorder !== 'undefined' && getVoiceCapability(language).stt === 'supported');
    return cleanup;
  }, [language, interviewId]);
  return { listening, transcribing, transcript, error, supported, start, stop, clearError: () => setError('') };
}
