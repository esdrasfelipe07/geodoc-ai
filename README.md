# 🌍 GeoDoc AI — Plataforma de RAG para Relatórios Geofísicos e Técnicos

GeoDoc AI é uma aplicação Fullstack desenvolvida com **React** e **FastAPI (Python)**, integrada a modelos de IA Generativa e fluxo de **RAG (Retrieval-Augmented Generation)**. A solução foi projetada para auxiliar equipes de engenharia, geofísica e geociências a consultar, analisar e extrair insights precisos de relatórios técnicos e documentos geológicos complexos.

---

## 🏗️ Arquitetura do Projeto

```
ProjetoIA/
├── docker-compose.yml             # Orquestração de containers (Frontend, Backend, VectorDB)
├── .gitignore                     # Arquivos ignorados pelo Git
├── README.md                      # Documentação principal
├── docs/                          # Documentação técnica e amostras
│   ├── architecture.md            # Detalhamento da arquitetura e fluxo de RAG
│   └── samples/                   # Relatórios/PDFs de teste para o pipeline
│
├── backend/                       # API Backend em Python (FastAPI + LangChain)
│   ├── Dockerfile                 # Imagem Docker do backend
│   ├── .dockerignore
│   ├── .env.example               # Variáveis de ambiente de exemplo
│   ├── requirements.txt           # Dependências Python
│   ├── app/
│   │   ├── main.py                # Ponto de entrada FastAPI e configurações CORS
│   │   ├── api/
│   │   │   ├── router.py          # Agregador de rotas
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── chat.py      # Endpoints de chat (suporte a Streaming SSE)
│   │   │           ├── documents.py # Upload, processamento e listagem de PDFs
│   │   │           └── health.py    # Health check da API e status dos modelos
│   │   ├── core/
│   │   │   └── config.py          # Configurações com Pydantic Settings
│   │   ├── models/
│   │   │   └── schemas.py         # Schemas de validação Pydantic (Request/Response)
│   │   └── services/
│   │       ├── document_service.py # Extração de texto e chunking de documentos
│   │       ├── llm_service.py      # Conectores LLM (OpenAI, Ollama, Groq)
│   │       └── rag_service.py      # Pipeline RAG, busca vetorial e prompt de contexto
│   ├── data/
│   │   ├── uploads/               # Armazenamento temporário de PDFs recebidos
│   │   └── vectorstore/           # Persistência do banco de vetores (ChromaDB)
│   └── tests/                     # Testes automatizados (pytest)
│       ├── test_health.py
│       ├── test_documents.py
│       └── test_chat.py
│
└── frontend/                      # Aplicação Web (React + TypeScript + Tailwind)
    ├── Dockerfile                 # Imagem Docker multi-stage (Node build -> Nginx)
    ├── nginx.conf                 # Configuração do Nginx para SPA e proxy reverso
    ├── package.json               # Dependências do frontend
    ├── tsconfig.json              # Configurações do TypeScript
    ├── vite.config.ts             # Configuração do Vite
    ├── index.html                 # HTML raiz
    └── src/
        ├── main.tsx               # Ponto de entrada da aplicação
        ├── App.tsx                # Layout principal e gerenciamento de estado
        ├── components/
        │   ├── Chat/              # Componentes de Chat, balões e streaming
        │   ├── Documents/         # Lista de arquivos, uploader e progresso
        │   ├── Layout/            # Header, Sidebar e navegação
        │   └── UI/                # Componentes reutilizáveis (Botões, Modais, Cards)
        ├── hooks/                 # Custom React hooks (ex: useChat, useDocuments)
        ├── services/              # Cliente HTTP (Axios / Fetch) e SSE streaming
        └── types/                 # Interfaces TypeScript
```

---

## 🚀 Tecnologias

* **Frontend:** React, TypeScript, Tailwind CSS, Lucide Icons.
* **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
* **IA / RAG:** LangChain / LlamaIndex, ChromaDB (Vector Store), OpenAI / Ollama.
* **DevOps & Qualidade:** Docker, Docker Compose, Pytest.
