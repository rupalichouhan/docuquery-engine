'use client';

import React from 'react';
import { RAGMetrics, ContextChunk } from '@/types';
import { Activity, Clock, Zap, Target, Database, FileText } from 'lucide-react';

interface MetricsPanelProps {
  metrics?: RAGMetrics | null;
  contextChunks?: ContextChunk[];
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  metrics,
  contextChunks = [],
}) => {
  if (!metrics) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-[#78716C] bg-[#FDFBF7] select-none">
        <Activity className="w-12 h-12 mb-3 opacity-30 text-[#2C4C3B]" />
        <p className="font-serif font-semibold text-sm text-[#292524]">No Telemetry Recorded</p>
        <p className="text-xs text-[#78716C] max-w-xs mt-1.5 leading-relaxed">
          Retrieval latency, FlashRank cross-encoder scores, and vector/graph candidate counts will display here after you run a research query.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#FDFBF7] p-4 overflow-y-auto space-y-5 select-none font-sans">
      {/* Metric Cards Grid */}
      <div>
        <h3 className="font-serif text-xs font-bold text-[#292524] uppercase tracking-wider mb-3">
          Retrieval & Rerank Performance
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3.5 rounded-2xl bg-white border border-[#E7E2D9] shadow-warm">
            <div className="flex items-center space-x-1.5 text-[#78716C] text-xs mb-1">
              <Clock className="w-4 h-4 text-[#2C4C3B]" />
              <span>Total Latency</span>
            </div>
            <div className="text-xl font-mono font-bold text-[#292524]">
              {metrics.total_latency_ms} <span className="text-xs font-normal text-[#78716C]">ms</span>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-[#E7E2D9] shadow-warm">
            <div className="flex items-center space-x-1.5 text-[#78716C] text-xs mb-1">
              <Zap className="w-4 h-4 text-[#D97706]" />
              <span>FlashRank Time</span>
            </div>
            <div className="text-xl font-mono font-bold text-[#292524]">
              {metrics.rerank_latency_ms} <span className="text-xs font-normal text-[#78716C]">ms</span>
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-[#E7E2D9] shadow-warm">
            <div className="flex items-center space-x-1.5 text-[#78716C] text-xs mb-1">
              <Target className="w-4 h-4 text-[#065F46]" />
              <span>Vector Candidates</span>
            </div>
            <div className="text-xl font-mono font-bold text-[#292524]">
              {metrics.vector_candidates}
            </div>
          </div>

          <div className="p-3.5 rounded-2xl bg-white border border-[#E7E2D9] shadow-warm">
            <div className="flex items-center space-x-1.5 text-[#78716C] text-xs mb-1">
              <Database className="w-4 h-4 text-[#2C4C3B]" />
              <span>Graph Candidates</span>
            </div>
            <div className="text-xl font-mono font-bold text-[#292524]">
              {metrics.graph_candidates}
            </div>
          </div>
        </div>
      </div>

      {/* Injected Context Chunks Breakdown */}
      <div className="flex-1">
        <h3 className="font-serif text-xs font-bold text-[#292524] uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Injected Top-K Chunks ({contextChunks.length})</span>
          <span className="text-[11px] text-[#78716C] font-normal font-sans">Ranked by FlashRank</span>
        </h3>

        <div className="space-y-2.5">
          {contextChunks.map((chunk, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-2xl bg-white border border-[#E7E2D9] text-xs text-[#292524] space-y-2 shadow-warm"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-serif font-bold text-[#2C4C3B] flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5 text-[#2C4C3B]" />
                  <span>
                    {chunk.doc_title} • Page {chunk.page_number}
                  </span>
                </span>
                <span className="font-mono text-[#065F46] bg-[#D1FAE5] px-2 py-0.5 rounded-full text-[10px] font-bold">
                  Score: {chunk.rerank_score.toFixed(4)}
                </span>
              </div>
              <p className="line-clamp-3 text-[#78716C] text-[11px] leading-relaxed">
                {chunk.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
