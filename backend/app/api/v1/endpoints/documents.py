import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse

from app.models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse,
    DocumentMetadata
)
from app.services.document_service import document_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload e indexação de relatório técnico em PDF"
)
async def upload_document(file: UploadFile = File(...)):
    """
    Recebe um arquivo PDF (relatório geofísico, estudo geológico ou documento técnico),
    extrai seu conteúdo textual página por página, realiza a divisão em chunks
    e indexa as passagens no banco de dados vetorial (ChromaDB) para consulta via RAG.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de arquivo inválido. Apenas documentos PDF são aceitos."
        )

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite máximo permitido de {MAX_FILE_SIZE // (1024 * 1024)}MB."
        )

    try:
        # 1. Salva o arquivo no diretório de uploads
        doc_id, file_path = document_service.save_file(file.filename, content)

        # 2. Extrai páginas e fragmenta em chunks estruturados
        total_pages, chunks = document_service.extract_text_and_chunks(
            file_path=file_path,
            doc_id=doc_id,
            filename=file.filename
        )

        # 3. Indexa os chunks no banco de vetores
        if chunks:
            rag_service.vector_store.add_chunks(chunks)

        # 4. Registra no manifesto de documentos
        doc_metadata = document_service.register_document(
            doc_id=doc_id,
            filename=file.filename,
            total_pages=total_pages,
            total_chunks=len(chunks),
            file_size_bytes=file_size
        )

        return DocumentUploadResponse(
            message=f"Documento '{file.filename}' processado e indexado com sucesso!",
            document=doc_metadata
        )

    except Exception as e:
        logger.error(f"Erro ao processar PDF {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao processar e indexar o documento: {str(e)}"
        )


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="Listar todos os relatórios indexados"
)
async def list_documents():
    """
    Retorna a lista completa de documentos disponíveis no sistema para consultas contextuais.
    """
    docs = document_service.list_documents()
    return DocumentListResponse(
        total_documents=len(docs),
        documents=docs
    )


@router.get(
    "/{doc_id}/content",
    summary="Obter arquivo PDF original para visualização inline"
)
async def get_document_content(doc_id: str):
    """
    Retorna o arquivo binário PDF para visualização embutida no frontend (PDF Viewer).
    """
    existing = document_service.get_document(doc_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento com ID '{doc_id}' não encontrado no manifesto."
        )

    file_path = document_service.get_document_file_path(doc_id)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico do PDF não encontrado no disco."
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=existing.filename,
        content_disposition_type="inline"
    )


@router.delete(
    "/{doc_id}",
    response_model=DocumentDeleteResponse,
    summary="Remover documento e seus vetores indexados"
)
async def delete_document(doc_id: str):
    """
    Exclui o arquivo físico do documento, remove seus registros do manifesto
    e apaga todos os embeddings/chunks associados do banco vetorial.
    """
    existing = document_service.get_document(doc_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento com ID '{doc_id}' não encontrado."
        )

    # 1. Exclui do banco vetorial
    rag_service.vector_store.delete_document_chunks(doc_id)

    # 2. Exclui do disco e do manifesto
    document_service.delete_document(doc_id)

    return DocumentDeleteResponse(
        message=f"Documento '{existing.filename}' e seus índices vetoriais foram removidos com sucesso.",
        doc_id=doc_id
    )
