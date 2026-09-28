import React, { useState } from 'react';
import { MapPin, Briefcase, Mic, CheckCircle2, X, Volume2 } from 'lucide-react';
import type { Language, JobOpportunity } from '../../types';
import { jobOpportunitiesData, voiceFAQData } from '../../data/mockData';
import { SoundFX, speakText } from '../../utils/speech';

interface JobPlacementMapProps {
  language: Language;
}

export const JobPlacementMap: React.FC<JobPlacementMapProps> = ({ language }) => {
  const [jobs, setJobs] = useState<JobOpportunity[]>(jobOpportunitiesData);
  const [selectedJobId, setSelectedJobId] = useState<string>(jobOpportunitiesData[0].id);
  const [selectedLocation, setSelectedLocation] = useState<string>('All');
  const [selectedSector, setSelectedSector] = useState<string>('All');
  const [applyingJobId, setApplyingJobId] = useState<string | null>(null);
  const [applicationSuccess, setApplicationSuccess] = useState<string | null>(null);
  const [viewDetailsJob, setViewDetailsJob] = useState<JobOpportunity | null>(null);

  const filteredJobs = jobs.filter((j) => {
    const matchSector = selectedSector === 'All' || j.sector === selectedSector;
    const matchLocation = selectedLocation === 'All' || j.location.includes(selectedLocation);
    return matchSector && matchLocation;
  });
  const selectedJob = filteredJobs.find((job) => job.id === selectedJobId) ?? filteredJobs[0] ?? null;

  const handleApplyVoice = (job: JobOpportunity) => {
    SoundFX.playChime('start');
    setApplyingJobId(job.id);

    setTimeout(() => {
      setApplyingJobId(null);
      setApplicationSuccess(job.title);
      SoundFX.playChime('success');

      // Update job state as applied
      setJobs((prev) =>
        prev.map((item) => (item.id === job.id ? { ...item, applied: true } : item))
      );

      const msg = language === 'hi'
        ? `${job.title} पद के लिए आपकी वॉयस अर्जी दर्ज कर ली गई है।`
        : `Voice application recorded for ${job.title} at ${job.company}.`;
      speakText(msg, language);
    }, 2000);
  };

  const handlePinClick = (job: JobOpportunity) => {
    SoundFX.playChime('click');
    setSelectedJobId(job.id);
  };

  return (
    <div className="module-page opportunities-page">
      {/* Top Header */}
      <div className="module-header mb-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 bg-teal-100 px-2.5 py-0.5 rounded-full">
            Localized Map & Listings
          </span>
          <span className="text-[11px] font-bold text-slate-400">
            Sample openings
          </span>
        </div>

        <h2 className="text-lg font-black text-slate-900 tracking-tight leading-tight">
          JOB PLACEMENT OPPORTUNITIES
        </h2>
      </div>

      {/* Quick FAQ Question Chips */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-3 scrollbar-none">
        {voiceFAQData.slice(0, 3).map((faq) => (
          <button
            key={faq.id}
            onClick={() => {
              SoundFX.playChime('question');
              speakText(language === 'hi' ? faq.answerHi : faq.answer, language);
            }}
            className="shrink-0 bg-white border border-slate-200 hover:border-emerald-400 px-2.5 py-1 rounded-xl text-[10px] font-semibold text-slate-700 shadow-2xs flex items-center gap-1 transition-all"
          >
            <Volume2 className="w-3 h-3 text-emerald-600" />
            <span>{language === 'hi' ? faq.hi : faq.en}</span>
          </button>
        ))}
      </div>

      {/* Location & Job Type Dropdown Filter Bar */}
      <div className="job-filters grid grid-cols-2 gap-2 mb-3">
        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Location
          </label>
          <select
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-2xs"
          >
            <option value="All">All locations</option>
            <option value="Moradabad">Moradabad Cluster</option>
            <option value="Chhajlet">Chhajlet Village</option>
          </select>
        </div>

        <div>
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
            Job Type
          </label>
          <select
            value={selectedSector}
            onChange={(e) => setSelectedSector(e.target.value)}
            className="w-full bg-white border border-slate-200 rounded-xl px-2.5 py-1.5 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-2xs"
          >
            <option value="All">All Sectors</option>
            <option value="Retail">Retail & Service</option>
            <option value="Logistics">Logistics & Delivery</option>
            <option value="Agriculture">Agriculture & Agro</option>
            <option value="Technical">Renewable / Solar</option>
          </select>
        </div>
      </div>

      {/* Interactive Map Canvas ("JOB LISTINGS: RETAIL & SERVICES") */}
      <div className="job-map relative w-full h-44 rounded-2xl bg-[#e5ede2] border-2 border-[#bdd1b8] overflow-hidden mb-4 shadow-inner">
        {/* Stylized vector map lines */}
        <svg className="w-full h-full opacity-60" viewBox="0 0 400 200">
          {/* River */}
          <path
            d="M-20,120 Q120,80 200,130 T420,100"
            stroke="#93c5fd"
            strokeWidth="14"
            fill="none"
          />
          {/* Roads */}
          <line x1="0" y1="50" x2="400" y2="70" stroke="#ffffff" strokeWidth="6" />
          <line x1="80" y1="0" x2="160" y2="200" stroke="#ffffff" strokeWidth="5" />
          <line x1="220" y1="0" x2="310" y2="200" stroke="#ffffff" strokeWidth="5" />
          <circle cx="160" cy="90" r="30" fill="#cbd5e1" opacity="0.3" />
        </svg>

        {/* Region Label */}
        <div className="absolute top-2 left-2 bg-white/90 backdrop-blur-xs px-2 py-0.5 rounded-lg border border-slate-200 text-[10px] font-extrabold text-slate-700 shadow-2xs">
          📍 {selectedLocation === 'All' ? 'All locations' : selectedLocation} Map View
        </div>

        {/* Interactive Map Pins */}
        {filteredJobs.map((job) => {
          const isSelected = selectedJob?.id === job.id;
          return (
            <button
              key={job.id}
              onClick={() => handlePinClick(job)}
              style={{ left: `${job.coordinates.x}%`, top: `${job.coordinates.y}%` }}
              className={`absolute -translate-x-1/2 -translate-y-1/2 p-1.5 rounded-full transition-all duration-300 shadow-md ${
                isSelected
                  ? 'bg-rose-600 text-white scale-125 ring-3 ring-rose-300 z-20'
                  : 'bg-emerald-700 text-white hover:scale-110 z-10'
              }`}
              title={`${job.title} - ${job.company}`}
            >
              <MapPin className="w-3.5 h-3.5" />
            </button>
          );
        })}

        {/* Selected Pin Info Card (Overlay) */}
        {selectedJob && (
          <div className="absolute bottom-2 left-2 right-2 bg-white/95 backdrop-blur-md rounded-xl p-2.5 border border-slate-200 shadow-lg flex items-center justify-between gap-2 z-30 animate-fadeIn">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-black text-slate-900 truncate">
                {selectedJob.title}, {selectedJob.company}
              </p>
              <div className="flex items-center gap-2 text-[10px] text-slate-500 font-medium">
                <span className="text-emerald-700 font-bold">Wage: {selectedJob.wage}</span>
                <span>•</span>
                <span>{selectedJob.distanceKm} km Distance</span>
              </div>
            </div>

            <div className="flex items-center gap-1.5 shrink-0">
              <button
                onClick={() => setViewDetailsJob(selectedJob)}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-bold px-2 py-1.5 rounded-lg transition-colors"
              >
                Details
              </button>
              <button
                onClick={() => handleApplyVoice(selectedJob)}
                disabled={applyingJobId === selectedJob.id || selectedJob.applied}
                className={`text-[10px] font-bold px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition-all ${
                  selectedJob.applied
                    ? 'bg-emerald-100 text-emerald-800'
                    : applyingJobId === selectedJob.id
                    ? 'bg-rose-500 text-white animate-pulse'
                    : 'bg-emerald-700 hover:bg-emerald-800 text-white'
                }`}
              >
                <Mic className="w-3 h-3" />
                <span>{selectedJob.applied ? 'Applied' : 'Apply'}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Job Opportunity Cards List */}
      <div className="job-list flex-1 overflow-y-auto space-y-2.5 pr-1 max-h-[220px]">
        {filteredJobs.length === 0 && <p className="job-empty-state">No sample opportunities match these filters. Try another location or sector.</p>}
        {filteredJobs.map((job) => {
          const isSelected = selectedJob?.id === job.id;
          return (
            <div
              key={job.id}
              onClick={() => setSelectedJobId(job.id)}
              className={`bg-white rounded-2xl p-3 border transition-all cursor-pointer ${
                isSelected
                  ? 'border-emerald-500 shadow-sm ring-1 ring-emerald-400'
                  : 'border-slate-200/90 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center shrink-0">
                    <Briefcase className="w-4 h-4 text-emerald-700" />
                  </div>
                  <div>
                    <h4 className="text-xs font-black text-slate-900 leading-snug">
                      {job.title}, {job.company}
                    </h4>
                    <p className="text-[11px] font-semibold text-emerald-700">
                      Wage: {job.wage}
                    </p>
                    <p className="text-[10px] text-slate-400 font-medium">
                      📍 {job.distanceKm} km Distance • {job.location}
                    </p>
                  </div>
                </div>

                <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md shrink-0">
                  {job.sector}
                </span>
              </div>

              <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-100">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setViewDetailsJob(job);
                  }}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold py-1.5 rounded-xl transition-colors"
                >
                  Details
                </button>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleApplyVoice(job);
                  }}
                  disabled={applyingJobId === job.id || job.applied}
                  className={`flex-1 text-xs font-bold py-1.5 rounded-xl flex items-center justify-center gap-1.5 transition-all ${
                    job.applied
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-300'
                      : applyingJobId === job.id
                      ? 'bg-rose-600 text-white animate-pulse'
                      : 'bg-emerald-700 hover:bg-emerald-800 text-white shadow-xs'
                  }`}
                >
                  <Mic className="w-3.5 h-3.5" />
                  <span>
                    {job.applied
                      ? 'Applied ✓'
                      : applyingJobId === job.id
                      ? 'Recording...'
                      : 'Apply by Voice'}
                  </span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Application Success Banner */}
      {applicationSuccess && (
        <div className="mt-3 bg-emerald-50 border border-emerald-300 rounded-2xl p-2.5 flex items-center justify-between text-xs text-emerald-900 font-bold animate-fadeIn">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Applied for {applicationSuccess}!
          </span>
          <button
            onClick={() => setApplicationSuccess(null)}
            className="text-emerald-700 hover:text-emerald-900"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Job Details Modal */}
      {viewDetailsJob && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-5 max-w-sm w-full shadow-2xl border border-slate-200 animate-fadeIn">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-base font-black text-slate-900">
                  {viewDetailsJob.title}
                </h3>
                <p className="text-xs font-bold text-emerald-700">{viewDetailsJob.company}</p>
              </div>
              <button
                onClick={() => setViewDetailsJob(null)}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600 mb-3">{viewDetailsJob.description}</p>

            <div className="space-y-1.5 mb-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Requirements:
              </span>
              {viewDetailsJob.requirements.map((req, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs text-slate-700 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
                  <span>{req}</span>
                </div>
              ))}
            </div>

            <button
              onClick={() => {
                handleApplyVoice(viewDetailsJob);
                setViewDetailsJob(null);
              }}
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 rounded-2xl text-xs flex items-center justify-center gap-2 shadow-md"
            >
              <Mic className="w-4 h-4" />
              <span>Submit Voice Application</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
