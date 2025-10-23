"""
Asistente de Trámites Municipales - Backend API
FastAPI application for RAG-based municipal procedures assistant
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.core.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
