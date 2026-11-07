'use client';

import React, { useRef, useState } from 'react';
import {
  FileText,
  UploadCloud,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  BookOpen,
  Database,
  BarChart3,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import { DocumentItem } from '@/types';
import { uploadDocument, deleteDocument, runEvaluation } from '@/lib/api';

interface SidebarProps {
  documents: DocumentItem[];
  selectedDocIds: string[];
  onToggleDocSelect: (id: string) => void;
  onRefreshDocs: () => void;
  onOpenPdf: (docId: string, pageNumber: number) => void;
  onShowEvalResults: (results: any) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocIds,
  onToggleDocSelect,
  onRefreshDocs,
  onOpenPdf,
  onShowEvalResults,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF files are supported.');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setUploadError('File size exceeds 20MB limit.');
      return;
    }

    setUploadError(null);
    setIsUploading(true);
    try {
      await uploadDocument(file);
      onRefreshDocs();
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this document and all extracted graph entities?')) {
      try {
        await deleteDocument(docId);
        onRefreshDocs();
      } catch (err) {
        console.error('Delete error:', err);
      }
    }
  };

  const handleRunEval = async () => {
    setIsEvaluating(true);
    try {
      const res = await runEvaluation();
      onShowEvalResults(res);
    } catch (err) {
      alert('Evaluation failed to run.');
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <aside className="w-80 bg-white border-r border-[#E7E2D9] flex flex-col h-full select-none shadow-warm">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#E7E2D9] bg-[#FDFBF7] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-[#E4EDE6] border border-[#2C4C3B]/20 flex items-center justify-center text-[#2C4C3B] shadow-warm">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-serif font-bold text-sm tracking-tight text-[#292524]">
              DocuQuery Engine
            </h1>
            <p className="text-[11px] text-[#78716C] font-sans">Research Library • Graph-RAG</p>
          </div>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="p-3.5 border-b border-[#E7E2D9]">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={handleFileUpload}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="w-full py-3 px-3.5 rounded-2xl border-2 border-dashed border-[#D6CEBE] hover:border-[#2C4C3B] bg-[#FDFBF7] hover:bg-[#F5EFE6] text-xs font-sans font-medium text-[#292524] flex items-center justify-center space-x-2 transition-all disabled:opacity-50 shadow-warm"
        >
          {isUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin text-[#2C4C3B]" />
              <span className="text-[#2C4C3B] font-medium">Ingesting PDF...</span>
            </>
          ) : (
            <>
              <UploadCloud className="w-4 h-4 text-[#2C4C3B]" />
              <span>Add PDF Document (Max 20MB)</span>
            </>
          )}
        </button>
        {uploadError && (
          <div className="mt-2 text-[11px] text-rose-600 bg-rose-50 border border-rose-200 p-2 rounded-xl flex items-center space-x-1.5">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}
      </div>

      {/* Document Collections */}
      <div className="flex-1 overflow-y-auto p-3.5 space-y-2">
        <div className="flex items-center justify-between px-1 mb-1">
          <span className="font-serif text-xs font-semibold tracking-wide text-[#292524]">
            Library Shelf ({documents.length})
          </span>
          <button
            onClick={onRefreshDocs}
            className="text-[11px] text-[#2C4C3B] hover:text-[#8FA998] font-medium hover:underline transition-colors"
          >
            Refresh
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="p-5 text-center rounded-2xl bg-[#FDFBF7] border border-[#E7E2D9] text-[#78716C] text-xs leading-relaxed shadow-warm">
            <BookOpen className="w-6 h-6 mx-auto mb-2 text-[#8FA998] opacity-70" />
            <p className="font-medium text-[#292524] mb-1">Your library is empty.</p>
            <p className="text-[11px]">Drag and drop a PDF here to begin your research.</p>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                onClick={() => onToggleDocSelect(doc.id)}
                className={`p-3 rounded-2xl border transition-all cursor-pointer group flex items-start justify-between shadow-warm ${
                  isSelected
                    ? 'bg-[#E4EDE6] border-[#2C4C3B]/40 text-[#292524]'
                    : 'bg-white hover:bg-[#FDFBF7] border-[#E7E2D9] text-[#292524]'
                }`}
              >
                <div className="flex items-start space-x-2.5 overflow-hidden">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => onToggleDocSelect(doc.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="mt-0.5 rounded-md border-[#D6CEBE] text-[#2C4C3B] focus:ring-0 cursor-pointer accent-[#2C4C3B]"
                  />
                  <div className="overflow-hidden">
                    <p className="font-serif text-xs font-semibold truncate text-[#292524]">
                      {doc.title}
                    </p>
                    <div className="flex items-center space-x-2 mt-1 text-[11px] text-[#78716C]">
                      <span>{(doc.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                      <span>•</span>
                      {doc.status === 'COMPLETED' ? (
                        <span className="bg-[#D1FAE5] text-[#065F46] px-2 py-0.5 rounded-full text-[10px] font-medium flex items-center space-x-1">
                          <CheckCircle2 className="w-2.5 h-2.5" />
                          <span>{doc.total_pages} pgs</span>
                        </span>
                      ) : ['PROCESSING', 'PARSING', 'CHUNKING', 'EXTRACTING', 'INDEXING'].includes(doc.status) ? (
                        <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full text-[10px] font-medium flex items-center space-x-1" title={doc.current_step}>
                          <Loader2 className="w-2.5 h-2.5 animate-spin" />
                          <span>{doc.current_step || 'Ingesting'}</span>
                        </span>
                      ) : doc.status === 'FAILED' ? (
                        <span
                          className="bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full text-[10px] font-medium flex items-center space-x-1"
                          title={doc.error_message || 'Ingestion failed'}
                        >
                          <AlertCircle className="w-2.5 h-2.5" />
                          <span>Failed</span>
                        </span>
                      ) : (
                        <span className="bg-stone-100 text-stone-700 px-2 py-0.5 rounded-full text-[10px] font-medium flex items-center space-x-1">
                          <Clock className="w-2.5 h-2.5" />
                          <span>Pending</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {doc.status === 'COMPLETED' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpenPdf(doc.id, 1);
                      }}
                      title="Read PDF"
                      className="p-1 hover:text-[#2C4C3B] text-[#78716C] rounded-lg hover:bg-[#E4EDE6]"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    onClick={(e) => handleDelete(doc.id, e)}
                    title="Delete document"
                    className="p-1 hover:text-rose-600 text-[#78716C] rounded-lg hover:bg-rose-50"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Footer Controls & Benchmark */}
      <div className="p-3.5 border-t border-[#E7E2D9] space-y-2 bg-[#FDFBF7]">
        <button
          onClick={handleRunEval}
          disabled={isEvaluating}
          className="w-full py-2.5 px-3 rounded-2xl bg-[#2C4C3B] hover:bg-[#8FA998] text-white text-xs font-medium flex items-center justify-center space-x-2 transition-all disabled:opacity-50 shadow-warm"
        >
          {isEvaluating ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Running 15-Q Benchmark...</span>
            </>
          ) : (
            <>
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Run RAG Benchmark (15 Qs)</span>
            </>
          )}
        </button>

        <div className="flex items-center justify-between text-[11px] text-[#78716C] px-1 pt-1">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-[#065F46]"></span>
            <span>FastEmbed & FlashRank</span>
          </div>
          <div className="flex items-center space-x-1 text-[#78716C]">
            <Database className="w-3 h-3 text-[#2C4C3B]" />
            <span>KùzuDB Ready</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
