from fastapi import APIRouter
from app.core.config import settings
from app.models.schemas import HealthResponse
from app.services.rag_service import rag_service
from app.services.document_service import document_service

router = APIRouter()


@router.get("/", response_model=HealthResponse, summary="Verificação de integridade da API")
async def health_check():
    """
    Retorna o status operacional da API GeoDoc AI, dados do provedor de LLM configurado
    e a quantidade de documentos indexados no sistema.
    """
    docs = document_service.list_documents()
    model_name = (
        settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai"
        else settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama"
        else "mock-llm-v1"
    )

    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=model_name,
        indexed_documents_count=len(docs)
    )
