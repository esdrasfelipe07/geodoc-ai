# 🔌 GeoDoc AI — Referência Completa da API REST

A API do **GeoDoc AI** é estruturada no padrão RESTful sobre o protocolo HTTP/1.1 e HTTP/2, serializando mensagens em formato JSON e suportando streaming contínuo via Server-Sent Events (SSE).

* **URL Base de Produção:** `http://localhost:8000/api/v1`
* **Swagger UI Interativo:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

---

## 📑 Sumário das Rotas

| Método | Endpoint | Descrição | Content-Type |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Informações de boas-vindas da API | `application/json` |
| `GET` | `/api/v1/health/` | Verificação de status e saúde do provedor LLM | `application/json` |
| `POST` | `/api/v1/documents/upload` | Upload e indexação vetorial de relatório PDF | `multipart/form-data` |
| `GET` | `/api/v1/documents/` | Listagem de todos os relatórios indexados | `application/json` |
| `GET` | `/api/v1/documents/{doc_id}/content` | Recuperação do PDF original para visualização inline | `application/pdf` |
| `DELETE`| `/api/v1/documents/{doc_id}` | Remoção do documento físico e dos índices vetoriais | `application/json` |
| `POST` | `/api/v1/chat/` | Consulta RAG convencional (resposta única) | `application/json` |
| `POST` | `/api/v1/chat/stream` | Consulta RAG com streaming em tempo real (SSE) | `text/event-stream` |

---

## 1. Monitoramento e Saúde

### `GET /api/v1/health/`
Verifica a disponibilidade da API, o provedor de inteligência artificial ativo e a contagem de documentos indexados no banco vetorial.

#### Exemplo de Requisição
```bash
curl -X GET http://localhost:8000/api/v1/health/
```

#### Resposta de Sucesso (`200 OK`)
```json
{
  "status": "healthy",
  "project": "GeoDoc AI",
  "environment": "production",
  "llm_provider": "mock",
  "llm_model": "mock-llm-v1",
  "indexed_documents_count": 2,
  "timestamp": "2026-10-08T22:30:00.000000"
}
```

---

## 2. Gerenciamento de Documentos

### `POST /api/v1/documents/upload`
Recebe um arquivo PDF técnico, executa a extração em blocos via PyMuPDF (`fitz`), particiona o texto em fragmentos semânticos e realiza o upsert no ChromaDB.

* **Limite máximo por arquivo:** 50 MB
* **Formato permitido:** Exclusivamente arquivos com extensão `.pdf`

#### Parâmetros de Formulário (Form-Data)
* `file`: Arquivo binário do relatório em PDF.

#### Exemplo de Requisição (cURL)
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@docs/samples/relatorio_geofisico_exemplo.pdf"
```

#### Resposta de Sucesso (`201 Created`)
```json
{
  "message": "Documento 'relatorio_geofisico_exemplo.pdf' processado e indexado com sucesso!",
  "document": {
    "doc_id": "a3f12c8b",
    "filename": "relatorio_geofisico_exemplo.pdf",
    "total_pages": 1,
    "total_chunks": 4,
    "uploaded_at": "2026-10-08T22:31:15.123456",
    "file_size_bytes": 1420
  }
}
```

#### Códigos de Erro Possíveis
* `400 Bad Request`: Formato de arquivo inválido (não é PDF).
* `413 Request Entity Too Large`: O arquivo ultrapassou 50 MB.
* `500 Internal Server Error`: Falha inesperada durante a extração ou indexação vetorial.

---

### `GET /api/v1/documents/`
Retorna a lista de todos os relatórios indexados atualmente disponíveis para consulta no sistema.

#### Exemplo de Requisição
```bash
curl -X GET http://localhost:8000/api/v1/documents/
```

#### Resposta de Sucesso (`200 OK`)
```json
{
  "total_documents": 1,
  "documents": [
    {
      "doc_id": "a3f12c8b",
      "filename": "relatorio_geofisico_exemplo.pdf",
      "total_pages": 1,
      "total_chunks": 4,
      "uploaded_at": "2026-10-08T22:31:15.123456",
      "file_size_bytes": 1420
    }
  ]
}
```

---

### `GET /api/v1/documents/{doc_id}/content`
Retorna o fluxo de bytes do PDF original com o cabeçalho HTTP `Content-Disposition: inline`. Permite que o frontend renderize o documento diretamente dentro de uma tag `<iframe>` ou `<object>` focando em uma página específica (ex: `#page=3`).

#### Exemplo de Requisição
```bash
curl -X GET http://localhost:8000/api/v1/documents/a3f12c8b/content --output visualizacao.pdf
```

