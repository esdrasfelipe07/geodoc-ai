# 🐳 Guia de Ambiência e Conteinerização com Docker — GeoDoc AI

Este guia documenta como o **GeoDoc AI** foi estruturado para cumprir os requisitos de isolamento de ambiente, reprodutibilidade e qualidade de software exigidos em ambientes de produção.

---

## 1. Estratégia de Conteinerização

O projeto adota uma arquitetura em microsserviços conteinerizada com **Docker** e **Docker Compose**, separando rigorosamente as responsabilidades de cada serviço:

| Serviço | Imagem Base | Porta Exposta | Função Principal |
| :--- | :--- | :--- | :--- |
| **Backend** | `python:3.11-slim` | `8000` | API FastAPI, extração de relatórios, RAG e orquestração de LLMs |
| **Frontend** | `node:20-alpine` -> `nginx:alpine` | `3000` | SPA React com compilação multi-stage e proxy reverso |
| **Ollama (Opcional)** | `ollama/ollama:latest` | `11434` | Execução local e offline de modelos open-source (Llama 3) |

---

## 2. Boas Práticas Adotadas nos Dockerfiles

### Backend ([`backend/Dockerfile`](../backend/Dockerfile))
* **Python 3.11-slim:** Imagem oficial enxuta e estável, reduzindo vulnerabilidades e tempo de download.
* **Cache Inteligente de Camadas:** O arquivo `requirements.txt` é copiado e instalado antes do código-fonte, evitando reinstalações desnecessárias a cada alteração de código.
* **Segurança com Usuário Não-Root (`appuser`):** A aplicação roda com permissões restritas (UID 1000), prevenindo escalonamento de privilégios.
* **Healthcheck Embutido:** O Docker monitora a rota `http://localhost:8000/api/v1/health/` a cada 15 segundos para assegurar a integridade do serviço.

### Frontend ([`frontend/Dockerfile`](../frontend/Dockerfile))
* **Multi-Stage Build:**
  * *Estágio 1 (Build):* Node 20 compila o TypeScript e o Tailwind em assets estáticos minificados na pasta `dist/`.
  * *Estágio 2 (Runtime):* Nginx Alpine leve (~25MB) serve apenas os arquivos estáticos compilados, descartando o compilador Node.js e `node_modules` da imagem final.
* **Otimização para Streaming SSE:** O `nginx.conf` desativa o *buffering* nas rotas `/api/` para garantir latência zero no envio de tokens do chat.

---

## 3. Ambientes: Produção vs Desenvolvimento

### A) Ambiente de Produção (Otimizado & Estável)
```bash
# Sobe Frontend e Backend em background
docker compose up -d --build
```
* Frontend servido via **Nginx** na porta `http://localhost:3000`.
* Backend servido com **Uvicorn** na porta `http://localhost:8000`.

### B) Ambiente de Desenvolvimento (Hot-Reloading)
```bash
# Sobe o ambiente de dev com recarregamento automático de código
docker compose -f docker-compose.dev.yml up
```
* **Hot-Reload no Python:** Altere qualquer arquivo em `backend/` e o Uvicorn reinicia instantaneamente.
* **Vite HMR no React:** Altere qualquer componente em `frontend/` e a tela atualiza em milissegundos sem perder o estado.
* Frontend em `http://localhost:5173`.

---

## 4. Testes Automatizados no Docker

Você pode rodar toda a suíte de testes unitários e de integração (`pytest`) isolada dentro do container:

```bash
docker compose run --rm backend pytest -v
```

---

## 5. Comandos Rápidos com o Makefile

Se o seu sistema tiver `make` instalado:
* `make up` — Inicia a aplicação completa
* `make dev` — Inicia com recarregamento em tempo real
* `make test` — Roda a suíte de testes
* `make logs` — Exibe os logs de todos os containers
* `make down` — Para os containers
