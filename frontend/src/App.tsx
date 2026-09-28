import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import ConsentScreen from './components/Beneficiary/ConsentScreen';
import VoiceInterview from './components/Beneficiary/VoiceInterview';

function Home() {
  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      <header className="text-center">
        <h1 className="text-4xl font-bold text-blue-900 mb-2">JeevanMitra 2.0</h1>
        <p className="text-gray-600 text-lg">A Verification-First, Multi-Layer Generative AI System for PM-AJAY Livelihood Matching</p>
      </header>

      <div className="grid md:grid-cols-3 gap-6">
        <Link to="/beneficiary/consent" className="block p-6 bg-white border border-gray-200 rounded-xl shadow hover:shadow-md transition-shadow">
          <h2 className="text-2xl font-semibold mb-3 text-blue-700">Beneficiary Flow</h2>
          <p className="text-gray-600">Voice Interview, Profile Confirmation, and Grounded Recommendations.</p>
        </Link>

        <Link to="/field-worker" className="block p-6 bg-white border border-gray-200 rounded-xl shadow hover:shadow-md transition-shadow">
          <h2 className="text-2xl font-semibold mb-3 text-teal-700">Field Worker Portal</h2>
          <p className="text-gray-600">Review flagged cases, correct transcripts, verify batch availability.</p>
        </Link>

        <Link to="/district-planner" className="block p-6 bg-white border border-gray-200 rounded-xl shadow hover:shadow-md transition-shadow">
          <h2 className="text-2xl font-semibold mb-3 text-purple-700">District Planning Console</h2>
          <p className="text-gray-600">View real-time supply-gap matrices and generated narrative briefs.</p>
        </Link>
      </div>
    </div>
  );
}

function FieldWorkerPortal() {
  return (
    <div className="p-8">
      <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Home</Link>
      <h1 className="text-3xl font-bold mb-4">Field Worker Portal</h1>
      <div className="bg-white p-6 rounded shadow">
        <p className="text-gray-600">Case Review Dashboard</p>
      </div>
    </div>
  );
}

function DistrictPlannerConsole() {
  return (
    <div className="p-8">
      <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Home</Link>
      <h1 className="text-3xl font-bold mb-4">District Planning Console</h1>
      <div className="bg-white p-6 rounded shadow">
        <p className="text-gray-600">Demand vs Supply Metrics</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/beneficiary/consent" element={<ConsentScreen />} />
        <Route path="/beneficiary/interview" element={<VoiceInterview />} />
        <Route path="/field-worker" element={<FieldWorkerPortal />} />
        <Route path="/district-planner" element={<DistrictPlannerConsole />} />
      </Routes>
    </div>
  );
}

export default App;
