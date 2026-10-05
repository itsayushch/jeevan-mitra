"use client";
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowRight, BookOpen, Clock3, Printer, Sprout } from 'lucide-react';
import { courseName, REGISTER_URL, sharedCourseIds } from '../../lib/courseShare';
import styles from './take-home.module.css';

type PublicCourse = { id: string; title: string; duration_hours: number; official_source_url?: string; skills_acquired?: string[] };

function TakeHome() {
  const params = useSearchParams();
  const hi = params.get('lang') === 'hi';
  const requested = params.get('courses') || '';
  const [courses, setCourses] = useState<PublicCourse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    const ids = sharedCourseIds(requested);
    setLoading(true); setError(''); setMissing(false);
    if (!ids.length) { setCourses([]); setLoading(false); return; }
    // This public catalogue request needs no kiosk token or beneficiary data.
    void fetch('/api/v1/catalogue/qualifications', { signal: controller.signal, cache: 'no-store' })
      .then(async response => {
        if (!response.ok) throw new Error('Catalogue unavailable');
        const result = await response.json();
        const selected = ids.flatMap(id => {
          const course = (result.qualifications as PublicCourse[]).find(course => course.id === id);
          return course ? [course] : [];
        });
        setCourses(selected); setMissing(selected.length !== ids.length);
      })
      .catch(() => { if (!controller.signal.aborted) setError(hi ? 'कोर्स नहीं खुल पाए। फिर कोशिश करें।' : 'Could not load your courses. Please try again.'); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [requested, hi, retry]);
  return <div className={styles.page} lang={hi ? 'hi' : 'en'}>
    <header><Sprout size={29}/>JeevanMitra</header>
    <h1>{hi ? 'आपके कोर्स' : 'Your courses'}</h1>
    <p>{hi ? 'कोर्स की जानकारी देखें। जुड़ने के लिए नाम लिखवाएँ दबाएँ।' : 'Keep this page to see your courses. Tap Register when you are ready to join.'}</p>
    {!loading && !!courses.length && <button className={styles.print} onClick={() => window.print()}><Printer size={20}/>{hi ? 'पर्ची छापें' : 'Print courses'}</button>}
    {loading && <p role="status">{hi ? 'कोर्स ला रहे हैं…' : 'Loading your courses…'}</p>}
    {error && <p role="alert">{error} <button onClick={() => setRetry(value => value + 1)}>{hi ? 'फिर कोशिश करें' : 'Try again'}</button></p>}
    {missing && <p role="status">{hi ? 'कुछ कोर्स अब सूची में नहीं हैं। मदद करने वाले से पूछें।' : 'Some courses are no longer listed. Ask a helper for current options.'}</p>}
    {!loading && !error && !courses.length && <p>{hi ? 'इस लिंक में अभी कोई कोर्स नहीं है। कियोस्क से नया QR लें।' : 'No current courses found in this link. Get a new QR code from the kiosk.'}</p>}
    <div className={styles.cards}>{courses.map((course, index) => <article key={course.id}>
      <span className={styles.number}><BookOpen size={20}/>{hi ? 'कोर्स' : 'Course'} {index + 1}</span>
      <h2>{courseName(course.title, hi)}</h2>
      <p className={styles.fullName}>{course.title}</p>
      <p><Clock3 size={17}/>{course.duration_hours} {hi ? 'घंटे' : 'hours'}</p>
      <p>{hi ? 'बैच है या नहीं और कौन जुड़ सकता है, केंद्र से पूछें।' : 'Ask the centre about batches and who can join.'}</p>
      <a className={styles.register} href={REGISTER_URL}><ArrowRight size={20}/>{hi ? 'नाम लिखवाएँ' : 'Register'}</a>
      {course.official_source_url?.startsWith('https://') && <a className={styles.details} href={course.official_source_url} target="_blank" rel="noreferrer">{hi ? 'NQR पर पूरी जानकारी' : 'Full details on NQR'} ↗</a>}
    </article>)}</div>
    <footer>{hi ? 'कोर्स में जगह या नौकरी की गारंटी नहीं है।' : 'A course place or job is not guaranteed.'}<span className={styles.printUrl}>{REGISTER_URL}</span></footer>
  </div>;
}
export default function Page() { return <Suspense fallback={<p role="status">Loading courses…</p>}><TakeHome/></Suspense>; }
