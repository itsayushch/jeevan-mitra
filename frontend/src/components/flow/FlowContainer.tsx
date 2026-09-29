import { useRef, useState } from 'react';
import type { Language } from '../../types';
import { api, type RecommendationItem } from '../../lib/api';
import { AskQuestionVoice } from '../modules/AskQuestionVoice';
import styles from './LiveJourney.module.css';
interface Props { language: Language; onSelectLanguage: (language: Language) => void; onNavigateModule: (key: string) => void; }
export function FlowContainer({ language, onSelectLanguage }: Props) {
  const hi = language === 'hi';
  const [step, setStep] = useState(1);
  const [review, setReview] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [error, setError] = useState('');
  const [interviewId, setInterviewId] = useState('');
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [selected, setSelected] = useState<RecommendationItem | null>(null);
  const [referralConsent, setReferralConsent] = useState(false);
  const [referralId, setReferralId] = useState('');
  const [profile, setProfile] = useState({ district: '', block: '', education: '', interests: '', skills: '', mobility: '', work: '', current_work: '', access_needs: '' });
  const labels = hi ? ['सहमति', 'आपकी जानकारी', 'आपके विकल्प'] : ['Your consent', 'Your profile', 'Your matches'];
  const field = (key: keyof typeof profile, label: string, required = true, type = 'text') => <label>{label}<input required={required} type={type} min={type === 'number' ? 1 : undefined} max={type === 'number' ? 500 : undefined} value={profile[key]} onChange={e => setProfile(p => ({ ...p, [key]: e.target.value }))} /></label>;
  async function perform(action: () => Promise<void>) {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError('');
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : 'Please try again.'); }
    finally { pending.current = false; setBusy(false); }
  }
  async function begin() {
    await perform(async () => {
      if (!api.getSessionToken()) await api.createAnonymousSession();
      await api.recordConsent('ai_processing', true, language);
      await api.recordConsent('profile_storage', true, language);
      const interview = await api.startInterview(language);
      setInterviewId(interview.interview_id); setStep(2);
    });
  }
  async function match() {
    await perform(async () => {
      const list = (value: string) => value.split(',').map(s => s.trim()).filter(Boolean);
      await api.confirmProfile(interviewId, {
        district: profile.district.trim(), block: profile.block.trim(), education: profile.education,
        interests: list(profile.interests), traditional_or_existing_skills: list(profile.skills),
        mobility: Number(profile.mobility), self_employment_or_wage_preference: profile.work,
        current_work: profile.current_work.trim(), access_needs: profile.access_needs.trim(), language,
      });
      const result = await api.generateRecommendations(interviewId);
      setRecommendations(result.recommendations); setSelected(null); setReferralId(''); setReferralConsent(false); setStep(3);
    });
  }
  return <div className="flow-layout">
    <aside className="flow-progress"><div className="eyebrow">JEEVANMITRA</div><h1>{hi ? 'मेरी यात्रा' : 'My journey'}</h1><p>{hi ? 'आपकी पसंद से आपके अवसर तक।' : 'From your interests to your opportunities.'}</p><ol>{labels.map((label, i) => <li key={label}><span className={`flow-step ${step === i + 1 ? 'current' : ''}`} aria-current={step === i + 1 ? 'step' : undefined}><span>{i + 1}</span>{label}</span></li>)}</ol></aside>
    <div className={`flow-canvas ${styles.page}`} aria-busy={busy}>
      {error && <p role="alert" className={styles.error}>{error} {hi ? 'कृपया फिर से कोशिश करें।' : 'Your answers are still here. Please try again.'}</p>}
      {step === 1 && <section><div className="eyebrow">LET’S BEGIN WITH YOU</div><h2>{hi ? 'आपके लिए सही रास्ता खोजें' : 'Find a path that fits you.'}</h2><p>{hi ? 'आपकी पढ़ाई, रुचि और यात्रा की सीमा के आधार पर विकल्प खोजें।' : 'Explore training pathways based on your education, interests and travel preferences.'}</p><label>{hi ? 'भाषा' : 'Language'}<select value={language} onChange={e => onSelectLanguage(e.target.value as Language)}><option value="en">English</option><option value="hi">हिन्दी</option></select></label><label className={styles.check}><input type="checkbox" checked={consent} onChange={e => setConsent(e.target.checked)} />{hi ? 'मैं अपनी दी गई जानकारी को सुरक्षित रखने और AI आधारित सुझावों के लिए उपयोग करने की सहमति देता/देती हूँ।' : 'I agree to store my answers and process them with the configured AI service to create my profile and recommendations.'}</label><p>{hi ? 'कोई आवेदन स्वतः नहीं भेजा जाएगा।' : 'No application is submitted automatically. Counselor sharing requires separate consent.'}</p><button className="primary-button" disabled={!consent || busy} onClick={begin}>{busy ? (hi ? 'शुरू हो रहा है…' : 'Starting…') : (hi ? 'शुरू करें' : 'Get started')}</button></section>}
      {step === 2 && !review && <AskQuestionVoice language={language} interviewId={interviewId} onReview={p => {
        setProfile({ district: p.district || '', block: p.block || '', education: p.education || '',
          interests: (p.interests || []).join(', '), skills: (p.traditional_or_existing_skills || []).join(', '),
          mobility: p.mobility == null ? '' : String(p.mobility), work: p.self_employment_or_wage_preference || '',
          current_work: p.current_work || '', access_needs: p.access_needs || '' });
        setReview(true);
      }} />}
      {step === 2 && review && <form onSubmit={e => { e.preventDefault(); void match(); }}><div className="eyebrow">YOUR PROFILE</div><h2>{hi ? 'अपनी जानकारी जाँचें' : 'Tell us what matters to you.'}</h2><p>{hi ? 'सुझाव पाने से पहले जानकारी की पुष्टि करें।' : 'Confirm these details to find your top three pathways. Separate multiple interests or skills with commas.'}</p><fieldset disabled={busy} className={styles.fields}>
        {field('district', hi ? 'जिला' : 'District')}{field('block', hi ? 'ब्लॉक' : 'Block')}
        <label>{hi ? 'पढ़ाई' : 'Education'}<select required value={profile.education} onChange={e => setProfile(p => ({ ...p, education: e.target.value }))}><option value="">{hi ? 'चुनें' : 'Choose education'}</option>{['No formal education', 'Class 5', 'Class 8', 'Class 10', 'Class 12', 'Graduate', 'Post Graduate'].map(x => <option key={x}>{x}</option>)}</select></label>
        {field('interests', hi ? 'रुचि' : 'Interests — e.g. farming, tailoring')}{field('skills', hi ? 'मौजूदा कौशल (वैकल्पिक)' : 'Existing skills (optional)', false)}{field('current_work', hi ? 'वर्तमान काम (वैकल्पिक)' : 'Current work (optional)', false)}{field('mobility', hi ? 'यात्रा की सीमा (किमी)' : 'Travel radius (km)', true, 'number')}
        <label>{hi ? 'काम की पसंद' : 'Work preference'}<select required value={profile.work} onChange={e => setProfile(p => ({ ...p, work: e.target.value }))}><option value="">{hi ? 'चुनें' : 'Choose preference'}</option><option value="both">{hi ? 'दोनों' : 'Open to both'}</option><option value="wage">{hi ? 'नौकरी' : 'Wage employment'}</option><option value="self_employment">{hi ? 'स्वरोजगार' : 'Self-employment'}</option></select></label>{field('access_needs', hi ? 'पहुँच संबंधी ज़रूरतें (वैकल्पिक)' : 'Accessibility needs (optional)', false)}
      </fieldset><button className="primary-button" disabled={busy} type="submit">{busy ? (hi ? 'विकल्प खोज रहे हैं…' : 'Finding your matches…') : (hi ? 'पुष्टि करें और विकल्प खोजें' : 'Confirm and find matches')}</button></form>}
      {step === 3 && <section><div className="eyebrow">YOUR NEXT CHAPTER</div><h2>{selected ? selected.qualification.title : hi ? 'आपके लिए विकल्प' : 'Your recommended pathways'}</h2><button className={styles.link} disabled={busy} onClick={() => selected ? setSelected(null) : setStep(2)}>{selected ? (hi ? 'सभी विकल्प' : 'Back to matches') : (hi ? 'जानकारी बदलें' : 'Edit my profile')}</button>
        {!recommendations.length && <p role="status">{hi ? 'अभी कोई उपयुक्त विकल्प नहीं मिला। अपनी जानकारी बदलें या सलाहकार की मदद लें।' : 'No pathways match these constraints yet. Edit your profile or request help from a counselor.'}</p>}
        {(selected ? [selected] : recommendations).map((rec, i) => <article key={rec.recommendation_id} className={styles.result}><div className={styles.meta}><span>{selected ? rec.qualification.sector : `0${i + 1} · ${rec.qualification.sector}`}</span><span>{rec.local_availability.status === 'verified_open' ? (hi ? 'स्थानीय बैच सत्यापित' : 'Local batch verified') : (hi ? 'स्थानीय बैच की पुष्टि बाकी' : 'Local batch pending verification')}</span></div>{!selected && <h3>{rec.qualification.title}</h3>}<p>NSQF {rec.qualification.nsqf_level} · {rec.qualification.duration_hours} {hi ? 'घंटे' : 'hours'} · {rec.qualification.nqr_code}</p><ul>{rec.why_recommended.map(reason => <li key={reason}>{reason}</li>)}</ul>{selected && <><p>{hi ? 'सीखने वाले कौशल: ' : 'Skills to develop: '}{rec.skill_gaps.join(', ') || '—'}</p>{rec.local_availability.centre_name && <p>{rec.local_availability.centre_name} · {rec.local_availability.district}</p>}<p>{rec.caveat}</p>{rec.qualification.official_url?.startsWith('https://') && <a href={rec.qualification.official_url} target="_blank" rel="noreferrer">{hi ? 'आधिकारिक योग्यता देखें' : 'View official qualification'} ↗</a>}</>}{!selected && <button className={styles.link} onClick={() => { setSelected(rec); setReferralId(''); setReferralConsent(false); }}>{hi ? 'विवरण देखें' : 'Explore this pathway'} →</button>}</article>)}
        <div className={styles.help}><h3>{hi ? 'अगले कदम में सहायता चाहिए?' : 'Need help with the next step?'}</h3>{referralId ? <p role="status">{hi ? 'अनुरोध भेज दिया गया: ' : 'Counselor request received: '}{referralId}</p> : <><label className={styles.check}><input type="checkbox" checked={referralConsent} onChange={e => setReferralConsent(e.target.checked)} />{hi ? 'मैं अपनी जानकारी सलाहकार के साथ साझा करने की सहमति देता/देती हूँ।' : 'I agree to share my profile with a counselor.'}</label><button className="primary-button" disabled={!referralConsent || busy} onClick={() => perform(async () => { await api.recordConsent('counselor_referral', true, language); const r = await api.createReferral(interviewId, 'user_requested_human_help', selected?.recommendation_id); setReferralId(r.referral_id); })}>{busy ? '…' : hi ? 'सहायता का अनुरोध करें' : 'Request counselor help'}</button></>}</div>
      </section>}
    </div>
  </div>;
}
