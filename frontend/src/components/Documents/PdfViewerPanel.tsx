import React, { useState, useEffect } from 'react';
import { X, ExternalLink, FileText, ChevronLeft, ChevronRight, Eye } from 'lucide-react';

interface PdfViewerPanelProps {
  docId: string;
  filename: string;
  initialPage?: number;
  onClose: () => void;
}

export const PdfViewerPanel: React.FC<PdfViewerPanelProps> = ({
  docId,
  filename,
  initialPage = 1,
  onClose,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(initialPage);

  useEffect(() => {
    if (initialPage) {
      setCurrentPage(initialPage);
    }
  }, [initialPage, docId]);

  const pdfUrl = `/api/v1/documents/${docId}/content#page=${currentPage}&view=FitH`;

  return (
    <div className="w-full md:w-[480px] lg:w-[560px] xl:w-[640px] border-l border-slate-800 bg-slate-900/95 flex flex-col h-full z-30 shadow-2xl transition-all duration-200">
      {/* Viewer Header */}
      <div className="h-14 px-4 border-b border-slate-800 flex items-center justify-between bg-slate-900">
        <div className="flex items-center space-x-2.5 overflow-hidden">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
            <FileText className="w-4 h-4" />
          </div>
          <div className="overflow-hidden">
            <h3 className="text-xs font-semibold text-slate-200 truncate" title={filename}>
              {filename}
            </h3>
            <div className="flex items-center space-x-2 text-[10px] text-slate-400">
              <span>Página focada: <strong className="text-emerald-400">{currentPage}</strong></span>
              <span>•</span>
              <span className="text-slate-500">Visualizador Integrado</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Page quick switcher */}
          <div className="flex items-center space-x-1 bg-slate-800/80 rounded-lg p-1 border border-slate-700/60">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="p-1 hover:text-white text-slate-400 rounded"
              title="Página anterior"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="text-xs font-mono px-1.5 text-slate-300">{currentPage}</span>
            <button
              onClick={() => setCurrentPage((p) => p + 1)}
              className="p-1 hover:text-white text-slate-400 rounded"
              title="Próxima página"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Open raw PDF in new browser tab */}
          <a
            href={`/api/v1/documents/${docId}/content`}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-emerald-400 rounded-lg transition-colors"
            title="Abrir em aba separada"
          >
            <ExternalLink className="w-4 h-4" />
          </a>

          {/* Close Panel */}
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-red-400 rounded-lg transition-colors"
            title="Fechar visualizador"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* PDF Iframe Display */}
      <div className="flex-1 bg-slate-950 relative">
        <iframe
          key={`${docId}-${currentPage}`}
          src={pdfUrl}
          className="w-full h-full border-0 bg-slate-950"
          title={`Visualizador de ${filename}`}
        />
      </div>
    </div>
  );
};
