"use client";
import { use, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { trainingApi, learningApi } from '../../../../lib/api/training';
import { BookOpen, ChevronLeft, Clock, PlayCircle } from 'lucide-react';
import Link from 'next/link';

export default function CoursePage(props: { params: Promise<{ courseId: string }> }) {
  const params = use(props.params);
  const router = useRouter();
  const [course, setCourse] = useState<any>(null);
  const [modules, setModules] = useState<any[]>([]);
  const [progress, setProgress] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [c, m, p] = await Promise.all([
          trainingApi.getCourse(params.courseId),
          trainingApi.getCourseModules(params.courseId),
          learningApi.getCourseProgress(params.courseId).catch(() => null)
        ]);
        setCourse(c);
        setModules(m);
        setProgress(p);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.courseId]);

  if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Loading course...</div>;
  if (!course) return <div className="p-8 text-center text-rose-500 font-medium">Course not found.</div>;

  const handleStartContinue = () => {
    if (progress?.resume_lesson_id) {
      router.push(`/skill-training/lesson/${progress.resume_lesson_id}`);
    } else {
      // Best effort fallback: let the user just click a lesson below
      alert("Please select a lesson below to start.");
    }
  };

  return (
    <div className="module-content">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-slate-500 hover:text-slate-800 text-xs font-bold mb-4">
        <ChevronLeft className="w-4 h-4" /> Back to courses
      </button>

      <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm mb-6">
        <div className="flex justify-between items-start mb-3">
          <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
            {course.sector}
          </span>
          {course.verification_status === 'Verified' && (
            <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
              ✓ Verified
            </span>
          )}
        </div>
        <h1 className="text-xl font-black text-slate-900 leading-tight mb-2">{course.title}</h1>
        <p className="text-sm text-slate-600 mb-4">{course.long_description}</p>
        
        <div className="flex flex-wrap gap-4 text-xs text-slate-500 font-medium bg-slate-50 p-3 rounded-xl mb-4">
          <div className="flex items-center gap-1"><Clock className="w-4 h-4 text-slate-400" /> {course.duration_hours} hrs</div>
          <div className="flex items-center gap-1"><BookOpen className="w-4 h-4 text-slate-400" /> {course.difficulty}</div>
          {course.source_name && (
            <div className="flex items-center gap-1 col-span-2">Source: {course.source_name}</div>
          )}
        </div>

        {progress && (
          <div className="mb-4">
            <div className="flex justify-between text-xs font-bold text-slate-700 mb-1">
              <span>Progress</span>
              <span>{progress.completion_percent}%</span>
            </div>
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-emerald-500 transition-all duration-500"
                style={{ width: `${progress.completion_percent}%` }}
              />
            </div>
          </div>
        )}

        <button 
          onClick={handleStartContinue} 
          className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-bold py-3 rounded-xl transition-colors shadow-sm"
        >
          {progress?.completion_percent > 0 ? (progress.completion_percent === 100 ? 'Review Course' : 'Continue Learning') : 'Start Learning'}
        </button>
      </div>

      <h2 className="text-base font-black text-slate-900 mb-3">Course Modules</h2>
      <div className="space-y-3">
        {modules.map((mod, i) => (
          <ModuleCard key={mod.id} module={mod} index={i} progress={progress} />
        ))}
      </div>
    </div>
  );
}

function ModuleCard({ module, index, progress }: { module: any, index: number, progress: any }) {
  const [lessons, setLessons] = useState<any[]>([]);
  const [expanded, setExpanded] = useState(index === 0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (expanded && lessons.length === 0) {
      setLoading(true);
      trainingApi.getModuleLessons(module.id).then(setLessons).finally(() => setLoading(false));
    }
  }, [expanded, module.id]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left p-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
      >
        <div>
          <span className="text-[10px] text-emerald-700 font-bold block mb-0.5">MODULE {module.sequence_number}</span>
          <h3 className="text-sm font-black text-slate-900">{module.title}</h3>
        </div>
        <span className="text-xs text-slate-400 font-semibold">{module.estimated_minutes} min</span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-slate-100 pt-3 bg-slate-50">
          <p className="text-xs text-slate-600 mb-3">{module.summary}</p>
          
          {loading ? (
            <p className="text-xs text-slate-400">Loading lessons...</p>
          ) : (
            <div className="space-y-2">
              {lessons.map((lesson) => {
                const isCompleted = progress?.lessons_progress?.find((p: any) => p.lesson_id === lesson.id)?.status === 'COMPLETED';
                return (
                  <Link 
                    key={lesson.id} 
                    href={`/skill-training/lesson/${lesson.id}`}
                    className={`flex items-center justify-between p-3 rounded-xl border transition-all ${
                      isCompleted 
                        ? 'bg-emerald-50 border-emerald-200' 
                        : 'bg-white border-slate-200 hover:border-emerald-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                        isCompleted ? 'bg-emerald-600 text-white' : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        {isCompleted ? '✓' : lesson.sequence_number}
                      </div>
                      <span className="text-xs font-bold text-slate-800">{lesson.title}</span>
                    </div>
                    <PlayCircle className={`w-4 h-4 ${isCompleted ? 'text-emerald-700' : 'text-emerald-600'}`} />
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
