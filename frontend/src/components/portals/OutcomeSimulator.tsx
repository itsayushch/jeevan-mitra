import React, { useState } from 'react';
import { api } from '../../lib/api';

export const OutcomeSimulator: React.FC<{ referralId: string }> = ({ referralId }) => {
  const [status, setStatus] = useState('documents_verified');
  const [outcome, setOutcome] = useState('');
  const [loading, setLoading] = useState(false);

  const states = [
    'documents_verified',
    'enrolled',
    'in_progress',
    'completed',
    'dropped_out'
  ];

  const handleAdvance = async (nextState: string) => {
    setLoading(true);
    try {
      await api.updateReferralStatus(referralId, {
        status: nextState,
        outcome: nextState === 'completed' ? 'Successfully completed course' : outcome
      });
      setStatus(nextState);
    } catch (err: any) {
      alert(err.message || 'Failed to update state');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-200 mt-6">
      <h3 className="font-black text-slate-900 mb-4">Outcome Simulator (Counselor/Worker)</h3>
      <div className="flex gap-2 mb-4 overflow-x-auto">
        {states.map((s, idx) => {
          const isPast = states.indexOf(status) >= idx;
          const isCurrent = status === s;
          return (
            <div key={s} className="flex items-center gap-2">
              <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                isCurrent ? 'bg-indigo-600 text-white' :
                isPast ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-400'
              }`}>
                {s.replace('_', ' ').toUpperCase()}
              </div>
              {idx < states.length - 1 && <span className="text-slate-300">→</span>}
            </div>
          );
        })}
      </div>
      
      <div className="flex gap-2">
        {status === 'documents_verified' && (
          <button onClick={() => handleAdvance('enrolled')} disabled={loading} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm">
            Mark Enrolled
          </button>
        )}
        {status === 'enrolled' && (
          <button onClick={() => handleAdvance('in_progress')} disabled={loading} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm">
            Mark In Progress
          </button>
        )}
        {status === 'in_progress' && (
          <>
            <button onClick={() => handleAdvance('completed')} disabled={loading} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm">
              Mark Completed
            </button>
            <button onClick={() => handleAdvance('dropped_out')} disabled={loading} className="bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm">
              Mark Dropped Out
            </button>
          </>
        )}
        {(status === 'completed' || status === 'dropped_out') && (
          <p className="text-xs font-bold text-slate-500">Workflow Complete</p>
        )}
      </div>
    </div>
  );
};
