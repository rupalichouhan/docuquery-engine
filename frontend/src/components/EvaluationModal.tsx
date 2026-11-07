'use client';

import React from 'react';
import { X, CheckCircle2, Award } from 'lucide-react';

interface EvaluationModalProps {
  results: any;
  onClose: () => void;
}

export const EvaluationModal: React.FC<EvaluationModalProps> = ({
  results,
  onClose,
}) => {
  if (!results) return null;

  return (
    <div className="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-sm flex items-center justify-center p-4 select-none font-sans">
      <div className="bg-white border border-[#E7E2D9] rounded-3xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-warm-lg animate-in fade-in zoom-in-95">
        {/* Header */}
        <div className="p-5 border-b border-[#E7E2D9] flex items-center justify-between bg-[#FDFBF7] rounded-t-3xl">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-[#E4EDE6] border border-[#2C4C3B]/20 text-[#2C4C3B]">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-serif font-bold text-base text-[#292524]">
                RAG Quantitative Benchmark Evaluation
              </h2>
              <p className="text-xs text-[#78716C] font-sans">
                15 Gold Standard Question-Answer-Context Benchmark Pairs
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#78716C] hover:text-[#292524] rounded-xl hover:bg-[#E4EDE6] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Aggregated Score Cards */}
        <div className="p-5 border-b border-[#E7E2D9] bg-white">
          <div className="grid grid-cols-4 gap-3.5 text-center">
            <div className="p-3.5 rounded-2xl bg-[#FDFBF7] border border-[#E7E2D9] shadow-warm">
              <span className="text-[10px] uppercase text-[#78716C] font-bold tracking-wider block mb-1">
                Context Precision
              </span>
              <span className="text-2xl font-bold font-mono text-[#2C4C3B]">
                {(results.average_context_precision * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#FDFBF7] border border-[#E7E2D9] shadow-warm">
              <span className="text-[10px] uppercase text-[#78716C] font-bold tracking-wider block mb-1">
                Faithfulness
              </span>
              <span className="text-2xl font-bold font-mono text-[#065F46]">
                {(results.average_faithfulness * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#FDFBF7] border border-[#E7E2D9] shadow-warm">
              <span className="text-[10px] uppercase text-[#78716C] font-bold tracking-wider block mb-1">
                Answer Relevance
              </span>
              <span className="text-2xl font-bold font-mono text-[#2C4C3B]">
                {(results.average_answer_relevance * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3.5 rounded-2xl bg-[#FDFBF7] border border-[#E7E2D9] shadow-warm">
              <span className="text-[10px] uppercase text-[#78716C] font-bold tracking-wider block mb-1">
                Formula Accuracy
              </span>
              <span className="text-2xl font-bold font-mono text-[#065F46]">
                {(results.math_verification_accuracy * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Detailed Breakdown List */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3 bg-[#FDFBF7]">
          <h4 className="font-serif text-xs font-bold text-[#292524] uppercase tracking-wider mb-2">
            Per-Question Benchmark Validation
          </h4>
          {results.benchmark_results?.map((item: any, i: number) => (
            <div
              key={i}
              className="p-3.5 rounded-2xl bg-white border border-[#E7E2D9] text-xs space-y-1.5 shadow-warm"
            >
              <div className="flex items-start justify-between">
                <span className="font-serif font-semibold text-[#292524]">
                  {i + 1}. {item.question}
                </span>
                <div className="flex items-center space-x-2 font-mono text-[11px] flex-shrink-0 ml-3">
                  <span className="text-[#2C4C3B] font-bold">Prec: {item.precision}</span>
                  <span className="text-[#065F46] font-bold">Faith: {item.faithfulness}</span>
                </div>
              </div>
              <p className="text-[11px] text-[#78716C] line-clamp-2">
                {item.generated_answer}
              </p>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E7E2D9] bg-[#FDFBF7] flex justify-end rounded-b-3xl">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-2xl bg-[#2C4C3B] hover:bg-[#8FA998] text-white text-xs font-medium transition-all shadow-warm"
          >
            Close Evaluation
          </button>
        </div>
      </div>
    </div>
  );
};
