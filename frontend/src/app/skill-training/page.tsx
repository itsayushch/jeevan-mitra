"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppSettings } from '../../components/AppShell';
import { trainingApi, learningApi } from '../../lib/api/training';
import { BookOpen, MapPin, MessageSquare, PlayCircle } from 'lucide-react';
import Link from 'next/link';
import { AskQuestionVoice } from '../../components/modules/AskQuestionVoice';

export default function SkillTrainingPage() {
  const { language } = useAppSettings();
  const router = useRouter();
  const [courses, setCourses] = useState<any[]>([]);
  const [overview, setOverview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'learn' | 'my-learning' | 'opportunities' | 'ask'>('learn');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await trainingApi.getCourses(language);
        setCourses(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [language]);

  useEffect(() => {
    if (activeTab === 'my-learning' && !overview) {
      learningApi.getMyOverview().then(setOverview).catch(e => console.error("Failed to load overview", e));
    }
  }, [activeTab, overview]);

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          course.short_description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSector = selectedSector ? course.sector === selectedSector : true;
    return matchesSearch && matchesSector;
  });

  const sectors = Array.from(new Set(courses.map(c => c.sector)));

  return (
    <div className="module-content">
      <div className="flex bg-white rounded-xl border border-slate-200 p-0.5 mb-4" role="tablist" aria-label="Skill Training Tabs">
        {['learn', 'my-learning', 'opportunities', 'ask'].map(tab => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            aria-controls={`tabpanel-${tab}`}
            onClick={() => setActiveTab(tab as any)}
            className={`flex-1 text-xs font-bold px-3 py-2 rounded-lg transition-all capitalize ${
              activeTab === tab ? 'bg-emerald-700 text-white' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {tab.replace('-', ' ')}
          </button>
        ))}
      </div>

      {activeTab === 'learn' && (
        <div className="space-y-4" role="tabpanel" id="tabpanel-learn" aria-labelledby="tab-learn">
          <div className="mb-4">
            <h2 className="text-xl font-black text-slate-900">Skill Training</h2>
            <p className="text-sm text-slate-500">Learn step by step in your preferred language.</p>
          </div>

          {!loading && courses.length > 0 && (
            <div className="flex gap-2 mb-4">
              <input 
                type="search"
                placeholder="Search courses..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search courses"
                className="flex-1 text-sm bg-white border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-emerald-500"
              />
              <select 
                value={selectedSector}
                onChange={(e) => setSelectedSector(e.target.value)}
                aria-label="Filter by sector"
                className="text-sm bg-white border border-slate-200 rounded-xl px-3 py-2 outline-none focus:border-emerald-500"
              >
                <option value="">All Sectors</option>
                {sectors.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}
          
          {loading ? (
            <div className="animate-pulse flex space-x-4">
              <div className="flex-1 space-y-4 py-1">
                <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-slate-200 rounded"></div>
                  <div className="h-4 bg-slate-200 rounded w-5/6"></div>
                </div>
              </div>
            </div>
          ) : filteredCourses.length === 0 ? (
            <div className="text-center py-10 bg-slate-50 rounded-2xl border border-slate-200" role="status">
              <p className="text-slate-500 font-medium">No courses found matching your criteria.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredCourses.map(course => (
                <div key={course.id} className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm hover:border-emerald-300 transition-all">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                      {course.sector}
                    </span>
                    {course.verification_status === 'Verified' && (
                      <span className="text-[10px] font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                        ✓ Verified
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-black text-slate-900 leading-tight mb-1">{course.title}</h3>
                  <p className="text-xs text-slate-600 mb-3 line-clamp-2">{course.short_description}</p>
                  
                  <div className="flex items-center gap-3 text-[11px] text-slate-500 font-medium mb-4">
                    <span className="flex items-center gap-1">⏱ {course.duration_hours} hrs</span>
                    <span className="flex items-center gap-1">📈 {course.difficulty}</span>
                  </div>
                  
                  <Link href={`/skill-training/course/${course.id}`} className="block w-full text-center bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-2.5 rounded-xl transition-colors">
                    View Course
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'my-learning' && (
        <div className="p-4 bg-white rounded-2xl border border-slate-200">
          <h3 className="font-black text-slate-900 mb-4">My Learning</h3>
          {!overview ? (
            <p className="text-sm text-slate-500">Loading progress...</p>
          ) : overview.inProgressCourses === 0 && overview.completedCourses === 0 ? (
            <p className="text-sm text-slate-500">No learning activity yet. Explore the Learn tab to start a course.</p>
          ) : (
            <div className="space-y-4">
              <div className="flex gap-4 mb-4">
                <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100 flex-1">
                  <div className="text-emerald-800 text-xs font-bold mb-1">In Progress</div>
                  <div className="text-xl font-black text-emerald-900">{overview.inProgressCourses}</div>
                </div>
                <div className="bg-blue-50 p-3 rounded-xl border border-blue-100 flex-1">
                  <div className="text-blue-800 text-xs font-bold mb-1">Completed</div>
                  <div className="text-xl font-black text-blue-900">{overview.completedCourses}</div>
                </div>
              </div>
              
              {overview.recentCourses?.length > 0 && (
                <div>
                  <h4 className="font-bold text-slate-800 text-sm mb-3">Recent Courses</h4>
                  {overview.recentCourses.map((c: any) => (
                    <div key={c.courseId} className="bg-slate-50 p-3 rounded-xl border border-slate-200 mb-3">
                      <div className="flex justify-between mb-1">
                        <span className="font-bold text-slate-900 text-sm">{c.title || 'Course'}</span>
                        <span className="text-xs font-bold text-emerald-700">{c.completionPercent}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden mb-3">
                        <div 
                          className="h-full bg-emerald-500 transition-all"
                          style={{ width: `${c.completionPercent}%` }}
                        />
                      </div>
                      <Link 
                        href={`/skill-training/${c.resumeLessonId ? 'lesson/' + c.resumeLessonId : 'course/' + c.courseId}`}
                        className="block w-full text-center bg-white border border-slate-200 hover:border-emerald-300 text-slate-700 hover:text-emerald-700 text-xs font-bold py-2 rounded-lg transition-all"
                      >
                        {c.completionPercent === 100 ? 'Review' : 'Continue'}
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'opportunities' && (
        <div className="p-4 bg-white rounded-2xl border border-slate-200">
          <h3 className="font-black text-slate-900 mb-2">Verified Local Opportunities</h3>
          <p className="text-sm text-slate-500 mb-4">Details may change; field worker confirmation is required.</p>
          
          <div className="space-y-4">
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl shadow-sm">
              <div className="flex justify-between items-start mb-2">
                <span className="text-[10px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-md">
                  Active Batch
                </span>
                <span className="text-[10px] font-bold text-slate-500">
                  Verified: Sep 10, 2026
                </span>
              </div>
              
              <h4 className="font-black text-slate-900 text-sm mb-1">Govt ITI Moradabad Training Centre</h4>
              <p className="text-xs text-slate-700 font-medium mb-1">Course: Solar PV Installer</p>
              <p className="text-xs text-slate-500 mb-3">Moradabad Rural, UP</p>
              
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="text-[10px] bg-white border border-slate-200 px-2 py-1 rounded text-slate-600">
                  Starts: Oct 15, 2026
                </span>
                <span className="text-[10px] bg-white border border-slate-200 px-2 py-1 rounded text-slate-600">
                  14 seats remaining
                </span>
              </div>
              
              <button className="w-full bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold py-2.5 rounded-lg transition-colors">
                Request Referral
              </button>
            </div>
            
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-xl text-center">
              <p className="text-sm text-slate-700 font-bold mb-1">Mushroom Cultivation</p>
              <p className="text-xs text-slate-500 mb-3">Local batch status: Not confirmed.</p>
              <div className="flex gap-2 justify-center">
                <button className="bg-white border border-slate-300 text-slate-700 text-xs font-bold py-1.5 px-3 rounded-lg hover:bg-slate-50 transition-colors">
                  Request worker support
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'ask' && (
        <div className="voice-wrapper">
          <AskQuestionVoice language={language} />
        </div>
      )}
    </div>
  );
}
