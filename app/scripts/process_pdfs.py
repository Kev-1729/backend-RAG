"""
Script to process PDFs from a local directory
Usage: python -m app.scripts.process_pdfs
"""
import os
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.pdf_processor import get_pdf_processor
from app.core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Process all PDFs in the documentos_a_procesar directory"""

    # Get the documents directory (relative to project root)
    project_root = Path(__file__).parent.parent.parent.parent
    documents_dir = project_root / "documentos_a_procesar"

    logger.info(f"🚀 Starting PDF processing from: {documents_dir}")

    if not documents_dir.exists():
        logger.warning(f"📂 Directory {documents_dir} doesn't exist. Creating it...")
        documents_dir.mkdir(parents=True)
        logger.info("✅ Directory created. Add PDFs to this folder and run the script again.")
        return

    # Get all PDF files
    pdf_files = list(documents_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning("⚠️  No PDF files found in the directory.")
        return

    logger.info(f"📄 Found {len(pdf_files)} PDF files to process")

    # Get PDF processor
    pdf_processor = get_pdf_processor()

    # Process each PDF
    results = []
    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_path.name}")
        logger.info(f"{'='*60}")

        result = await pdf_processor.process_pdf(
            str(pdf_path),
            pdf_path.name,
            category=None  # Auto-detect category
        )

        results.append(result)

        if result.status == "completed":
            logger.info(f"✅ Successfully processed: {pdf_path.name}")
            logger.info(f"   - Document ID: {result.document_id}")
            logger.info(f"   - Chunks created: {result.chunks_created}")
        elif result.status == "error":
            logger.error(f"❌ Failed to process: {pdf_path.name}")
            logger.error(f"   - Error: {result.error_message}")

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 PROCESSING SUMMARY")
    logger.info(f"{'='*60}")

    successful = sum(1 for r in results if r.status == "completed")
    failed = sum(1 for r in results if r.status == "error")
    total_chunks = sum(r.chunks_created or 0 for r in results)

    logger.info(f"✅ Successful: {successful}/{len(results)}")
    logger.info(f"❌ Failed: {failed}/{len(results)}")
    logger.info(f"📦 Total chunks created: {total_chunks}")
    logger.info(f"\n🎉 Processing complete!")


if __name__ == "__main__":
    asyncio.run(main())
