import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { SourceCitation } from '../../types';

interface CitationsListProps {
  sources: SourceCitation[];
}

export const CitationsList: React.FC<CitationsListProps> = ({ sources }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/60">
      <div className="flex items-center space-x-1.5 text-xs font-semibold text-emerald-400 mb-2">
        <BookOpen className="w-3.5 h-3.5" />
        <span>Fontes Consultadas no Relatório ({sources.length}):</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {sources.map((src, idx) => {
          const isExpanded = expandedIndex === idx;
          return (
            <div
              key={`${src.doc_id}-${src.chunk_index}-${idx}`}
              className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition-all text-xs"
            >
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedIndex(isExpanded ? null : idx)}
              >
                <div className="flex items-center space-x-1.5 overflow-hidden">
                  <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <span className="font-medium text-slate-300 truncate" title={src.filename}>
                    {src.filename}
                  </span>
                </div>
                <div className="flex items-center space-x-1.5 flex-shrink-0 ml-2">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-emerald-400 font-mono">
                    Pág. {src.page}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                  )}
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
