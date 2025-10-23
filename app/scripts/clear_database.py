"""
Script to clear all documents and chunks from Supabase
Usage: python -m app.scripts.clear_database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.supabase_client import supabase
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_database():
    """Clear all documents and chunks from the database"""

    logger.info("🗑️  Starting database cleanup...")

    try:
        # Get current counts
        chunks_response = supabase.table('document_chunks').select('id', count='exact').execute()
        docs_response = supabase.table('documents').select('id', count='exact').execute()

        chunks_count = chunks_response.count if chunks_response.count else 0
        docs_count = docs_response.count if docs_response.count else 0

        logger.info(f"📊 Current database status:")
        logger.info(f"   - Documents: {docs_count}")
        logger.info(f"   - Chunks: {chunks_count}")

        if chunks_count == 0 and docs_count == 0:
            logger.info("✅ Database is already empty!")
            return

        # Delete all chunks first (due to foreign key constraint)
        logger.info("\n🗑️  Deleting all document chunks...")
        supabase.table('document_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        logger.info(f"✅ Deleted {chunks_count} chunks")

        # Delete all documents
        logger.info("🗑️  Deleting all documents...")
        supabase.table('documents').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        logger.info(f"✅ Deleted {docs_count} documents")

        logger.info("\n🎉 Database cleanup completed successfully!")
        logger.info("You can now process PDFs to generate new chunks.")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    clear_database()
