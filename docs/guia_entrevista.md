# 🎯 GeoDoc AI — Guia de Preparação Estratégica para a Entrevista Técnica

Este guia foi elaborado para consolidar os principais conceitos e fornecer roteiros mentais práticos para a sua entrevista técnica.

---

## 1. O Pitch do Projeto (Apresentação Inicial)

### Versão Curta (30 segundos — "Elevator Pitch")
> *"O **GeoDoc AI** é uma plataforma Web Fullstack que desenvolvi para solucionar um gargalo real na análise de relatórios de geociências e engenharia. Ele permite fazer upload de documentos técnicos complexos em PDF e conversar com eles em tempo real via **RAG Híbrido** (combinando ChromaDB e BM25). O frontend foi construído em **React com TypeScript** e inclui um **visualizador de PDF lado a lado sincronizado com as citações da IA**, enquanto o backend em **Python com FastAPI e Gunicorn** gerencia o streaming token a token via SSE e a persistência vetorial, tudo isolado e orquestrado em **Docker**."*

### Versão Completa (2 minutos — Método STAR)
* **Situação:** *"Em projetos técnicos de energia e geofísica, equipes multidisciplinares lidam com estudos de poço e sísmica de centenas de páginas, repletos de tabelas, layouts de várias colunas e termos densos."*
* **Tarefa:** *"Precisávamos de uma solução que permitisse consultas ágeis em linguagem natural, mas com rigor técnico absoluto: sem alucinações e com auditoria visual direta da página citada."*
* **Ação:** *"Desenvolvi o GeoDoc AI. No backend, implementei um parser com PyMuPDF para preservar o fluxo de colunas e chunking semântico por parágrafos. Para a busca, criei um pipeline híbrido com ChromaDB para semântica e BM25 para termos exatos (códigos de poço e números). No frontend, construí uma interface em React com Server-Sent Events (SSE) para digitação em tempo real e um leitor de PDF embutido que pula direto para a página referenciada pela IA. Para a ambiência, estruturei containers Docker com Nginx, Gunicorn e hot-reload."*
* **Resultado:** *"Uma aplicação auditável, robusta, conteinerizada e pronta para ser utilizada por engenheiros e cientistas de dados com zero tempo de espera."*

---

## 2. Perguntas Técnicas Prováveis & Respostas Recomendadas

### 🔹 Inteligência Artificial & RAG

**1. "Por que você implementou RAG Híbrido em vez de apenas busca vetorial?"**
* *Conceito:* A busca vetorial densa por cosseno é ótima para similaridade semântica (conceitos afins), mas pode ser imprecisa para códigos alfanuméricos curtos (ex: `1-GEO-01-SPS`, `29° API`, `4500 m/s`).
* *Resposta:* *"Em documentos técnicos, os usuários buscam tanto por conceitos gerais ('qual a porosidade do reservatório?') quanto por identificadores exatos de equipamentos e poços. Combinei o **ChromaDB** para capturar o sentido semântico e o **BM25 nativo** para garantir precisão cirúrgica em termos léxicos raros."*

**2. "Como você mitiga o problema de alucinações na LLM?"**
* *Resposta:* *"Em três frentes: primeiro, no **Prompt de Sistema**, restringindo a resposta exclusivamente às passagens fornecidas; segundo, na obrigatoriedade do modelo citar o documento e a página de referência; terceiro, na temperatura baixa da LLM (0.2), que prioriza respostas determinísticas e factuais."*

**3. "Como o sistema lida com privacidade de dados corporativos?"**
* *Resposta:* *"O GeoDoc AI é agnóstico ao provedor. Ele suporta tanto a API da OpenAI quanto modelos open-source locais via **Ollama (como o Llama 3)**, garantindo que nenhum relatório sigiloso de exploração precise sair da infraestrutura privada da empresa."*

---

### 🔹 Backend & Arquitetura (Python / FastAPI)

**4. "Por que escolheu FastAPI e como tratou a concorrência?"**
* *Resposta:* *"O FastAPI foi escolhido pelo suporte nativo a operações assíncronas com `async/await` (essencial para streaming SSE e I/O de banco vetorial), além da validação rigorosa de dados com Pydantic v2 e documentação OpenAPI automática. Em produção, empacotei o backend com **Gunicorn gerenciando 4 workers Uvicorn**, evitando que tarefas intensivas de parsing de PDF bloqueiem o atendimento a novas mensagens do chat."*

