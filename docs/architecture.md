# 🏛️ Arquitetura do Sistema — GeoDoc AI

Este documento detalha o funcionamento arquitetural do **GeoDoc AI**, cobrindo o fluxo de dados, pipeline de **RAG (Retrieval-Augmented Generation)**, estratégias de ingestão documental e integração Fullstack.

---

## 1. Visão Geral da Arquitetura

O sistema é baseado em uma arquitetura de serviços desacoplada:
* **Frontend SPA (React + TypeScript):** Interface rica com visualização de PDFs, citações de fontes e consumo de respostas em streaming contínuo.
* **Backend API (Python / FastAPI):** Processamento assíncrono de documentos, geração de embeddings, persistência vetorial e orquestração de LLMs.
* **Vector Store (ChromaDB):** Armazenamento indexado com cálculo de similaridade por cosseno em espaço HNSW.

```mermaid
flowchart TD
    User([Usuário / Geofísico]) -->|Navegador| UI[Frontend React / Vite]
    
    subgraph Frontend [Camada de Apresentação]
        UI -->|EventSource / SSE Reader| ChatStream[Hook useChat & Streaming]
        UI -->|Multipart Upload| DocUploader[Hook useDocuments]
    end
    
    subgraph Backend [Camada de Aplicação - FastAPI]
        DocUploader -->|POST /documents/upload| PDFProcessor[Serviço de Documentos]
        ChatStream -->|POST /chat/stream| RAGOrchestrator[Serviço RAG]
        
        PDFProcessor -->|Extração de Texto & Chunking| Chunker[Sliding Window Chunking]
        Chunker -->|Upsert Chunks & Metadados| ChromaDB[(ChromaDB Vector Store)]
        
        RAGOrchestrator -->|Busca por Similaridade Semântica| ChromaDB
        ChromaDB -->|Trechos Recuperados + Páginas| ContextBuilder[Construtor de Prompt Geofísico]
        
        ContextBuilder -->|Prompt Enriquecido| LLMService[Provedor de LLM]
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

2. **Extração e Chunking com Janela Deslizante:**
   - `pypdf` realiza a extração do texto página a página.
   - O texto é particionado com tamanho fixo (800 caracteres) e overlap (150 caracteres), preservando termos geológicos contínuos (ex.: *velocidade intervalar sísmica*, *horizontes refletores*, *arenitos turbidíticos*).
   - Cada chunk recebe metadados estruturados:
     ```json
     {
       "doc_id": "a1b2c3d4",
       "filename": "relatorio_bacia_santos.pdf",
       "page": 4,
       "chunk_index": 12
     }
     ```

3. **Indexação Vetorial:**
   - Os chunks são enviados ao `ChromaDB` sob uma coleção HNSW configurada com distância por cosseno.

---

## 3. Fluxo de Consulta e Streaming (SSE)

```mermaid
sequenceDiagram
    autonumber
    actor User as Geofísico / Usuário
    participant React as React Frontend
    participant FastAPI as FastAPI Backend
    participant Chroma as ChromaDB
    participant LLM as Modelo de IA (LLM)

    User->>React: Digita pergunta técnica
    React->>FastAPI: POST /api/v1/chat/stream { question, doc_id }
    FastAPI->>Chroma: Query de similaridade (Top K=4)
    Chroma-->>FastAPI: Retorna chunks mais relevantes com metadados
    FastAPI-->>React: SSE event: 'sources' (Lista de páginas e documentos)
    React->>User: Renderiza cartões de citação imediatamente
    
    FastAPI->>LLM: Invocação com Prompt Contextualizado
    loop Streaming de Tokens
        LLM-->>FastAPI: Token delta
        FastAPI-->>React: SSE event: 'delta' { token }
        React->>User: Efeito de digitação em tempo real
    end
    FastAPI-->>React: SSE event: 'done'
```

---

## 4. Estratégia de Resiliência

* **Mock Mode:** Caso não haja conexão ativa com a internet ou credenciais da OpenAI/Ollama, a aplicação alterna automaticamente para o modo de simulação contextual geofísica, permitindo demonstrar 100% da interface e dos fluxos em entrevistas técnicas e testes locais.
