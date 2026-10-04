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
  const notice = hi
    ? 'इस डेमो में आपकी रुचि, पढ़ाई और काम की पसंद के नमूना जवाब दिखाए जाएंगे। आप कभी भी रुक सकते हैं। कोई आवेदन नहीं भेजा जाएगा।'
    : 'This demo explores your interests, education and work preferences using sample responses. You can stop at any time. No application will be submitted.';

  const enabledLocales = getEnabledLocales();

  return (
    <div className="consent-welcome">
      <span className="welcome-icon">
        <Sprout size={28} />
      </span>
      <div className="eyebrow">LET’S BEGIN WITH YOU</div>
      <h2>{hi ? 'बेहतर कल की ओर पहला कदम।' : 'A little about you. A new way forward.'}</h2>
      <p>
        {hi
          ? 'अपनी भाषा चुनें, फिर कौशल और आजीविका के रास्ते जानें।'
          : 'Choose your language, then explore skills and livelihoods that could suit you.'}
      </p>

      <h3>{hi ? 'अपनी भाषा चुनें' : 'Choose your language'}</h3>
      <div className="language-options">
        {enabledLocales.map((x) => (
          <button
            key={x.code}
            aria-pressed={language === x.code}
            onClick={() => onSelectLanguage(x.code)}
          >
            {x.nativeLabel} ({x.label})
          </button>
        ))}
      </div>

      <h3>{hi ? 'शुरू करने से पहले' : 'Before we get started'}</h3>
      <p>{notice}</p>
      <label className="consent-label">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
        />
        <span>
          {hi
            ? 'मैं समझता/समझती हूँ और नमूना यात्रा शुरू करना चाहता/चाहती हूँ।'
            : 'I understand and would like to explore the sample journey.'}
        </span>
      </label>

      <div className="consent-actions">
        <button
          className="primary-button"
          disabled={!consent}
          onClick={onNext}
        >
          {hi ? 'आगे बढ़ें' : 'Let’s get started'}
          <ArrowRight size={17} />
        </button>
        <button
          className="audio-button"
          onClick={() => speakText(notice, language)}
        >
          <Volume2 size={17} />
          {hi ? 'सुनें' : 'Listen to this'}
        </button>
      </div>
      <p className="privacy-note">
        {hi
          ? 'कोई पहचान पत्र या बायोमेट्रिक आवश्यक नहीं है।'
          : 'No identity documents or biometric sign-in needed for this preview.'}
      </p>
    </div>
  );
}
