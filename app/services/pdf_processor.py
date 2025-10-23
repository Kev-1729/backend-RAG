"""
PDF processing service
Handles PDF parsing, chunking, and storage with intelligent document type detection
"""
import os
import re
import hashlib
from typing import List, Dict, Any, Tuple
import logging
from pypdf import PdfReader

from app.core.config import settings
from app.utils.supabase_client import supabase
from app.services.embedding_service import get_embedding_service
from app.models.schemas import ProcessingStatus, ProcessingStatusEnum

logger = logging.getLogger(__name__)


class DocumentTypeDetector:
    """Detects document type and extracts metadata"""

    @staticmethod
    def detect(filename: str, text: str) -> Dict[str, Any]:
        """
        Detect document type based on filename and content

        Args:
            filename: Name of the file
            text: Document text content

        Returns:
            Dictionary with type, category, and metadata
        """
        filename_lower = filename.lower()
        text_lower = text.lower()

        # Formularios
        if any(keyword in filename_lower for keyword in ['formato', 'formulario', 'solicitud']):
            return DocumentTypeDetector._detect_form(filename_lower, text_lower)

        # Leyes
        if 'ley' in filename_lower or 'ley n°' in text_lower or 'ley nº' in text_lower:
            return DocumentTypeDetector._detect_law(filename_lower, text_lower)

        # Ordenanzas
        if 'ordenanza' in filename_lower or 'ordenanza' in text_lower:
            return {
                'type': 'ordenanza',
                'category': 'normativa',
                'metadata': {
                    'palabras_clave': ['ordenanza', 'municipalidad', 'normativa']
                }
            }

        # Decretos
        if 'decreto' in filename_lower or 'decreto' in text_lower:
            return {
                'type': 'decreto',
                'category': 'normativa',
                'metadata': {
                    'palabras_clave': ['decreto', 'alcaldía', 'municipalidad']
                }
            }

        # Reglamentos
        if 'reglamento' in filename_lower or 'reglamento' in text_lower:
            return {
                'type': 'reglamento',
                'category': 'normativa',
                'metadata': {
                    'palabras_clave': ['reglamento', 'normativa']
                }
            }

        # Trípticos/Guías
        if 'triptico' in filename_lower or 'guia' in filename_lower:
            return {
                'type': 'guia',
                'category': 'informacion',
                'metadata': {
                    'palabras_clave': ['información', 'guía', 'trámite']
                }
            }

        # Default
        return {
            'type': 'documento_general',
            'category': 'general',
            'metadata': {
                'palabras_clave': ['documento', 'municipal']
            }
        }

    @staticmethod
    def _detect_form(filename: str, text: str) -> Dict[str, Any]:
        """Detect form type"""
        tramite = 'Formulario General'
        keywords = ['formulario']

        if 'bodega' in filename or 'bodega' in text:
            tramite = 'Licencia Provisional de Funcionamiento para Bodegas'
            keywords.extend(['bodega', 'licencia', 'provisional'])
        elif 'ambulatorio' in filename or 'ambulatorio' in text:
            tramite = 'Autorización de Comercio Ambulatorio'
            keywords.extend(['ambulante', 'comercio', 'calle', 'permiso'])
        elif 'licencia' in filename or 'funcionamiento' in filename:
            tramite = 'Licencia de Funcionamiento'
            keywords.extend(['licencia', 'funcionamiento', 'comercio'])

        return {
            'type': 'formulario',
            'category': 'comercio',
            'metadata': {
                'nombre_tramite': tramite,
                'palabras_clave': keywords
            }
        }

    @staticmethod
    def _detect_law(filename: str, text: str) -> Dict[str, Any]:
        """Detect law type"""
        nombre_norma = 'Ley'
        numero_norma = ''
        keywords = ['ley', 'normativa', 'artículos']

        if '27972' in filename or 'municipalidades' in filename:
            nombre_norma = 'Ley Orgánica de Municipalidades'
            numero_norma = '27972'
            keywords.extend(['municipalidades', 'orgánica'])
        elif '1200' in filename:
            nombre_norma = 'Decreto Legislativo 1200'
            numero_norma = '1200'

        return {
            'type': 'ley',
            'category': 'normativa',
            'metadata': {
                'nombre_norma': nombre_norma,
                'numero_norma': numero_norma,
                'palabras_clave': keywords
            }
        }


