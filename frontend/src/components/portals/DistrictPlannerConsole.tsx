import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft, AlertCircle, Download, LayoutDashboard, CalendarDays, BookOpen,
  Plus, RefreshCw, FileText, ShieldCheck, ChevronDown, ChevronRight, KeyRound
} from 'lucide-react';
import { SoundFX } from '../../utils/speech';
import { api, PlanningMatrix, PlanningMatrixCell, PlanningBrief } from '../../lib/api';

interface DistrictPlannerProps {
  onBack: () => void;
}

const DISTRICT = 'Moradabad';
const PERIOD = 'FY 2026-27';

export const DistrictPlannerConsole: React.FC<DistrictPlannerProps> = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'batches' | 'qualifications'>('dashboard');
  const [officerKey, setOfficerKey] = useState<string>(api.getOfficerKey() || '');
  const [keyUnlocked, setKeyUnlocked] = useState<boolean>(!!api.getOfficerKey());

  return (
    <div className="w-full max-w-5xl mx-auto p-4 md:p-6 text-slate-800">
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors border border-slate-200"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-xl md:text-2xl font-black text-slate-900">
            PM-AJAY District Planning Console
          </h1>
          <p className="text-xs font-semibold text-indigo-700">
            Understand demand and gaps in local training capacity
          </p>
        </div>
        <span className="ml-auto text-xs font-bold text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-full shadow-2xs">
          District: {DISTRICT} | {PERIOD}
        </span>
      </div>

      {!keyUnlocked ? (
        <OfficerGate officerKey={officerKey} setOfficerKey={setOfficerKey} onUnlock={() => {
          api.setOfficerKey(officerKey);
          setKeyUnlocked(true);
          SoundFX.playChime('success');
        }} />
      ) : (
        <>
          <div className="flex gap-2 mb-6 border-b border-slate-200 pb-2">
            <TabButton active={activeTab === 'dashboard'} onClick={() => { SoundFX.playChime('click'); setActiveTab('dashboard'); }} icon={<LayoutDashboard className="w-4 h-4" />} label="Demand & Supply" />
            <TabButton active={activeTab === 'batches'} onClick={() => { SoundFX.playChime('click'); setActiveTab('batches'); }} icon={<CalendarDays className="w-4 h-4" />} label="Batch Management" />
            <TabButton active={activeTab === 'qualifications'} onClick={() => { SoundFX.playChime('click'); setActiveTab('qualifications'); }} icon={<BookOpen className="w-4 h-4" />} label="Qualifications" />
          </div>

          {activeTab === 'dashboard' && <DashboardTab />}
          {activeTab === 'batches' && <BatchesTab />}
          {activeTab === 'qualifications' && <QualificationsTab />}
        </>
      )}
    </div>
  );
};