#### Resposta de Sucesso (`200 OK`)
* **Headers:**
  * `Content-Type: application/pdf`
  * `Content-Disposition: inline; filename="relatorio_geofisico_exemplo.pdf"`
* **Body:** Stream binário do arquivo.

#### Códigos de Erro
* `404 Not Found`: Documento não registrado no manifesto ou arquivo ausente no disco.

---

### `DELETE /api/v1/documents/{doc_id}`
Remove permanentemente o arquivo PDF do disco, expurga seu registro do manifesto e remove todos os seus chunks e embeddings do ChromaDB.

#### Exemplo de Requisição
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/a3f12c8b
```

#### Resposta de Sucesso (`200 OK`)
```json
{
  "message": "Documento 'relatorio_geofisico_exemplo.pdf' e seus índices vetoriais foram removidos com sucesso.",
  "doc_id": "a3f12c8b"
}
```

---

## 3. Chat & Inteligência Artificial (RAG)

### `POST /api/v1/chat/`
Endpoint síncrono convencional. Realiza a busca híbrida (vetorial + BM25), constrói o prompt técnico e retorna a resposta completa acompanhada das fontes citadas.

#### Corpo da Requisição (JSON)
```json
{
  "question": "Qual a velocidade sísmica intervalar registrada na camada de sal?",
  "doc_id": "a3f12c8b",
  "top_k": 3
}
```
* `question` *(obrigatório, string)*: Pergunta do usuário (mínimo de 2 caracteres).
* `doc_id` *(opcional, string)*: Restringe a busca apenas ao documento com este identificador. Se for omitido ou `null`, a pesquisa busca em todos os documentos.
* `top_k` *(opcional, inteiro, default: 4)*: Quantidade de trechos mais relevantes a recuperar.

#### Resposta de Sucesso (`200 OK`)
```json
{
  "answer": "De acordo com os dados apresentados no relatório, a camada de sal (localizada entre 2100m e 4800m de profundidade) é composta por espessos evaporitos (halita e anidrita) e apresenta uma velocidade sísmica de propagação característica de 4500 m/s.",
  "sources": [
    {
      "doc_id": "a3f12c8b",
      "filename": "relatorio_geofisico_exemplo.pdf",
      "page": 1,
      "chunk_index": 2,
      "content": "Camada de Sal (2100m - 4800m): Evaporitos espessos (halita e anidrita). Velocidade sismica: 4500 m/s.",
      "relevance_score": 0.942
    }
  ],
  "model": "gpt-4o-mini",
  "provider": "openai",
  "timestamp": "2026-10-08T22:35:00.000000"
}
```

---

### `POST /api/v1/chat/stream`
Endpoint de alto desempenho com **Server-Sent Events (SSE)**. Transmite a resposta token a token conforme ela é calculada pela IA.

#### Exemplo de Requisição (cURL)
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Descreva as características do reservatório carbonático.",
    "doc_id": null,
    "top_k": 4
  }'
```

#### Formato dos Eventos SSE Transmitidos

1. **Evento de Fontes (`sources`):** Emitido logo no início com a lista de citações:
   ```text
   event: sources
   data: [{"doc_id": "a3f12c8b", "filename": "relatorio.pdf", "page": 1, "chunk_index": 3, "content": "...", "relevance_score": 0.91}]

   ```

2. **Eventos de Tokens (`delta`):** Emitidos sequencialmente com cada fragmento de texto:
   ```text
   event: delta
   data: {"token": "O "}

   event: delta
   data: {"token": "reservatório "}

   event: delta
   data: {"token": "carbonático "}

   event: delta
   data: {"token": "apresenta..."}

   ```

3. **Evento de Conclusão (`done`):**
   ```text
   event: done
   data: {}

   ```

---

## 4. Códigos de Status HTTP Padronizados

| Código | Significado | Situação Típica |
| :---: | :--- | :--- |
| `200` | OK | Sucesso na requisição GET, DELETE ou POST síncrono |
| `201` | Created | Documento PDF criado e indexado no banco vetorial |
| `400` | Bad Request | Formato de arquivo rejeitado (ex: extensão diferente de .pdf) |
| `404` | Not Found | ID do documento inexistente no manifesto ou arquivo apagado |
| `413` | Payload Too Large | Arquivo enviado acima do limite de 50 MB |
| `422` | Unprocessable Entity | Corpo JSON inválido (ex: pergunta com menos de 2 caracteres) |
| `500` | Internal Server Error | Falha de execução inesperada nos serviços de backend ou LLM |
