'use client';

import React, { useState, useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { PdfViewer } from '@/components/PdfViewer';
import { GraphCanvas } from '@/components/GraphCanvas';
import { MetricsPanel } from '@/components/MetricsPanel';
import { EvaluationModal } from '@/components/EvaluationModal';
import { DocumentItem, ChatMessage, GraphData, RAGMetrics, ContextChunk } from '@/types';
import { fetchDocuments, executeQuery } from '@/lib/api';
import { FileText, Network, BarChart3, PanelRightClose, PanelRightOpen } from 'lucide-react';

export default function WorkspacePage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Right Panel Tabs
  const [activeTab, setActiveTab] = useState<'source' | 'graph' | 'metrics'>('source');
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(true);

  // Inspector States
  const [activePdfDocId, setActivePdfDocId] = useState<string | null>(null);
  const [activePdfPage, setActivePdfPage] = useState<number>(1);
  const [activeGraphData, setActiveGraphData] = useState<GraphData | null>(null);
  const [latestMetrics, setLatestMetrics] = useState<RAGMetrics | null>(null);
  const [latestContextChunks, setLatestContextChunks] = useState<ContextChunk[]>([]);

  // Benchmark Evaluation Modal
  const [evalResults, setEvalResults] = useState<any>(null);

  const loadDocuments = async () => {
    const docs = await fetchDocuments();
    setDocuments(docs);
  };

  useEffect(() => {
    loadDocuments();
    // Fast polling (2s) while documents are being ingested, relaxed (8s) when idle
    const hasActiveIngestion = documents.some(
      (d) => !['COMPLETED', 'FAILED'].includes(d.status)
    );
    const pollIntervalMs = hasActiveIngestion ? 2000 : 8000;

    const interval = setInterval(loadDocuments, pollIntervalMs);
    return () => clearInterval(interval);
  }, [documents]);

  const handleToggleDocSelect = (id: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((dId) => dId !== id) : [...prev, id]
    );
  };

  const handleCitationClick = (docId: string, pageNumber: number) => {
    setActivePdfDocId(docId);
    setActivePdfPage(pageNumber);
    setActiveTab('source');
    if (!isRightPanelOpen) setIsRightPanelOpen(true);
  };

  const handleOpenPdfFromSidebar = (docId: string, pageNumber: number) => {
    setActivePdfDocId(docId);
    setActivePdfPage(pageNumber);
    setActiveTab('source');
    if (!isRightPanelOpen) setIsRightPanelOpen(true);
  };

  const handleSendMessage = async (queryText: string, verifyMath: boolean) => {
    const userMessage: ChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await executeQuery(queryText, selectedDocIds, verifyMath);

      const assistantMessage: ChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        verification: response.verification,
        metrics: response.metrics,
        graph_subgraph: response.graph_subgraph,
        context_chunks: response.context_chunks,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Update Inspector Panel with query results
      if (response.graph_subgraph) {
        setActiveGraphData(response.graph_subgraph);
      }
      if (response.metrics) {
        setLatestMetrics(response.metrics);
      }
      if (response.context_chunks) {
        setLatestContextChunks(response.context_chunks);
      }
      if (response.citations && response.citations.length > 0) {
        const topCitation = response.citations[0];
        if (topCitation.doc_id) {
          setActivePdfDocId(topCitation.doc_id);
          setActivePdfPage(topCitation.page_number);
        }
      }
    } catch (err: any) {
      const errorMessage: ChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: `Error executing query: ${err.message || 'Please check backend logs.'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const activeDoc = documents.find((d) => d.id === activePdfDocId);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#FDFBF7] font-sans text-[#292524]">
      {/* 1. Left Navigation */}
      <Sidebar
        documents={documents}
        selectedDocIds={selectedDocIds}
        onToggleDocSelect={handleToggleDocSelect}
        onRefreshDocs={loadDocuments}
        onOpenPdf={handleOpenPdfFromSidebar}
        onShowEvalResults={(results) => setEvalResults(results)}
      />

      {/* 2. Main Research Workspace (Center Chat) */}
      <main className="flex-1 flex flex-col h-full min-w-0">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          selectedDocCount={selectedDocIds.length}
          onCitationClick={handleCitationClick}
        />
      </main>

      {/* 3. Right Inspector Panel (Collapsible Split-Screen with Tabs) */}
      {isRightPanelOpen ? (
        <aside className="w-[490px] border-l border-[#E7E2D9] bg-white flex flex-col h-full flex-shrink-0 transition-all shadow-warm">
          {/* Tab Selector Header */}
          <div className="h-14 border-b border-[#E7E2D9] px-3.5 flex items-center justify-between bg-[#FDFBF7]">
            <div className="flex items-center space-x-1.5">
              <button
                onClick={() => setActiveTab('source')}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all shadow-warm ${
                  activeTab === 'source'
                    ? 'bg-[#E4EDE6] text-[#2C4C3B] border border-[#2C4C3B]/20'
                    : 'text-[#78716C] hover:text-[#292524] hover:bg-white'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-[#2C4C3B]" />
                <span className="font-serif">Source PDF</span>
              </button>

              <button
                onClick={() => setActiveTab('graph')}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all shadow-warm ${
                  activeTab === 'graph'
                    ? 'bg-[#E4EDE6] text-[#2C4C3B] border border-[#2C4C3B]/20'
                    : 'text-[#78716C] hover:text-[#292524] hover:bg-white'
                }`}
              >
                <Network className="w-3.5 h-3.5 text-[#2C4C3B]" />
                <span className="font-serif">Knowledge Graph</span>
              </button>

              <button
                onClick={() => setActiveTab('metrics')}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium flex items-center space-x-1.5 transition-all shadow-warm ${
                  activeTab === 'metrics'
                    ? 'bg-[#E4EDE6] text-[#2C4C3B] border border-[#2C4C3B]/20'
                    : 'text-[#78716C] hover:text-[#292524] hover:bg-white'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5 text-[#2C4C3B]" />
                <span className="font-serif">Telemetry</span>
              </button>
            </div>

            <button
              onClick={() => setIsRightPanelOpen(false)}
              className="p-1.5 hover:bg-[#E4EDE6] rounded-xl text-[#78716C] hover:text-[#292524] transition-colors"
              title="Collapse Inspector"
            >
              <PanelRightClose className="w-4 h-4" />
            </button>
          </div>

          {/* Active Tab View */}
          <div className="flex-1 overflow-hidden bg-white">
            {activeTab === 'source' && (
              <PdfViewer
                documentId={activePdfDocId}
                documentTitle={activeDoc?.title}
                totalPages={activeDoc?.total_pages}
                initialPage={activePdfPage}
              />
            )}
            {activeTab === 'graph' && (
              <GraphCanvas graphData={activeGraphData} />
            )}
            {activeTab === 'metrics' && (
              <MetricsPanel
                metrics={latestMetrics}
                contextChunks={latestContextChunks}
              />
            )}
          </div>
        </aside>
      ) : (
        <button
          onClick={() => setIsRightPanelOpen(true)}
          className="absolute right-4 top-4 z-20 p-2.5 bg-white border border-[#E7E2D9] text-[#2C4C3B] hover:text-[#8FA998] rounded-xl shadow-warm transition-all"
          title="Open Inspector Panel"
        >
          <PanelRightOpen className="w-4 h-4" />
        </button>
      )}

      {/* Evaluation Modal */}
      {evalResults && (
        <EvaluationModal
          results={evalResults}
          onClose={() => setEvalResults(null)}
        />
      )}
    </div>
  );
}
