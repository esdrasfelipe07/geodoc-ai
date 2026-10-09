# 🏛️ Arquitetura do Sistema — GeoDoc AI

Este documento detalha o funcionamento arquitetural do **GeoDoc AI**, cobrindo o fluxo de dados, pipeline de **RAG Híbrido (Retrieval-Augmented Generation)**, estratégias de ingestão documental com **PyMuPDF**, ranking léxico **BM25**, concorrência com **Gunicorn** e o visualizador integrado lado a lado.

---

## 1. Visão Geral da Arquitetura

O sistema é baseado em uma arquitetura de serviços desacoplada:
* **Frontend SPA (React 18 + TypeScript):** Interface rica com visualização de PDFs lado a lado, citações de fontes com salto de página e consumo de respostas em streaming contínuo (SSE).
* **Backend API (Python 3.11 / FastAPI + Gunicorn):** Processamento assíncrono com 4 workers Uvicorn, extração em blocos com PyMuPDF, geração de embeddings, persistência vetorial e orquestração de LLMs.
* **Mecanismo RAG Híbrido:** Armazenamento vetorial com **ChromaDB** (espaço HNSW por cosseno) combinado com ranking léxico **BM25** para termos literais e códigos de poço.

```mermaid
flowchart TD
    User([Usuário / Geofísico]) -->|Navegador| UI[Frontend React / Vite]
    
    subgraph Frontend [Camada de Apresentação]
        UI -->|EventSource / SSE Reader| ChatStream[Hook useChat & Streaming]
        UI -->|Multipart Upload| DocUploader[Hook useDocuments]
        UI -->|Visualização Inline| PDFViewer[Painel PdfViewerPanel]
    end
    
    subgraph Backend [Camada de Aplicação - FastAPI + Gunicorn]
        DocUploader -->|POST /documents/upload| PDFProcessor[Serviço de Documentos]
        ChatStream -->|POST /chat/stream| RAGOrchestrator[Serviço RAG Híbrido]
        PDFViewer -->|GET /documents/doc_id/content| ContentRouter[Endpoint de Streaming Binário]
        
        PDFProcessor -->|Extração Geométrica por Blocos| PyMuPDF[Parser PyMuPDF fitz]
        PyMuPDF -->|Divisão por Parágrafos e Seções| Chunker[Semantic Chunking]
        Chunker -->|Upsert Chunks & Metadados| ChromaDB[(ChromaDB Vector Store)]
        Chunker -->|Índice Invertido e Frequência| BM25[BM25 Lexical Ranker]
        
        RAGOrchestrator -->|Busca por Cosseno HNSW| ChromaDB
        RAGOrchestrator -->|Busca por Palavras-Chave Exatas| BM25
        ChromaDB -->|Score Híbrido RRF / Relevância| ContextBuilder[Construtor de Prompt Geofísico]
        BM25 -->|Identificadores de Poço / Métricas| ContextBuilder
        
        ContextBuilder -->|Prompt Enriquecido & Restritivo| LLMService[Provedor de LLM]
    end

    subgraph Models [Provedores de Inteligência Artificial]
        LLMService -->|API REST| OpenAI[OpenAI GPT-4o-mini]
        LLMService -->|Local REST| Ollama[Ollama Local / Llama3]
        LLMService -->|Zero-Dep| MockLLM[Mock Engine Resiliente]
    end

    LLMService -->|Chunk a Chunk via SSE| UI
```

---

## 2. Pipeline de Ingestão e Vetorização (RAG)

1. **Upload de Documentos:**
   - O usuário faz o upload de um relatório técnico em formato PDF (ex.: estudos sísmicos, dados de perfilagem ou relatórios de perfuração).
   - O arquivo é salvo de forma segura em `data/uploads/` com UUID gerado para auditoria.

2. **Extração Geométrica com PyMuPDF:**
   - O PyMuPDF (`fitz`) realiza a extração do texto por caixas delimitadoras e blocos (`page.get_text("blocks")`).
   - Isso garante que relatórios em 2 ou 3 colunas e tabelas de dados não tenham suas linhas truncadas ou lidas de forma cruzada.

3. **Chunking Semântico Estruturado:**
   - O particionamento respeita quebras de parágrafos (`\n\n`) e títulos, agrupando até 800 caracteres com overlap de 150 caracteres para preservar o contexto geológico contínuo.
   - Cada chunk recebe metadados estruturados:
     ```json
     {
       "doc_id": "a1b2c3d4",
       "filename": "relatorio_bacia_santos.pdf",
       "page": 4,
       "chunk_index": 12
     }
     ```

4. **Indexação Vetorial & Léxica:**
   - Os chunks são enviados ao `ChromaDB` sob uma coleção HNSW com distância por cosseno e paralelamente registrados no ranker `BM25`.

---

## 3. Fluxo de Consulta e Streaming (SSE)

```mermaid
sequenceDiagram
    autonumber
    actor User as Geofísico / Usuário
    participant React as React Frontend
    participant FastAPI as FastAPI Backend
    participant RAG as Mecanismo Híbrido (Chroma + BM25)
    participant LLM as Modelo de IA (LLM)

    User->>React: Digita pergunta técnica
    React->>FastAPI: POST /api/v1/chat/stream { question, doc_id }
    FastAPI->>RAG: Busca híbrida (Top K=4)
    RAG-->>FastAPI: Retorna chunks mais relevantes com metadados e score
    FastAPI-->>React: SSE event: 'sources' (Lista de páginas e documentos)
    React->>User: Renderiza cartões de citação imediatamente
    
    FastAPI->>LLM: Invocação com Prompt Contextualizado
    loop Streaming de Tokens
        LLM-->>FastAPI: Token delta
        FastAPI-->>React: SSE event: 'delta' { token }
        React->>User: Efeito de digitação em tempo real
    end
    FastAPI-->>React: SSE event: 'done'

    opt Auditoria Visual pelo Usuário
        User->>React: Clica em "Pág. 4" na citação
        React->>FastAPI: GET /api/v1/documents/doc_id/content#page=4
        FastAPI-->>React: Stream binário inline do PDF
        React->>User: Abre painel lateral focado exatamente na página 4
    end
```

---

## 4. Estratégia de Resiliência

* **Mock Mode:** Caso não haja conexão ativa com a internet ou credenciais da OpenAI/Ollama, a aplicação alterna automaticamente para o modo de simulação contextual geofísica, permitindo demonstrar 100% da interface e dos fluxos em entrevistas técnicas e testes locais.
* **SSE Fallback:** Se a conexão de streaming for bloqueada por proxies corporativos, o frontend recorre automaticamente ao endpoint REST síncrono.
* **AbortController:** O usuário pode interromper a geração a qualquer momento ou clicar em "Tentar novamente" em caso de instabilidade.

---

## 📚 Documentação Complementar

* [Documentação Técnica Completa](documentacao_completa.md)
* [Referência Completa da API REST](api_reference.md)
* [Guia de Estratégia para a Entrevista Técnica](guia_entrevista.md)
* [Guia de Conteinerização e Docker](docker_guide.md)