class TextChunker:
    """Handles intelligent text chunking strategies"""

    @staticmethod
    def chunk_text(
        text: str,
        document_type: str,
        num_pages: int = 1,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """
        Split text into chunks based on document type and size

        Args:
            text: Input text
            document_type: Type of document
            num_pages: Number of pages in the document
            chunk_size: Maximum chunk size
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        # Strategy 1: Small documents (≤5 pages) - Keep whole for forms, guides, and procedures
        if num_pages <= 5 and document_type in ['formulario', 'guia', 'documento_general']:
            logger.info(f"Small document ({num_pages} pages, type: {document_type}) - keeping as single chunk")
            return [text]

        # Strategy 2: Legal documents - Split by articles (regardless of size)
        if document_type in ['ley', 'ordenanza', 'decreto', 'reglamento']:
            logger.info(f"Legal document detected - attempting to split by articles")
            article_chunks = TextChunker._chunk_by_articles(text)
            if len(article_chunks) > 1:
                logger.info(f"Successfully split into {len(article_chunks)} articles")
                return article_chunks
            # If no articles found, fall through to semantic chunking
            logger.info("No articles found, using semantic chunking")

        # Strategy 3: Large non-legal documents - Semantic chunking by paragraphs
        logger.info(f"Using semantic paragraph-based chunking for {document_type}")
        return TextChunker._chunk_by_paragraphs(text, chunk_size, overlap)

    @staticmethod
    def _chunk_by_articles(text: str) -> List[str]:
        """Split legal text by articles"""
        # Pattern for "ARTÍCULO X.-" or "Artículo Xº.-"
        pattern = r'(?:ART[ÍI]CULO\s+\d+[º°]?\s*\.?\s*-)'
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        chunks = []
        for i, match in enumerate(matches):
            chunk = (match + parts[i + 1]).strip()
            if chunk:
                chunks.append(chunk)

        return chunks if chunks else []

    @staticmethod
    def _chunk_by_paragraphs(text: str, max_chunk_size: int = 1500, overlap: int = 200) -> List[str]:
        """
        Split text by paragraphs while respecting semantic boundaries

        This method:
        1. Splits text into paragraphs
        2. Groups paragraphs until reaching max_chunk_size
        3. Maintains complete paragraphs (no mid-paragraph cuts)
        4. Adds overlap between chunks for context continuity
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        if not paragraphs:
            return [text]

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)

            # If single paragraph exceeds max size, split it by sentences
            if paragraph_size > max_chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph by sentences
                sentence_chunks = TextChunker._split_by_sentences(paragraph, max_chunk_size)
                chunks.extend(sentence_chunks)
                continue

            # If adding this paragraph exceeds max size, start new chunk
            if current_size + paragraph_size > max_chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))

                # Add overlap: keep last paragraph from previous chunk
                if len(current_chunk) > 1:
                    current_chunk = [current_chunk[-1], paragraph]
                    current_size = len(current_chunk[-2]) + paragraph_size
                else:
                    current_chunk = [paragraph]
                    current_size = paragraph_size
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size

        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [text]

    @staticmethod
    def _split_by_sentences(text: str, max_size: int = 1500) -> List[str]:
        """Split text by sentences when paragraphs are too large"""
        # Split by common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If single sentence is too large, force split
            if sentence_size > max_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                # Force split large sentence
                chunks.append(sentence[:max_size])
                if len(sentence) > max_size:
                    chunks.append(sentence[max_size:])
                continue

            if current_size + sentence_size > max_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    @staticmethod
    def _chunk_with_overlap(text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        DEPRECATED: Legacy method kept for backwards compatibility
        Use _chunk_by_paragraphs instead for better semantic chunking
        """
        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start += chunk_size - overlap

        return chunks


class PDFProcessor:
    """Service for processing PDF documents"""

    def __init__(self):
        """Initialize PDF processor"""
        self.embedding_service = get_embedding_service()
        self.detector = DocumentTypeDetector()
        self.chunker = TextChunker()
        logger.info("PDFProcessor initialized")

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def process_pdf(
        self,
        file_path: str,
        filename: str,
        category: str = None
    ) -> ProcessingStatus:
        """
        Process a single PDF document

        Args:
            file_path: Path to PDF file
            filename: Name of the file
            category: Optional category override

        Returns:
            ProcessingStatus with results
        """
        status = ProcessingStatus(
            document_id="",
            filename=filename,
            status=ProcessingStatusEnum.PROCESSING,
            progress=0
        )

        try:
            # 1. Parse PDF
            logger.info(f"Processing PDF: {filename}")
            text, num_pages = self._extract_text_from_pdf(file_path)
            status.progress = 20

            # 2. Detect document type
            doc_info = self.detector.detect(filename, text)
            logger.info(f"Document type detected: {doc_info['type']} (category: {doc_info['category']})")

            # 3. Calculate file hash
            file_hash = self.calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)
            status.progress = 30

            # 4. Check if document already exists
            existing = supabase.table('documents').select('id').eq('file_hash', file_hash).execute()
            if existing.data:
                logger.info(f"Document already exists: {filename}")
                status.status = ProcessingStatusEnum.COMPLETED
                status.progress = 100
                status.document_id = existing.data[0]['id']
                return status

            # 5. Insert document record
            document = supabase.table('documents').insert({
                'filename': filename,
                'original_path': file_path,
                'file_hash': file_hash,
                'file_size': file_size,
                'total_pages': num_pages,
                'document_type': doc_info['type'],
                'category': category or doc_info['category'],
                'metadata': doc_info['metadata'],
                'processed': False
            }).execute()

            if not document.data:
                raise Exception("Failed to insert document")

            document_id = document.data[0]['id']
            status.document_id = document_id
            status.progress = 40

            # 6. Chunk text with intelligent strategy
            chunks = self.chunker.chunk_text(
                text,
                doc_info['type'],
                num_pages=num_pages,
                chunk_size=settings.RAG_CHUNK_SIZE,
                overlap=settings.RAG_CHUNK_OVERLAP
            )
            logger.info(f"Created {len(chunks)} chunks for {num_pages}-page document (type: {doc_info['type']})")
            status.progress = 50

            # 7. Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            embeddings = await self.embedding_service.generate_batch_embeddings(chunks)
            status.progress = 80

            # 8. Insert chunks with embeddings
            chunks_to_insert = [
                {
                    'document_id': document_id,
                    'chunk_text': chunk,
                    'chunk_index': i,
                    'embedding': embedding,
                    'metadata': {'source': filename}
                }
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
            ]

            supabase.table('document_chunks').insert(chunks_to_insert).execute()

            # 9. Mark as processed
            supabase.table('documents').update({'processed': True}).eq('id', document_id).execute()

            status.status = ProcessingStatusEnum.COMPLETED
            status.progress = 100
            status.chunks_created = len(chunks)

            logger.info(f"Successfully processed: {filename} ({len(chunks)} chunks)")
            return status

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}", exc_info=True)
            status.status = ProcessingStatusEnum.ERROR
            status.error_message = str(e)
            return status

    def _extract_text_from_pdf(self, file_path: str) -> Tuple[str, int]:
        """
        Extract text from PDF file

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (text, number_of_pages)
        """
        try:
            reader = PdfReader(file_path)
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            text = "\n\n".join(text_parts)
            text = self._clean_text(text)

            return text, len(reader.pages)

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted PDF text"""
        # Fix hyphenated words across lines
        text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    async def process_multiple_pdfs(
        self,
        file_paths: List[str],
        category: str = None
    ) -> List[ProcessingStatus]:
        """
        Process multiple PDF files

        Args:
            file_paths: List of file paths
            category: Optional category for all files

        Returns:
            List of processing statuses
        """
        results = []

        for file_path in file_paths:
            filename = os.path.basename(file_path)
            result = await self.process_pdf(file_path, filename, category)
            results.append(result)

        return results


# Singleton instance
_pdf_processor: PDFProcessor = None


def get_pdf_processor() -> PDFProcessor:
    """Get singleton PDF processor instance"""
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PDFProcessor()
    return _pdf_processor
