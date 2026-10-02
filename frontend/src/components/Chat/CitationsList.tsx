import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText, Eye } from 'lucide-react';
import { SourceCitation } from '../../types';

interface CitationsListProps {
  sources: SourceCitation[];
  onOpenPdf?: (docId: string, page: number, filename: string) => void;
}

export const CitationsList: React.FC<CitationsListProps> = ({ sources, onOpenPdf }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/60">
      <div className="flex items-center justify-between text-xs font-semibold text-emerald-400 mb-2">
        <div className="flex items-center space-x-1.5">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Fontes Consultadas no Relatório ({sources.length}):</span>
        </div>
        <span className="text-[10px] text-slate-400 font-normal">Clique na página para visualizar no PDF</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {sources.map((src, idx) => {
          const isExpanded = expandedIndex === idx;
          return (
            <div
              key={`${src.doc_id}-${src.chunk_index}-${idx}`}
              className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all text-xs"
            >
              <div className="flex items-center justify-between">
                <div
                  className="flex items-center space-x-1.5 overflow-hidden cursor-pointer flex-1 mr-2"
                  onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                >
                  <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <span className="font-medium text-slate-300 truncate" title={src.filename}>
                    {src.filename}
                  </span>
                </div>

                <div className="flex items-center space-x-1.5 flex-shrink-0">
                  {/* Jump to page in viewer button */}
                  {onOpenPdf && (
                    <button
                      onClick={() => onOpenPdf(src.doc_id, src.page, src.filename)}
                      className="px-2 py-0.5 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-mono flex items-center space-x-1 transition-colors"
                      title={`Abrir página ${src.page} no visualizador`}
                    >
                      <Eye className="w-3 h-3" />
                      <span>Pág. {src.page}</span>
                    </button>
                  )}

                  <button
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="p-0.5 text-slate-400 hover:text-slate-200"
                    title={isExpanded ? 'Recolher trecho' : 'Expandir trecho'}
                  >
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="mt-2 pt-2 border-t border-slate-800 text-[11px] text-slate-400 leading-relaxed font-mono bg-slate-950/50 p-2 rounded">
                  <p className="whitespace-pre-wrap">{src.content}</p>
                  {src.relevance_score !== undefined && (
                    <div className="mt-1 text-[10px] text-slate-400 text-right">
                      Relevância: {(src.relevance_score * 100).toFixed(0)}%
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
