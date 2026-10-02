# Sugestões de Melhorias para GeoDoc AI

Abaixo estão listadas algumas sugestões de melhorias arquiteturais, de backend, frontend e infraestrutura para evoluir o projeto GeoDoc AI, focando em escalabilidade, precisão nas buscas (RAG) e experiência do usuário.

## 1. Melhorias de Backend e Pipeline de Dados (RAG)
* **Substituição do PyPDF por bibliotecas mais avançadas:** O uso do `pypdf` funciona bem para textos simples, mas relatórios geofísicos geralmente possuem layout complexo em colunas, tabelas e figuras. A adoção de bibliotecas como **Unstructured** (com OCR via Tesseract), **pdfplumber** ou **PyMuPDF (fitz)** pode extrair o texto de maneira mais coerente, preservando a semântica e ignorando cabeçalhos repetitivos.
* **Refinamento do *Chunking*:** Implementar estratégias semânticas de *chunking* (e.g. quebrar por parágrafos, seções Markdown, ou títulos) usando recursos avançados do LangChain, ao invés de apenas uma janela deslizante fixa (800 caracteres).
* **Gerenciamento de Embeddings:** No `rag_service.py`, a adição de vetores ao ChromaDB depende do modelo padrão dele. Seria ideal configurar explicitamente um `HuggingFaceEmbeddings` (usando `sentence-transformers`) ou `OpenAIEmbeddings` para ter maior controle sobre o dimensionamento e a qualidade vetorial.
* **Mecanismo de *Fallback* de Busca Robusto:** O fallback de busca (caso o ChromaDB falhe) atualmente usa uma lógica simples de contagem de palavras (*bag of words* sem TF-IDF). Integrar o algoritmo de BM25 (via LangChain BM25Retriever) ofereceria resultados consideravelmente mais precisos sem necessitar de embeddings neurais em memória.
* **Testes e Dependências:** Incluir os pacotes de teste no `requirements-dev.txt` de modo que a dependência `httpx` (requerida pela `fastapi.testclient`) não interfira ou quebre as importações ao executar a suíte de testes.

## 2. Melhorias de Frontend e Experiência do Usuário
* **Visualizador de PDF Integrado (PDF Viewer):** Atualmente, a plataforma exibe o número da página citada. Integrar uma biblioteca como **react-pdf** permitiria que o usuário clique na citação e abra um painel lateral visualizando exatamente a página do relatório em questão.
* **Autenticação e Sessões (Auth & State Management):** O chat atualmente não armazena histórico persistente por usuário. Incluir um mecanismo simples de *auth* (como NextAuth.js ou JWT nativo) e persistir conversas no backend (via PostgreSQL + SQLAlchemy) seria vital para uso corporativo.
* **Animações de Streaming e Feedback de Erro:** Melhorar o tratamento das exceções no SSE (Server-Sent Events) no hook `useChat.ts` caso a conexão caia ou o provedor LLM demore a responder, implementando retries automáticos.

## 3. Infraestrutura e Docker
* **Servidor ASGI de Produção:** O `Dockerfile` do backend inicializa via `uvicorn app.main:app`. Em produção, para lidar com cargas concorrentes, é recomendado utilizar o `gunicorn` com *workers uvicorn* (`gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`).
* **Multi-stage Build e Segurança Docker:**
  - Garantir que o `docker-compose.yml` limite o consumo de memória, especialmente ao executar contêineres do Ollama.
  - Implementar verificação de *healthcheck* não só na API, mas também entre o contêiner do Ollama (caso utilizado) e o backend.
* **Centralização de Configurações (.env):** O Pydantic Settings suporta validações avançadas (ex: verificar se a chave da OpenAI existe se o provider for openai). Garantir essas validações antecipadas (fail-fast) ao invés de lançar o erro na hora da geração.

## 4. Próximos Passos Sugeridos
* Implementar o parser aprimorado com `PyMuPDF`.
* Refatorar o ambiente de testes corrigindo a execução inicial do `pytest`.
* Configurar o Gunicorn no Dockerfile.
