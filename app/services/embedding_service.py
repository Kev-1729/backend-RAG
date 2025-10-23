"""
Embedding service using Google Gemini AI
"""
import google.generativeai as genai
from typing import List
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using Gemini"""

    def __init__(self):
        """Initialize Gemini AI client"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_EMBEDDING_MODEL
        logger.info(f"EmbeddingService initialized with model: {self.model_name}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector (768 dimensions)
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=f"models/{self.model_name}",
                    content=text,
                    task_type="retrieval_document"
                )
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query

        Args:
            query: Search query text

        Returns:
            List of floats representing the embedding vector
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=f"models/{self.model_name}",
                    content=query,
                    task_type="retrieval_query"
                )
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        delay_ms: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with rate limiting

        Args:
            texts: List of texts to embed
            delay_ms: Delay between requests in milliseconds

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for i, text in enumerate(texts):
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)

                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(f"Generated embeddings: {i + 1}/{len(texts)}")

                # Rate limiting
                if i < len(texts) - 1:
                    await asyncio.sleep(delay_ms / 1000)

            except Exception as e:
                logger.error(f"Error embedding text {i}: {e}")
                raise

        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings


# Singleton instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
