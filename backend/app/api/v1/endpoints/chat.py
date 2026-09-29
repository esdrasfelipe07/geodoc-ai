import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ChatResponse,
    summary="Consulta com IA Generativa e RAG sobre os relatórios"
)
async def chat_with_documents(request: ChatRequest):
    """
    Executa o fluxo RAG completo:
    1. Busca os trechos mais relevantes no banco vetorial com base na pergunta e filtros.
    2. Monta o prompt contextualizado com as citações técnicas.
    3. Invoca o modelo de IA e retorna a resposta com a lista das fontes consultadas.
    """
    try:
        response = await rag_service.answer_question(
            question=request.question,
            doc_id=request.doc_id,
            top_k=request.top_k
        )
        return response
    except Exception as e:
        logger.error(f"Erro ao processar consulta de chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao gerar resposta da IA: {str(e)}"
        )


@router.post(
    "/stream",
    summary="Consulta em streaming via Server-Sent Events (SSE)"
)
async def chat_stream(request: ChatRequest):
    """
    Endpoint de streaming em tempo real:
    - Envia primeiro o evento 'sources' com os trechos recuperados.
    - Em seguida, transmite os tokens conforme são gerados ('delta') para efeito de digitação em tempo real.
    - Finaliza com o evento 'done'.
    """
    try:
        generator = rag_service.answer_question_stream(
            question=request.question,
            doc_id=request.doc_id,
            top_k=request.top_k
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Erro no streaming de chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao iniciar streaming: {str(e)}"
        )
