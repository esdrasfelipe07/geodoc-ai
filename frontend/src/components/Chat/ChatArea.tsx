import React, { useEffect, useRef } from 'react';
import { Bot, User, Sparkles, Compass, RotateCcw, AlertTriangle } from 'lucide-react';
import { ChatMessage } from '../../types';
import { CitationsList } from './CitationsList';

interface ChatAreaProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  error?: string | null;
  onSendSuggestion: (text: string) => void;
  onOpenPdf?: (docId: string, page: number, filename: string) => void;
  onRetry?: () => void;
}

const SUGGESTIONS = [
  'Qual a velocidade sísmica intervalar registrada na camada de sal?',
  'Quais são as características de porosidade e fluido do reservatório?',
  'Apresente um resumo executivo dos horizontes refletores identificados.',
  'Qual a profundidade estimada da formação superior e evaporitos?',
];

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  isStreaming,
  error,
  onSendSuggestion,
  onOpenPdf,
  onRetry,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const showSuggestions = messages.length <= 1;

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {messages.map((msg, index) => {
          const isUser = msg.role === 'user';
          const isLastMessage = index === messages.length - 1;

          return (
            <div
              key={msg.id}
              className={`flex items-start gap-3.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-white shadow-md ${
                  isUser
                    ? 'bg-slate-700'
                    : 'bg-gradient-to-tr from-emerald-600 to-teal-500'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] sm:max-w-[78%] rounded-2xl p-4 shadow-sm ${
                  isUser
                    ? 'bg-slate-800 text-slate-100 border border-slate-700/80 rounded-tr-none'
                    : 'bg-slate-850/90 text-slate-200 border border-slate-800 rounded-tl-none'
                }`}
              >
                {/* Header with role and timestamp */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
                  <span className="font-semibold">
                    {isUser ? 'Você' : 'GeoDoc AI'}
                  </span>
                  <span>{msg.timestamp}</span>
                </div>

                {/* Content */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                  {msg.isStreaming && (
                    <span className="inline-block w-2 h-4 ml-1 bg-emerald-400 animate-pulse align-middle" />
                  )}
                </div>

                {/* Citations if available */}
                {msg.sources && msg.sources.length > 0 && (
                  <CitationsList sources={msg.sources} onOpenPdf={onOpenPdf} />
                )}

                {/* Retry action for last assistant message if errored */}
                {!isUser && isLastMessage && error && onRetry && (
                  <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
                    <span className="text-amber-400 flex items-center space-x-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>Falha de comunicação temporária</span>
                    </span>
                    <button
                      onClick={onRetry}
                      disabled={isStreaming}
                      className="px-2.5 py-1 rounded bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center space-x-1.5 transition-colors"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Tentar novamente</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Geophysics Starter Prompts */}
        {showSuggestions && (
          <div className="mt-8 pt-6 border-t border-slate-800/80">
            <div className="flex items-center space-x-2 text-xs font-semibold text-slate-400 mb-3">
              <Compass className="w-4 h-4 text-emerald-400" />
              <span>Perguntas Rápidas de Geofísica & Engenharia:</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SUGGESTIONS.map((text, i) => (
                <button
                  key={i}
                  onClick={() => onSendSuggestion(text)}
                  disabled={isStreaming}
                  className="p-3 text-left rounded-xl bg-slate-850/60 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/40 text-xs text-slate-300 transition-all flex items-start space-x-2 disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{text}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
};
