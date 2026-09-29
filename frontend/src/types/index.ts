export interface DocumentMetadata {
  doc_id: string;
  filename: string;
  total_pages: number;
  total_chunks: number;
  uploaded_at: string;
  file_size_bytes: number;
}

export interface DocumentListResponse {
  total_documents: number;
  documents: DocumentMetadata[];
}

export interface DocumentUploadResponse {
  message: string;
  document: DocumentMetadata;
}

export interface SourceCitation {
  doc_id: string;
  filename: string;
  page: number;
  chunk_index: number;
  content: string;
  relevance_score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  isStreaming?: boolean;
  timestamp: string;
}

export interface ChatRequest {
  question: string;
  doc_id?: string | null;
  top_k?: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  model: string;
  provider: string;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  project: string;
  environment: string;
  llm_provider: string;
  llm_model: string;
  indexed_documents_count: number;
  timestamp: string;
}