**5. "Qual a diferença do PyMuPDF em relação ao PyPDF?"**
* *Resposta:* *"O PyMuPDF (`fitz`) é implementado em C++ e oferece extração geométrica por blocos (`page.get_text('blocks')`). Isso significa que ele lê colunas e blocos de texto respeitando a ordem visual de leitura, enquanto leitores lineares simples misturam as linhas de colunas adjacentes em estudos técnicos."*

---

### 🔹 Frontend & Experiência do Usuário (React + TypeScript)

**6. "Por que usar Server-Sent Events (SSE) em vez de WebSockets ou polling?"**
* *Resposta:* *"Para o fluxo de IA Generativa, a comunicação em tempo de resposta é unidirecional (o servidor envia continuamente os tokens para o cliente). O SSE opera nativamente sobre HTTP padrão, consome menos recursos de rede, suporta reconexão automática e não sofre com as complexidades de proxy/firewall que o protocolo WebSocket impõe."*

**7. "Como foi pensada a usabilidade da aplicação?"**
* *Resposta:* *"O foco foi em produtividade e auditoria. Em vez de apenas exibir um texto no chat, a aplicação divide a tela: o usuário vê a resposta com o selo de relevância e, ao clicar na citação, o **leitor de PDF abre ao lado já posicionado na página exata**, permitindo conferência visual imediata de gráficos e tabelas."*

---

### 🔹 DevOps & Qualidade de Software (Docker & Git)

**8. "Como você organizou os ambientes no Docker?"**
* *Resposta:* *"Criei dois arquivos: no `docker-compose.yml` de produção, utilizei **multi-stage build** no frontend entregue via Nginx Alpine leve (~25MB) com proxy reverso e cabeçalhos de no-buffering para SSE, e backend com usuário não-root e limites de memória definidos. No `docker-compose.dev.yml`, usei montagem de volumes diretos para garantir **hot-reload** em tempo real no código."*

**9. "Como você utiliza o Git no seu dia a dia?"**
* *Resposta:* *"Utilizo a convenção de **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`), trabalho com branches por funcionalidade (`feature/*`) e estruturo mensagens descritivas para facilitar code reviews e rastreabilidade de código."*

---

## 3. Glossário Rápido de Termos Técnicos

* **RAG (Retrieval-Augmented Generation):** Técnica de IA que busca fatos em uma base de dados externa (banco vetorial) e injeta esses trechos no prompt da LLM antes de gerar a resposta.
* **Embeddings:** Representações matemáticas de texto na forma de vetores densos (listas de centenas de números) onde textos com significados próximos ficam espacialmente próximos.
* **Cosine Similarity:** Cálculo do cosseno do ângulo entre dois vetores para medir sua semelhança semântica independente do tamanho do texto.
* **BM25:** Algoritmo estatístico clássico de recuperação de informação baseado em frequência de termos (TF) e frequência inversa no corpus (IDF).
* **SSE (Server-Sent Events):** Padrão web que permite ao servidor empurrar dados continuamente para o cliente sobre uma conexão HTTP aberta.
* **Multi-Stage Build:** Prática do Docker de usar um container temporário para compilar o código e transferir apenas os binários minificados para a imagem final, reduzindo drasticamente o tamanho e a superfície de ataque da imagem.

---

## 4. O Papel de "Ponte" com o Time de Geofísica

Quando te perguntarem sobre **trabalho em equipe e metodologias ágeis**:
> *"Vejo meu papel como uma ponte natural entre as necessidades complexas dos especialistas de Geociências/IA e uma interface intuitiva para o usuário final. Sei que geofísicos precisam de respostas embasadas e auditáveis, por isso projetei a aplicação para exibir a página exata e o trecho de contexto de cada conclusão gerada pela IA."*

---

## 5. Perguntas Estratégicas para Você Fazer no Final

Quando os entrevistadores abrirem espaço para suas dúvidas:
1. *"Como é a dinâmica de comunicação diária entre a equipe de desenvolvimento Web e os pesquisadores/engenheiros de Geofísica e IA?"*
2. *"Quais são os principais formatos de relatórios ou dados que vocês planejam ingerir no pipeline de IA nos próximos meses?"*
3. *"Quais tecnologias ou práticas têm sido o foco de inovação do time atualmente?"*
