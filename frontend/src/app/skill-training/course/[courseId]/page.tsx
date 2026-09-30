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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const c = await trainingApi.getCourse(params.courseId);
        const m = await trainingApi.getCourseModules(params.courseId);
        setCourse(c);
        setModules(m);
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

        <button 
          onClick={() => learningApi.startCourse(course.id)} 
          className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-sm font-bold py-3 rounded-xl transition-colors shadow-sm"
        >
          Start / Continue Learning
        </button>
      </div>

      <h2 className="text-base font-black text-slate-900 mb-3">Course Modules</h2>
      <div className="space-y-3">
        {modules.map((mod, i) => (
          <ModuleCard key={mod.id} module={mod} index={i} />
        ))}
      </div>
    </div>
  );
}

function ModuleCard({ module, index }: { module: any, index: number }) {
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
              {lessons.map((lesson) => (
                <Link 
                  key={lesson.id} 
                  href={`/skill-training/lesson/${lesson.id}`}
                  className="flex items-center justify-between bg-white p-3 rounded-xl border border-slate-200 hover:border-emerald-300 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">
                      {lesson.sequence_number}
                    </div>
                    <span className="text-xs font-bold text-slate-800">{lesson.title}</span>
                  </div>
                  <PlayCircle className="w-4 h-4 text-emerald-600" />
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
