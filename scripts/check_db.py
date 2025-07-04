#!/usr/bin/env python3
"""
Database connection health check script.
Tests database connectivity and basic operations.
"""

import sys
from pathlib import Path

from sqlalchemy import text

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from e1_certification.config import settings  # noqa: E402
from e1_certification.db import get_db_session, init_db  # noqa: E402
from e1_certification.utils.logging_config import logger  # noqa: E402


def check_database() -> bool:
    """Run database health checks."""
    logger.info("🩺 Starting database health check...")

    # Check configuration
    if not settings.database_url:
        logger.error("❌ Database URL not configured!")
        logger.info("👉 Please set the following environment variables:")
        logger.info("Please set the following environment variables:")
        logger.info("  - DB_HOST")
        logger.info("  - DB_USER")
        logger.info("  - DB_PASSWORD")
        return False

    logger.info(
        f"✅ Database URL configured: mysql://{settings.db_user}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )

    # Test connection
    try:
        logger.info("🧪 Testing database connection...")
        init_db()
        logger.info("  ✅ Database connection successful!")
    except Exception as e:
        logger.error(f"  ❌ Database connection failed: {e}")
        return False

    # Test session creation
    try:
        logger.info("🧪 Testing session creation...")
        with get_db_session() as session:
            result = session.execute(text("SELECT VERSION()"))
            version = result.scalar()
            logger.info(f"✅ MySQL version: {version}")
    except Exception as e:
        logger.error(f"❌ Session test failed: {e}")
        return False

    logger.info("✅ All database health checks passed!")
    return True


if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)  # Exit with 0 if checks passed, 1 if failed
