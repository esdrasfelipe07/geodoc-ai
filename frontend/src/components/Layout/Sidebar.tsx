import React, { useRef } from 'react';
import {
  FileText,
  UploadCloud,
  Trash2,
  FolderOpen,
  Filter,
  Loader2,
  AlertCircle,
  Eye
} from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface SidebarProps {
  documents: DocumentMetadata[];
  selectedDocId: string | null;
  onSelectDoc: (docId: string | null) => void;
  onUpload: (file: File) => Promise<any>;
  onDelete: (docId: string) => Promise<void>;
  onViewPdf?: (docId: string, filename: string) => void;
  isUploading: boolean;
  error: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onUpload,
  onDelete,
  onViewPdf,
  isUploading,
  error
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      onUpload(file);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/60 flex flex-col h-[calc(100vh-4rem)]">
      {/* Upload Zone */}
      <div className="p-4 border-b border-slate-800">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center justify-between">
          <span>Relatórios & Amostras</span>
          <span className="text-emerald-400 font-mono text-xs">{documents.length}</span>
        </h2>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-all ${
            isUploading
              ? 'border-emerald-500/50 bg-emerald-500/5 cursor-wait'
              : 'border-slate-700/80 hover:border-emerald-500/60 hover:bg-slate-800/40 bg-slate-850/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFileChange}
            disabled={isUploading}
          />
          <div className="flex flex-col items-center">
            {isUploading ? (
              <>
                <Loader2 className="w-7 h-7 text-emerald-400 animate-spin mb-2" />
                <p className="text-xs font-medium text-emerald-400">Processando e vetorizando...</p>
                <p className="text-[10px] text-slate-500 mt-1">Extraindo páginas e gerando embeddings</p>
              </>
            ) : (
              <>
                <div className="w-9 h-9 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-2 group-hover:text-emerald-400">
                  <UploadCloud className="w-5 h-5 text-emerald-400" />
                </div>
                <p className="text-xs font-semibold text-slate-200">
                  Clique ou arraste um PDF
                </p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Estudos geológicos, sísmicos ou perfuração
                </p>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-3 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Scope / Filter Selector */}
      <div className="px-4 py-2 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-1.5 text-slate-400">
          <Filter className="w-3.5 h-3.5" />
          <span>Filtro de busca:</span>
        </div>
        <button
          onClick={() => onSelectDoc(null)}
          className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
            selectedDocId === null
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Todos
        </button>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {documents.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-slate-500">
            <FolderOpen className="w-10 h-10 mb-2 opacity-40 text-slate-400" />
            <p className="text-xs font-medium text-slate-400">Nenhum relatório carregado</p>
            <p className="text-[11px] mt-1 text-slate-500 max-w-[200px]">
              Faça upload de um arquivo PDF para iniciar as consultas contextuais via RAG.
            </p>
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.doc_id;
            return (
              <div
                key={doc.doc_id}
                onClick={() => onSelectDoc(isSelected ? null : doc.doc_id)}
                className={`group relative p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'border-emerald-500/50 bg-emerald-950/20 shadow-sm'
                    : 'border-slate-800 hover:border-slate-700 bg-slate-850/50 hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start space-x-2.5 overflow-hidden">
                    <FileText className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isSelected ? 'text-emerald-400' : 'text-slate-400'}`} />
                    <div className="overflow-hidden">
                      <p className="text-xs font-medium text-slate-200 truncate" title={doc.filename}>
                        {doc.filename}
                      </p>
                      <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-400">
                        <span>{doc.total_pages} {doc.total_pages === 1 ? 'pág' : 'págs'}</span>
                        <span>•</span>
                        <span>{doc.total_chunks} chunks</span>
                        <span>•</span>
                        <span>{formatFileSize(doc.file_size_bytes)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1">
                    {onViewPdf && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onViewPdf(doc.doc_id, doc.filename);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-emerald-400 text-slate-500 transition-all rounded hover:bg-slate-800"
                        title="Visualizar PDF"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    )}

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm(`Excluir ${doc.filename}?`)) {
                          onDelete(doc.doc_id);
                        }
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-500 transition-all rounded hover:bg-slate-800"
                      title="Excluir relatório"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
