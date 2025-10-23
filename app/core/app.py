"""
FastAPI application factory
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from app.core.config import settings
from app.api import rag_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="API para asistente virtual de trámites municipales usando RAG",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @application.get("/health")
    async def health_check():
        """Health check endpoint"""
        return JSONResponse({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.APP_NAME,
            "version": settings.VERSION
        })

    # Include routers
    application.include_router(
        rag_routes.router,
        prefix="/api/rag",
        tags=["RAG"]
    )

    # Global exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Error interno del servidor",
                "message": str(exc) if settings.DEBUG else "Error procesando solicitud"
            }
        )

    logger.info(f"🚀 {settings.APP_NAME} v{settings.VERSION} initialized")
    logger.info(f"📊 Health check: http://localhost:{settings.PORT}/health")
    logger.info(f"💬 API RAG: http://localhost:{settings.PORT}/api/rag/query")
    logger.info(f"📚 API Docs: http://localhost:{settings.PORT}/docs")

    return application


app = create_application()
