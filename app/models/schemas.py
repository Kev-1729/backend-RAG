"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ProcessingStatusEnum(str, Enum):
    """Processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class QueryRequest(BaseModel):
    """Request model for RAG query"""
    query: str = Field(..., min_length=1, description="User query text")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "¿Cómo solicito una licencia de funcionamiento para mi bodega?"
            }
        }


class QueryResponse(BaseModel):
    """Response model for RAG query"""
    answer: str = Field(..., description="Generated answer")
    document_name: Optional[str] = Field(None, description="Source document name")
    download_url: Optional[str] = Field(None, description="Document download URL")
    sources: Optional[List[str]] = Field(None, description="List of source documents")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "<p>Para solicitar una licencia de funcionamiento...</p>",
                "document_name": "Formato_Licencia_Bodega.pdf",
                "sources": ["Formato_Licencia_Bodega.pdf", "Ley_27972.pdf"]
            }
        }


class ProcessPDFRequest(BaseModel):
    """Request model for processing a single PDF"""
    file_path: str = Field(..., description="Path to PDF file")
    filename: str = Field(..., description="PDF filename")
    category: Optional[str] = Field(None, description="Document category")

    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "./documentos/ley_27972.pdf",
                "filename": "ley_27972.pdf",
                "category": "normativa"
            }
        }


class ProcessingStatus(BaseModel):
    """Processing status for PDF documents"""
    document_id: str = Field(default="", description="Document ID in database")
    filename: str = Field(..., description="Filename")
    status: ProcessingStatusEnum = Field(..., description="Processing status")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    chunks_created: Optional[int] = Field(None, description="Number of chunks created")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "uuid-123",
                "filename": "ley_27972.pdf",
                "status": "completed",
                "progress": 100,
                "chunks_created": 45
            }
        }


class ProcessPDFResponse(ProcessingStatus):
    """Response model for processing a single PDF"""
    pass


class ProcessBatchRequest(BaseModel):
    """Request model for batch PDF processing"""
    file_paths: List[str] = Field(..., description="List of PDF file paths")
    category: Optional[str] = Field(None, description="Category for all documents")

    class Config:
        json_schema_extra = {
            "example": {
                "file_paths": ["./docs/ley1.pdf", "./docs/ley2.pdf"],
                "category": "normativa"
            }
        }


class ProcessBatchResponse(BaseModel):
    """Response model for batch PDF processing"""
    results: List[ProcessingStatus] = Field(..., description="Processing results")
    total: int = Field(..., description="Total files processed")
    successful: int = Field(..., description="Successfully processed")
    failed: int = Field(..., description="Failed to process")


class DocumentStats(BaseModel):
    """Document statistics"""
    total_documents: int = Field(..., description="Total documents")
    total_chunks: int = Field(..., description="Total chunks")
    total_pages: int = Field(..., description="Total pages")
    categories: Dict[str, int] = Field(default_factory=dict, description="Documents by category")
    document_types: Dict[str, int] = Field(default_factory=dict, description="Documents by type")

    class Config:
        json_schema_extra = {
            "example": {
                "total_documents": 50,
                "total_chunks": 1250,
                "total_pages": 850,
                "categories": {"normativa": 30, "comercio": 20},
                "document_types": {"ley": 15, "formulario": 20, "ordenanza": 15}
            }
        }
