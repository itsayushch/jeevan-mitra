import React, { useState } from 'react';
import { Layers, ArrowRight, Sparkles, X } from 'lucide-react';
import type { Language, CareerNode } from '../../types';
import { careerPathwaysData } from '../../data/mockData';
import { SoundFX } from '../../utils/speech';

interface CareerPathwaysProps {
  language: Language;
}

export const CareerPathways: React.FC<CareerPathwaysProps> = ({ language }) => {
  const [selectedNode, setSelectedNode] = useState<CareerNode | null>(null);

  const retailNodes = careerPathwaysData.filter((n) => n.pathway === 'Retail');
  const agriNodes = careerPathwaysData.filter((n) => n.pathway === 'Agri');
  const enterpriseNodes = careerPathwaysData.filter((n) => n.pathway === 'Enterprise');

  const handleNodeClick = (node: CareerNode) => {
    SoundFX.playChime('click');
    setSelectedNode(node);
  };

  return (
    <div className="w-full max-w-[540px] mx-auto bg-[#fbf9f1] border border-amber-900/10 rounded-[36px] shadow-xl p-5 text-slate-800 flex flex-col justify-between min-h-[620px]">
      <div>
        {/* Top Header */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full">
              NSQF Level 1 to 10 Progression
            </span>
            <span className="text-[11px] font-bold text-slate-400">
              MoSJE GIA Architecture
            </span>
          </div>

          <h2 className="text-lg font-black text-slate-900 tracking-tight leading-tight">
            YOUR CAREER PATHWAY PROGRESSION
          </h2>
          <p className="text-xs font-semibold text-slate-500">
            {language === 'hi'
              ? 'वर्तमान कौशल से लेकर उच्च स्तरीय प्रबंधन तक का स्पष्ट रोडमैप'
              : 'Clear growth roadmap from initial skilling to enterprise leadership'}
          </p>
        </div>

        {/* Tree Container */}
        <div className="relative bg-white rounded-3xl p-4 border border-slate-200/90 shadow-sm space-y-4">
          {/* Root: Current Skills */}
          <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
            <div className="bg-slate-800 text-white text-[11px] font-extrabold px-3 py-1.5 rounded-xl shadow-xs flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              <span>Current Skills</span>
            </div>
            <span className="text-[11px] font-bold text-slate-400">
              Baseline: NSQF Level 2 (Agri & General)
            </span>
          </div>

          {/* Path 1: Retail */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-teal-800 bg-teal-50 px-2 py-0.5 rounded-md">
                Path 1: Retail
              </span>
              <span className="text-[10px] font-semibold text-slate-400">Services & FMCG</span>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {retailNodes.map((node, i) => (
                <React.Fragment key={node.id}>
                  <button
                    onClick={() => handleNodeClick(node)}
                    className="shrink-0 bg-slate-50 hover:bg-teal-50 border border-slate-200 hover:border-teal-400 rounded-xl p-2 text-left transition-all max-w-[125px] shadow-2xs group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[9px] font-bold text-teal-700 bg-teal-100/70 px-1 rounded">
                        {node.level}
                      </span>
                      <span className="text-xs">{node.avatar}</span>
                    </div>
                    <p className="text-[11px] font-extrabold text-slate-900 leading-tight group-hover:text-teal-900 truncate">
                      {node.title}
                    </p>
                    <p className="text-[9px] text-slate-400 font-semibold">{node.avgSalary}</p>
                  </button>
                  {i < retailNodes.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Path 2: Agri */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md">
                Path 2: Agri
              </span>
              <span className="text-[10px] font-semibold text-slate-400">Cold Chain & Exports</span>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {agriNodes.map((node, i) => (
                <React.Fragment key={node.id}>
                  <button
                    onClick={() => handleNodeClick(node)}
                    className="shrink-0 bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-400 rounded-xl p-2 text-left transition-all max-w-[125px] shadow-2xs group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[9px] font-bold text-emerald-700 bg-emerald-100/70 px-1 rounded">
                        {node.level}
                      </span>
                      <span className="text-xs">{node.avatar}</span>
                    </div>
                    <p className="text-[11px] font-extrabold text-slate-900 leading-tight group-hover:text-emerald-900 truncate">
                      {node.title}
                    </p>
                    <p className="text-[9px] text-slate-400 font-semibold">{node.avgSalary}</p>
                  </button>
                  {i < agriNodes.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Path 3: Enterprise */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-black uppercase tracking-wider text-amber-800 bg-amber-50 px-2 py-0.5 rounded-md">
                Path 3: Enterprise
              </span>
              <span className="text-[10px] font-semibold text-slate-400">Micro-Business to Scale</span>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
              {enterpriseNodes.map((node, i) => (
                <React.Fragment key={node.id}>
                  <button
                    onClick={() => handleNodeClick(node)}
                    className="shrink-0 bg-slate-50 hover:bg-amber-50 border border-slate-200 hover:border-amber-400 rounded-xl p-2 text-left transition-all max-w-[125px] shadow-2xs group"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[9px] font-bold text-amber-700 bg-amber-100/70 px-1 rounded">
                        {node.level}
                      </span>
                      <span className="text-xs">{node.avatar}</span>
                    </div>
                    <p className="text-[11px] font-extrabold text-slate-900 leading-tight group-hover:text-amber-900 truncate">
                      {node.title}
                    </p>
                    <p className="text-[9px] text-slate-400 font-semibold">{node.avgSalary}</p>
                  </button>
                  {i < enterpriseNodes.length - 1 && (
                    <ArrowRight className="w-3.5 h-3.5 text-slate-300 shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Node Detail Modal */}
      {selectedNode && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-5 max-w-sm w-full shadow-2xl border border-slate-200 animate-fadeIn">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2.5">
                <span className="text-3xl">{selectedNode.avatar}</span>
                <div>
                  <h3 className="text-base font-black text-slate-900">
                    {selectedNode.title}
                  </h3>
                  <span className="text-xs font-bold text-emerald-700">
                    {selectedNode.level} • {selectedNode.experienceYears}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 hover:bg-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-600 mb-3">{selectedNode.description}</p>

            <div className="space-y-2 mb-4 bg-slate-50 p-3 rounded-2xl border border-slate-100 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-500">Expected Earnings:</span>
                <span className="font-black text-emerald-700">{selectedNode.avgSalary}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-500">Certification:</span>
                <span className="font-bold text-slate-800">{selectedNode.certifications[0]}</span>
              </div>
              <div>
                <span className="font-bold text-slate-500 block mb-1">Key Skills:</span>
                <div className="flex flex-wrap gap-1">
                  {selectedNode.keySkills.map((sk, idx) => (
                    <span
                      key={idx}
                      className="bg-white text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md border border-slate-200"
                    >
                      {sk}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-2.5 mb-4 text-[11px] text-amber-900">
              <strong>Govt Scheme Linkage:</strong> {selectedNode.govtSupport}
            </div>

            <button
              onClick={() => setSelectedNode(null)}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-2.5 rounded-2xl text-xs"
            >
              Close Pathway
            </button>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="pt-3 border-t border-slate-200/60 flex items-center justify-between text-[11px] text-slate-500 font-medium">
        <span className="flex items-center gap-1 text-emerald-700 font-bold">
          <Sparkles className="w-3.5 h-3.5" /> Tap any role to view salary & certifications
        </span>
        <span>NCVET Aligned</span>
      </div>
    </div>
  );
};
