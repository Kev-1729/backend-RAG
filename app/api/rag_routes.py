"""
RAG API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
import logging

from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    ProcessPDFRequest,
    ProcessPDFResponse,
    ProcessBatchRequest,
    ProcessBatchResponse,
    DocumentStats,
    ProcessingStatusEnum
)
from app.services.rag_service import get_rag_service
from app.services.pdf_processor import get_pdf_processor
from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest) -> QueryResponse:
    """
    Query the RAG system with a user question

    Args:
        request: QueryRequest with user query

    Returns:
        QueryResponse with generated answer and metadata
    """
    try:
        logger.info(f"Received query: {request.query}")
        rag_service = get_rag_service()
        response = await rag_service.query(request.query)
        return response

    except Exception as e:
        logger.error(f"Error in /query endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error procesando consulta",
                "message": str(e)
            }
        )


@router.post("/process-pdf", response_model=ProcessPDFResponse)
async def process_pdf(request: ProcessPDFRequest) -> ProcessPDFResponse:
    """
    Process a single PDF document

    Args:
        request: ProcessPDFRequest with file details

    Returns:
        ProcessPDFResponse with processing status
    """
    try:
        logger.info(f"Processing PDF: {request.filename}")
        pdf_processor = get_pdf_processor()
        result = await pdf_processor.process_pdf(
            request.file_path,
            request.filename,
            request.category
        )
        return result

    except Exception as e:
        logger.error(f"Error in /process-pdf endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error procesando PDF",
                "message": str(e)
            }
        )


@router.post("/process-batch", response_model=ProcessBatchResponse)
async def process_batch(request: ProcessBatchRequest) -> ProcessBatchResponse:
    """
    Process multiple PDF documents in batch

    Args:
        request: ProcessBatchRequest with list of file paths

    Returns:
        ProcessBatchResponse with results for each file
    """
    try:
        logger.info(f"Processing batch of {len(request.file_paths)} PDFs")
        pdf_processor = get_pdf_processor()
        results = await pdf_processor.process_multiple_pdfs(
            request.file_paths,
            request.category
        )

        successful = sum(1 for r in results if r.status == ProcessingStatusEnum.COMPLETED)
        failed = sum(1 for r in results if r.status == ProcessingStatusEnum.ERROR)

        return ProcessBatchResponse(
            results=results,
            total=len(results),
            successful=successful,
            failed=failed
        )

    except Exception as e:
        logger.error(f"Error in /process-batch endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error procesando PDFs en batch",
                "message": str(e)
            }
        )


@router.get("/stats", response_model=DocumentStats)
async def get_stats() -> DocumentStats:
    """
    Get statistics about processed documents

    Returns:
        DocumentStats with aggregated statistics
    """
    try:
        # Get document counts by category
        docs_response = supabase.table('documents').select('category, document_type').execute()

        if not docs_response.data:
            return DocumentStats(
                total_documents=0,
                total_chunks=0,
                total_pages=0,
                categories={},
                document_types={}
            )

        # Count chunks
        chunks_response = supabase.table('document_chunks').select('id', count='exact').execute()
        total_chunks = chunks_response.count if chunks_response.count else 0

        # Get total pages
        pages_response = supabase.table('documents').select('total_pages').execute()
        total_pages = sum(doc.get('total_pages', 0) for doc in pages_response.data) if pages_response.data else 0

        # Aggregate by category and type
        categories = {}
        document_types = {}

        for doc in docs_response.data:
            category = doc.get('category', 'unknown')
            doc_type = doc.get('document_type', 'unknown')

            categories[category] = categories.get(category, 0) + 1
            document_types[doc_type] = document_types.get(doc_type, 0) + 1

        return DocumentStats(
            total_documents=len(docs_response.data),
            total_chunks=total_chunks,
            total_pages=total_pages,
            categories=categories,
            document_types=document_types
        )

    except Exception as e:
        logger.error(f"Error in /stats endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Error obteniendo estadísticas",
                "message": str(e)
            }
        )
