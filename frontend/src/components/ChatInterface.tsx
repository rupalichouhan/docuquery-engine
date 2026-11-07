'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ChevronDown,
  ChevronUp,
  Calculator,
  ArrowRight,
  BookOpen,
} from 'lucide-react';
import { ChatMessage, Citation, VerificationBadge } from '@/types';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (query: string, verifyMath: boolean) => void;
  isLoading: boolean;
  selectedDocCount: number;
  onCitationClick: (docId: string, pageNumber: number) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSendMessage,
  isLoading,
  selectedDocCount,
  onCitationClick,
}) => {
  const [input, setInput] = useState('');
  const [verifyMath, setVerifyMath] = useState(true);
  const [expandedVerification, setExpandedVerification] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Dynamic greeting based on current hour
  const [greeting, setGreeting] = useState('Good morning, Rupali.');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 12) {
      setGreeting('Good morning, Rupali.');
    } else if (hour < 17) {
      setGreeting('Good afternoon, Rupali.');
    } else {
      setGreeting('Good evening, Rupali.');
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim(), verifyMath);
    setInput('');
  };

  const toggleVerification = (idxKey: string) => {
    setExpandedVerification((prev) => ({ ...prev, [idxKey]: !prev[idxKey] }));
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#FDFBF7] relative overflow-hidden font-sans">
      {/* Header Bar */}
      <div className="h-14 border-b border-[#E7E2D9] px-6 flex items-center justify-between bg-white/80 backdrop-blur-sm z-10 shadow-warm">
        <div className="flex items-center space-x-3">
          <span className="font-serif font-bold text-xs tracking-wide text-[#292524]">
            Research Workspace
          </span>
          <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#F0F4F1] border border-[#2C4C3B]/20 text-[#2C4C3B] font-medium">
            {selectedDocCount === 0
              ? 'All Documents (Global Library)'
              : `${selectedDocCount} Document${selectedDocCount > 1 ? 's' : ''} Selected`}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-xs text-[#78716C] cursor-pointer select-none bg-[#FDFBF7] border border-[#E7E2D9] px-3 py-1.5 rounded-xl shadow-warm hover:border-[#8FA998] transition-colors">
            <input
              type="checkbox"
              checked={verifyMath}
              onChange={(e) => setVerifyMath(e.target.checked)}
              className="rounded-md border-[#D6CEBE] text-[#2C4C3B] focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-[#2C4C3B]"
            />
            <span className="flex items-center space-x-1.5 text-[#292524] font-medium">
              <Calculator className="w-3.5 h-3.5 text-[#2C4C3B]" />
              <span>AST Formula Verification</span>
            </span>
          </label>
        </div>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto select-none py-8">
            <div className="w-14 h-14 rounded-2xl bg-[#E4EDE6] border border-[#2C4C3B]/20 flex items-center justify-center text-[#2C4C3B] mb-4 shadow-warm">
              <BookOpen className="w-7 h-7" />
            </div>

            {/* Dynamic Personalized Greeting */}
            <h2 className="font-serif text-2xl font-bold text-[#292524] mb-2">
              {greeting}
            </h2>
            <p className="font-serif text-sm text-[#78716C] italic mb-4">
              What are we researching today?
            </p>
            <p className="text-xs text-[#78716C] leading-relaxed mb-6 max-w-md">
              Ask nuanced questions across your uploaded documents. DocuQuery Engine retrieves
              dense vector passages, traverses knowledge graphs, and deterministically verifies arithmetic claims with an AST engine.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
              {[
                'What was the total revenue growth rate between 2023 and 2024?',
                'Explain the operating margin changes and verify calculations.',
                'Which entities are linked in the knowledge graph?',
                'Summarize the core technical architecture and trade-offs.',
              ].map((example, i) => (
                <button
                  key={i}
                  onClick={() => setInput(example)}
                  className="p-3.5 text-xs bg-white hover:bg-[#F5EFE6] border border-[#E7E2D9] hover:border-[#2C4C3B]/40 rounded-2xl text-[#292524] transition-all flex items-center justify-between group shadow-warm"
                >
                  <span className="line-clamp-2 font-medium">{example}</span>
                  <ArrowRight className="w-4 h-4 text-[#78716C] group-hover:text-[#2C4C3B] transition-colors flex-shrink-0 ml-2" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-2xl rounded-2xl p-5 text-xs leading-relaxed shadow-warm ${
                  msg.role === 'user'
                    ? 'bg-[#2C4C3B] text-white rounded-br-sm'
                    : 'bg-white border border-[#E7E2D9] text-[#292524] rounded-bl-sm'
                }`}
              >
                {/* Message Content */}
                <div className="whitespace-pre-wrap font-sans text-xs leading-relaxed">
                  {msg.content}
                </div>

                {/* Inline Citations List (Soft rounded pills in verified colors) */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3.5 border-t border-[#E7E2D9] space-y-2">
                    <div className="text-[10px] uppercase font-bold text-[#78716C] tracking-wider font-serif">
                      Grounding Citations ({msg.citations.length})
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {msg.citations.map((c, cIdx) => (
                        <button
                          key={cIdx}
                          onClick={() => c.doc_id && onCitationClick(c.doc_id, c.page_number)}
                          className="px-3 py-1 rounded-full bg-[#D1FAE5] hover:bg-[#A7F3D0] border border-[#A7F3D0]/60 text-[#065F46] text-[11px] font-medium flex items-center space-x-1.5 transition-all shadow-warm"
                          title="Click to jump to page in PDF"
                        >
                          <FileText className="w-3 h-3 text-[#065F46]" />
                          <span>
                            {c.doc_title.slice(0, 18)} • Page {c.page_number}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* AST Numerical Verification Badges */}
                {msg.verification && msg.verification.length > 0 && (
                  <div className="mt-4 pt-3.5 border-t border-[#E7E2D9] space-y-2.5">
                    <div className="text-[10px] uppercase font-bold text-[#78716C] tracking-wider flex items-center space-x-1.5 font-serif">
                      <Calculator className="w-3.5 h-3.5 text-[#065F46]" />
                      <span>Mathematical Verification</span>
                    </div>

                    {msg.verification.map((v, vIdx) => {
                      const vKey = `${idx}-${vIdx}`;
                      const isExpanded = !!expandedVerification[vKey];
                      return (
                        <div
                          key={vIdx}
                          className={`rounded-xl border p-3 transition-all text-xs shadow-warm ${
                            v.is_verified
                              ? 'bg-[#D1FAE5]/60 border-[#10B981]/40 text-[#065F46]'
                              : 'bg-amber-50 border-amber-300 text-amber-900'
                          }`}
                        >
                          <div
                            onClick={() => toggleVerification(vKey)}
                            className="flex items-center justify-between cursor-pointer"
                          >
                            <div className="flex items-center space-x-2">
                              {v.is_verified ? (
                                <CheckCircle2 className="w-4 h-4 text-[#065F46] flex-shrink-0" />
                              ) : (
                                <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0" />
                              )}
                              <span className="font-semibold bg-white/70 px-2 py-0.5 rounded-md border border-[#065F46]/20">
                                {v.is_verified ? 'Formula Verified' : 'Formula Discrepancy'}
                              </span>
                              <span className="font-medium">{v.claim}</span>
                            </div>
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5 opacity-60" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5 opacity-60" />
                            )}
                          </div>

                          {isExpanded && (
                            <div className="mt-2.5 pt-2 border-t border-[#065F46]/20 space-y-1.5 font-mono text-[11px]">
                              <div>
                                <span className="opacity-75 font-sans">Formula Evaluated: </span>
                                <span className="bg-white/80 px-1.5 py-0.5 rounded border border-[#065F46]/20 font-bold">
                                  {v.formula}
                                </span>
                              </div>
                              <div>
                                <span className="opacity-75 font-sans">Calculated Result: </span>
                                <span className="font-bold text-[#065F46] bg-white/90 px-1.5 py-0.5 rounded">
                                  {v.calculated_value}%
                                </span>
                                <span className="opacity-75 font-sans"> | Reported in Text: </span>
                                <span className="font-semibold">{v.claimed_value}%</span>
                              </div>
                              {v.evidence && (
                                <div className="mt-1.5">
                                  <span className="opacity-75 font-sans block mb-1">Source Table Data:</span>
                                  <pre className="p-2 rounded-xl bg-white border border-[#E7E2D9] text-[#292524] overflow-x-auto text-[10px]">
                                    {v.evidence}
                                  </pre>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Telemetry Footer */}
                {msg.metrics && (
                  <div className="mt-3 pt-2 border-t border-[#E7E2D9] text-[10px] text-[#78716C] flex items-center justify-between font-mono">
                    <span>Latency: {msg.metrics.total_latency_ms}ms (Rerank: {msg.metrics.rerank_latency_ms}ms)</span>
                    <span>Chunks Fused: {msg.metrics.context_chunks_used}</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Skeleton */}
        {isLoading && (
          <div className="flex flex-col items-start space-y-2 max-w-md">
            <div className="bg-white border border-[#E7E2D9] p-4 rounded-2xl rounded-bl-sm w-full space-y-2.5 shadow-warm animate-pulse">
              <div className="flex items-center space-x-2 text-[#2C4C3B] text-xs font-serif font-semibold">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
                <span>Consulting library & reranking evidence...</span>
              </div>
              <div className="h-2.5 bg-[#E4EDE6] rounded-full w-5/6"></div>
              <div className="h-2.5 bg-[#E4EDE6] rounded-full w-4/6"></div>
              <div className="h-2.5 bg-[#E4EDE6] rounded-full w-3/6"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="p-4 border-t border-[#E7E2D9] bg-white/90 backdrop-blur-md shadow-warm">
        <form onSubmit={handleSubmit} className="flex items-center space-x-2 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a technical or financial research question... (e.g. 'What was the Q3 revenue growth?')"
            disabled={isLoading}
            className="flex-1 bg-[#FDFBF7] border border-[#E7E2D9] focus:border-[#2C4C3B] rounded-2xl px-4 py-3 text-xs text-[#292524] placeholder-[#78716C] outline-none transition-all shadow-warm"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-5 py-3 bg-[#2C4C3B] hover:bg-[#8FA998] disabled:bg-[#E7E2D9] text-white disabled:text-[#78716C] rounded-2xl transition-all font-medium text-xs flex items-center space-x-2 flex-shrink-0 shadow-warm"
          >
            <span>Research</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
