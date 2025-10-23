"""
Supabase client configuration and initialization
"""
from supabase import create_client, Client
from functools import lru_cache
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get cached Supabase client instance

    Returns:
        Client: Supabase client instance
    """
    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise


# Export singleton instance
supabase = get_supabase_client()
