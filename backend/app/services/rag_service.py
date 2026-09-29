import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.core.config import settings
from app.models.schemas import SourceCitation, ChatResponse
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Manages vector storage and similarity search.
    Defaults to ChromaDB PersistentClient if available, with resilient fallback.
    """
    def __init__(self):
        self.persist_dir = settings.chroma_path
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.client = None
        self.collection = None
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB vector store successfully initialized.")
        except Exception as e:
            logger.warning(f"ChromaDB not available or initialization failed ({e}). Using in-memory fallback store.")
            self.client = None
            self.collection = None
            self._fallback_store: List[Dict[str, Any]] = []
            self._load_fallback_store()

    def _get_fallback_file(self) -> Path:
        return self.persist_dir / "fallback_vectors.json"

    def _load_fallback_store(self):
        fallback_file = self._get_fallback_file()
        if fallback_file.exists():
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    self._fallback_store = json.load(f)
            except Exception:
                self._fallback_store = []
        else:
            self._fallback_store = []

    def _save_fallback_store(self):
        fallback_file = self._get_fallback_file()
        try:
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(self._fallback_store, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist fallback store: {e}")

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        if self.collection:
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                return
            except Exception as e:
                logger.error(f"Error upserting to Chroma collection: {e}")

        # Fallback mechanism
        existing_ids = {item["id"] for item in self._fallback_store}
        for chunk in chunks:
            if chunk["id"] in existing_ids:
                self._fallback_store = [i for i in self._fallback_store if i["id"] != chunk["id"]]
            self._fallback_store.append(chunk)
        self._save_fallback_store()

    def delete_document_chunks(self, doc_id: str):
        if self.collection:
            try:
                self.collection.delete(where={"doc_id": doc_id})
                return
            except Exception as e:
                logger.error(f"Error deleting from Chroma: {e}")

        # Fallback
        self._fallback_store = [
            c for c in self._fallback_store
            if c.get("metadata", {}).get("doc_id") != doc_id
        ]
        self._save_fallback_store()

    def search_similar(
        self,
        query: str,
        top_k: int = 4,
        doc_id: Optional[str] = None
    ) -> List[SourceCitation]:
        where_filter = {"doc_id": doc_id} if doc_id else None

        if self.collection:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=where_filter
                )

                citations: List[SourceCitation] = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else []
                    distances = results["distances"][0] if "distances" in results and results["distances"] else []

                    for i, doc_text in enumerate(docs):
                        meta = metas[i] if i < len(metas) else {}
                        score = 1.0 - distances[i] if i < len(distances) else 0.85
                        citations.append(SourceCitation(
                            doc_id=meta.get("doc_id", "unknown"),
                            filename=meta.get("filename", "document.pdf"),
                            page=meta.get("page", 1),
                            chunk_index=meta.get("chunk_index", 0),
                            content=doc_text,
                            relevance_score=round(score, 3)
                        ))
                return citations
            except Exception as e:
                logger.warning(f"Chroma query failed ({e}). Using fallback search.")

        # Fallback keyword and lexical matching
        candidates = self._fallback_store
        if doc_id:
            candidates = [c for c in candidates if c.get("metadata", {}).get("doc_id") == doc_id]

        query_terms = set(query.lower().split())
        scored_chunks = []
        for c in candidates:
            text = c.get("text", "")
            matches = sum(1 for term in query_terms if term in text.lower())
            scored_chunks.append((matches, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_chunks[:top_k]

        citations = []
        for match_count, chunk in top_matches:
            meta = chunk.get("metadata", {})
            score = 0.5 + min(match_count * 0.1, 0.45)
            citations.append(SourceCitation(
                doc_id=meta.get("doc_id", "unknown"),
                filename=meta.get("filename", "relatorio.pdf"),
                page=meta.get("page", 1),
                chunk_index=meta.get("chunk_index", 0),
                content=chunk.get("text", ""),
                relevance_score=round(score, 3)
            ))
        return citations

    def count(self) -> int:
        if self.collection:
            try:
                return self.collection.count()
            except Exception:
                pass
        return len(self._fallback_store)


class RAGService:
    def __init__(self):
        self.vector_store = VectorStoreService()

    def build_system_prompt(self) -> str:
        return (
            "Você é o GeoDoc AI, um assistente especializado em análise técnica de dados geofísicos, "
            "geológicos e relatórios de engenharia da indústria de energia e mineração. "
            "Responda à pergunta do usuário com rigor técnico e clareza, baseando-se estritamente nas passagens "
            "fornecidas no contexto. "
            "Se a informação não estiver disponível nos trechos fornecidos, declare com clareza que o documento não "
            "contém essa informação específica, sem inventar dados."
        )

    def build_user_prompt(self, question: str, sources: List[SourceCitation]) -> str:
        if not sources:
            return (
                f"Pergunta do Usuário:\n{question}\n\n"
                "Aviso: Nenhum trecho relevante foi recuperado do banco de dados vetorial."
            )

        context_blocks = []
        for idx, src in enumerate(sources, start=1):
            context_blocks.append(
                f"[Documento {idx}: {src.filename} - Página {src.page}]\n{src.content}"
            )
        context_str = "\n\n---\n\n".join(context_blocks)

        return (
            f"Contexto Recuperado:\n{context_str}\n\n"
            f"Pergunta do Usuário:\n{question}\n\n"
            "Instruções: Elabore uma resposta técnica detalhada explicando os pontos solicitados, "
            "citando quando apropriado as páginas ou documentos de referência."
        )

    async def answer_question(
        self,
        question: str,
        doc_id: Optional[str] = None,
        top_k: int = 4
    ) -> ChatResponse:
        sources = self.vector_store.search_similar(query=question, top_k=top_k, doc_id=doc_id)
        system_instruction = self.build_system_prompt()
        prompt = self.build_user_prompt(question, sources)

        answer = await llm_service.generate_response(prompt, system_instruction)

        model_name = (
            settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai"
            else settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama"
            else "geodoc-mock-v1"
        )

        return ChatResponse(
            answer=answer,
            sources=sources,
            model=model_name,
            provider=settings.LLM_PROVIDER
        )

    async def answer_question_stream(
        self,
        question: str,
        doc_id: Optional[str] = None,
        top_k: int = 4
    ) -> AsyncGenerator[str, None]:
        """
        Yields Server-Sent Events (SSE) formatted events:
        1. 'sources': Array of retrieved document citations
        2. 'delta': Text token stream
        3. 'done': Stream finished flag
        """
        sources = self.vector_store.search_similar(query=question, top_k=top_k, doc_id=doc_id)
        system_instruction = self.build_system_prompt()
        prompt = self.build_user_prompt(question, sources)

        # 1. Send sources first
        sources_payload = [s.model_dump(mode="json") for s in sources]
        yield f"event: sources\ndata: {json.dumps(sources_payload)}\n\n"

        # 2. Stream tokens
        async for chunk in llm_service.generate_stream(prompt, system_instruction):
            token_payload = json.dumps({"token": chunk})
            yield f"event: delta\ndata: {token_payload}\n\n"

        # 3. Finished signal
        yield "event: done\ndata: {}\n\n"


rag_service = RAGService()
