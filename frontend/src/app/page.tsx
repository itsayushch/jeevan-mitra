"use client";
import { useRef, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Phone, KeyRound, ArrowRight, Mic, Sprout, ArrowLeft, LoaderCircle } from 'lucide-react';
import { useAppSettings } from '../components/AppShell';
import { Step1WelcomeLogin } from '../components/flow/Step1WelcomeLogin';
import { SoundFX } from '../utils/speech';
import { startSpeechCapture } from '../utils/speechCapture';

const DUMMY_MOBILE_NUMBER = '9876543210';
const DUMMY_OTP = '1234';
export default function AppFlow() {
  const { language, setLanguage } = useAppSettings();
  const router = useRouter();
  const [step, setStep] = useState<'welcome' | 'mobile_login' | 'otp'>('welcome');
  const [mobileNumber, setMobileNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [busy, setBusy] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelCapture = useRef<(() => void) | null>(null);
  const hi = language === 'hi';
  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
    cancelCapture.current?.();
  }, []);

  // Retain the existing mobile-number -> four-digit OTP kiosk onboarding.
  const handleSendOtp = () => {
    if (mobileNumber.length !== 10 || busy) return;
    setBusy(true); setError('');
    timer.current = setTimeout(() => { setBusy(false); setStep('otp'); }, 800);
  };
  const handleVerifyOtp = () => {
    if (otp.length !== 4 || busy) return;
    setBusy(true); setError('');
    timer.current = setTimeout(() => { setBusy(false); router.push('/voice-assistant'); }, 800);
  };
  // Demo values are applied only after speech, a pause, and microphone shutdown.
  const handleFakeVoiceInput = (type: 'mobile' | 'otp') => {
    if (busy) return;
    if (cancelCapture.current) {
      cancelCapture.current();
      cancelCapture.current = null;
      setIsListening(false);
      return;
    }
    setError('');
    setIsListening(true);
    cancelCapture.current = startSpeechCapture(() => {
      cancelCapture.current = null;
      setIsListening(false);
      if (type === 'mobile') setMobileNumber(DUMMY_MOBILE_NUMBER);
      else setOtp(DUMMY_OTP);
      SoundFX.playChime('success');
    }, captureError => {
      cancelCapture.current = null;
      setIsListening(false);
      setError(captureError.message);
    });
  };
  return <div className="kiosk-onboarding">
    <header className="kiosk-brand"><span className="kiosk-brand-icon"><Sprout size={29}/></span><span>Jeevan<span>Mitra</span><small>{hi ? 'आपके बेहतर कल का साथी' : 'Your livelihood companion'}</small></span></header>
    <nav className="kiosk-progress" aria-label={hi ? 'शुरुआत की प्रगति' : 'Onboarding progress'}><div className={`flow-step ${step === 'welcome' ? 'current' : 'complete'}`} aria-current={step === 'welcome' ? 'step' : undefined}><span>1</span>{hi ? 'स्वागत' : 'Welcome'}</div><span className="kiosk-progress-line"/><div className={`flow-step ${step !== 'welcome' ? 'current' : ''}`} aria-current={step !== 'welcome' ? 'step' : undefined}><span>2</span>{hi ? 'लॉगिन' : 'Login'}</div></nav>
    <div className="flow-canvas kiosk-card" aria-busy={busy || isListening}>
      {step === 'welcome' && <Step1WelcomeLogin language={language} onSelectLanguage={setLanguage} onNext={() => setStep('mobile_login')}/>}
      {step === 'mobile_login' && <section className="consent-welcome kiosk-login"><span className="welcome-icon"><Phone size={30}/></span><div className="eyebrow">{hi ? 'लॉगिन' : 'LOGIN'}</div><h2>{hi ? 'अपना मोबाइल नंबर डालें' : 'Enter your mobile number'}</h2><p>{hi ? 'हम आपके नंबर पर एक छोटा सा कोड भेजेंगे। आप बोलकर भी नंबर दर्ज कर सकते हैं।' : 'We will send a short code to your number. You can also tap the mic to speak.'}</p><form onSubmit={event => { event.preventDefault(); handleSendOtp(); }}><label className="kiosk-field-label" htmlFor="kiosk-mobile">{hi ? 'मोबाइल नंबर' : 'Mobile number'}</label><div className="kiosk-phone-field"><span>+91</span><input id="kiosk-mobile" type="tel" inputMode="numeric" autoComplete="tel-national" placeholder={hi ? '10 अंकों का नंबर' : '10-digit mobile number'} value={mobileNumber} onChange={event => setMobileNumber(event.target.value.replace(/\D/g, '').slice(0, 10))} disabled={busy || isListening}/><button type="button" className={`kiosk-voice-number ${isListening ? 'is-listening' : ''}`} onClick={() => handleFakeVoiceInput('mobile')} disabled={busy} aria-pressed={isListening} aria-label={isListening ? (hi ? 'माइक बंद करें' : 'Stop microphone') : (hi ? 'अपना मोबाइल नंबर बोलें' : 'Speak your mobile number')}><Mic size={23}/></button></div>{isListening && <p className="kiosk-listening" role="status">{hi ? 'बोलें। रुकने के बाद नंबर अपने आप भर जाएगा। माइक दबाकर रद्द करें।' : 'Speak now. After you pause, the demo value will appear. Tap the mic to cancel.'}</p>}<div className="consent-actions"><button className="primary-button" type="submit" disabled={mobileNumber.length !== 10 || busy || isListening}>{busy ? <LoaderCircle size={20} className="spin"/> : null}{busy ? (hi ? 'भेज रहे हैं…' : 'Sending…') : (hi ? 'कोड भेजें' : 'Send code')}<ArrowRight size={20}/></button><button className="audio-button" type="button" onClick={() => { setStep('welcome'); setError(''); }} disabled={busy || isListening}><ArrowLeft size={18}/>{hi ? 'पीछे जाएँ' : 'Go back'}</button></div></form></section>}
      {step === 'otp' && <section className="consent-welcome kiosk-login"><span className="welcome-icon"><KeyRound size={30}/></span><div className="eyebrow">{hi ? 'सत्यापन' : 'VERIFICATION'}</div><h2>{hi ? 'कोड डालें' : 'Enter the code'}</h2><p>{hi ? `हमने +91 ${mobileNumber} पर 4 अंकों का कोड भेजा है। उसे यहाँ लिखें।` : `We sent a 4-digit code to +91 ${mobileNumber}. Please enter it here.`}</p><form onSubmit={event => { event.preventDefault(); handleVerifyOtp(); }}><label className="kiosk-field-label" htmlFor="kiosk-otp">{hi ? '4 अंकों का OTP' : '4-digit OTP'}</label><div className="kiosk-otp-row"><div className="kiosk-otp-input"><input id="kiosk-otp" type="tel" inputMode="numeric" autoComplete="one-time-code" value={otp} onChange={event => setOtp(event.target.value.replace(/\D/g, '').slice(0, 4))} disabled={busy || isListening}/><div className="kiosk-otp-boxes" aria-hidden="true">{[0,1,2,3].map(index => <span key={index} className={otp.length === index ? 'active' : otp[index] ? 'filled' : ''}>{otp[index] || '–'}</span>)}</div></div><button type="button" className={`kiosk-voice-number ${isListening ? 'is-listening' : ''}`} onClick={() => handleFakeVoiceInput('otp')} disabled={busy} aria-pressed={isListening} aria-label={isListening ? (hi ? 'माइक बंद करें' : 'Stop microphone') : (hi ? 'OTP बोलें' : 'Speak your OTP')}><Mic size={23}/></button></div>{isListening && <p className="kiosk-listening" role="status">{hi ? 'बोलें। रुकने के बाद नंबर अपने आप भर जाएगा। माइक दबाकर रद्द करें।' : 'Speak now. After you pause, the demo value will appear. Tap the mic to cancel.'}</p>}<div className="consent-actions"><button className="primary-button" type="submit" disabled={otp.length !== 4 || busy || isListening}>{busy ? <LoaderCircle size={20} className="spin"/> : null}{busy ? (hi ? 'जाँच रहे हैं…' : 'Verifying…') : (hi ? 'पुष्टि करें और आगे बढ़ें' : 'Verify & continue')}<ArrowRight size={20}/></button><button className="audio-button" type="button" onClick={() => { setOtp(''); setStep('mobile_login'); setError(''); }} disabled={busy || isListening}><ArrowLeft size={18}/>{hi ? 'नंबर बदलें' : 'Change number'}</button></div></form></section>}
      {error && <p className="inline-error" role="alert">{error}</p>}
    </div><p className="kiosk-bottom-note">{hi ? 'बोलें या टाइप करें। अपनी गति से आगे बढ़ें।' : 'Speak or type. Continue at your own pace.'}</p>
  </div>;
}
