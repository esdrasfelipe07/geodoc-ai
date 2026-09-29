import { useState, useCallback } from 'react';
import { ChatMessage, SourceCitation } from '../types';
import { api } from '../services/api';

export function useChat(selectedDocId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-msg',
      role: 'assistant',
      content:
        'Olá! Sou o assistente de inteligência artificial da **GeoDoc AI**. Você pode fazer upload de relatórios técnicos e geofísicos (dados sísmicos, poços, estratigrafia) e me fazer perguntas sobre eles. Como posso ajudar hoje?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (questionText: string) => {
      const trimmed = questionText.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `asst-${Date.now()}`;
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      // 1. Add user message
      const userMessage: ChatMessage = {
        id: userMsgId,
        role: 'user',
        content: trimmed,
        timestamp: nowStr,
      };

      // 2. Add placeholder assistant message
      const assistantPlaceholder: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        sources: [],
        isStreaming: true,
        timestamp: nowStr,
      };

      setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
      setIsStreaming(true);

      // 3. Initiate SSE Streaming
      let accumulatedText = '';
      let retrievedSources: SourceCitation[] = [];

      await api.streamChat(
        {
          question: trimmed,
          doc_id: selectedDocId,
          top_k: 4,
        },
        {
          onSources: (sources) => {
            retrievedSources = sources;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, sources: retrievedSources }
                  : msg
              )
            );
          },
          onToken: (token) => {
            accumulatedText += token;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, content: accumulatedText }
                  : msg
              )
            );
          },
          onDone: () => {
            setIsStreaming(false);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? { ...msg, isStreaming: false }
                  : msg
              )
            );
          },
          onError: (err) => {
            setIsStreaming(false);
            setError(err.message || 'Falha na comunicação com o assistente.');
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      content:
                        accumulatedText ||
                        '⚠️ Desculpe, ocorreu um erro ao gerar a resposta. Verifique a conexão com a API.',
                      isStreaming: false,
                    }
                  : msg
              )
            );
          },
        }
      );
    },
    [isStreaming, selectedDocId]
  );

  const clearChat = () => {
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'Histórico de conversa reiniciado. O que deseja consultar agora?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearChat,
  };
}
