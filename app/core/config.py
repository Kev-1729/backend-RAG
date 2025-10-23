"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "Asistente de Trámites Municipales"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:8000"]

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Google Gemini AI
    GEMINI_API_KEY: str
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    GEMINI_CHAT_MODEL: str = "gemini-2.0-flash-exp"

    # RAG Configuration
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_SIMILARITY_THRESHOLD: float = 0.4
    RAG_TOP_K_RESULTS: int = 5

    # PDF Processing
    PDF_STORAGE_BUCKET: str = "documentos_municipales"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

        # Map VITE_ prefixed variables
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            return raw_val


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
