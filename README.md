# 🌍 GeoDoc AI — Plataforma de RAG para Relatórios Geofísicos e Técnicos

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)

**GeoDoc AI** é uma aplicação Fullstack de alta performance projetada para equipes de engenharia, geociências e geofísica. Ela permite carregar relatórios técnicos complexos (dados sísmicos 3D, perfis de poço, reservatórios e estudos ambientais) e realizar consultas semânticas utilizando **IA Generativa** e **RAG (Retrieval-Augmented Generation)** com citação de fontes por página e streaming em tempo real.

---

## 📸 Funcionalidades Principais

* **⚡ Chat com Streaming em Tempo Real (SSE):** Efeito de digitação contínuo via *Server-Sent Events* consumindo modelos da OpenAI ou instâncias locais do Ollama.
* **📑 RAG com Citação de Fontes:** Cada resposta técnica exibe as páginas exatas e os trechos de onde a informação foi extraída, combatendo alucinações.
* **📂 Ingestão de PDFs e Chunking Geofísico:** Extração textual e particionamento em janela deslizante (*sliding window*) com overlap para reter integridade contextual.
* **🎯 Filtro de Escopo por Relatório:** Permite alternar entre consultar toda a base de relatórios ou isolar a consulta a um único documento técnico selecionado.
* **🛡️ Arquitetura Resiliente & Modo Mock:** Opera perfeitamente com OpenAI, Ollama ou em modo Mock sem exigir chaves externas para demonstrações rápidas.
* **🐳 Docker Compose Unificado:** Suba toda a infraestrutura (frontend React, backend FastAPI e volumes de persistência) com um único comando.

---

## 🏗️ Arquitetura do Sistema

```mermaid
flowchart LR
    User([Usuário / Geofísico]) --> ReactApp[Frontend React + Vite]
    ReactApp -->|Upload Multipart & SSE Streaming| FastAPI[Backend FastAPI]
    FastAPI -->|Chunking & Indexação| ChromaDB[(Vector Store ChromaDB)]
    FastAPI -->|Prompt Enriquecido| LLM[OpenAI / Ollama / Mock]
    LLM -.->|Tokens em Streaming| ReactApp
```

> 📖 **Para mais detalhes:** Consulte o documento completo em [`docs/architecture.md`](docs/architecture.md).

---

## 🚀 Como Executar

### Opção 1: Via Docker Compose (Recomendado)

Certifique-se de ter o Docker instalado e execute na raiz do projeto:

```bash
docker compose up --build
```

* **Frontend:** [http://localhost:3000](http://localhost:3000)
* **Backend API / Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)

*(Para rodar com modelo local do Ollama no Docker)*:
```bash
docker compose --profile local-llm up --build
```

---

### Opção 2: Execução Local para Desenvolvimento

#### 1. Backend (Python)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copie o arquivo de variáveis de ambiente
cp .env.example .env

# Inicie o servidor
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
Acesse [http://localhost:5173](http://localhost:5173).

---

## 🧪 Amostra para Testes

O repositório já inclui um relatório técnico geofísico de teste para você subir imediatamente na plataforma:
* 📄 [`docs/samples/relatorio_geofisico_exemplo.pdf`](docs/samples/relatorio_geofisico_exemplo.pdf) (Contém dados simulados de sísmica 3D, velocidades intervalares e reservatórios do Pré-Sal na Bacia de Santos).

---

## 📋 Padrão de Commits

Este projeto segue a convenção de [Conventional Commits](https://www.conventionalcommits.org/):
* `feat`: Novas funcionalidades
* `fix`: Correção de bugs
* `chore`: Configurações de build e dependências
* `docs`: Alterações na documentação