const TabButton: React.FC<{ active: boolean; onClick: () => void; icon: React.ReactNode; label: string }> = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
      active ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
    }`}
  >
    {icon}
    {label}
  </button>
);

const OfficerGate: React.FC<{ officerKey: string; setOfficerKey: (k: string) => void; onUnlock: () => void }> = ({ officerKey, setOfficerKey, onUnlock }) => (
  <div className="animate-fadeIn max-w-md mx-auto mt-10 bg-white p-8 rounded-3xl shadow-sm border border-slate-200 text-center">
    <div className="w-14 h-14 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center mx-auto mb-4">
      <KeyRound className="w-7 h-7" />
    </div>
    <h2 className="text-lg font-black text-slate-900 mb-1">District Officer Access</h2>
    <p className="text-sm text-slate-500 mb-5">
      Planning data is restricted to authorised district officers. Enter your officer API key to continue.
    </p>
    <input
      type="password"
      value={officerKey}
      onChange={(e) => setOfficerKey(e.target.value)}
      placeholder="X-Officer-API-Key"
      className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
    />
    <button
      onClick={onUnlock}
      disabled={!officerKey.trim()}
      className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-bold text-sm py-2.5 rounded-xl transition-colors"
    >
      Unlock Console
    </button>
  </div>
);

const DashboardTab: React.FC = () => {
  const [matrix, setMatrix] = useState<PlanningMatrix | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [brief, setBrief] = useState<PlanningBrief | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [officerName, setOfficerName] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const m = await api.getPlanningMatrix(DISTRICT, PERIOD);
      setMatrix(m);
    } catch (e: any) {
      setError(e.message || 'Failed to load planning matrix');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const generateBrief = async () => {
    setBriefLoading(true);
    setError(null);
    try {
      const b = await api.generatePlanningBrief(DISTRICT, PERIOD);
      setBrief(b);
      SoundFX.playChime('success');
    } catch (e: any) {
      setError(e.message || 'Brief generation failed');
    } finally {
      setBriefLoading(false);
    }
  };

  if (loading) return <div className="animate-fadeIn text-center py-16 text-slate-500 font-bold"><RefreshCw className="w-6 h-6 animate-spin mx-auto mb-3" />Loading district data...</div>;
  if (error) return <div className="animate-fadeIn text-center py-16"><AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-3" /><p className="font-bold text-rose-700">{error}</p><button onClick={load} className="mt-4 text-sm font-bold text-indigo-600 hover:underline">Retry</button></div>;
  if (!matrix) return null;

  if (matrix.status === 'insufficient_data') {
    return (
      <div className="animate-fadeIn bg-amber-50 border border-amber-200 p-8 rounded-3xl text-center">
        <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
        <h2 className="text-base font-black text-amber-900 mb-1">Insufficient data</h2>
        <p className="text-sm text-amber-800">{matrix.message}</p>
        <p className="text-xs text-amber-700 mt-2">No figures are shown rather than estimated. Complete more consented interviews to build the demand record.</p>
      </div>
    );
  }

  const m = matrix.metrics;

  return (
    <div className="animate-fadeIn space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Demand Records" value={String(m.total_demand_records)} color="text-slate-900" />
        <StatCard label="Verified Matches" value={String(m.demand_with_verified_match_count)} color="text-emerald-600" />
        <StatCard label="Unmet Demand (seats)" value={String(m.total_unmet_demand)} color="text-rose-600" />
        <StatCard label="Verified Supply Batches" value={String(m.supply_batches_considered)} color="text-indigo-600" />
      </div>

      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-black text-slate-900">Trade Aspiration vs Verified Training Supply</h2>
            <p className="text-xs text-slate-500">
              {m.blocks_with_demand} blocks | {m.qualifications_demanded} trades | severity = demand x (1 - coverage) x distance penalty
            </p>
          </div>
          <button
            onClick={load}
            className="flex items-center gap-1.5 text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-extrabold uppercase">
                <th className="py-3 px-3">Block / Trade</th>
                <th className="py-3 px-3 text-right">Demand</th>
                <th className="py-3 px-3 text-right">Verified Seats</th>
                <th className="py-3 px-3 text-right">Gap</th>
                <th className="py-3 px-3 text-right">Nearest Centre</th>
                <th className="py-3 px-3 text-right">Severity</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {matrix.matrix.map((cell) => (
                <MatrixRow
                  key={`${cell.block}:${cell.qualification_id}`}
                  cell={cell}
                  expanded={expanded === `${cell.block}:${cell.qualification_id}`}
                  onToggle={() => setExpanded(expanded === `${cell.block}:${cell.qualification_id}` ? null : `${cell.block}:${cell.qualification_id}`)}
                />
              ))}
            </tbody>
          </table>
        </div>
        {m.suppressed_cell_count > 0 && (
          <p className="text-[11px] text-slate-400 mt-3">
            {m.suppressed_cell_count} cell(s) suppressed under k-anonymity (fewer than {matrix.data_basis.k_anonymity_threshold} demand records) and excluded from gap ranking.
          </p>
        )}
      </div>

      <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-black text-slate-900">Planning Brief</h2>
            <p className="text-xs text-slate-500">Template-generated; every figure traced to query {matrix.query_id}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={generateBrief}
              disabled={briefLoading}
              className="flex items-center gap-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-xl transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              {briefLoading ? 'Generating...' : brief ? 'Regenerate' : 'Generate Brief'}
            </button>
          </div>
        </div>

        {brief ? (
          <BriefPanel brief={brief} officerName={officerName} setOfficerName={setOfficerName} />
        ) : (
          <p className="text-sm text-slate-500">Generate a brief to see the plain-language summary of supply gaps for district planning.</p>
        )}
      </div>
    </div>
  );
};

const StatCard: React.FC<{ label: string; value: string; color: string }> = ({ label, value, color }) => (
  <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
    <p className="text-xs font-bold text-slate-500 mb-1">{label}</p>
    <p className={`text-2xl font-black ${color}`}>{value}</p>
  </div>
);

const MatrixRow: React.FC<{ cell: PlanningMatrixCell; expanded: boolean; onToggle: () => void }> = ({ cell, expanded, onToggle }) => {
  const status = cell.suppressed
    ? { label: 'Suppressed', cls: 'bg-slate-100 text-slate-500' }
    : (cell.gap ?? 0) > 0
      ? { label: `Gap ${cell.gap}`, cls: 'bg-rose-100 text-rose-800' }
      : { label: 'Balanced', cls: 'bg-emerald-100 text-emerald-800' };

  return (
    <>
      <tr onClick={onToggle} className="hover:bg-slate-50 transition-colors cursor-pointer">
        <td className="py-3.5 px-3 font-bold text-slate-900">
          <span className="flex items-center gap-1.5">
            {expanded ? <ChevronDown className="w-3.5 h-3.5 text-slate-400" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400" />}
            {cell.block} - {cell.qualification_title}
          </span>
        </td>
        <td className="py-3.5 px-3 text-right font-bold text-slate-900">{cell.demand_count ?? "< 5"}</td>
        <td className="py-3.5 px-3 text-right text-slate-500">{cell.verified_seats ?? '-'}</td>
        <td className="py-3.5 px-3 text-right">{cell.gap ?? '-'}</td>
        <td className="py-3.5 px-3 text-right text-slate-500">
          {cell.nearest_verified_centre_km !== null ? `${cell.nearest_verified_centre_km} km` : 'none in district'}
        </td>
        <td className="py-3.5 px-3 text-right">{cell.severity_score ?? '-'}</td>
        <td className="py-3.5 px-3">
          <span className={`${status.cls} px-2.5 py-1 rounded-full text-[10px] font-black`}>{status.label}</span>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-slate-50">
          <td colSpan={7} className="py-3 px-4 text-[11px] text-slate-500">
            <div className="grid md:grid-cols-2 gap-3">
              <div>
                <p className="font-bold text-slate-600 mb-1">Source reference</p>
                <p>Query: <span className="font-mono">{cell.source.query_id}</span></p>
                <p>Demand rows: {cell.source.demand_row_ids.length > 0
                  ? <span className="font-mono">{cell.source.demand_row_ids.join(', ')}</span>
                  : 'withheld (k-anonymity)'}</p>
                <p>Supply batches: {cell.source.supply_batch_ids.length > 0
                  ? <span className="font-mono">{cell.source.supply_batch_ids.join(', ')}</span>
                  : 'none eligible'}</p>
              </div>
              <div>
                <p className="font-bold text-slate-600 mb-1">Detail</p>
                <p>Total seats (verified batches): {cell.total_seats ?? 0}</p>
                <p>Coverage: {cell.coverage !== null ? `${(cell.coverage * 100).toFixed(0)}%` : '-'}</p>
                <p>Demand with no verified batch: {cell.share_of_demand_with_no_verified_batch !== null ? `${(cell.share_of_demand_with_no_verified_batch * 100).toFixed(0)}%` : '-'}</p>
                {cell.nearest_verified_centre_name && <p>Nearest centre: {cell.nearest_verified_centre_name}</p>}
                {cell.suppressed && <p className="text-amber-600 font-bold">{cell.suppression_reason}</p>}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

const BriefPanel: React.FC<{ brief: PlanningBrief; officerName: string; setOfficerName: (n: string) => void }> = ({ brief, officerName, setOfficerName }) => {
  const [signing, setSigning] = useState(false);
  const [signError, setSignError] = useState<string | null>(null);
  const [signed, setSigned] = useState(false);

  const signOff = async () => {
    setSigning(true);
    setSignError(null);
    try {
      await api.signOffBrief(brief.brief_id, officerName || 'District Officer', 'sign_off');
      setSigned(true);
      SoundFX.playChime('success');
    } catch (e: any) {
      setSignError(e.message);
    } finally {
      setSigning(false);
    }
  };

  const exportCsv = async () => {
    try {
      await api.exportBrief(brief.brief_id, 'csv');
    } catch (e: any) {
      setSignError(e.message);
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-black bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full uppercase tracking-wider">
            {brief.status}
          </span>
          <span className="text-[10px] font-bold text-slate-400">
            {brief.narrative_meta.rewritten_by_llm ? 'LLM-rephrased' : 'template'} | validation: {brief.narrative_meta.validation}
          </span>
        </div>
        <pre className="whitespace-pre-wrap font-sans text-sm text-slate-700 leading-relaxed">{brief.generated_narrative}</pre>
      </div>

      {brief.suggested_policy_actions.length > 0 && (
        <div>
          <p className="text-xs font-black text-slate-500 uppercase mb-2">Suggested Actions</p>
          <ul className="space-y-1.5">
            {brief.suggested_policy_actions.map((a, i) => (
              <li key={i} className="text-xs text-slate-600 flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
        <input
          value={officerName}
          onChange={(e) => setOfficerName(e.target.value)}
          placeholder="Officer name for sign-off"
          className="border border-slate-200 rounded-xl px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-300"
        />
        <button
          onClick={signOff}
          disabled={signing || signed}
          className="flex items-center gap-1.5 text-xs font-bold bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-3 py-2 rounded-xl transition-colors"
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          {signed ? 'Signed Off' : signing ? 'Signing...' : 'Sign Off'}
        </button>
        <button
          onClick={exportCsv}
          disabled={!signed}
          title={signed ? 'Export CSV' : 'Brief must be signed off before export'}
          className="flex items-center gap-1.5 text-xs font-bold bg-slate-100 hover:bg-slate-200 disabled:opacity-40 text-slate-700 px-3 py-2 rounded-xl transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          Export CSV
        </button>
        {signError && <p className="text-xs text-rose-600 font-bold">{signError}</p>}
      </div>
    </div>
  );
};

const BatchesTab: React.FC = () => {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOpportunities(DISTRICT)
      .then((data) => setOpportunities(data.opportunities || data || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-fadeIn text-center py-16 text-slate-500 font-bold"><RefreshCw className="w-6 h-6 animate-spin mx-auto mb-3" />Loading batches...</div>;
  if (error) return <div className="animate-fadeIn text-center py-16"><AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-3" /><p className="font-bold text-rose-700">{error}</p></div>;

  return (
    <div className="animate-fadeIn space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-900">Training Batch Directory</h2>
          <p className="text-sm text-slate-500">Worker-verified PM-AJAY sanctioned skilling batches across the district.</p>
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
                <th className="py-3 px-3">Batch & Qualification</th>
                <th className="py-3 px-3">Training Centre</th>
                <th className="py-3 px-3">Schedule</th>
                <th className="py-3 px-3">Capacity</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {opportunities.map((o: any) => (
                <tr key={o.id} className="hover:bg-slate-50 transition-colors cursor-pointer">
                  <td className="py-3 px-3">
                    <p className="font-black text-slate-900">{o.qualification_title || o.qualification?.title || o.id}</p>
                    <p className="text-xs text-slate-500">{o.block}</p>
                  </td>
                  <td className="py-3 px-3">
                    <p className="font-bold text-slate-800">{o.centre_or_employer_name}</p>
                    <p className="text-xs text-slate-500">{o.district}</p>
                  </td>
                  <td className="py-3 px-3">
                    <p className="font-bold text-slate-800">{o.batch_start_date} - {o.batch_end_date}</p>
                    <p className="text-xs text-slate-500">{o.type}</p>
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-full bg-slate-100 rounded-full h-2 max-w-[100px]">
                        <div
                          className={`h-2 rounded-full ${(o.available_seats / Math.max(o.total_seats, 1)) > 0.5 ? 'bg-emerald-500' : 'bg-amber-500'}`}
                          style={{ width: `${Math.min(100, (o.available_seats / Math.max(o.total_seats, 1)) * 100)}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-slate-700">{o.available_seats}/{o.total_seats}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase ${
                      o.availability === 'verified_open' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {o.availability || o.batch_status}
                    </span>
                  </td>
                </tr>
              ))}
              {opportunities.length === 0 && (
                <tr><td colSpan={5} className="py-8 text-center text-slate-400 font-bold">No opportunities found for this district.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const QualificationsTab: React.FC = () => {
  const [quals, setQuals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getQualifications()
      .then((data) => setQuals(data.qualifications || data || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-fadeIn text-center py-16 text-slate-500 font-bold"><RefreshCw className="w-6 h-6 animate-spin mx-auto mb-3" />Loading qualifications...</div>;
  if (error) return <div className="animate-fadeIn text-center py-16"><AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-3" /><p className="font-bold text-rose-700">{error}</p></div>;

  return (
    <div className="animate-fadeIn space-y-6">
      <div>
        <h2 className="text-lg font-black text-slate-900">National Qualification Register (NQR)</h2>
        <p className="text-sm text-slate-500">Approved NSQF job roles for PM-AJAY funding.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {quals.map((q: any) => (
          <div key={q.id || q.nqr_code} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-colors">
            <div className="flex items-start justify-between mb-2">
              <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">
                NSQF Level {q.nsqf_level}
              </span>
              <span className="text-xs font-bold text-indigo-700">{q.nqr_code}</span>
            </div>
            <h3 className="text-base font-black text-slate-900 mb-1">{q.title}</h3>
            <p className="text-sm text-slate-600 mb-4 line-clamp-2">{q.curriculum_summary}</p>
            <div className="flex gap-4 text-xs font-bold text-slate-500">
              <span>{q.duration_hours} Hours</span>
              <span>{q.sector}</span>
            </div>
          </div>
        ))}
        {quals.length === 0 && <p className="text-slate-400 font-bold col-span-2 text-center py-8">No qualifications found.</p>}
      </div>
    </div>
  );
};
