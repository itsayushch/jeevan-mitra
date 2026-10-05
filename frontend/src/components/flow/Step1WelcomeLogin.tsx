import { useState } from 'react';
import { Sprout, ArrowRight, Volume2 } from 'lucide-react';
import type { Language } from '../../types';
import { speakText } from '../../utils/speech';
import { getEnabledLocales } from '../../lib/i18n/locales';

interface Step1Props {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  onNext: () => void;
}

export function Step1WelcomeLogin({ language, onSelectLanguage, onNext }: Step1Props) {
  const [consent, setConsent] = useState(false);
  const hi = language === 'hi';

  // Simplified text for villagers
  const notice = hi
    ? 'हम आपसे कुछ आसान सवाल पूछेंगे ताकि आपके लिए सही काम और ट्रेनिंग ढूंढ सकें। आपकी जानकारी सुरक्षित रहेगी।'
    : 'We will ask a few simple questions to find the right training and jobs for you. Your information is safe.';

  const enabledLocales = getEnabledLocales();

  return (
    <div className="consent-welcome">
      <span className="welcome-icon">
        <Sprout size={28} />
      </span>
      <div className="eyebrow">{hi ? 'शुरुआत करें' : 'LET’S BEGIN'}</div>
      <h2>{hi ? 'जीवन मित्रा में आपका स्वागत है' : 'Welcome to Jeevan Mitra'}</h2>
      <p>
        {hi
          ? 'आप किस भाषा में बात करना चाहेंगे?'
          : 'Which language do you prefer to talk in?'}
      </p>

      <div className="language-options">
        {enabledLocales.map((x) => (
          <button
            key={x.code}
            aria-pressed={language === x.code}
            onClick={() => onSelectLanguage(x.code)}
          >
            {x.nativeLabel}
          </button>
        ))}
      </div>

      <h3>{hi ? 'जरूरी जानकारी' : 'Important Information'}</h3>
      <p>{notice}</p>

      <label className="consent-label">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
        />
        <span>
          {hi
            ? 'हां, मैं समझ गया/गई हूँ।'
            : 'Yes, I understand.'}
        </span>
      </label>

      <div className="consent-actions">
        <button
          className="primary-button"
          disabled={!consent}
          onClick={onNext}
        >
          {hi ? 'आगे बढ़ें' : 'Next Step'}
          <ArrowRight size={17} />
        </button>
        <button
          className="audio-button"
          onClick={() => speakText(notice, language)}
        >
          <Volume2 size={17} />
          {hi ? 'सुनें' : 'Listen'}
        </button>
      </div>
    </div>
  );
}
