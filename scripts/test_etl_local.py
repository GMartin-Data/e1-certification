#!/usr/bin/env python3
"""
Test ETL processor locally with sample Excel files.
Place test Excel files in data/excel/pending before running.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from e1_certification.db import init_db  # noqa: E402
from e1_certification.etl.processor import CollibraETLProcessor  # noqa: E402
from e1_certification.utils.logging_config import logger  # noqa: E402


def test_etl_local() -> None:
    """Test ETL processing with local files."""

    # Initialize database
    logger.info("🔌 Initializing database connection...")
    init_db()

    # Define test file paths
    excel_dir = Path("data/excel/pending")
    file_paths = {}

    # Look for Excel files
    for pattern, entity_type in [
        ("*commun*.xlsx", "communautes"),
        ("*domain*.xlsx", "domaines"),
        ("*table*.xlsx", "data_tables"),
        ("*col*.xlsx", "data_colonnes"),
    ]:
        files = list(excel_dir.glob(pattern))
        if files and entity_type not in file_paths:
            file_paths[entity_type] = files[0]
            logger.info(f"📄 Found {entity_type}: {files[0].name}")

    if not file_paths:
        logger.error("❌ No Excel files found in data/excel/pending")
        return

    # Process files
    logger.info("\n🚀 Starting ETL processing...")

    try:
        processor = CollibraETLProcessor(file_paths)
        stats = processor.process_all()

        logger.info("\n✅ ETL processing complete!")
        logger.info("📊 Statistics:")
        for entity, entity_stats in stats.items():
            if isinstance(entity_stats, dict):
                logger.info(f"  - {entity}: {entity_stats['loaded']} records")

        # Show errors if any were collected
        if stats.get("errors"):
            logger.warning(f"⚠️  Errors encountered: {stats['errors']}")

    except Exception as e:
        logger.error(f"❌ ETL processing failed: {e}")
        raise


if __name__ == "__main__":
    test_etl_local()
