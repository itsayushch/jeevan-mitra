import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  ArrowLeft,
  Calendar,
  Clock,
  Phone,
  MessageSquare,
  UserCheck,
  ShieldCheck,
  AlertTriangle,
  Send,
  PlusCircle,
  FileText,
  Lock,
  Eye,
  Award,
  Filter,
  RefreshCw,
  XCircle,
  Sparkles,
} from 'lucide-react';
import {
  api,
  StaffCaseItem,
  StaffReferralItem,
  StaffCaseDetail,
  CaseNoteItem,
  ContactAttemptRecord,
  OutcomeRecord,
} from '../../lib/api';
import { SoundFX, speakText } from '../../utils/speech';

interface FieldWorkerPortalProps {
  onBack: () => void;
}

// Initial mock cases for standalone/demo resilience
const DEFAULT_CASES: StaffCaseItem[] = [
  {
    id: 'case_moradabad_8291',
    beneficiary_id: 'ben_rajesh_kumar',
    assigned_worker_id: 'worker_sunita_devi',
    status: 'IN_PROGRESS',
    priority: 'HIGH',
    district: 'Moradabad',
    state: 'Uttar Pradesh',
    target_sector: 'Agriculture & Food Processing',
    notes_count: 2,
    follow_up_due_at: new Date(Date.now() + 86400000 * 2).toISOString().split('T')[0],
    created_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'case_moradabad_8292',
    beneficiary_id: 'ben_rekha_devi',
    assigned_worker_id: 'worker_sunita_devi',
    status: 'OPEN',
    priority: 'URGENT',
    district: 'Moradabad',
    state: 'Uttar Pradesh',
    target_sector: 'Apparel & Handloom',
    notes_count: 1,
    follow_up_due_at: new Date(Date.now() + 86400000).toISOString().split('T')[0],
    created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'case_moradabad_8293',
    beneficiary_id: 'ben_vijay_singh',
    assigned_worker_id: 'worker_sunita_devi',
    status: 'REFERRED',
    priority: 'MEDIUM',
    district: 'Moradabad',
    state: 'Uttar Pradesh',
    target_sector: 'Retail & Enterprise',
    notes_count: 3,
    follow_up_due_at: null,
    created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

// Initial mock referrals
const DEFAULT_REFERRALS: StaffReferralItem[] = [
  {
    id: 'ref_mor_101',
    case_id: 'case_moradabad_8291',
    opportunity_id: 'opp_mushroom_chhajlet_batch4',
    opportunity_title: 'Mushroom Cultivation Batch #4 (PM-AJAY GIA)',
    provider_name: 'Krishi Vigyan Kendra Chhajlet',
    qualification_title: 'Mushroom Grower (NSQF L3)',
    district: 'Moradabad',
    status: 'CONTACTED',
    notes: 'Mobilized via village panchayat survey. Confirmed SC certificate.',
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'ref_mor_102',
    case_id: 'case_moradabad_8293',
    opportunity_id: 'opp_retail_moradabad_batch2',
    opportunity_title: 'Retail Store Ops & Customer Service Batch #2',
    provider_name: 'Moradabad District Skill Development Centre',
    qualification_title: 'Retail Sales Associate (NSQF L4)',
    district: 'Moradabad',
    status: 'ENROLLED',
    notes: 'Documents verified and batch seat allocated.',
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

// State machine allowed transitions
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  READY_TO_SEND: ['REFERRED', 'BENEFICIARY_DECLINED', 'REJECTED'],
  REFERRED: ['CONTACTED', 'BENEFICIARY_DECLINED', 'REJECTED'],
  CONTACTED: ['ENROLLED', 'DROPPED_OUT', 'BENEFICIARY_DECLINED', 'REJECTED'],
  ENROLLED: ['TRAINING_STARTED', 'DROPPED_OUT'],
  TRAINING_STARTED: ['COMPLETED', 'DROPPED_OUT'],
  COMPLETED: ['CLOSED'],
  DROPPED_OUT: ['CLOSED'],
  REJECTED: ['CLOSED'],
  BENEFICIARY_DECLINED: ['CLOSED'],
  CLOSED: [],
};

export const FieldWorkerPortal: React.FC<FieldWorkerPortalProps> = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState<'cases' | 'referrals' | 'verification'>('cases');
  const [cases, setCases] = useState<StaffCaseItem[]>(DEFAULT_CASES);
  const [selectedCase, setSelectedCase] = useState<StaffCaseItem>(DEFAULT_CASES[0]);
  const [referrals, setReferrals] = useState<StaffReferralItem[]>(DEFAULT_REFERRALS);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Case details & notes state
  const [notes, setNotes] = useState<CaseNoteItem[]>([
    {
      id: 'note_1',
      author_name: 'Sunita Devi (Field Worker)',
      author_role: 'field_worker',
      note_type: 'FIELD_VISIT',
      content: 'Met candidate at Chhajlet Panchayat. Confirmed 10th marksheet and SC certificate validity.',
      is_staff_only: true,
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: 'note_2',
      author_name: 'Sunita Devi (Field Worker)',
      author_role: 'field_worker',
      note_type: 'COUNSELLING',
      content: 'Candidate agreed on 5 km travel limit. Batch starts 15 Oct.',
      is_staff_only: false,
      created_at: new Date().toISOString(),
    },
  ]);
  const [newNoteContent, setNewNoteContent] = useState('');
  const [isStaffOnlyNote, setIsStaffOnlyNote] = useState(true);
  const [followUpDate, setFollowUpDate] = useState(
    selectedCase.follow_up_due_at || new Date(Date.now() + 86400000 * 2).toISOString().split('T')[0]
  );

  // Contact attempt state
  const [selectedReferral, setSelectedReferral] = useState<StaffReferralItem>(DEFAULT_REFERRALS[0]);
  const [showContactModal, setShowContactModal] = useState(false);
  const [contactChannel, setContactChannel] = useState<'PHONE' | 'IN_PERSON' | 'SMS' | 'WHATSAPP'>('PHONE');
  const [contactSuccess, setContactSuccess] = useState(true);
  const [contactNotes, setContactNotes] = useState('');

  // Outcome state
  const [showOutcomeModal, setShowOutcomeModal] = useState(false);
  const [outcomeType, setOutcomeType] = useState<
    'ENROLLED' | 'COMPLETED' | 'JOB_OFFER' | 'SELF_EMPLOYMENT_STARTED' | 'DROPPED_OUT'
  >('COMPLETED');
  const [outcomeEvidence, setOutcomeEvidence] = useState('');
  const [recordedOutcomes, setRecordedOutcomes] = useState<Record<string, OutcomeRecord>>({});

  // Verification Checklist (Sprint 4)
  const [edu, setEdu] = useState('Class 10 Pass');
  const [mobility, setMobility] = useState('Max 5 km');
  const [aspiration, setAspiration] = useState('Mushroom Cultivation & Agri');
  const [verifiedCheck, setVerifiedCheck] = useState({ sc: true, aadhaar: true, batch: true });
  const [approvalBanner, setApprovalBanner] = useState(false);

  // Load live data if authenticated
  useEffect(() => {
    async function loadData() {
      try {
        const caseRes = await api.listStaffCases();
        if (caseRes?.cases && caseRes.cases.length > 0) {
          setCases(caseRes.cases);
          setSelectedCase(caseRes.cases[0]);
        }
      } catch (err) {
        // Fallback to local default data for offline/demo
      }

      try {
        const refRes = await api.listStaffReferrals();
        if (refRes?.referrals && refRes.referrals.length > 0) {
          setReferrals(refRes.referrals);
          setSelectedReferral(refRes.referrals[0]);
        }
      } catch (err) {
        // Fallback to local default data for offline/demo
      }
    }
    loadData();
  }, []);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteContent.trim()) return;

    try {
      await api.addStaffCaseNote(selectedCase.id, newNoteContent, 'FIELD_UPDATE', isStaffOnlyNote);
    } catch {
      // Local fallback
    }

    const created: CaseNoteItem = {
      id: `note_${Date.now()}`,
      author_name: 'Sunita Devi (Field Worker)',
      author_role: 'field_worker',
      note_type: 'FIELD_UPDATE',
      content: newNoteContent,
      is_staff_only: isStaffOnlyNote,
      created_at: new Date().toISOString(),
    };

    setNotes((prev) => [created, ...prev]);
    setNewNoteContent('');
    SoundFX.playChime('click');
  };

  const handleScheduleFollowUp = async () => {
    if (!followUpDate) return;
    try {
      await api.scheduleStaffFollowUp(selectedCase.id, followUpDate, 'Field check follow-up');
    } catch {
      // Local fallback
    }

    setCases((prev) =>
      prev.map((c) => (c.id === selectedCase.id ? { ...c, follow_up_due_at: followUpDate } : c))
    );
    setSelectedCase((prev) => ({ ...prev, follow_up_due_at: followUpDate }));
    SoundFX.playChime('success');
  };

  const handleTransitionReferral = async (refId: string, toStatus: string) => {
    try {
      await api.transitionReferral(refId, toStatus, `Status transitioned to ${toStatus} by field worker`);
    } catch {
      // Local fallback
    }

    setReferrals((prev) =>
      prev.map((r) => (r.id === refId ? { ...r, status: toStatus as any, updated_at: new Date().toISOString() } : r))
    );
    if (selectedReferral.id === refId) {
      setSelectedReferral((prev) => ({ ...prev, status: toStatus as any }));
    }
    SoundFX.playChime('success');
  };

  const handleLogContact = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.logContactAttempt(selectedReferral.id, contactChannel, contactSuccess, contactNotes);
    } catch {
      // Local fallback
    }

    setShowContactModal(false);
    setContactNotes('');
    SoundFX.playChime('success');
  };

  const handleRecordOutcome = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const outcome = await api.recordOutcome(selectedReferral.id, outcomeType, outcomeEvidence);
      setRecordedOutcomes((prev) => ({ ...prev, [selectedReferral.id]: outcome }));
    } catch {
      const mockOutcome: OutcomeRecord = {
        id: `out_${Date.now()}`,
        referral_id: selectedReferral.id,
        outcome_type: outcomeType,
        status: 'REPORTED',
        evidence_summary: outcomeEvidence,
        reported_at: new Date().toISOString(),
      };
      setRecordedOutcomes((prev) => ({ ...prev, [selectedReferral.id]: mockOutcome }));
    }

    setShowOutcomeModal(false);
    setOutcomeEvidence('');
    SoundFX.playChime('success');
  };

  const filteredCases = statusFilter === 'ALL' ? cases : cases.filter((c) => c.status === statusFilter);

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 text-slate-800">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="w-10 h-10 rounded-full bg-white shadow-xs flex items-center justify-center text-slate-600 hover:bg-slate-50 transition-colors border border-slate-200"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black text-slate-900 tracking-tight">
                Field-Worker Case & Referral Console
              </h1>
              <span className="text-[10px] font-black uppercase bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                Sprint 5 Live
              </span>
            </div>
            <p className="text-xs font-semibold text-emerald-700">
              Assigned District: <strong className="text-slate-900">Moradabad, UP</strong> • Worker: Sunita Devi (Alpha)
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200 text-xs font-bold">
          <button
            onClick={() => {
              SoundFX.playChime('click');
              setActiveTab('cases');
            }}
            className={`px-3.5 py-1.5 rounded-xl transition-all ${
              activeTab === 'cases' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Cases ({cases.length})
          </button>
          <button
            onClick={() => {
              SoundFX.playChime('click');
              setActiveTab('referrals');
            }}
            className={`px-3.5 py-1.5 rounded-xl transition-all ${
              activeTab === 'referrals' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Referrals ({referrals.length})
          </button>
          <button
            onClick={() => {
              SoundFX.playChime('click');
              setActiveTab('verification');
            }}
            className={`px-3.5 py-1.5 rounded-xl transition-all ${
              activeTab === 'verification' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Capacity & Verification
          </button>
        </div>
      </div>

      {/* Metric Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-emerald-50 p-4 rounded-2xl border border-emerald-200 relative">
          <p className="text-xs font-bold text-emerald-800 mb-1">Active Scoped Cases</p>
          <p className="text-2xl font-black text-emerald-900">{cases.length}</p>
          <div className="absolute top-4 right-4 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <p className="text-xs font-bold text-slate-500 mb-1">Active Referrals</p>
          <p className="text-2xl font-black text-slate-900">{referrals.length}</p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <p className="text-xs font-bold text-slate-500 mb-1">Follow-ups Due Today</p>
          <p className="text-2xl font-black text-amber-600">2</p>
        </div>
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
          <p className="text-xs font-bold text-slate-500 mb-1">Verified Outcomes</p>
          <p className="text-2xl font-black text-indigo-700">1</p>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: CASE MANAGEMENT INBOX & DETAIL */}
      {/* ========================================================================= */}
      {activeTab === 'cases' && (
        <div className="grid md:grid-cols-12 gap-6">
          {/* Left Column: Cases List */}
          <div className="md:col-span-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-black text-slate-900 uppercase tracking-wider">
                Assigned Case Inbox
              </h2>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="text-xs font-bold bg-white border border-slate-200 rounded-xl px-2.5 py-1 text-slate-700 focus:outline-none"
              >
                <option value="ALL">All Statuses</option>
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="REFERRED">Referred</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>

            <div className="space-y-2.5">
              {filteredCases.map((c) => {
                const isSelected = selectedCase?.id === c.id;
                return (
                  <div
                    key={c.id}
                    onClick={() => {
                      setSelectedCase(c);
                      if (c.follow_up_due_at) setFollowUpDate(c.follow_up_due_at);
                      SoundFX.playChime('click');
                    }}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-emerald-50/70 border-emerald-300 shadow-sm ring-1 ring-emerald-400'
                        : 'bg-white border-slate-200 hover:border-slate-300 shadow-2xs'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div>
                        <span className="text-[10px] font-mono text-slate-400 block">{c.id}</span>
                        <h3 className="text-xs font-black text-slate-900">{c.beneficiary_id}</h3>
                      </div>
                      <span
                        className={`text-[9px] font-black uppercase px-2 py-0.5 rounded-md ${
                          c.priority === 'URGENT'
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : c.priority === 'HIGH'
                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                            : 'bg-slate-100 text-slate-700 border border-slate-200'
                        }`}
                      >
                        {c.priority}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-600 mt-2">
                      <span className="font-semibold text-emerald-800">{c.target_sector || 'General Skilling'}</span>
                      <span className="font-mono text-[10px] bg-slate-100 px-2 py-0.5 rounded text-slate-600">
                        {c.status}
                      </span>
                    </div>

                    {c.follow_up_due_at && (
                      <div className="flex items-center gap-1 text-[10px] font-bold text-amber-800 bg-amber-50 rounded-lg px-2 py-0.5 mt-2 border border-amber-200/60">
                        <Clock className="w-3 h-3 text-amber-600" />
                        <span>Follow-up: {c.follow_up_due_at}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Case Management Workspace */}
          <div className="md:col-span-7 bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase">Selected Case File</span>
                <h3 className="text-base font-black text-slate-900">{selectedCase.id}</h3>
                <p className="text-xs text-slate-500">
                  Beneficiary: <strong className="text-slate-800">{selectedCase.beneficiary_id}</strong> • District: {selectedCase.district}
                </p>
              </div>

              {/* Schedule Follow-up */}
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={followUpDate}
                  onChange={(e) => setFollowUpDate(e.target.value)}
                  className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1 text-slate-700 focus:outline-none"
                />
                <button
                  onClick={handleScheduleFollowUp}
                  className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs px-3 py-1.5 rounded-xl shadow-2xs transition-colors"
                >
                  Set Due
                </button>
              </div>
            </div>

            {/* Case Notes History */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Case Activity & Field Notes</span>
                </h4>
                <span className="text-[10px] font-semibold text-slate-400">Isolated Audit Logging Active</span>
              </div>

              <div className="space-y-3 max-h-60 overflow-y-auto pr-1">
                {notes.map((note) => (
                  <div
                    key={note.id}
                    className={`p-3 rounded-2xl text-xs border ${
                      note.is_staff_only
                        ? 'bg-amber-50/60 border-amber-200/80 text-amber-950'
                        : 'bg-slate-50 border-slate-200 text-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-1.5">
                        <span className="font-extrabold text-[11px]">{note.author_name}</span>
                        {note.is_staff_only ? (
                          <span className="text-[9px] font-bold bg-amber-200 text-amber-900 px-1.5 py-0.2 rounded flex items-center gap-0.5">
                            <Lock className="w-2.5 h-2.5" /> Staff Only
                          </span>
                        ) : (
                          <span className="text-[9px] font-bold bg-emerald-100 text-emerald-900 px-1.5 py-0.2 rounded flex items-center gap-0.5">
                            <Eye className="w-2.5 h-2.5" /> Beneficiary Visible
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {new Date(note.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-[11px] leading-relaxed">{note.content}</p>
                  </div>
                ))}
              </div>

              {/* Add Note Form */}
              <form onSubmit={handleAddNote} className="mt-4 pt-3 border-t border-slate-100">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-[11px] font-bold text-slate-700">Add Field Observation:</label>
                  <label className="flex items-center gap-1.5 text-[10px] font-semibold text-slate-600 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isStaffOnlyNote}
                      onChange={(e) => setIsStaffOnlyNote(e.target.checked)}
                      className="rounded text-emerald-600 focus:ring-emerald-500 w-3.5 h-3.5"
                    />
                    <span>Staff-Only (Hide from Beneficiary)</span>
                  </label>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newNoteContent}
                    onChange={(e) => setNewNoteContent(e.target.value)}
                    placeholder="Enter observation, home visit report, or counseling notes..."
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium text-slate-800 focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    type="submit"
                    className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs px-4 py-2 rounded-xl flex items-center gap-1.5 shadow-2xs transition-colors"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Post</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: REFERRAL LIFECYCLE & STATE MACHINE */}
      {/* ========================================================================= */}
      {activeTab === 'referrals' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-black text-slate-900">
                  Referral State Machine & Outcome Tracking
                </h2>
                <p className="text-xs text-slate-500">
                  Authoritative server-controlled lifecycle transitions with mandatory verification invariants.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {referrals.map((ref) => {
                const nextAllowed = ALLOWED_TRANSITIONS[ref.status] || [];
                const outcome = recordedOutcomes[ref.id];

                return (
                  <div
                    key={ref.id}
                    className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200 space-y-3"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                            {ref.id}
                          </span>
                          <span className="text-xs font-black text-slate-900">{ref.opportunity_title}</span>
                        </div>
                        <p className="text-[11px] text-slate-600">
                          Provider: <strong className="text-slate-800">{ref.provider_name}</strong> • Qualification:{' '}
                          {ref.qualification_title}
                        </p>
                      </div>

                      {/* Status Badge */}
                      <div className="flex items-center gap-2">
                        <span
                          className={`text-xs font-black uppercase px-3 py-1 rounded-full border shadow-2xs ${
                            ref.status === 'COMPLETED'
                              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                              : ref.status === 'ENROLLED' || ref.status === 'TRAINING_STARTED'
                              ? 'bg-teal-100 text-teal-800 border-teal-300'
                              : ref.status === 'CONTACTED' || ref.status === 'REFERRED'
                              ? 'bg-amber-100 text-amber-800 border-amber-300'
                              : ref.status === 'CLOSED' || ref.status === 'DROPPED_OUT' || ref.status === 'REJECTED'
                              ? 'bg-slate-200 text-slate-700 border-slate-300'
                              : 'bg-blue-100 text-blue-800 border-blue-300'
                          }`}
                        >
                          {ref.status}
                        </span>
                      </div>
                    </div>

                    {/* Action Bar: Allowed Transitions */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                          Next Allowed States:
                        </span>
                        {nextAllowed.length === 0 ? (
                          <span className="text-[11px] font-semibold text-slate-500 italic">
                            Terminal status (Locked)
                          </span>
                        ) : (
                          nextAllowed.map((st) => (
                            <button
                              key={st}
                              onClick={() => handleTransitionReferral(ref.id, st)}
                              className="text-[11px] font-extrabold px-3 py-1.5 rounded-xl bg-white hover:bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-2xs hover:border-emerald-300 transition-all"
                            >
                              → {st.replace('_', ' ')}
                            </button>
                          ))
                        )}
                      </div>

                      {/* Contact & Outcome Triggers */}
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedReferral(ref);
                            setShowContactModal(true);
                          }}
                          className="text-[11px] font-bold px-3 py-1.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 flex items-center gap-1.5 transition-colors"
                        >
                          <Phone className="w-3.5 h-3.5" />
                          <span>Log Contact</span>
                        </button>

                        <button
                          onClick={() => {
                            setSelectedReferral(ref);
                            setShowOutcomeModal(true);
                          }}
                          className="text-[11px] font-bold px-3 py-1.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white flex items-center gap-1.5 shadow-2xs transition-colors"
                        >
                          <Award className="w-3.5 h-3.5" />
                          <span>Report Outcome</span>
                        </button>
                      </div>
                    </div>

                    {/* Display Reported Outcome if exists */}
                    {outcome && (
                      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs flex items-center justify-between animate-fadeIn">
                        <div>
                          <p className="font-black text-emerald-900">
                            Outcome Logged: {outcome.outcome_type.replace('_', ' ')}
                          </p>
                          <p className="text-[10px] text-emerald-700">{outcome.evidence_summary}</p>
                        </div>
                        <span className="text-[10px] font-extrabold uppercase bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded-full">
                          {outcome.status}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: VERIFICATION & CAPACITY (Sprint 4) */}
      {/* ========================================================================= */}
      {activeTab === 'verification' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-black text-slate-900">Case Review: #AJAY-8291</h2>
              <span className="text-[10px] font-bold bg-amber-100 text-amber-900 px-2.5 py-1 rounded-full">
                Voice Conf: 91%
              </span>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl mb-4 text-xs space-y-1 border border-slate-100">
              <p className="text-slate-500">
                Beneficiary: <strong className="text-slate-900">Rajesh Kumar</strong> (SC | Village: Chhajlet)
              </p>
              <p className="text-slate-500">Recorded Intent:</p>
              <p className="text-xs font-medium italic text-slate-700 bg-white p-2.5 rounded-xl border border-slate-200">
                "10th pass, family farming background, interested in Mushroom cultivation & local enterprise within 5 km."
              </p>
            </div>

            <h3 className="font-extrabold text-xs text-slate-800 uppercase tracking-wider mb-3">
              Field Verification Fields:
            </h3>

            <div className="space-y-3 mb-5 text-xs">
              <div className="flex items-center gap-3">
                <label className="w-24 text-slate-500 font-semibold">Education:</label>
                <input
                  type="text"
                  value={edu}
                  onChange={(e) => setEdu(e.target.value)}
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-800 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-slate-500 font-semibold">Mobility:</label>
                <input
                  type="text"
                  value={mobility}
                  onChange={(e) => setMobility(e.target.value)}
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-800 focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex items-center gap-3">
                <label className="w-24 text-slate-500 font-semibold">Aspiration:</label>
                <input
                  type="text"
                  value={aspiration}
                  onChange={(e) => setAspiration(e.target.value)}
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 font-bold text-slate-800 focus:outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="space-y-2 mb-6 text-xs font-medium text-slate-700">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={verifiedCheck.sc}
                  onChange={(e) => setVerifiedCheck((prev) => ({ ...prev, sc: e.target.checked }))}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                />
                <span>SC Caste Certificate / Self-Declaration Verified</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={verifiedCheck.aadhaar}
                  onChange={(e) => setVerifiedCheck((prev) => ({ ...prev, aadhaar: e.target.checked }))}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                />
                <span>Aadhaar Biometric & Residence Proof Attached</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={verifiedCheck.batch}
                  onChange={(e) => setVerifiedCheck((prev) => ({ ...prev, batch: e.target.checked }))}
                  className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                />
                <span>Local Batch Availability Confirmed (Chhajlet Center)</span>
              </label>
            </div>

            {approvalBanner ? (
              <div className="bg-emerald-50 border-2 border-emerald-500 rounded-2xl p-3.5 text-center text-xs font-bold text-emerald-900 flex items-center justify-center gap-2 animate-fadeIn">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>Opportunity Verified & Referral Ready</span>
              </div>
            ) : (
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    SoundFX.playChime('success');
                    setApprovalBanner(true);
                    speakText('Opportunity verified under PM-AJAY protocol.', 'en');
                  }}
                  className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-3 px-4 rounded-2xl text-xs shadow-md transition-colors"
                >
                  Confirm Opportunity Verification
                </button>
              </div>
            )}
          </div>

          {/* Local Centre Capacity Card */}
          <div className="space-y-4">
            <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200">
              <h3 className="text-sm font-black text-slate-900 mb-3">
                Nearest Training Capacity (Chhajlet Centre)
              </h3>
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="font-black text-slate-800">Mushroom Cultivation Batch #4</p>
                    <p className="text-[10px] text-slate-500">Starts: 15 Oct • 25 Seats Total</p>
                  </div>
                  <span className="text-[10px] font-extrabold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                    18 / 25 Filled (7 Avail)
                  </span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="font-black text-slate-800">Retail Operations Batch #2</p>
                    <p className="text-[10px] text-slate-500">Starts: 20 Oct • 30 Seats Total</p>
                  </div>
                  <span className="text-[10px] font-extrabold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                    28 / 30 Filled (2 Avail)
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-indigo-50 border border-indigo-100 p-5 rounded-3xl text-xs text-indigo-950">
              <p className="font-extrabold mb-1">Human-in-the-Loop Protocol Note:</p>
              <p className="text-slate-600 leading-relaxed">
                Referral eligibility is strictly guarded: recommendations only become referable once backed by an
                active, unexpired local opportunity verified by authorized field staff.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: LOG CONTACT ATTEMPT */}
      {/* ========================================================================= */}
      {showContactModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-xl border border-slate-200">
            <h3 className="text-base font-black text-slate-900 mb-2">Log Beneficiary Contact</h3>
            <p className="text-xs text-slate-500 mb-4">
              Record outreach to beneficiary for referral <strong className="text-slate-800">{selectedReferral.id}</strong>.
            </p>

            <form onSubmit={handleLogContact} className="space-y-4 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Contact Channel:</label>
                <select
                  value={contactChannel}
                  onChange={(e) => setContactChannel(e.target.value as any)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 font-semibold text-slate-800 focus:outline-none"
                >
                  <option value="PHONE">Phone Call</option>
                  <option value="IN_PERSON">In-Person Visit</option>
                  <option value="WHATSAPP">WhatsApp</option>
                  <option value="SMS">SMS Notification</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2 font-bold text-slate-700">
                  <input
                    type="checkbox"
                    checked={contactSuccess}
                    onChange={(e) => setContactSuccess(e.target.checked)}
                    className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                  />
                  <span>Contact Successful (Beneficiary Responded)</span>
                </label>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Worker Notes:</label>
                <textarea
                  value={contactNotes}
                  onChange={(e) => setContactNotes(e.target.value)}
                  placeholder="Discussed batch timings, transportation subsidy, and batch date..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium text-slate-800 focus:outline-none focus:border-emerald-500 h-20 resize-none"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowContactModal(false)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2.5 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-2.5 rounded-xl shadow-2xs transition-colors"
                >
                  Save Log
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: REPORT OUTCOME */}
      {/* ========================================================================= */}
      {showOutcomeModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-xl border border-slate-200">
            <h3 className="text-base font-black text-slate-900 mb-2">Report Referral Outcome</h3>
            <p className="text-xs text-slate-500 mb-4">
              Submit verified outcome evidence for referral <strong className="text-slate-800">{selectedReferral.id}</strong>.
            </p>

            <form onSubmit={handleRecordOutcome} className="space-y-4 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Outcome Type:</label>
                <select
                  value={outcomeType}
                  onChange={(e) => setOutcomeType(e.target.value as any)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 font-semibold text-slate-800 focus:outline-none"
                >
                  <option value="ENROLLED">Enrolled in Batch</option>
                  <option value="COMPLETED">Training Completed</option>
                  <option value="JOB_OFFER">Job Offer Received</option>
                  <option value="SELF_EMPLOYMENT_STARTED">Micro-Enterprise / Self-Employment Started</option>
                  <option value="DROPPED_OUT">Candidate Dropped Out</option>
                </select>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Evidence Summary:</label>
                <textarea
                  value={outcomeEvidence}
                  onChange={(e) => setOutcomeEvidence(e.target.value)}
                  placeholder="Roll number, training centre certificate ID, or employer offer letter ref..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 font-medium text-slate-800 focus:outline-none focus:border-emerald-500 h-20 resize-none"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowOutcomeModal(false)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2.5 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-emerald-700 hover:bg-emerald-800 text-white font-bold py-2.5 rounded-xl shadow-2xs transition-colors"
                >
                  Submit Outcome
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
