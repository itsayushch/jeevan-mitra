"use client";
import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { trainingApi, learningApi } from '../../../../lib/api/training';
import { Bookmark, ChevronLeft, CheckCircle, Volume2, ShieldAlert, ListChecks, FileText } from 'lucide-react';

export default function LessonPage(props: { params: Promise<{ lessonId: string }> }) {
  const params = use(props.params);
  const router = useRouter();
  const [lesson, setLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [completed, setCompleted] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [resources, setResources] = useState<any[]>([]);

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const l = await trainingApi.getLesson(params.lessonId);
        setLesson(l);
        
        // Use the authenticated API to record access and fetch progress
        if (l.course_id) {
          try {
            await learningApi.recordLessonAccess(l.id);
            const courseProg = await learningApi.getCourseProgress(l.course_id);
            
            // Set initial state from backend
            const lessonProg = courseProg.lessons_progress.find((p: any) => p.lesson_id === l.id);
            setCompleted(lessonProg?.status === 'COMPLETED');
            setBookmarked(courseProg.bookmarked_lesson_ids.includes(l.id));
          } catch (e) {
            console.error("Auth required or failed", e);
          }
        }
        
        setResources([
          { id: '1', title: 'Lesson Worksheet', type: 'PDF' },
          { id: '2', title: 'Video Demonstration', type: 'Link' }
        ]);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.lessonId]);

  const toggleComplete = async () => {
    if (saving) return;
    setSaving(true);
    const newState = !completed;
    try {
      await learningApi.updateLessonProgress(params.lessonId, newState);
      setCompleted(newState);
    } catch (e) {
      alert("Failed to update progress. Please login again.");
    } finally {
      setSaving(false);
    }
  };

  const toggleBookmark = async () => {
    const newState = !bookmarked;
    setBookmarked(newState);
    try {
      await learningApi.toggleBookmark(params.lessonId, newState);
    } catch (e) {
      setBookmarked(!newState); // revert
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Loading lesson...</div>;
  if (!lesson) return <div className="p-8 text-center text-rose-500 font-medium">Lesson not found.</div>;

  return (
    <div className="module-content pb-20">
      <div className="flex items-center justify-between mb-4">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-slate-500 hover:text-slate-800 text-xs font-bold">
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        <button 
          onClick={toggleBookmark}
          className={`p-2 rounded-full border ${bookmarked ? 'bg-amber-100 border-amber-300 text-amber-700' : 'bg-white border-slate-200 text-slate-400'}`}
        >
          <Bookmark className="w-4 h-4" />
        </button>
      </div>

      <h1 className="text-xl font-black text-slate-900 leading-tight mb-2">{lesson.title}</h1>
      
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 mb-6">
        <div className="flex items-start gap-3">
          <Volume2 className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-xs font-black text-emerald-900 mb-1">Simple Explanation</h3>
            <p className="text-xs text-emerald-800 leading-relaxed">{lesson.plain_language_summary}</p>
          </div>
        </div>
      </div>

      <div className="prose prose-sm max-w-none text-slate-700 mb-8 bg-white p-5 rounded-2xl border border-slate-200">
        <p>{lesson.content_markdown}</p>
      </div>

      {lesson.key_points && lesson.key_points.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-emerald-600" /> Key Points
          </h3>
          <ul className="space-y-2">
            {lesson.key_points.map((pt: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <span className="text-emerald-500 font-bold">•</span>
                <span>{pt}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {lesson.practical_steps && lesson.practical_steps.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-2 mb-3">
            <ListChecks className="w-4 h-4 text-blue-600" /> Practical Steps
          </h3>
          <div className="space-y-2">
            {lesson.practical_steps.map((step: string, i: number) => (
              <div key={i} className="flex items-start gap-3 text-xs text-slate-700 bg-blue-50 p-3 rounded-xl border border-blue-100">
                <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0">
                  {i + 1}
                </div>
                <span className="mt-0.5">{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {lesson.safety_notes && lesson.safety_notes.length > 0 && (
        <div className="mb-8">
          <h3 className="text-sm font-black text-rose-900 flex items-center gap-2 mb-3">
            <ShieldAlert className="w-4 h-4 text-rose-600" /> Do Not Do This
          </h3>
          <ul className="space-y-2" aria-label="Safety warnings">
            {lesson.safety_notes.map((note: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-xs text-rose-700 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
                <span className="text-rose-500 font-bold" aria-hidden="true">×</span>
                <span>{note}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {resources.length > 0 && (
        <div className="mb-8" aria-label="Lesson resources">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-emerald-600" /> Additional Resources
          </h3>
          <ul className="space-y-2">
            {resources.map((res: any, i: number) => (
              <li key={i} className="flex items-center justify-between text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-500 font-bold" aria-hidden="true">↓</span>
                  <span className="font-medium">{res.title}</span>
                </div>
                <span className="text-[10px] bg-white border border-slate-200 px-2 py-0.5 rounded text-slate-500">{res.type}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-slate-200 shadow-[0_-4px_10px_rgba(0,0,0,0.05)] md:max-w-md md:mx-auto md:left-auto md:right-auto w-full z-10 flex justify-center">
        <button 
          onClick={toggleComplete}
          className={`flex-1 flex items-center justify-center gap-2 text-sm font-bold py-3.5 rounded-xl transition-all ${
            completed 
              ? 'bg-slate-100 text-emerald-700 border-2 border-emerald-500' 
              : 'bg-emerald-700 text-white hover:bg-emerald-800'
          }`}
        >
          {completed ? (
            <>
              <CheckCircle className="w-5 h-5" /> Completed
            </>
          ) : (
            'Mark as Complete'
          )}
        </button>
      </div>
    </div>
  );
}
