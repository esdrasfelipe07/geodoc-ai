import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "GeoDoc AI"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: str = "data/uploads"
    CHROMA_PERSIST_DIR: str = "data/vectorstore"
    CHROMA_COLLECTION_NAME: str = "geodoc_documents"

    # LLM & Embedding Settings
    LLM_PROVIDER: str = "mock"  # "openai", "ollama", or "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.2

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    @property
    def upload_path(self) -> Path:
        path = self.BASE_DIR / self.UPLOAD_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chroma_path(self) -> Path:
        path = self.BASE_DIR / self.CHROMA_PERSIST_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

    @model_validator(mode="after")
    def validate_provider_configuration(self) -> "Settings":
        provider = self.LLM_PROVIDER.lower().strip()
        allowed_providers = ["mock", "openai", "ollama"]
        if provider not in allowed_providers:
            raise ValueError(
                f"LLM_PROVIDER inválido ('{self.LLM_PROVIDER}'). "
                f"Opções aceitas: {', '.join(allowed_providers)}"
            )

        if provider == "openai" and not self.OPENAI_API_KEY.strip():
            # In testing environment we can allow empty if mocked, otherwise fail-fast
            if self.ENVIRONMENT != "testing":
                raise ValueError(
                    "OPENAI_API_KEY é obrigatória quando LLM_PROVIDER='openai'. "
                    "Configure sua chave no arquivo .env ou defina LLM_PROVIDER='mock'."
                )

        if provider == "ollama" and not self.OLLAMA_BASE_URL.strip():
            raise ValueError(
                "OLLAMA_BASE_URL é obrigatória quando LLM_PROVIDER='ollama'."
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
