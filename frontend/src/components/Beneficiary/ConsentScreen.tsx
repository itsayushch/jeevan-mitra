import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, ShieldCheck, ArrowRight } from 'lucide-react';

export default function ConsentScreen() {
  const [agreed, setAgreed] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="max-w-2xl mx-auto mt-10 p-8 bg-white rounded-2xl shadow-sm border border-gray-100">
      <div className="flex justify-center mb-6">
        <div className="bg-blue-100 p-4 rounded-full">
          <ShieldCheck className="w-12 h-12 text-blue-600" />
        </div>
      </div>
      
      <h2 className="text-3xl font-bold text-center text-gray-800 mb-6">
        Welcome to JeevanMitra
      </h2>
      
      <div className="space-y-4 text-gray-600 mb-8 bg-gray-50 p-6 rounded-xl">
        <p>
          Namaste! I am JeevanMitra, your AI assistant to help you discover the best livelihood and skilling opportunities under the PM-AJAY scheme.
        </p>
        <p>
          We will have a simple voice conversation in Hindi to understand your skills, interests, and background.
        </p>
        <p className="font-medium text-gray-700">
          Please note:
        </p>
        <ul className="list-disc pl-5 space-y-2">
          <li>Your audio will be recorded and transcribed for processing.</li>
          <li>Your personal data will be kept secure and used only for livelihood matching.</li>
          <li>You can choose to stop the interview at any time.</li>
        </ul>
      </div>

      <label className="flex items-start space-x-3 mb-8 cursor-pointer p-4 border border-blue-100 rounded-lg bg-blue-50/50 hover:bg-blue-50 transition-colors">
        <input 
          type="checkbox" 
          checked={agreed} 
          onChange={(e) => setAgreed(e.target.checked)}
          className="mt-1 w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
        />
        <span className="text-gray-700 font-medium">
          I agree to the terms and consent to using my voice for the interview.
          (मुझे शर्तें मंजूर हैं और मैं वॉइस इंटरव्यू के लिए अपनी सहमति देता/देती हूँ।)
        </span>
      </label>

      <button
        disabled={!agreed}
        onClick={() => navigate('/beneficiary/interview')}
        className={`w-full flex items-center justify-center space-x-2 py-4 px-6 rounded-xl font-bold text-lg transition-all ${
          agreed 
            ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg shadow-blue-200' 
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        }`}
      >
        <Mic className="w-6 h-6" />
        <span>Start Voice Interview (शुरू करें)</span>
        <ArrowRight className="w-5 h-5 ml-2" />
      </button>
    </div>
  );
}
