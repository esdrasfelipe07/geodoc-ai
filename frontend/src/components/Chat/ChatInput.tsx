import React, { useState, useRef, useEffect } from 'react';
import { Send, CornerDownLeft, FileText, X } from 'lucide-react';
import { DocumentMetadata } from '../../types';

interface ChatInputProps {
  onSend: (message: string) => void;
  isStreaming: boolean;
  selectedDoc: DocumentMetadata | undefined;
  onClearDocFilter: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isStreaming,
  selectedDoc,
  onClearDocFilter,
}) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isStreaming) {
      textareaRef.current?.focus();
    }
  }, [isStreaming]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!text.trim() || isStreaming) return;
    onSend(text);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  return (
    <div className="p-4 bg-slate-900/90 border-t border-slate-800">
      <div className="max-w-4xl mx-auto">
        {/* Scoped Document Filter Pill */}
        {selectedDoc && (
          <div className="mb-2 flex items-center space-x-2">
            <span className="text-[11px] text-slate-400">Contexto limitado a:</span>
            <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs">
              <FileText className="w-3 h-3" />
              <span className="font-medium max-w-xs truncate">{selectedDoc.filename}</span>
              <button
                type="button"
                onClick={onClearDocFilter}
                className="hover:text-emerald-200"
                title="Remover filtro de documento"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="relative flex items-end bg-slate-800/80 rounded-2xl border border-slate-700/80 focus-within:border-emerald-500/80 focus-within:ring-1 focus-within:ring-emerald-500/40 shadow-lg transition-all">
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            placeholder={
              selectedDoc
                ? `Faça uma pergunta sobre ${selectedDoc.filename}...`
                : 'Faça uma pergunta técnica sobre os relatórios geofísicos...'
            }
            className="w-full resize-none py-3.5 pl-4 pr-12 text-sm bg-transparent text-slate-100 placeholder-slate-400 focus:outline-none max-h-32 disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={!text.trim() || isStreaming}
            className="absolute right-2 bottom-2 p-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-30 disabled:hover:bg-emerald-600 text-white transition-all shadow-md shadow-emerald-950/50"
            title="Enviar mensagem"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span>Use <strong>Enter</strong> para enviar e <strong>Shift + Enter</strong> para quebra de linha.</span>
          <span className="font-mono">RAG Ativo • ChromaDB</span>
        </div>
      </div>
    </div>
  );
};
