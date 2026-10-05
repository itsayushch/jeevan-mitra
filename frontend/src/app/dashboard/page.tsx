"use client";
import { Suspense, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, BookOpen, Check, Clock3, GraduationCap, HeartHandshake, Leaf, LoaderCircle, MapPin, MessageCircle, Pencil, Sparkles, Sprout, X } from 'lucide-react';
import { useAppSettings } from '../../components/AppShell';
import { ProfileReview } from '../../components/flow/ProfileReview';
import { api, type RecommendationItem } from '../../lib/api';
import { EMPTY_PROFILE, profileFromFields, type Profile } from '../../lib/interview';
import styles from './dashboard.module.css';
import { courseName } from '../../lib/courseShare';
import { CourseTools } from '../../components/dashboard/CourseTools';

function simpleReason(reason: string, hi: boolean, verified: boolean) {
  const text = reason.toLowerCase();
  if (/interest/.test(text)) return hi ? 'यह आपकी पसंद के काम से जुड़ा है।' : 'This course matches the work you like.';
  if (/not.*verified|verification pending/.test(text)) return hi ? 'पास में बैच है या नहीं, पहले पूछें।' : 'Ask a helper to check for a nearby batch.';
  if (!verified && /mobility|travel|within.*km|district|local|active batch/.test(text)) return hi ? 'पास में बैच है या नहीं, पहले पूछें।' : 'Ask a helper to check for a nearby batch.';
  if (/mobility|travel|within.*km/.test(text)) return hi ? 'यह आपकी बताई यात्रा की दूरी में आता है।' : 'This fits the distance you can travel.';
  if (/education/.test(text)) return hi ? 'आपकी पढ़ाई इस कोर्स के लिए पर्याप्त है।' : 'You have the schooling needed for this course.';
  if (/district|local|active batch/.test(text)) return hi ? 'यह आपके जिले में मिल सकता है।' : 'This may be available in your district.';
  if (/preference|livelihood/.test(text)) return hi ? 'यह आपके चुने हुए काम से जुड़ा है।' : 'This fits the type of work you chose.';
  return hi ? 'यह आपके बताए उत्तरों के आधार पर चुना गया है।' : 'This was chosen using your answers.';
}

