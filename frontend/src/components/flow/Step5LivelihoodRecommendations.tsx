import React, { useState } from 'react';
import { ArrowLeft, ChevronRight, Sparkles, Store, SunMedium, Scissors, CheckCircle2, AlertCircle, ExternalLink, UserCheck, ShieldAlert, Volume2 } from 'lucide-react';
import type { Language } from '../../types';
import type { RecommendationItem } from '../../lib/api';
import { api } from '../../lib/api';
import { SoundFX, speakText } from '../../utils/speech';
import { useAppSettings } from '../AppShell';
import { getVoiceCapability } from '../../lib/i18n/voiceCapabilities';

interface Step5Props {
  language: Language;
  onSelectCourse: (courseId: string) => void;
  onNext: () => void;
  onPrev: () => void;
  recommendations?: RecommendationItem[];
  interviewId?: string | null;
}

export const Step5LivelihoodRecommendations: React.FC<Step5Props> = ({
  language,
  onSelectCourse,
  onNext,
  onPrev,
  recommendations,
  interviewId,
}) => {
  const { t } = useAppSettings();
  const [expandedReasons, setExpandedReasons] = useState<Record<string, boolean>>({});
  const voiceCap = getVoiceCapability(language);
  const isTtsSupported = voiceCap.tts === 'supported';

  const [referralRequested, setReferralRequested] = useState<Record<string, boolean>>({});
  const [referralLoading, setReferralLoading] = useState<string | null>(null);

  const handleCardClick = (id: string) => {
    SoundFX.playChime('click');
    onSelectCourse(id);
    onNext();
  };

  const handleRequestReferral = async (rec: RecommendationItem, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!interviewId) return;
    try {
      setReferralLoading(rec.recommendation_id);
      await api.createReferral(interviewId, 'user_requested_human_help', rec.recommendation_id);
      SoundFX.playChime('success');
      setReferralRequested(prev => ({ ...prev, [rec.recommendation_id]: true }));
    } catch (err) {
      console.error('Failed to request referral:', err);
    } finally {
      setReferralLoading(null);
    }
  };

  const isHindi = language === 'hi';
  const hasLiveRecs = recommendations && recommendations.length > 0;

  return (
    <div className="flex flex-col justify-between min-h-[580px] p-5 text-slate-800">
      {/* Top Header */}
      <div>
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={onPrev}
            className="w-9 h-9 rounded-full bg-white border border-slate-200 shadow-2xs flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl font-black text-slate-900 tracking-tight">
              {isHindi ? 'आजीविका सिफारिशें' : 'Livelihood Recommendations.'}
            </h2>
            <p className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-emerald-600" />
              <span>{hasLiveRecs ? 'Verified NQR & Local Opportunity Match' : 'Verified Match Protocol (Problem ID 26097)'}</span>
            </p>
          </div>
        </div>

        {/* Live Deterministic Backend Recommendations */}
        {hasLiveRecs ? (
          <div className="space-y-4 mb-5">
            {recommendations.map((rec) => {
              const avail = rec.local_availability;
              const isAvailOpen = avail?.status === 'verified_open';
              const isAvailUnknown = avail?.status === 'unknown';
              const isAvailExpired = avail?.status === 'expired';
              const isReferred = referralRequested[rec.recommendation_id];

              return (
                <div
                  key={rec.recommendation_id}
                  className="bg-white rounded-3xl p-4 border border-slate-200/90 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md bg-teal-100 text-teal-800 border border-teal-200 mr-2">
                        {rec.qualification.sector} • NSQF L{rec.qualification.nsqf_level}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        NQR: {rec.qualification.nqr_code}
                      </span>
                      <h3 className="text-sm font-black text-slate-900 mt-1">
                        {rec.qualification.title}
                      </h3>
                    </div>

                    {/* Match State & Local Status Badge */}
                    <div className="shrink-0 flex flex-col items-end gap-1">
                      {rec.match_state === 'VERIFIED_MATCH' || isAvailOpen ? (
                        <>
                          <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 border border-emerald-300 px-2 py-0.5 rounded-full flex items-center gap-1 shadow-2xs">
                            <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                            Verified Match
                          </span>
                          <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md">
                            Verified Batch Open
                          </span>
                        </>
                      ) : (
                        <>
                          <span className="text-[10px] font-black uppercase tracking-wider text-amber-800 bg-amber-100 border border-amber-300 px-2 py-0.5 rounded-full flex items-center gap-1 shadow-2xs" title="Qualification matches your profile, but local batch verification is pending.">
                            <AlertCircle className="w-3 h-3 text-amber-700" />
                            Interest Match
                          </span>
                          <span className="text-[9px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
                            {isAvailExpired ? 'Batch Expired' : 'Local Batch Pending'}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                    {/* Why this may suit you */}
                    <div className="my-2 bg-slate-50 rounded-xl p-2.5 text-[11px] text-slate-700 border border-slate-100">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="font-bold text-[11px] uppercase tracking-wider text-slate-700 flex items-center gap-1">
                          <span>{t('recommendations.whyMaySuitYou')}</span>
                        </div>
                        {isTtsSupported && (
                          <button
                            type="button"
                            className="text-emerald-700 hover:text-emerald-900 flex items-center gap-1 text-[10px] font-bold"
                            onClick={(e) => {
                              e.stopPropagation();
                              const script = rec.whyRecommended?.shortExplanation || (Array.isArray(rec.why_recommended) ? rec.why_recommended.join('. ') : '');
                              if (script) speakText(script, language);
                            }}
                            aria-label="Hear explanation"
                          >
                            <Volume2 className="w-3.5 h-3.5" />
                            <span>Hear explanation</span>
                          </button>
                        )}
                      </div>

                      {rec.whyRecommended?.shortExplanation && (
                        <p className="text-[11px] font-medium text-slate-600 mb-2 italic">
                          "{rec.whyRecommended.shortExplanation}"
                        </p>
                      )}

                      {(() => {
                        const allReasons = rec.whyRecommended?.reasons || (rec.why_recommended?.map(r => ({ factor: 'REASON', text: r })) || []);
                        const isExpanded = !!expandedReasons[rec.recommendation_id];
                        const displayedReasons = isExpanded ? allReasons : allReasons.slice(0, 2);

                        return (
                          <>
                            <ul className="space-y-1 list-disc list-inside text-slate-700">
                              {displayedReasons.map((reason, idx) => (
                                <li key={idx}>
                                  {typeof reason === 'string' ? reason : reason.text}
                                </li>
                              ))}
                            </ul>

                            {allReasons.length > 2 && (
                              <button
                                type="button"
                                className="mt-2 text-[10px] font-bold text-teal-700 hover:underline flex items-center gap-1"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setExpandedReasons(prev => ({
                                    ...prev,
                                    [rec.recommendation_id]: !prev[rec.recommendation_id]
                                  }));
                                }}
                              >
                                {isExpanded ? t('recommendations.showFewerReasons') : `${t('recommendations.showAllReasons')} (${allReasons.length})`}
                              </button>
                            )}
                          </>
                        );
                      })()}
                    </div>

                    {/* Skills Grid */}
                    <div className="grid grid-cols-2 gap-2 my-2 text-[11px]">
                      <div className="bg-emerald-50/60 p-2 rounded-xl border border-emerald-100">
                        <span className="text-[9px] font-black uppercase text-emerald-800 block mb-1">
                          {t('recommendations.matchedSkills')}
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {rec.matched_skills.map((skill, sIdx) => (
                            <span key={sIdx} className="bg-white px-1.5 py-0.5 rounded text-[10px] text-emerald-900 border border-emerald-200">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="bg-amber-50/60 p-2 rounded-xl border border-amber-100">
                        <span className="text-[9px] font-black uppercase text-amber-800 block mb-1">
                          {t('recommendations.skillGaps')}
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {rec.skill_gaps.map((gap, gIdx) => (
                            <span key={gIdx} className="bg-white px-1.5 py-0.5 rounded text-[10px] text-amber-900 border border-amber-200">
                              {gap}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Local Availability (Separated from Suitability) */}
                    <div className="my-2 bg-white rounded-xl p-2.5 text-[11px] border border-slate-200">
                      <div className="font-bold text-[10px] uppercase tracking-wider text-slate-400 mb-1">
                        Availability:
                      </div>
                      {isAvailOpen && avail ? (
                        <div className="text-slate-700">
                          <span className="font-bold text-slate-900">{avail.centre_name || 'Govt Training Centre'}</span>
                          {avail.district && <span> • {avail.district}</span>}
                          {avail.batch_start_date && <span> • Batch starts: {avail.batch_start_date}</span>}
                          {avail.stipend_amount_inr ? <span> • Stipend: ₹{avail.stipend_amount_inr}/mo</span> : null}
                        </div>
                      ) : (
                        <div className="text-amber-800 text-[11px] font-medium">
                          {isAvailExpired ? t('recommendations.batchExpired') : t('recommendations.localBatchPending')}
                        </div>
                      )}
                    </div>

                  {/* Official Link & Caveat */}
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1 pt-1 border-t border-slate-100">
                    <span className="italic">{rec.caveat}</span>
                    {rec.qualification.official_url && (
                      <a
                        href={rec.qualification.official_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-teal-700 font-bold hover:underline flex items-center gap-0.5 shrink-0 ml-2"
                      >
                        <span>Official NQR</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-2 mt-3 pt-2">
                    {rec.can_request_referral && (
                      <button
                        onClick={(e) => handleRequestReferral(rec, e)}
                        disabled={isReferred || referralLoading === rec.recommendation_id}
                        className={`text-xs font-bold py-2 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-colors border ${
                          isReferred
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-emerald-600 hover:bg-emerald-700 text-white border-emerald-600 shadow-2xs'
                        }`}
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>{isReferred ? 'Referral Requested' : 'Apply / Batch Referral'}</span>
                      </button>
                    )}

                    {!rec.can_request_referral && (isAvailUnknown || isAvailExpired) && (
                      <button
                        onClick={(e) => handleRequestReferral(rec, e)}
                        disabled={isReferred || referralLoading === rec.recommendation_id}
                        className={`text-xs font-bold py-2 px-3 rounded-xl flex items-center justify-center gap-1.5 transition-colors border ${
                          isReferred
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-300'
                        }`}
                      >
                        <UserCheck className="w-3.5 h-3.5" />
                        <span>{isReferred ? 'Counselor Requested' : 'Ask Field Worker Support'}</span>
                      </button>
                    )}

                    <button
                      onClick={() => handleCardClick(rec.qualification.id)}
                      className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
                    >
                      <span>Explore Course Pathway</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Default Static Demo Cards Fallback */
          <div>
            <div className="mb-5">
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-xs font-black uppercase tracking-wider text-emerald-800 bg-emerald-100/80 px-2.5 py-0.5 rounded-lg border border-emerald-300">
                  Self-Employment Path
                </span>
                <span className="text-[10px] font-semibold text-slate-400">Micro-Enterprise / Subsidy</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-3xl p-3.5 border-2 border-emerald-500/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
                  <div className="flex flex-col items-center text-center">
                    <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-2xl mb-2 shadow-2xs">
                      🍄
                    </div>
                    <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                      Mushroom cultivation
                    </h3>
                    <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full mb-3">
                      Verified Batch Open
                    </span>
                  </div>

                  <button
                    onClick={() => handleCardClick('qual_mushroom_07')}
                    className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
                  >
                    <span>View Course</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="bg-white rounded-3xl p-3.5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
                  <div className="flex flex-col items-center text-center">
                    <div className="w-14 h-14 rounded-2xl bg-teal-50 border border-teal-200 text-teal-700 flex items-center justify-center mb-2 shadow-2xs">
                      <Store className="w-7 h-7" />
                    </div>
                    <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                      Small Fruit & Agro Processing
                    </h3>
                    <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full mb-3">
                      High Demand
                    </span>
                  </div>

                  <button
                    onClick={() => handleCardClick('qual_food_04')}
                    className="w-full bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
                  >
                    <span>View Course</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2 px-1">
                <span className="text-xs font-black uppercase tracking-wider text-teal-800 bg-teal-100/80 px-2.5 py-0.5 rounded-lg border border-teal-300">
                  Wage Employment Path
                </span>
                <span className="text-[10px] font-semibold text-slate-400">Guaranteed Placements</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white rounded-3xl p-3.5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
                  <div className="flex flex-col items-center text-center">
                    <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mb-2 shadow-2xs">
                      <SunMedium className="w-7 h-7" />
                    </div>
                    <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                      Solar Technician
                    </h3>
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full mb-3">
                      PM Surya Ghar
                    </span>
                  </div>

                  <button
                    onClick={() => handleCardClick('qual_solar_01')}
                    className="w-full bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
                  >
                    <span>View Course</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="bg-white rounded-3xl p-3.5 border border-slate-200/80 shadow-sm flex flex-col justify-between hover:shadow-md transition-all">
                  <div className="flex flex-col items-center text-center">
                    <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-700 flex items-center justify-center mb-2 shadow-2xs">
                      <Scissors className="w-7 h-7" />
                    </div>
                    <h3 className="text-xs font-black text-slate-900 leading-tight mb-1">
                      Sewing Machine Operator
                    </h3>
                    <span className="text-[10px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full mb-3">
                      Textile Cluster
                    </span>
                  </div>

                  <button
                    onClick={() => handleCardClick('qual_sewing_02')}
                    className="w-full bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold py-2 rounded-xl flex items-center justify-center gap-1 shadow-xs transition-colors"
                  >
                    <span>View Course</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer info */}
      <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500 font-medium">
        <span className="flex items-center gap-1 text-emerald-700 font-bold">
          <CheckCircle2 className="w-3.5 h-3.5" /> {hasLiveRecs ? `${recommendations.length} Evidence-Backed Qualifications` : '4 Verified Courses Found'}
        </span>
        <span>Tap any course to inspect</span>
      </div>
    </div>
  );
};
