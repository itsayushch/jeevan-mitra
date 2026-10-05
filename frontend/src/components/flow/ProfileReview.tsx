import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, ClipboardCheck, Keyboard, LoaderCircle, Mic, Pencil, X } from 'lucide-react';
import { api } from '../../lib/api';
import { displayAnswer, missingProfileFields, PROFILE_FIELDS, type Profile } from '../../lib/interview';
import { useVoiceInput } from '../../hooks/useVoiceInput';
import type { Language } from '../../types';

const EDUCATION = ['No formal education', ...Array.from({ length: 12 }, (_, index) => `Class ${index + 1}`), 'ITI / Diploma', 'Graduate', 'Post Graduate'];
type Props = { profile: Profile; language: Language; interviewId: string; busy: boolean; onChange: (profile: Profile) => void; onConfirm: () => void };

export function ProfileReview({ profile, language, interviewId, busy, onChange, onConfirm }: Props) {
  const hi = language === 'hi';
  const [editing, setEditing] = useState<keyof Profile | null>(null);
  const [draft, setDraft] = useState('');
  const [voiceDraft, setVoiceDraft] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [changed, setChanged] = useState<keyof Profile | null>(null);
  const [approved, setApproved] = useState(false);
  const editor = useRef<HTMLInputElement | HTMLSelectElement | null>(null);
  const editingRef = useRef(editing); editingRef.current = editing;
  const pending = useRef(false);
  const mounted = useRef(true);
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  const voice = useVoiceInput(language, text => { setDraft(text); setVoiceDraft(true); }, interviewId);
  const missing = missingProfileFields(profile);
  const field = PROFILE_FIELDS.find(item => item.key === editing);

  function edit(key: keyof Profile, withVoice = false) {
    voice.stop(); voice.clearError(); setError(''); setEditing(key); setVoiceDraft(false);
    const value = profile[key]; setDraft(Array.isArray(value) ? value.join(', ') : value == null ? '' : String(value));
    if (withVoice) { setVoiceDraft(true); voice.start(); }
  }
  useEffect(() => { if (editing && !voiceDraft) editor.current?.focus(); }, [editing]);
  function close() { voice.stop(); setEditing(null); setError(''); }
  async function save() {
    if (!editing || pending.current) return;
    const key = editing; let value: Profile[keyof Profile];
    pending.current = true; setSaving(true); setError(''); voice.stop();
    try {
      if (voiceDraft) {
        if (!draft.trim()) throw new Error(hi ? 'पहले अपना नया उत्तर बोलें या टाइप करें।' : 'Speak or type your new answer first.');
        const correction = await api.correctInterviewAnswer(interviewId, key, draft.trim());
        value = correction.value as Profile[keyof Profile];
      } else if (key === 'mobility') {
        value = Number(draft);
        if (!draft.trim() || !Number.isFinite(value) || value < 0 || value > 500) throw new Error(hi ? '0 से 500 किमी के बीच की दूरी लिखें। यात्रा नहीं कर सकते तो 0 लिखें।' : 'Enter 0 to 500 km. Use 0 if you cannot travel.');
      } else if (key === 'interests' || key === 'traditional_or_existing_skills') {
        value = draft.split(',').map(item => item.trim()).filter(Boolean);
        if (key === 'interests' && !value.length) throw new Error(hi ? 'कम से कम एक रुचि लिखें।' : 'Add at least one interest.');
        if (value.length > 10) throw new Error(hi ? 'अधिकतम 10 विकल्प लिखें।' : 'Use up to 10 interests or skills.');
      } else {
        value = draft.trim();
        if (!field?.optional && !value) throw new Error(hi ? 'इस सवाल का उत्तर लिखें।' : 'Please answer this question.');
      }
      if (!mounted.current) return;
      onChange({ ...profile, [key]: value }); setApproved(false); setChanged(key); close();
    } catch (err) { if (mounted.current) setError(err instanceof Error ? err.message : 'Please try again.'); }
    finally { pending.current = false; if (mounted.current) setSaving(false); }
  }
  return <section className="profile-review">
    <header className="interview-heading"><div><span className="eyebrow">{hi ? 'आपके शब्द, आपकी पसंद' : 'YOUR WORDS. YOUR CHOICES.'}</span><h2>{hi ? 'क्या हमने सही समझा?' : 'Did we get that right?'}</h2><p>{hi ? 'हर उत्तर जाँचें। बदलने के लिए पेंसिल या माइक दबाएँ।' : 'Here’s what you shared. Edit any answer, or tap its mic to change it by voice.'}</p></div><span className="review-symbol"><ClipboardCheck size={26}/></span></header>
    <div className="review-note"><Check size={18}/><span>{hi ? 'आपकी पुष्टि के बाद ही प्रशिक्षण और पाठ्यक्रम के सुझाव बनाए जाएँगे।' : 'Your training and course recommendations begin after you confirm these answers.'}</span></div>
    <div className="answer-grid">{PROFILE_FIELDS.map(item => {
      const answer = displayAnswer(profile, item.key, hi);
      return <article className={`answer-card ${changed === item.key ? 'updated' : ''} ${!item.optional && !answer ? 'needs-answer' : ''}`} key={item.key}>
        <div className="answer-card-label"><span>{hi ? item.hi : item.en}{item.optional && <small>{hi ? 'वैकल्पिक' : 'optional'}</small>}</span><div><button className="icon-button" disabled={busy || saving} onClick={() => edit(item.key)} aria-label={`${hi ? 'बदलें' : 'Edit'} ${hi ? item.hi : item.en}`}><Pencil size={16}/></button><button className="icon-button" disabled={busy || saving || !voice.supported} onClick={() => edit(item.key, true)} aria-label={`${hi ? 'आवाज़ से बदलें' : 'Change by voice:'} ${hi ? item.hi : item.en}`}><Mic size={16}/></button></div></div>
        <p>{answer || (item.optional ? (hi ? 'नहीं बताया गया' : 'Not shared') : (hi ? 'उत्तर जोड़ें' : 'Add your answer'))}</p>{changed === item.key && <span className="answer-updated"><Check size={13}/>{hi ? 'बदल दिया गया' : 'Updated'}</span>}
        {editing === item.key && <form className="answer-editor" onSubmit={event => { event.preventDefault(); void save(); }}>
          <label htmlFor={`edit-${item.key}`}>{voiceDraft ? (hi ? 'अपना नया उत्तर बोलें या टाइप करें' : 'Speak or type your new answer') : (hi ? 'आपका उत्तर' : 'Your answer')}</label>
          {!voiceDraft && item.key === 'education' ? <select id={`edit-${item.key}`} ref={element => { editor.current = element; }} value={draft} onChange={event => setDraft(event.target.value)} disabled={saving}><option value="">{hi ? 'शिक्षा चुनें' : 'Choose education'}</option>{EDUCATION.map(value => <option key={value}>{value}</option>)}</select> : !voiceDraft && item.key === 'self_employment_or_wage_preference' ? <select id={`edit-${item.key}`} ref={element => { editor.current = element; }} value={draft} onChange={event => setDraft(event.target.value)} disabled={saving}><option value="">{hi ? 'पसंद चुनें' : 'Choose preference'}</option><option value="wage">{hi ? 'नौकरी' : 'A job'}</option><option value="self_employment">{hi ? 'स्वरोजगार' : 'Self-employment'}</option><option value="both">{hi ? 'दोनों' : 'Open to both'}</option></select> : <input id={`edit-${item.key}`} ref={element => { editor.current = element; }} type={!voiceDraft && item.key === 'mobility' ? 'number' : 'text'} step="any" min={0} max={500} value={voice.listening ? voice.transcript || draft : draft} onFocus={() => voice.stop()} onChange={event => setDraft(event.target.value)} maxLength={400} disabled={saving}/>}
          {(item.key === 'interests' || item.key === 'traditional_or_existing_skills') && <small>{hi ? 'कई उत्तरों को कॉमा से अलग करें।' : 'Separate multiple answers with commas.'}</small>}
          {(error || voice.error) && <p className="inline-error" role="alert">{error || voice.error}</p>}
          {(voice.listening || voice.transcribing) && <p className="editor-listening" role="status">{voice.transcribing ? (hi ? 'उत्तर समझ रहे हैं…' : 'Transcribing your answer…') : (hi ? 'सुन रहे हैं…' : 'Listening…')}</p>}
          <div className="editor-actions"><button type="button" className="icon-button" disabled={saving || !voice.supported} aria-label={hi ? 'नया उत्तर बोलें' : 'Speak a new answer'} onClick={() => { setVoiceDraft(true); voice.start(); }}><Mic size={17}/></button><button type="button" className="icon-button" disabled={saving} aria-label={hi ? 'टाइप करें' : 'Use typing'} onClick={() => { voice.stop(); setVoiceDraft(false); }}><Keyboard size={17}/></button><button type="button" className="text-button" onClick={close} disabled={saving}><X size={15}/>{hi ? 'रद्द करें' : 'Cancel'}</button><button type="submit" className="primary-button" disabled={saving || voice.listening || voice.transcribing}>{saving ? <LoaderCircle className="spin" size={16}/> : <Check size={16}/>} {hi ? 'उत्तर रखें' : 'Save answer'}</button></div>
        </form>}
      </article>;
    })}</div>
    {missing.length > 0 && <p className="review-missing" role="status">{hi ? 'जारी रखने के लिए उत्तर जोड़ें: ' : 'Before continuing, add: '}{missing.map(item => hi ? item.hi : item.en).join(', ')}.</p>}
    <div className="review-confirm"><label className="confirm-check"><input type="checkbox" checked={approved} disabled={busy || saving || !!editing || missing.length > 0} onChange={event => setApproved(event.target.checked)}/><span>{hi ? 'मैंने अपने उत्तर जाँच लिए हैं और पुष्टि करता/करती हूँ।' : 'I’ve reviewed my answers and confirm they are correct.'}</span></label><button className="primary-button" disabled={!approved || missing.length > 0 || busy || saving || !!editing} onClick={() => { voice.stop(); onConfirm(); }}>{busy ? <LoaderCircle className="spin" size={18}/> : <ArrowRight size={18}/>} {busy ? (hi ? 'आपके विकल्प खोज रहे हैं…' : 'Finding your pathways…') : (hi ? 'पुष्टि करें और पाठ्यक्रम खोजें' : 'Confirm & find my courses')}</button></div>
  </section>;
}