function Dashboard() {
  const { language } = useAppSettings();
  const hi = language === 'hi';
  const interviewId = useSearchParams().get('interview') || '';
  const [profile, setProfile] = useState<Profile>(EMPTY_PROFILE);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const [helpOpen, setHelpOpen] = useState(false);
  const [helpCourse, setHelpCourse] = useState<RecommendationItem | null>(null);
  const helpDialog = useRef<HTMLDialogElement>(null);
  const [helpConsent, setHelpConsent] = useState(false);
  const [helpError, setHelpError] = useState('');
  const [helpRequests, setHelpRequests] = useState<Record<string, string>>({});
  const helpPending = useRef(false);
  const [whatsappNotice, setWhatsappNotice] = useState(0);
  useEffect(() => {
    if (!whatsappNotice) return;
    const timeout = window.setTimeout(() => setWhatsappNotice(0), 10000);
    return () => window.clearTimeout(timeout);
  }, [whatsappNotice]);
  useEffect(() => {
    let cancelled = false;
    if (!interviewId) { setLoading(false); return; }
    setLoading(true); setError('');
    try { setHelpRequests(JSON.parse(sessionStorage.getItem(`jeevanmitra:help:${interviewId}`) || '{}')); }
    catch { setHelpRequests({}); }
    void api.getDashboard(interviewId).then(result => {
      if (cancelled) return;
      if (result.interview.status !== 'recommendations_generated') {
        throw new Error(hi ? 'विकल्प पाने से पहले अपने उत्तरों की पुष्टि करें।' : 'Confirm your answers before opening your options.');
      }
      setProfile(profileFromFields(result.interview.fields));
      setRecommendations(result.recommendations);
    }).catch(err => { if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load your dashboard.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [interviewId, retry, hi]);

  async function updateMatches() {
    if (busy) return;
    setBusy(true); setError('');
    try {
      await api.confirmProfile(interviewId, { ...profile, language });
      const result = await api.generateRecommendations(interviewId);
      setRecommendations(result.recommendations); setEditing(false); setExpanded(null);
    } catch (err) { setError(err instanceof Error ? err.message : 'Please try again.'); }
    finally { setBusy(false); }
  }

  async function refreshCourses() {
    if (busy) return;
    setBusy(true); setError('');
    try {
      const result = await api.generateRecommendations(interviewId);
      setRecommendations(result.recommendations);
    } catch (err) { setError(err instanceof Error ? err.message : 'Could not refresh courses.'); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    const dialog = helpDialog.current;
    if (helpOpen) dialog?.showModal();
    else dialog?.close();
  }, [helpOpen]);

  function openHelp(course: RecommendationItem | null) {
    setHelpCourse(course); setHelpConsent(false); setHelpError(''); setHelpOpen(true);
  }
  async function requestHelp() {
    if (!helpConsent || helpPending.current) return;
    helpPending.current = true; setBusy(true); setHelpError('');
    try {
      await api.recordConsent('counselor_referral', true, language);
      const result = await api.createReferral(interviewId, 'user_requested_human_help', helpCourse?.recommendation_id,
        helpCourse ? `Please help me with ${helpCourse.qualification.title}.` : 'Please help me choose a course.');
      setHelpRequests(current => {
        const updated = { ...current, [helpCourse?.qualification.id || 'general']: result.referral_id };
        try { sessionStorage.setItem(`jeevanmitra:help:${interviewId}`, JSON.stringify(updated)); } catch { /* Keep the sent state when browser storage is unavailable. */ }
        return updated;
      });
      setHelpOpen(false);
    } catch (err) { setHelpError(err instanceof Error ? err.message : (hi ? 'अनुरोध नहीं भेजा गया। फिर कोशिश करें।' : 'Request not sent. Please try again.')); }
    finally { helpPending.current = false; setBusy(false); }
  }
  if (!interviewId) return <section className={styles.empty}><Sprout size={42}/><h1>{hi ? 'आपका अगला कदम यहाँ शुरू होता है।' : 'Find a course for you'}</h1><p>{hi ? 'अपनी रुचियाँ बताएँ और अपने लिए विकल्प पाएँ।' : 'Answer a few questions. We will show you courses you can learn.'}</p><Link className="primary-button" href="/">{hi ? 'शुरू करें' : 'Get started'}<ArrowRight size={19}/></Link></section>;
  if (loading) return <section className={styles.empty} role="status"><LoaderCircle className="spin" size={35}/><p>{hi ? 'आपके कोर्स ला रहे हैं…' : 'Finding your courses…'}</p></section>;
  return <div className={styles.dashboard}>
    <header className={styles.header}><Link href="/" className={styles.brand}><span><Sprout size={27}/></span>JeevanMitra</Link><span className={styles.headerNote}><Check size={16}/>{hi ? 'नया काम सीखें' : 'Learn a new skill'}</span></header>
    {error && <div className="inline-error" role="alert">{error} <button className="text-button" onClick={() => setRetry(value => value + 1)}>{hi ? 'फिर कोशिश करें' : 'Try again'}</button></div>}
    {editing ? <div className={styles.review}><button className="text-button" disabled={busy} onClick={() => { setEditing(false); setRetry(value => value + 1); }}><ArrowLeft size={18}/>{hi ? 'मेरे कोर्स पर वापस जाएँ' : 'Back to my courses'}</button><ProfileReview profile={profile} language={language} interviewId={interviewId} busy={busy} onChange={setProfile} onConfirm={() => void updateMatches()}/></div> : <>
      <section className={styles.hero}><div><span className={styles.eyebrow}><Sparkles size={16}/>{hi ? 'आपके लिए कोर्स' : 'YOUR COURSES'}</span><h1>{hi ? 'आप क्या सीखना चाहते हैं?' : 'What would you like to learn?'}</h1><p>{hi ? 'आपके उत्तरों के आधार पर ये कोर्स चुने हैं। अधिक जानने के लिए कोर्स दबाएँ।' : 'These courses are based on your answers. Tap a course to know more.'}</p><div className={styles.profileTags}>{profile.district && <span><MapPin size={15}/>{profile.district}{profile.block ? ` · ${profile.block}` : ''}</span>}{profile.education && <span><GraduationCap size={15}/>{profile.education}</span>}{profile.mobility != null && <span>{profile.mobility} {hi ? 'किमी तक जा सकते हैं' : 'km you can travel'}</span>}</div><button className="text-button" onClick={() => setEditing(true)}><Pencil size={15}/>{hi ? 'मेरे उत्तर बदलें' : 'Change my answers'}</button></div><div className={styles.heroArt} aria-hidden="true"><div><Leaf size={57}/></div><span><Sparkles size={23}/></span><i/><small>{hi ? 'नया काम सीखें' : 'LEARN A NEW SKILL'}</small></div></section>
      <CourseTools courses={recommendations} language={language} disabled={busy}/>
      <section aria-labelledby="pathways-title"><div className={styles.sectionHeading}><div><span className={styles.eyebrow}>{hi ? 'एक कोर्स चुनें' : 'CHOOSE A COURSE'}</span><h2 id="pathways-title">{hi ? 'आपके लिए कोर्स' : 'Courses for you'}</h2></div><div className={styles.sectionActions}><span>{recommendations.length} {hi ? 'कोर्स' : 'courses'}</span><button className={styles.whatsapp} disabled={!recommendations.length || busy || !!error} onClick={() => setWhatsappNotice(current => current + 1)}><MessageCircle size={18}/>{hi ? 'सभी कोर्स WhatsApp पर भेजें' : 'Send all courses to WhatsApp'}</button></div></div>
        {!recommendations.length ? <div className={styles.noMatches}><BookOpen size={30}/><h3>{hi ? 'अभी कोई कोर्स नहीं मिला' : 'No course found yet'}</h3><p>{hi ? 'अपने उत्तर बदलें या मदद माँगें।' : 'Change your answers or ask a helper to find a course.'}</p><button className={styles.askHelp} disabled={busy || !!helpRequests.general} onClick={() => openHelp(null)}><HeartHandshake size={18}/>{helpRequests.general ? (hi ? "मदद का अनुरोध भेज दिया" : "Help requested") : (hi ? "मदद माँगें" : "Ask for help")}</button><button className="primary-button" disabled={busy} onClick={() => void refreshCourses()}>{hi ? "नए कोर्स देखें" : "Find current courses"}<ArrowRight size={18}/></button><button className="primary-button" onClick={() => setEditing(true)}>{hi ? 'उत्तर बदलें' : 'Change my answers'}<ArrowRight size={18}/></button></div> : <div className={styles.cards}>{recommendations.map((rec, index) => {
          const open = expanded === rec.recommendation_id;
          const verified = rec.local_availability.status === 'verified_open';
          return <article className={`${styles.card} ${styles[`tone${index % 3}`]}`} key={rec.recommendation_id}>
            <div className={styles.cardArtwork}><span>{index === 0 ? <Leaf size={38}/> : index === 1 ? <GraduationCap size={40}/> : <BookOpen size={39}/>}</span><small>{index === 0 ? (hi ? 'कोर्स 1' : 'Course 1') : (hi ? `कोर्स ${index + 1}` : `Course ${index + 1}`)}</small><i/></div>
            <div className={styles.cardBody}><h3>{courseName(rec.qualification.title, hi)}</h3><p className={styles.availability}>{hi ? "सरकारी NQR सूची का कोर्स" : "Listed in the official NQR"}</p><div className={styles.courseFacts}><span><Clock3 size={15}/>{hi ? 'कुल समय: ' : 'Total time: '}{rec.qualification.duration_hours} {hi ? 'घंटे' : 'hours'}</span></div>
              <p className={`${styles.availability} ${verified ? styles.verified : ''}`}><MapPin size={15}/>{verified ? (hi ? 'कोर्स का बैच जाँच लिया गया है' : 'Training batch checked') : (hi ? 'बैच है या नहीं, पहले पूछें' : 'Ask if a batch is available')}</p>
              {rec.local_availability.centre_name && <p className={styles.centre}><MapPin size={16}/><span>{rec.local_availability.centre_name}</span></p>}
              <div className={styles.reasons}><strong>{hi ? 'यह कोर्स क्यों?' : 'Why this course?'}</strong><ul>{[...new Set(rec.why_recommended.map(reason => simpleReason(reason, hi, verified)))].slice(0, 2).map(reason => <li key={reason}><Check size={14}/><span>{reason}</span></li>)}</ul></div>
              {open && <div className={styles.details} id={`details-${index}`}><p><strong>{hi ? 'कोर्स का पूरा नाम' : 'Full course name'}</strong><br/>{rec.qualification.title}</p><p><strong>{hi ? 'आप क्या सीखेंगे' : 'What you will learn'}</strong><br/>{(rec.qualification.skills || rec.skill_gaps).join(', ') || (hi ? 'इस कोर्स में क्या सिखाते हैं, मदद करने वाले से पूछें।' : 'Ask the helper about what this course teaches.')}</p>{rec.local_availability.centre_name && <p><strong>{rec.local_availability.centre_name}</strong><br/>{rec.local_availability.district}</p>}{rec.local_availability.batch_start_date && <p>{hi ? 'बैच शुरू: ' : 'Batch starts: '}{rec.local_availability.batch_start_date}</p>}<p>{hi ? 'कोर्स में जगह और नौकरी की गारंटी नहीं है। जुड़ने से पहले केंद्र से पूछें।' : 'A course place or job is not guaranteed. Check with the training centre before joining.'}</p><p><strong>{hi ? "कौन जुड़ सकता है" : "Who can join"}</strong><br/>{hi ? "पढ़ाई: " : "School entry: "}{rec.qualification.school_entry}<br/>{hi ? "मदद करने वाला आपकी पात्रता जाँच करेगा।" : "Less schooling? Ask a helper about the work experience entry routes."}</p><p><strong>{hi ? "प्रमाणपत्र देने वाला" : "Certificate from"}</strong><br/>{rec.qualification.certification_body}</p><p>{hi ? "NQR स्तर: " : "NQR level: "}{rec.qualification.nsqf_level}<br/>{hi ? "मान्य होने की अंतिम तारीख: " : "Valid until: "}{rec.qualification.valid_to}<br/>{hi ? "जानकारी जाँची: " : "Information checked: "}{rec.qualification.source_checked_at?.slice(0, 10)}</p>{rec.qualification.official_url?.startsWith('https://') && <a href={rec.qualification.official_url} target="_blank" rel="noreferrer">{hi ? 'कोर्स की पूरी जानकारी देखें' : 'See full course information'} ↗</a>}</div>}
              <div className={styles.cardActions}>
                <a className={styles.register} href="https://www.skillindiadigital.gov.in/home" aria-label={`${hi ? 'नाम लिखवाएँ' : 'Register'}: ${rec.qualification.title} — Skill India Digital Hub`}><ArrowRight size={19}/>{hi ? 'नाम लिखवाएँ' : 'Register'}</a>
                <button className={styles.askHelp} disabled={busy || !!helpRequests[rec.qualification.id]} onClick={() => openHelp(rec)}>{helpRequests[rec.qualification.id] ? <Check size={18}/> : <HeartHandshake size={18}/>} {helpRequests[rec.qualification.id] ? (hi ? 'मदद का अनुरोध भेज दिया' : 'Help requested') : (hi ? 'मदद माँगें' : 'Ask for help')}</button>
                <button className={styles.explore} aria-expanded={open} aria-controls={`details-${index}`} onClick={() => setExpanded(open ? null : rec.recommendation_id)}>{open ? (hi ? 'विवरण छिपाएँ' : 'Close details') : (hi ? 'और जानें' : 'Know more')}{open ? <X size={16}/> : <ArrowRight size={16}/>}</button>
              </div>

            </div></article>;
        })}</div>}
      </section>
      <footer className={styles.footer}><Sprout size={18}/>{hi ? 'एक छोटा कदम, एक बेहतर कल।' : 'Learn today. Build your future.'}</footer>
    </>}
    {whatsappNotice > 0 && <aside className={styles.notification} key={whatsappNotice} aria-label={hi ? 'सूचना' : 'Notification'}>
      <MessageCircle size={22} aria-hidden="true"/>
      <p role="status" aria-live="polite" aria-atomic="true">{hi ? 'WhatsApp से सभी कोर्स भेजने की सुविधा जल्द शुरू होगी। अभी कोर्स नहीं भेजे गए हैं।' : 'Sending all your courses to WhatsApp will be available soon. No courses have been sent yet.'}</p>
      <button type="button" aria-label={hi ? 'सूचना बंद करें' : 'Dismiss notification'} onClick={() => setWhatsappNotice(0)}><X size={19}/></button>
    </aside>}
    <dialog ref={helpDialog} className={styles.helpDialog} aria-labelledby="help-title" onCancel={event => {
      event.preventDefault(); if (!busy) setHelpOpen(false);
    }} onClick={event => { if (event.target === event.currentTarget && !busy) setHelpOpen(false); }}>
      <div className={styles.modalBody}>
        <button className={styles.closeModal} type="button" disabled={busy} aria-label={hi ? 'बंद करें' : 'Close help'} onClick={() => setHelpOpen(false)}><X size={22}/></button>
        <span className={styles.helpIcon}><HeartHandshake size={30}/></span>
        <h2 id="help-title">{hi ? 'मदद चाहिए?' : 'How can we help?'}</h2>
        {helpCourse && <p className={styles.selectedCourse}>{courseName(helpCourse.qualification.title, hi)}</p>}
        {helpRequests[helpCourse?.qualification.id || 'general'] ? <>
          <p className={styles.success} role="status"><Check size={20}/>{hi ? 'आपका मदद का अनुरोध भेज दिया गया है।' : 'Your help request has been sent.'}</p>
          <button className={styles.register} onClick={() => setHelpOpen(false)}>{hi ? 'ठीक है' : 'Done'}</button>
        </> : <form onSubmit={event => { event.preventDefault(); void requestHelp(); }}>
          <p>{hi ? 'मदद करने वाला व्यक्ति कोर्स, पास के बैच और जुड़ने का तरीका समझा सकता है।' : 'A helper can explain this course, check nearby batches and help you join.'}</p>
          <label className={styles.consent}><input type="checkbox" checked={helpConsent} disabled={busy} onChange={event => setHelpConsent(event.target.checked)}/>{hi ? 'मेरे उत्तर मदद करने वाले व्यक्ति को बता सकते हैं।' : 'You may share my answers with the person helping me.'}</label>
          {helpError && <p className="inline-error" role="alert">{helpError}</p>}
          <button className={styles.register} type="submit" disabled={busy || !helpConsent}>{busy ? <LoaderCircle size={18} className="spin"/> : <HeartHandshake size={18}/>} {busy ? (hi ? 'भेज रहे हैं…' : 'Sending…') : (hi ? 'मदद माँगें' : 'Send help request')}</button>
        </form>}
      </div>
    </dialog>
  </div>;
}
export default function Page() { return <Suspense fallback={<div role="status">Loading…</div>}><Dashboard/></Suspense>; }
