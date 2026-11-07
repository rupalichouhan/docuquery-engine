'use client';

import React, { useState, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  FileText,
  Download,
  BookOpen,
  ExternalLink,
  RotateCcw,
} from 'lucide-react';
import { getDocumentPdfUrl } from '@/lib/api';

interface PdfViewerProps {
  documentId: string | null;
  documentTitle?: string;
  totalPages?: number;
  initialPage?: number;
}

export const PdfViewer: React.FC<PdfViewerProps> = ({
  documentId,
  documentTitle,
  totalPages,
  initialPage = 1,
}) => {
  const [pageNumber, setPageNumber] = useState<number>(initialPage);
  const [zoom, setZoom] = useState<number>(100);
  const [pageInput, setPageInput] = useState<string>(String(initialPage));

  useEffect(() => {
    if (initialPage) {
      setPageNumber(initialPage);
      setPageInput(String(initialPage));
    }
  }, [initialPage, documentId]);

  const handlePageJump = (e: React.FormEvent) => {
    e.preventDefault();
    const target = parseInt(pageInput, 10);
    if (!isNaN(target) && target >= 1 && (!totalPages || target <= totalPages)) {
      setPageNumber(target);
    } else {
      setPageInput(String(pageNumber));
    }
  };

  const handlePrevPage = () => {
    setPageNumber((p) => {
      const nextP = Math.max(1, p - 1);
      setPageInput(String(nextP));
      return nextP;
    });
  };

  const handleNextPage = () => {
    setPageNumber((p) => {
      const nextP = totalPages ? Math.min(totalPages, p + 1) : p + 1;
      setPageInput(String(nextP));
      return nextP;
    });
  };

  if (!documentId) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center text-[#78716C] bg-[#FDFBF7] select-none font-sans">
        <div className="w-14 h-14 rounded-2xl bg-[#E4EDE6] border border-[#2C4C3B]/20 flex items-center justify-center text-[#2C4C3B] mb-3 shadow-warm">
          <BookOpen className="w-7 h-7" />
        </div>
        <p className="font-serif font-bold text-base text-[#292524]">No Document Open</p>
        <p className="text-xs text-[#78716C] max-w-sm mt-1.5 leading-relaxed">
          Select a document from your library or click any inline citation chip in your research conversation to inspect the page here.
        </p>
      </div>
    );
  }

  const pdfUrl = getDocumentPdfUrl(documentId);

  return (
    <div className="h-full flex flex-col bg-[#FDFBF7] select-none font-sans">
      {/* Top Controls Toolbar */}
      <div className="h-14 border-b border-[#E7E2D9] px-4 flex items-center justify-between text-xs text-[#292524] bg-white shadow-warm">
        {/* Document Info */}
        <div className="flex items-center space-x-2.5 truncate max-w-[190px]">
          <div className="p-1.5 rounded-lg bg-[#E4EDE6] text-[#2C4C3B] flex-shrink-0">
            <FileText className="w-4 h-4" />
          </div>
          <div className="truncate">
            <span className="truncate block text-xs font-serif font-bold text-[#292524]">
              {documentTitle || 'Document'}
            </span>
            <span className="text-[10px] text-[#78716C] block">
              {totalPages ? `${totalPages} Pages Total` : 'Document Viewer'}
            </span>
          </div>
        </div>

        {/* Page Navigation & Jump */}
        <div className="flex items-center space-x-1.5 bg-[#FDFBF7] border border-[#E7E2D9] px-2 py-1 rounded-xl shadow-warm">
          <button
            onClick={handlePrevPage}
            disabled={pageNumber <= 1}
            className="p-1 hover:bg-[#E4EDE6] disabled:opacity-40 rounded-lg text-[#78716C] hover:text-[#292524] transition-colors"
            title="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <form onSubmit={handlePageJump} className="flex items-center space-x-1">
            <span className="text-[11px] text-[#78716C]">Page</span>
            <input
              type="text"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              onBlur={handlePageJump}
              className="w-8 text-center text-xs font-bold text-[#292524] bg-white border border-[#E7E2D9] rounded-md py-0.5 outline-none focus:border-[#2C4C3B]"
            />
            <span className="text-[11px] text-[#78716C]">
              of {totalPages || '—'}
            </span>
          </form>

          <button
            onClick={handleNextPage}
            disabled={totalPages ? pageNumber >= totalPages : false}
            className="p-1 hover:bg-[#E4EDE6] disabled:opacity-40 rounded-lg text-[#78716C] hover:text-[#292524] transition-colors"
            title="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Zoom & Safe Manual Download Controls */}
        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setZoom((z) => Math.max(50, z - 15))}
            className="p-1.5 hover:bg-[#E4EDE6] rounded-xl text-[#78716C] hover:text-[#292524] transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-[11px] font-mono text-[#78716C] min-w-[34px] text-center">
            {zoom}%
          </span>
          <button
            onClick={() => setZoom((z) => Math.min(200, z + 15))}
            className="p-1.5 hover:bg-[#E4EDE6] rounded-xl text-[#78716C] hover:text-[#292524] transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>

          <button
            onClick={() => setZoom(100)}
            className="p-1.5 hover:bg-[#E4EDE6] rounded-xl text-[#78716C] hover:text-[#292524] transition-colors"
            title="Reset zoom to 100%"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Explicit single download button only when user desires */}
          <a
            href={pdfUrl}
            download={documentTitle ? `${documentTitle}.pdf` : 'document.pdf'}
            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-xl bg-[#E4EDE6] hover:bg-[#2C4C3B] text-[#2C4C3B] hover:text-white text-[11px] font-medium transition-all shadow-warm ml-1"
            title="Download a copy of this PDF to your computer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </a>
        </div>
      </div>

      {/* Embedded Document Frame (Inline viewing without download triggers) */}
      <div className="flex-1 overflow-auto bg-[#F5EFE6] p-3 flex items-center justify-center">
        <iframe
          key={`${documentId}-${pageNumber}`}
          src={`${pdfUrl}#page=${pageNumber}&zoom=${zoom}&view=FitH&toolbar=0`}
          className="w-full h-full rounded-2xl bg-white border border-[#E7E2D9] shadow-warm"
          title={documentTitle || 'PDF Document Viewer'}
        />
      </div>
    </div>
  );
};
