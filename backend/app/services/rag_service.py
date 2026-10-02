import json
import logging
import math
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.core.config import settings
from app.models.schemas import SourceCitation, ChatResponse
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class BM25Ranker:
    """
    Lightweight, high-performance BM25 ranking implementation.
    Standard parameters: k1=1.5, b=0.75.
    Provides robust lexical retrieval for technical codes, well IDs, and exact geological terms.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def rank(self, query: str, chunks: List[Dict[str, Any]], top_k: int = 4) -> List[tuple[float, Dict[str, Any]]]:
        if not chunks:
            return []

        query_tokens = [t.lower() for t in query.split() if len(t) > 1]
        if not query_tokens:
            return [(0.0, c) for c in chunks[:top_k]]

        N = len(chunks)
        tokenized_corpus = []
        doc_lengths = []

        for c in chunks:
            tokens = [t.lower() for t in c.get("text", "").split()]
            tokenized_corpus.append(tokens)
            doc_lengths.append(len(tokens))

        avg_dl = sum(doc_lengths) / max(N, 1)

        # Calculate Document Frequency (DF) for each query term
        df = Counter()
        for tokens in tokenized_corpus:
            unique_tokens = set(tokens)
            for qt in query_tokens:
                if qt in unique_tokens:
                    df[qt] += 1

        # Compute BM25 scores
        scores = []
        for idx, tokens in enumerate(tokenized_corpus):
            doc_len = doc_lengths[idx]
            token_counts = Counter(tokens)
            score = 0.0

            for qt in query_tokens:
                n = df[qt]
                if n == 0:
                    continue
                # IDF formula with floor clipping
                idf = math.log(((N - n + 0.5) / (n + 0.5)) + 1.0)
                freq = token_counts[qt]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / max(avg_dl, 1.0)))
                score += idf * (numerator / max(denominator, 1e-6))

            scores.append((score, chunks[idx]))

        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]


class VectorStoreService:
    """
    Manages vector storage and similarity search.
    Combines ChromaDB PersistentClient with BM25 ranking for hybrid lexical-semantic retrieval.
    """
    def __init__(self):
        self.persist_dir = settings.chroma_path
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self.client = None
        self.collection = None
        self.bm25 = BM25Ranker()
        self._fallback_store: List[Dict[str, Any]] = []
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB vector store inicializado com sucesso.")
        except Exception as e:
            logger.warning(f"ChromaDB indisponível ({e}). Ativando fallback em memória e disco com BM25.")
            self.client = None
            self.collection = None
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
            logger.error(f"Falha ao persistir fallback store: {e}")

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
                logger.error(f"Erro ao inserir chunks no ChromaDB: {e}")

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
                logger.error(f"Erro ao remover do ChromaDB: {e}")

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
                if citations:
                    return citations
            except Exception as e:
                logger.warning(f"Busca vetorial no Chroma falhou ({e}). Recorrendo ao BM25.")

        # BM25 Lexical Ranking fallback
        candidates = self._fallback_store
        if doc_id:
            candidates = [c for c in candidates if c.get("metadata", {}).get("doc_id") == doc_id]

        ranked_results = self.bm25.rank(query=query, chunks=candidates, top_k=top_k)

        citations = []
        for score, chunk in ranked_results:
            meta = chunk.get("metadata", {})
            normalized_score = min(0.95, 0.5 + score * 0.1) if score > 0 else 0.5
            citations.append(SourceCitation(
                doc_id=meta.get("doc_id", "unknown"),
                filename=meta.get("filename", "relatorio.pdf"),
                page=meta.get("page", 1),
                chunk_index=meta.get("chunk_index", 0),
                content=chunk.get("text", ""),
                relevance_score=round(normalized_score, 3)
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
