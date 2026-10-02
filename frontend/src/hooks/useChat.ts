import { useState, useCallback, useRef } from 'react';
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
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastQuestionRef = useRef<string>('');

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(
    async (questionText: string, isRetry: boolean = false) => {
      const trimmed = questionText.trim();
      if (!trimmed || isStreaming) return;

      lastQuestionRef.current = trimmed;
      setError(null);
      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `asst-${Date.now()}`;
      const nowStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      // Create new abort controller
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      // Add user message if not retrying an existing prompt
      if (!isRetry) {
        const userMessage: ChatMessage = {
          id: userMsgId,
          role: 'user',
          content: trimmed,
          timestamp: nowStr,
        };
        setMessages((prev) => [...prev, userMessage]);
      }

      // Add placeholder assistant message
      const assistantPlaceholder: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        sources: [],
        isStreaming: true,
        timestamp: nowStr,
      };

      setMessages((prev) => [...prev, assistantPlaceholder]);
      setIsStreaming(true);

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
            abortControllerRef.current = null;
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
            abortControllerRef.current = null;
            setError(err.message || 'Falha na comunicação com o assistente.');
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      content:
                        accumulatedText ||
                        '⚠️ Desculpe, ocorreu uma instabilidade na conexão com o modelo de IA. Você pode tentar novamente clicando no botão abaixo.',
                      isStreaming: false,
                    }
                  : msg
              )
            );
          },
        },
        signal
      );
    },
    [isStreaming, selectedDocId]
  );

  const retryLastMessage = useCallback(() => {
    if (lastQuestionRef.current) {
      sendMessage(lastQuestionRef.current, true);
    }
  }, [sendMessage]);

  const clearChat = () => {
    cancelStreaming();
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'Histórico de conversa reiniciado. O que deseja consultar agora?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setError(null);
  };

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    retryLastMessage,
    cancelStreaming,
    clearChat,
  };
}
