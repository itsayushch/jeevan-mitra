import React, { useState } from 'react';
import { ArrowLeft, AlertCircle, Download, LayoutDashboard, CalendarDays, BookOpen, Plus } from 'lucide-react';
import { SoundFX } from '../../utils/speech';

interface DistrictPlannerProps {
  onBack: () => void;
}

export const DistrictPlannerConsole: React.FC<DistrictPlannerProps> = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'batches' | 'qualifications'>('dashboard');

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
            Claim 2: Planning Loop (Aggregate Demand vs Local Training Supply)
          </p>
        </div>
        <span className="ml-auto text-xs font-bold text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-full shadow-2xs">
          District: Moradabad | FY 2026-27
        </span>
      </div>

      <div className="flex gap-2 mb-6 border-b border-slate-200 pb-2">
        <button
          onClick={() => { SoundFX.playChime('click'); setActiveTab('dashboard'); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'dashboard'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          Demand & Supply
        </button>
        <button
          onClick={() => { SoundFX.playChime('click'); setActiveTab('batches'); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'batches'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <CalendarDays className="w-4 h-4" />
          Batch Management
        </button>
        <button
          onClick={() => { SoundFX.playChime('click'); setActiveTab('qualifications'); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'qualifications'
              ? 'bg-indigo-600 text-white shadow-sm'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Qualifications
        </button>
      </div>

      {activeTab === 'dashboard' && (
        <div className="animate-fadeIn">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Beneficiaries Interviewed</p>
              <p className="text-2xl font-black text-slate-900">1,840</p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Verified Matches</p>
              <p className="text-2xl font-black text-emerald-600">1,410</p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Planning Supply Gaps</p>
              <p className="text-2xl font-black text-rose-600">430</p>
            </div>
            <div className="bg-white p-4 rounded-2xl shadow-xs border border-slate-200">
              <p className="text-xs font-bold text-slate-500 mb-1">Sanctioned Budget</p>
              <p className="text-2xl font-black text-indigo-600">₹3.82 Cr</p>
            </div>
          </div>

          {/* Trade Aspiration vs Training Supply Table */}
          <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-black text-slate-900">
                  Trade Aspiration vs Training Supply
                </h2>
                <p className="text-xs text-slate-500">
                  Aggregated from voice interview transcripts across 8 blocks.
                </p>
              </div>
              <button
                onClick={() => SoundFX.playChime('click')}
                className="flex items-center gap-1.5 text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export AAP Data</span>
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-extrabold uppercase">
                    <th className="py-3 px-3">Trade Name</th>
                    <th className="py-3 px-3 text-right">Voice Demand</th>
                    <th className="py-3 px-3 text-right">Sanctioned Seats</th>
                    <th className="py-3 px-3">Supply Gap Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  <tr>
                    <td className="py-3.5 px-3 font-bold text-slate-900">Mushroom Cultivation & Processing</td>
                    <td className="py-3.5 px-3 text-right font-bold text-slate-900">460</td>
                    <td className="py-3.5 px-3 text-right text-slate-500">120</td>
                    <td className="py-3.5 px-3">
                      <span className="bg-rose-100 text-rose-800 px-2.5 py-1 rounded-full text-[10px] font-black">
                        -340 (High Deficit)
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3.5 px-3 font-bold text-slate-900">Solar Technician (Rooftop)</td>
                    <td className="py-3.5 px-3 text-right font-bold text-slate-900">420</td>
                    <td className="py-3.5 px-3 text-right text-slate-500">120</td>
                    <td className="py-3.5 px-3">
                      <span className="bg-rose-100 text-rose-800 px-2.5 py-1 rounded-full text-[10px] font-black">
                        -300 (Severe Deficit)
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3.5 px-3 font-bold text-slate-900">Apparel Making & Industrial Sewing</td>
                    <td className="py-3.5 px-3 text-right font-bold text-slate-900">510</td>
                    <td className="py-3.5 px-3 text-right text-slate-500">480</td>
                    <td className="py-3.5 px-3">
                      <span className="bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full text-[10px] font-black">
                        -30 (Balanced Supply)
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-3.5 px-3 font-bold text-slate-900">Retail Sales & Store Ops</td>
                    <td className="py-3.5 px-3 text-right font-bold text-slate-900">380</td>
                    <td className="py-3.5 px-3 text-right text-slate-500">200</td>
                    <td className="py-3.5 px-3">
                      <span className="bg-amber-100 text-amber-800 px-2.5 py-1 rounded-full text-[10px] font-black">
                        -180 (Waitlisted)
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Geographic Cluster Alert */}
          <div className="bg-indigo-50 border border-indigo-200 p-6 rounded-3xl flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-black text-indigo-950 mb-1">
                  Geographic Cluster Recommendation: Block Bahjoi
                </h3>
                <p className="text-xs text-indigo-900 leading-relaxed">
                  180 SC youth requested Agro-processing & Mushroom farming, but nearest training centre is 42 km away. Recommended: Deploy Mobile Skilling Unit or sanction new batch at Bahjoi Block Panchayat.
                </p>
              </div>
            </div>

            <button
              onClick={() => SoundFX.playChime('success')}
              className="bg-indigo-700 hover:bg-indigo-800 text-white font-bold text-xs py-3 px-5 rounded-2xl whitespace-nowrap shadow-sm transition-colors"
            >
              Approve Mobile Unit
            </button>
          </div>
        </div>
      )}

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
                    <th className="py-3 px-3">Batch ID & Qualification</th>
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
                  <tr className="hover:bg-slate-50 transition-colors cursor-pointer">
                    <td className="py-3 px-3">
                      <p className="font-black text-slate-900">BATCH-26-039</p>
                      <p className="text-xs text-slate-500">Retail Sales Associate (NSQF L3)</p>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-bold text-slate-800">Bahjoi Skill Hub</p>
                      <p className="text-xs text-slate-500">Bahjoi</p>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-bold text-slate-800">10 Sep 2026 - 10 Nov 2026</p>
                      <p className="text-xs text-slate-500">200 Hours</p>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-slate-100 rounded-full h-2 max-w-[100px]">
                          <div className="bg-indigo-500 h-2 rounded-full" style={{ width: '100%' }}></div>
                        </div>
                        <span className="text-xs font-bold text-slate-700">30/30</span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="bg-indigo-100 text-indigo-800 px-2.5 py-1 rounded-full text-[10px] font-black uppercase">
                        In Progress
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

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
                <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">NSQF Level 3</span>
                <span className="text-xs font-bold text-indigo-700">AGR/Q7803</span>
              </div>
              <h3 className="text-base font-black text-slate-900 mb-1">Mushroom Grower</h3>
              <p className="text-sm text-slate-600 mb-4 line-clamp-2">Cultivation of mushrooms under controlled conditions, including preparation of compost, spawning, crop management and harvesting.</p>
              <div className="flex gap-4 text-xs font-bold text-slate-500">
                <span>🕒 200 Hours</span>
                <span>💼 Agriculture</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">NSQF Level 4</span>
                <span className="text-xs font-bold text-indigo-700">SGJ/Q0101</span>
              </div>
              <h3 className="text-base font-black text-slate-900 mb-1">Solar PV Installer (Suryamitra)</h3>
              <p className="text-sm text-slate-600 mb-4 line-clamp-2">Installs, tests, and commissions solar PV plants while ensuring compliance with safety and environmental standards.</p>
              <div className="flex gap-4 text-xs font-bold text-slate-500">
                <span>🕒 400 Hours</span>
                <span>💼 Green Jobs</span>
              </div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">NSQF Level 3</span>
                <span className="text-xs font-bold text-indigo-700">RAS/Q0104</span>
              </div>
              <h3 className="text-base font-black text-slate-900 mb-1">Retail Sales Associate</h3>
              <p className="text-sm text-slate-600 mb-4 line-clamp-2">Assists customers in making purchases, handles inventory, and maintains visual merchandising displays.</p>
              <div className="flex gap-4 text-xs font-bold text-slate-500">
                <span>🕒 280 Hours</span>
                <span>💼 Retail</span>
              </div>
            </div>
            
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 transition-colors">
              <div className="flex items-start justify-between mb-2">
                <span className="text-[10px] font-black bg-slate-100 text-slate-600 px-2 py-1 rounded uppercase tracking-wider">NSQF Level 4</span>
                <span className="text-xs font-bold text-indigo-700">AMH/Q0301</span>
              </div>
              <h3 className="text-base font-black text-slate-900 mb-1">Sewing Machine Operator</h3>
              <p className="text-sm text-slate-600 mb-4 line-clamp-2">Operates sewing machines to join pieces of fabric or garments, ensuring quality and meeting production targets.</p>
              <div className="flex gap-4 text-xs font-bold text-slate-500">
                <span>🕒 270 Hours</span>
                <span>💼 Apparel</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
