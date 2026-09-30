import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  AlertCircle,
  Download,
  LayoutDashboard,
  CalendarDays,
  BookOpen,
  Plus,
  RefreshCw,
  FileSpreadsheet,
  FileText,
  ShieldCheck,
  Languages,
  Mic,
  TrendingUp,
  BarChart3,
  CheckCircle2,
  Clock,
  Lock,
} from 'lucide-react';
import { SoundFX } from '../../utils/speech';
import {
  api,
  PlanningOverview,
  GapMetricItem,
  ReferralFunnelMetrics,
  PlanningDataQuality,
  PlanningSnapshot,
} from '../../lib/api';

interface DistrictPlannerProps {
  onBack: () => void;
}

export const DistrictPlannerConsole: React.FC<DistrictPlannerProps> = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState<
    'dashboard' | 'gaps' | 'funnel' | 'data-quality' | 'snapshots' | 'batches' | 'qualifications'
  >('dashboard');
  const [district, setDistrict] = useState<string>('Moradabad');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Live state
  const [overview, setOverview] = useState<PlanningOverview | null>(null);
  const [gaps, setGaps] = useState<GapMetricItem[]>([]);
  const [gapSummary, setGapSummary] = useState<Record<string, number>>({});
  const [funnel, setFunnel] = useState<ReferralFunnelMetrics | null>(null);
  const [dataQuality, setDataQuality] = useState<PlanningDataQuality | null>(null);
  const [snapshots, setSnapshots] = useState<PlanningSnapshot[]>([]);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [snapshotNotes, setSnapshotNotes] = useState<string>('');

  const loadPlanningData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [ovData, gapData, fnData, dqData, snapList] = await Promise.all([
        api.getPlanningOverview(district).catch(() => null),
        api.getPlanningGaps(district).catch(() => ({ metadata: {} as any, gaps: [], summary_by_status: {} })),
        api.getPlanningFunnel(district).catch(() => ({ metadata: {} as any, funnel: {} as any })),
        api.getPlanningDataQuality(district).catch(() => null),
        api.listPlanningSnapshots(district).catch(() => []),
      ]);

      if (ovData) setOverview(ovData);
      if (gapData) {
        setGaps(gapData.gaps || []);
        setGapSummary(gapData.summary_by_status || {});
      }
      if (fnData && fnData.funnel) setFunnel(fnData.funnel);
      if (dqData) setDataQuality(dqData);
      setSnapshots(snapList);
    } catch (err: any) {
      setError(err?.message || 'Failed to load district planning data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPlanningData();
  }, [district]);

  const handleGenerateSnapshot = async () => {
    try {
      SoundFX.playChime('click');
      const now = new Date();
      const year = now.getFullYear();
      const res = await api.createPlanningSnapshot({
        district_id: district,
        period_start: `${year}-01-01`,
        period_end: `${year}-12-31`,
        notes: snapshotNotes || 'Manual snapshot generated from console',
      });
      setSnapshots([res, ...snapshots]);
      setSnapshotNotes('');
      SoundFX.playChime('success');
      alert(`Snapshot generated successfully! ID: ${res.id}`);
    } catch (err: any) {
      alert(`Snapshot generation failed: ${err.message}`);
    }
  };

  const handleExport = async (snapshotId: string, type: 'CSV' | 'PDF') => {
    setIsExporting(true);
    try {
      SoundFX.playChime('click');
      const exportMeta = await api.createPlanningExport(snapshotId, type);
      const { blob, filename } = await api.downloadPlanningExportBlob(exportMeta.id);

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      SoundFX.playChime('success');
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleReviewSnapshot = async (id: string) => {
    try {
      const res = await api.reviewPlanningSnapshot(id, 'Reviewed by district planner');
      setSnapshots(snapshots.map((s) => (s.id === id ? res : s)));
      SoundFX.playChime('success');
    } catch (err: any) {
      alert(`Review failed: ${err.message}`);
    }
  };

  const handleApproveSnapshot = async (id: string) => {
    try {
      const res = await api.approvePlanningSnapshot(id, 'Approved for PM-AJAY annual plan');
      setSnapshots(snapshots.map((s) => (s.id === id ? res : s)));
      SoundFX.playChime('success');
    } catch (err: any) {
      alert(`Approval failed: ${err.message}`);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 text-slate-800">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full bg-white shadow-xs flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors border border-slate-200"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl md:text-2xl font-black text-slate-900">
              PM-AJAY District Planning & Aggregation Console
            </h1>
            <p className="text-xs font-semibold text-indigo-700">
              Evidence-based demand, verified training capacity, gaps, and controlled exports
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="text-xs font-bold bg-white border border-slate-200 px-3 py-2 rounded-xl shadow-2xs text-slate-700 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          >
            <option value="Moradabad">District: Moradabad</option>
            <option value="Varanasi">District: Varanasi</option>
            <option value="Lucknow">District: Lucknow</option>
          </select>
          <button
            onClick={loadPlanningData}
            disabled={isLoading}
            className="p-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 text-slate-600"
            title="Refresh planning aggregations"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-indigo-600' : ''}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-200 pb-2 overflow-x-auto text-xs font-bold">
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('dashboard');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'dashboard' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          Overview
        </button>
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('gaps');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'gaps' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          Demand & Gaps
        </button>
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('funnel');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'funnel' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Referral Funnel
        </button>
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('data-quality');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'data-quality' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          Quality & Access
        </button>
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('snapshots');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'snapshots' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          Snapshots & Exports
        </button>
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('batches');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'batches' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <CalendarDays className="w-4 h-4" />
          Batches
        </button>
        <button
          onClick={() => {
            SoundFX.playChime('click');
            setActiveTab('qualifications');
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl transition-all whitespace-nowrap ${
            activeTab === 'qualifications' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Qualifications
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-2xl mb-6 text-xs font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'dashboard' && (
        <div className="animate-fadeIn space-y-6">
          {/* Executive Narrative Brief */}
          <div className="bg-linear-to-r from-indigo-900 to-indigo-800 text-white p-6 rounded-3xl shadow-sm border border-indigo-700">
            <div className="flex items-center gap-2 mb-2 text-indigo-200 text-xs font-bold uppercase tracking-wider">
              <Clock className="w-3.5 h-3.5" />
              <span>Authoritative Planning Brief &bull; Fresh as of {overview?.metadata?.data_freshness_at?.slice(0, 10) || 'Current'}</span>
            </div>
            <p className="text-sm md:text-base leading-relaxed font-medium">
              {overview?.narrative_brief ||
                `Aggregating live intake demand, capacity, and outcomes across ${district} under PM-AJAY rules.`}
            </p>
            <div className="mt-4 pt-3 border-t border-indigo-700/60 flex items-center justify-between text-[11px] text-indigo-200">
              <span>Minimum cell-size privacy threshold: k = 5. Aggregate cells with &lt; 5 unique beneficiaries are suppressed.</span>
              <span className="font-bold">Metric Engine: {overview?.metadata?.metric_version || 'v1'}</span>
            </div>
          </div>

          {/* Key Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Beneficiaries Profiled</p>
              <p className="text-2xl font-black text-slate-900">
                {overview?.beneficiaries_profiled ?? (overview?.is_suppressed ? '< 5 (Suppressed)' : '0')}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Verified Matches</p>
              <p className="text-2xl font-black text-emerald-600">
                {overview?.verified_matches ?? (overview?.is_suppressed ? '< 5 (Suppressed)' : '0')}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Active Verified Capacity</p>
              <p className="text-2xl font-black text-indigo-600">
                {overview?.available_verified_capacity ?? 0} seats
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Planning Supply Gaps</p>
              <p className="text-2xl font-black text-rose-600">
                {overview?.planning_supply_gaps ?? (overview?.is_suppressed ? '< 5 (Suppressed)' : '0')}
              </p>
            </div>
          </div>

          {/* Quick Snapshot Action Banner */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-black text-slate-900">Need reproducible Annual Action Plan indicators?</h2>
              <p className="text-xs text-slate-500">
                Generate an immutable snapshot to create tamper-evident CSV and PDF exports with SHA-256 checksums.
              </p>
            </div>
            <button
              onClick={() => setActiveTab('snapshots')}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-2.5 px-4 rounded-xl shadow-xs transition-colors flex items-center gap-2 shrink-0"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Go to Snapshots & Exports</span>
            </button>
          </div>
        </div>
      )}

      {/* TAB 2: DEMAND & GAPS */}
      {activeTab === 'gaps' && (
        <div className="animate-fadeIn space-y-6">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-black text-slate-900">Trade Demand vs Verified Capacity Gaps</h2>
                <p className="text-xs text-slate-500">
                  Authoritative demand from confirmed profile facts compared strictly against ACTIVE verified local batches.
                </p>
              </div>
              <div className="flex gap-2">
                {Object.entries(gapSummary).map(([status, cnt]) => (
                  <span key={status} className="text-[10px] font-bold px-2 py-1 rounded-lg bg-slate-100 text-slate-700">
                    {status}: {cnt}
                  </span>
                ))}
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-extrabold uppercase">
                    <th className="py-3 px-3">Qualification / Trade</th>
                    <th className="py-3 px-3">Sector</th>
                    <th className="py-3 px-3 text-right">Expressed Demand</th>
                    <th className="py-3 px-3 text-right">Verified Capacity</th>
                    <th className="py-3 px-3 text-right">Supply Gap</th>
                    <th className="py-3 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {gaps.map((g) => (
                    <tr key={g.qualification_id} className="hover:bg-slate-50">
                      <td className="py-3.5 px-3 font-bold text-slate-900">{g.qualification_title}</td>
                      <td className="py-3.5 px-3 text-slate-600">{g.sector}</td>
                      <td className="py-3.5 px-3 text-right font-bold text-slate-900">
                        {g.is_suppressed ? (
                          <span className="text-amber-600 font-normal italic">&lt; 5 (Suppressed)</span>
                        ) : (
                          g.demand_count ?? 0
                        )}
                      </td>
                      <td className="py-3.5 px-3 text-right text-slate-700 font-bold">
                        {g.available_verified_capacity}
                      </td>
                      <td className="py-3.5 px-3 text-right font-bold text-rose-600">
                        {g.is_suppressed ? (
                          <span className="text-amber-600 font-normal italic">&lt; 5</span>
                        ) : (
                          g.supply_gap ?? 0
                        )}
                      </td>
                      <td className="py-3.5 px-3">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase ${
                            g.gap_status === 'CAPACITY_SURPLUS'
                              ? 'bg-emerald-100 text-emerald-800'
                              : g.gap_status === 'CAPACITY_BALANCED'
                              ? 'bg-blue-100 text-blue-800'
                              : g.gap_status === 'CAPACITY_DEFICIT'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {g.gap_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {gaps.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                        No gap records available for {district}.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: REFERRAL FUNNEL */}
      {activeTab === 'funnel' && (
        <div className="animate-fadeIn space-y-6">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <h2 className="text-base font-black text-slate-900 mb-1">Referral & Conversion Funnel</h2>
            <p className="text-xs text-slate-500 mb-6">
              Track progression from verified qualification matches through enrolment, training completion, and verified livelihood outcomes.
            </p>

            <div className="space-y-4 max-w-3xl">
              {[
                { name: '1. Verified Match', count: funnel?.verified_matches, rate: null },
                {
                  name: '2. Referral Created',
                  count: funnel?.referrals_created,
                  rate: funnel?.conversion_match_to_referral_pct,
                },
                {
                  name: '3. Field Worker Contacted',
                  count: funnel?.contacted,
                  rate: funnel?.conversion_referral_to_contact_pct,
                },
                {
                  name: '4. Enrolled in Batch',
                  count: funnel?.enrolled,
                  rate: funnel?.conversion_contact_to_enrolment_pct,
                },
                {
                  name: '5. Training Started',
                  count: funnel?.training_started,
                  rate: funnel?.conversion_enrolment_to_start_pct,
                },
                {
                  name: '6. Training Completed',
                  count: funnel?.completed,
                  rate: funnel?.conversion_start_to_complete_pct,
                },
                {
                  name: '7. Verified Livelihood',
                  count: funnel?.verified_livelihood,
                  rate: funnel?.conversion_complete_to_livelihood_pct,
                },
              ].map((stage, idx) => (
                <div key={stage.name} className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-100">
                  <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-slate-900">{stage.name}</p>
                    <p className="text-[11px] text-slate-500">
                      {stage.rate !== null && stage.rate !== undefined ? `Conversion: ${stage.rate}%` : 'Baseline Stage'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-base font-black text-slate-900">
                      {funnel?.is_suppressed ? (
                        <span className="text-xs font-normal text-amber-600 italic">&lt; 5 (Suppressed)</span>
                      ) : (
                        stage.count ?? '0'
                      )}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: DATA QUALITY & ACCESS */}
      {activeTab === 'data-quality' && (
        <div className="animate-fadeIn space-y-6">
          {/* Quality & Hygiene Metric Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Stale / Expired Opps</p>
              <p className="text-2xl font-black text-slate-900">
                {dataQuality?.data_quality.stale_or_expired_opportunities_count ?? 0}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Reverification Due (&lt;14d)</p>
              <p className="text-2xl font-black text-amber-600">
                {dataQuality?.data_quality.opportunities_due_reverification_count ?? 0}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Overdue Case Follow-ups</p>
              <p className="text-2xl font-black text-rose-600">
                {dataQuality?.data_quality.overdue_follow_ups_count ?? 0}
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Cases Without Referral Consent</p>
              <p className="text-2xl font-black text-indigo-600">
                {dataQuality?.data_quality.cases_without_referral_consent_count ?? 0}
              </p>
            </div>
          </div>

          {/* Multimodal Accessibility & Multilingual Breakdown */}
          <div className="grid md:grid-cols-3 gap-6">
            {/* Language distribution */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200">
              <div className="flex items-center gap-2 mb-3">
                <Languages className="w-4 h-4 text-indigo-600" />
                <h3 className="text-xs font-black text-slate-900 uppercase tracking-wider">Language Distribution</h3>
              </div>
              <p className="text-[11px] text-slate-500 mb-4">
                Beneficiary preferred languages in {district} (Minimum cell-size privacy threshold: k = 5).
              </p>
              <div className="space-y-2">
                {dataQuality?.data_quality.language_distribution &&
                Object.keys(dataQuality.data_quality.language_distribution).length > 0 ? (
                  Object.entries(dataQuality.data_quality.language_distribution).map(([lang, cnt]) => (
                    <div key={lang} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-xl">
                      <span className="font-bold text-slate-700 uppercase">{lang}</span>
                      <span className="font-black text-slate-900">
                        {cnt === null ? (
                          <span className="text-[10px] text-amber-600 font-semibold italic">&lt; 5 (Suppressed)</span>
                        ) : (
                          cnt
                        )}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 italic">No language preference data recorded.</p>
                )}
              </div>
            </div>

            {/* Opportunity submission channels */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200">
              <div className="flex items-center gap-2 mb-3">
                <Mic className="w-4 h-4 text-indigo-600" />
                <h3 className="text-xs font-black text-slate-900 uppercase tracking-wider">Multimodal Submissions</h3>
              </div>
              <p className="text-[11px] text-slate-500 mb-4">
                Community input channels reviewed by field staff.
              </p>
              <div className="space-y-2">
                {dataQuality?.data_quality.opportunity_submissions_by_mode &&
                Object.keys(dataQuality.data_quality.opportunity_submissions_by_mode).length > 0 ? (
                  Object.entries(dataQuality.data_quality.opportunity_submissions_by_mode).map(([mode, cnt]) => (
                    <div key={mode} className="flex justify-between items-center text-xs p-2 bg-slate-50 rounded-xl">
                      <span className="font-bold text-slate-700 capitalize">{mode} Submissions</span>
                      <span className="font-black text-slate-900">
                        {cnt === null ? (
                          <span className="text-[10px] text-amber-600 font-semibold italic">&lt; 5 (Suppressed)</span>
                        ) : (
                          cnt
                        )}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 italic">No opportunity submissions found.</p>
                )}
              </div>
            </div>

            {/* Explainability Quality */}
            <div className="bg-white p-5 rounded-3xl shadow-sm border border-slate-200">
              <div className="flex items-center gap-2 mb-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <h3 className="text-xs font-black text-slate-900 uppercase tracking-wider">Explainability Quality</h3>
              </div>
              <p className="text-[11px] text-slate-500 mb-4">
                Deterministic verified facts vs disposable rephrasings (strictly zero raw text).
              </p>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center p-2 bg-slate-50 rounded-xl">
                  <span className="text-slate-600">Confirmed Fact Recs</span>
                  <span className="font-black text-slate-900">
                    {dataQuality?.data_quality.explainability_quality.recommendations_with_confirmed_facts ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center p-2 bg-slate-50 rounded-xl">
                  <span className="text-slate-600">Template Explanations</span>
                  <span className="font-black text-emerald-700">
                    {dataQuality?.data_quality.explainability_quality.template_count ?? 0}
                  </span>
                </div>
                <div className="flex justify-between items-center p-2 bg-slate-50 rounded-xl">
                  <span className="text-slate-600">Grounded LLM Rewrites</span>
                  <span className="font-black text-indigo-700">
                    {dataQuality?.data_quality.explainability_quality.llm_count ?? 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: SNAPSHOTS & EXPORTS */}
      {activeTab === 'snapshots' && (
        <div className="animate-fadeIn space-y-6">
          {/* Snapshot Creator */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <h2 className="text-base font-black text-slate-900 mb-1">Generate Immutable Planning Snapshot</h2>
            <p className="text-xs text-slate-500 mb-4">
              Freezes authoritative aggregates for auditing, state reporting, and reproducible exports.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 items-center">
              <input
                type="text"
                value={snapshotNotes}
                onChange={(e) => setSnapshotNotes(e.target.value)}
                placeholder="Optional snapshot notes (e.g. Q1 District Planning Review)..."
                className="flex-1 text-xs border border-slate-200 p-2.5 rounded-xl text-slate-800 w-full focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={handleGenerateSnapshot}
                className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs py-2.5 px-5 rounded-xl shadow-xs transition-colors flex items-center justify-center gap-2 shrink-0"
              >
                <Plus className="w-4 h-4" />
                <span>Generate Snapshot</span>
              </button>
            </div>
          </div>

          {/* Snapshot History Table */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <h2 className="text-base font-black text-slate-900 mb-4">Snapshot Archive & Controlled Exports</h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-extrabold uppercase">
                    <th className="py-3 px-3">Snapshot ID</th>
                    <th className="py-3 px-3">Period</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-3">Created</th>
                    <th className="py-3 px-3">Workflow Actions</th>
                    <th className="py-3 px-3 text-right">Controlled Export</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {snapshots.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50">
                      <td className="py-3.5 px-3 font-bold text-slate-900">
                        <code>{s.id}</code>
                        {s.notes && <p className="text-[11px] text-slate-500 font-normal">{s.notes}</p>}
                      </td>
                      <td className="py-3.5 px-3 text-slate-600">
                        {s.period_start} to {s.period_end}
                      </td>
                      <td className="py-3.5 px-3">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase ${
                            s.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : s.status === 'REVIEWED'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-slate-500">{s.generated_at?.slice(0, 10)}</td>
                      <td className="py-3.5 px-3">
                        <div className="flex gap-2">
                          {s.status === 'GENERATED' && (
                            <button
                              onClick={() => handleReviewSnapshot(s.id)}
                              className="text-[11px] font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-lg"
                            >
                              Review
                            </button>
                          )}
                          {s.status === 'REVIEWED' && (
                            <button
                              onClick={() => handleApproveSnapshot(s.id)}
                              className="text-[11px] font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg"
                            >
                              Approve
                            </button>
                          )}
                          {s.status === 'APPROVED' && (
                            <span className="text-[11px] font-bold text-emerald-600 flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Approved
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleExport(s.id, 'CSV')}
                            disabled={isExporting}
                            className="flex items-center gap-1 text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1.5 rounded-lg transition-colors"
                          >
                            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                            <span>CSV</span>
                          </button>
                          <button
                            onClick={() => handleExport(s.id, 'PDF')}
                            disabled={isExporting}
                            className="flex items-center gap-1 text-[11px] font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1.5 rounded-lg transition-colors"
                          >
                            <FileText className="w-3.5 h-3.5 text-rose-600" />
                            <span>PDF</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {snapshots.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                        No planning snapshots generated yet for {district}. Click &quot;Generate Snapshot&quot; above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: BATCHES (Preserved) */}
      {activeTab === 'batches' && (
        <div className="animate-fadeIn space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-black text-slate-900">Training Batch Directory</h2>
              <p className="text-sm text-slate-500">Manage PM-AJAY sanctioned skilling batches across the district.</p>
            </div>
            <button
              onClick={() => SoundFX.playChime('click')}
              className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-md transition-colors"
            >
              <Plus className="w-4 h-4" />
              Sanction New Batch
            </button>
          </div>

          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-extrabold uppercase text-xs">
                    <th className="py-3 px-3">Batch ID &amp; Qualification</th>
                    <th className="py-3 px-3">Training Centre</th>
                    <th className="py-3 px-3">Schedule</th>
                    <th className="py-3 px-3">Capacity</th>
                    <th className="py-3 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  <tr className="hover:bg-slate-50 transition-colors cursor-pointer">
                    <td className="py-3 px-3">
                      <p className="font-black text-slate-900">BATCH-26-041</p>
                      <p className="text-xs text-slate-500">Mushroom Cultivation (NSQF L3)</p>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-bold text-slate-800">Chhajlet Block Centre</p>
                      <p className="text-xs text-slate-500">Moradabad</p>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-bold text-slate-800">15 Oct 2026 - 15 Dec 2026</p>
                      <p className="text-xs text-slate-500">200 Hours</p>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-slate-100 rounded-full h-2 max-w-[100px]">
                          <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '72%' }}></div>
                        </div>
                        <span className="text-xs font-bold text-slate-700">18/25</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full text-[10px] font-black uppercase">
                        Enrolling
                      </span>
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors cursor-pointer">
                    <td className="py-3 px-3">
                      <p className="font-black text-slate-900">BATCH-26-042</p>
                      <p className="text-xs text-slate-500">Solar PV Installer (NSQF L4)</p>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-bold text-slate-800">Govt ITI, Moradabad City</p>
                      <p className="text-xs text-slate-500">Moradabad</p>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-bold text-slate-800">01 Nov 2026 - 30 Jan 2027</p>
                      <p className="text-xs text-slate-500">400 Hours</p>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-slate-100 rounded-full h-2 max-w-[100px]">
                          <div className="bg-amber-500 h-2 rounded-full" style={{ width: '10%' }}></div>
                        </div>
                        <span className="text-xs font-bold text-slate-700">3/30</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="bg-amber-100 text-amber-800 px-2.5 py-1 rounded-full text-[10px] font-black uppercase">
                        Scheduled
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 7: QUALIFICATIONS (Preserved) */}
      {activeTab === 'qualifications' && (
        <div className="animate-fadeIn space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-black text-slate-900">National Qualification Register (NQR)</h2>
              <p className="text-sm text-slate-500">Approved NSQF job roles for PM-AJAY funding.</p>
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">
                  NSQF Level 4
                </span>
                <span className="text-xs font-bold text-indigo-700">SGJ/Q0101</span>
              </div>
              <h3 className="text-base font-black text-slate-900 mb-1">Solar PV Installer (Suryamitra)</h3>
              <p className="text-sm text-slate-600 mb-4 line-clamp-2">
                Installs, tests, and commissions solar PV plants while ensuring compliance with safety and environmental standards.
              </p>
              <div className="flex gap-4 text-xs font-bold text-slate-500">
                <span>🕒 400 Hours</span>
                <span>💼 Green Jobs</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">
                  NSQF Level 3
                </span>
                <span className="text-xs font-bold text-indigo-700">AGR/Q7803</span>
              </div>
              <h3 className="text-base font-black text-slate-900 mb-1">Mushroom Grower</h3>
              <p className="text-sm text-slate-600 mb-4 line-clamp-2">
                Cultivation of mushrooms under controlled conditions, including preparation of compost, spawning, crop management and harvesting.
              </p>
              <div className="flex gap-4 text-xs font-bold text-slate-500">
                <span>🕒 200 Hours</span>
                <span>💼 Agriculture</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
