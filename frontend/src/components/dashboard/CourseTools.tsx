"use client";
import { useEffect, useRef, useState } from 'react';
import QRCode from 'qrcode';
import { Check, LogOut, Pause, Play, Printer, QrCode, RotateCcw, Square, Volume2, X } from 'lucide-react';
import type { SupportedLocale } from '../../lib/i18n/locales';
import { api, type RecommendationItem } from '../../lib/api';
import { courseName, courseShareUrl, REGISTER_URL } from '../../lib/courseShare';
import { pauseSpeaking, resumeSpeaking, speakText, stopSpeaking } from '../../utils/speech';
import styles from './course-tools.module.css';

export function CourseTools({ courses, language, disabled = false }: { courses: RecommendationItem[]; language: SupportedLocale; disabled?: boolean }) {
  const hi = language === 'hi';
  const [audio, setAudio] = useState<'off' | 'playing' | 'paused'>('off');
  const narration = useRef(0);
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const [qr, setQr] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [error, setError] = useState('');
  const [exiting, setExiting] = useState(false);

  function stop() { narration.current++; stopSpeaking(); setAudio('off'); }
  useEffect(() => {
    stop();
    return () => { narration.current++; stopSpeaking(); };
  }, [courses, language, disabled]); // Cancel stale narration when answers or the language change.
  useEffect(() => {
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted && !api.getSessionToken()) window.location.reload();
    };
    window.addEventListener('pageshow', onPageShow);
    return () => window.removeEventListener('pageshow', onPageShow);
  }, []);
  useEffect(() => {
    if (open) dialog.current?.showModal(); else dialog.current?.close();
  }, [open]);
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setQr(''); setShareUrl(''); setError('');
    try {
      const url = courseShareUrl(process.env.NEXT_PUBLIC_APP_URL || window.location.origin, courses, language);
      setShareUrl(url);
      void QRCode.toDataURL(url, { width: 280, margin: 4, errorCorrectionLevel: 'M' })
        .then(data => { if (!cancelled) setQr(data); })
        .catch(() => { if (!cancelled) setError(hi ? 'QR नहीं बना। फिर कोशिश करें।' : 'Could not make the QR code. Please try again.'); });
    } catch { setError(hi ? 'कोर्स का लिंक नहीं मिला।' : 'Course link unavailable.'); }
    return () => { cancelled = true; };
  }, [open, courses, language, hi]);

  function listen() {
    stop();
    const generation = narration.current;
    setAudio('playing');
    const sections = courses.map((course, index) => {
      const title = courseName(course.qualification.title, hi);
      const hours = course.qualification.duration_hours;
      return hi
        ? `कोर्स ${index + 1}। ${title}। कुल समय ${hours} घंटे। यह आपके उत्तरों के आधार पर चुना गया है। पास में बैच है या नहीं, पहले पूछें। अधिक जानकारी के लिए मदद माँगें दबाएँ। नाम लिखवाने के लिए नाम लिखवाएँ दबाएँ।`
        : `Course ${index + 1}. ${title}. Total time ${hours} hours. This course was chosen using your answers. Ask if a nearby batch is available. Tap Ask for help for more information, or Register to visit the joining portal.`;
    });
    const read = (index: number) => {
      if (generation !== narration.current) return;
      if (index >= sections.length) { setAudio('off'); return; }
      speakText(sections[index], language, () => read(index + 1));
    };
    read(0);
  }
  function finish() {
    setExiting(true); stop();
    api.clearKioskSession();
    window.location.replace('/');
  }

  return <>
    <div className={styles.tools} aria-label={hi ? 'कोर्स के विकल्प' : 'Course tools'}>
      <div className={styles.listen}>
        {audio === 'off' ? <button disabled={!courses.length || disabled} onClick={listen}><Volume2 size={22}/>{hi ? 'मेरे कोर्स सुनाएँ' : 'Listen to my courses'}</button> : <>
          <button onClick={() => { if (audio === 'paused') { resumeSpeaking(); setAudio('playing'); } else { pauseSpeaking(); setAudio('paused'); } }}>
            {audio === 'paused' ? <Play size={22}/> : <Pause size={22}/>}{audio === 'paused' ? (hi ? 'आगे सुनें' : 'Continue listening') : (hi ? 'रोकें' : 'Pause')}
          </button>
          <button onClick={listen}><RotateCcw size={19}/>{hi ? 'फिर सुनें' : 'Repeat'}</button>
          <button onClick={stop}><Square size={18}/>{hi ? 'बंद करें' : 'Stop'}</button>
        </>}
      </div>
      <button disabled={!courses.length || disabled} onClick={() => { stop(); setOpen(true); }}><QrCode size={22}/>{hi ? 'कोर्स घर ले जाएँ' : 'Take courses home'}</button>
      <button className={styles.finish} disabled={disabled || exiting} onClick={finish}><LogOut size={21}/>{hi ? 'समाप्त करें और बाहर जाएँ' : 'Finish & exit'}</button>
    </div>
    {audio !== 'off' && <p className={styles.audioStatus} role="status">{audio === 'paused' ? (hi ? 'सुनाना रुका है। आगे सुनें दबाएँ।' : 'Paused. Tap Continue listening when ready.') : (hi ? 'आपके कोर्स सुना रहे हैं…' : 'Reading your courses aloud…')}</p>}
    <dialog ref={dialog} className={styles.dialog} aria-labelledby="take-home-title" onCancel={event => { event.preventDefault(); setOpen(false); }} onClick={event => { if (event.target === event.currentTarget) setOpen(false); }}>
      <div className={styles.modal}>
        <button className={styles.close} aria-label={hi ? 'बंद करें' : 'Close take-home options'} onClick={() => setOpen(false)}><X size={23}/></button>
        <span className={styles.icon}><QrCode size={30}/></span>
        <h2 id="take-home-title">{hi ? 'अपने कोर्स घर ले जाएँ' : 'Keep your courses with you'}</h2>
        <p>{hi ? 'फोन के कैमरे से QR स्कैन करें। सभी कोर्स फोन पर खुल जाएँगे।' : 'Scan this QR with your phone camera. All your courses will open on your phone.'}</p>
        {qr ? <img className={styles.qr} src={qr} alt={hi ? 'सभी कोर्स खोलने का QR कोड' : 'QR code to open all your courses'} width={280} height={280}/> : <p role="status">{error || (hi ? 'QR बना रहे हैं…' : 'Making your QR code…')}</p>}
        {shareUrl && <a className={styles.link} href={shareUrl} target="_blank" rel="noreferrer">{hi ? 'कोर्स का लिंक खोलें' : 'Open course link'} ↗</a>}
        <p className={styles.note}><Check size={16}/>{hi ? 'इस लिंक में केवल कोर्स हैं। आपके निजी उत्तर नहीं हैं।' : 'This link contains courses only. Your personal answers are private.'}</p>
        <button className={styles.print} disabled={!qr} onClick={() => window.print()}><Printer size={20}/>{hi ? 'कोर्स की पर्ची छापें' : 'Print my courses'}</button>
        <small>{hi ? 'प्रिंटर जुड़ा हो तो पर्ची छाप सकते हैं।' : 'Print a copy if a printer is connected.'}</small>
      </div>
    </dialog>
    <section className={styles.printSummary} aria-hidden="true">
      <h1>JeevanMitra — {hi ? 'आपके कोर्स' : 'Your courses'}</h1>
      {courses.map((course, index) => <article key={course.recommendation_id}><h2>{index + 1}. {courseName(course.qualification.title, hi)}</h2><p>{course.qualification.title}</p><p>{course.qualification.duration_hours} {hi ? 'घंटे' : 'hours'}</p><p>{hi ? 'बैच और पात्रता केंद्र से जाँचें।' : 'Check batch availability and entry requirements with the training centre.'}</p><p>{course.qualification.official_url}</p></article>)}
      <p>{hi ? 'नाम लिखवाने का पोर्टल' : 'Registration portal'}: {REGISTER_URL}</p>
      {qr && <img src={qr} alt="Course QR" width={150} height={150}/>}
      <p>{shareUrl}</p>
    </section>
  </>;
}
