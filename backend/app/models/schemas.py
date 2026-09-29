from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==========================================
# Document Schemas
# ==========================================

class DocumentBase(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    file_size_bytes: int


class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    total_chunks: int
    uploaded_at: datetime
    file_size_bytes: int


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    total_documents: int
    documents: List[DocumentMetadata]


class DocumentDeleteResponse(BaseModel):
    message: str
    doc_id: str


# ==========================================
# Chat & RAG Schemas
# ==========================================

class SourceCitation(BaseModel):
    doc_id: str
    filename: str
    page: int
    chunk_index: int
    content: str
    relevance_score: Optional[float] = None


class MessageRole(str):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender ('user', 'assistant', 'system')")
    content: str = Field(..., description="Message text content")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question or query about geophysical documents")
    doc_id: Optional[str] = Field(None, description="Optional document ID to restrict search context")
    chat_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turns for contextual continuity")
    top_k: int = Field(default=4, ge=1, le=10, description="Number of most relevant context chunks to retrieve")


class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = []
    model: str
    provider: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==========================================
# System & Health Schemas
# ==========================================

class HealthResponse(BaseModel):
    status: str
    project: str
    environment: str
    llm_provider: str
    llm_model: str
    indexed_documents_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
