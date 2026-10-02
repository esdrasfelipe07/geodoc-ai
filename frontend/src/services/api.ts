import {
  DocumentListResponse,
  DocumentUploadResponse,
  ChatRequest,
  ChatResponse,
  HealthStatus,
  SourceCitation
} from '../types';

const API_BASE = '/api/v1';

export const api = {
  /**
   * Health check to get system status and active LLM configuration
   */
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health/`);
    if (!res.ok) throw new Error('Falha ao obter status do sistema');
    return res.json();
  },

  /**
   * Fetch all indexed documents
   */
  async getDocuments(): Promise<DocumentListResponse> {
    const res = await fetch(`${API_BASE}/documents/`);
    if (!res.ok) throw new Error('Falha ao listar documentos');
    return res.json();
  },

  /**
   * Upload a PDF file for processing and vector indexing
   */
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Falha ao enviar documento');
    }

    return res.json();
  },

  /**
   * Delete document by ID
   */
  async deleteDocument(docId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Falha ao excluir documento');
  },

  /**
   * Standard JSON chat response (non-streaming fallback)
   */
  async sendChat(payload: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Erro ao consultar IA');
    }

    return res.json();
  },

  /**
   * Server-Sent Events (SSE) streaming chat with fallback resilience
   */
  async streamChat(
    payload: ChatRequest,
    callbacks: {
      onSources: (sources: SourceCitation[]) => void;
      onToken: (token: string) => void;
      onDone: () => void;
      onError: (error: Error) => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal,
      });

      if (!response.ok) {
        // Fallback to standard chat endpoint if streaming endpoint is unavailable
        console.warn('Streaming falhou, tentando fallback para endpoint REST convencional...');
        const fallbackRes = await this.sendChat(payload);
        if (fallbackRes.sources) callbacks.onSources(fallbackRes.sources);
        if (fallbackRes.answer) callbacks.onToken(fallbackRes.answer);
        callbacks.onDone();
        return;
      }

      if (!response.body) {
        throw new Error('ReadableStream não suportado pelo navegador.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const evtBlock of events) {
          if (!evtBlock.trim()) continue;

          let eventType = 'message';
          let eventData = '';

          const lines = evtBlock.split('\n');
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              eventData = line.slice(6).trim();
            }
          }

          if (eventType === 'sources') {
            try {
              const parsedSources: SourceCitation[] = JSON.parse(eventData);
              callbacks.onSources(parsedSources);
            } catch (e) {
              console.error('Erro ao decodificar fontes:', e);
            }
          } else if (eventType === 'delta') {
            try {
              const deltaObj = JSON.parse(eventData);
              if (deltaObj.token) {
                callbacks.onToken(deltaObj.token);
              }
            } catch (e) {
              console.error('Erro ao decodificar token delta:', e);
            }
          } else if (eventType === 'done') {
            callbacks.onDone();
            return;
          }
        }
      }

      callbacks.onDone();
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Stream abortado pelo usuário.');
        return;
      }
      callbacks.onError(err instanceof Error ? err : new Error(String(err)));
    }
  }
};
