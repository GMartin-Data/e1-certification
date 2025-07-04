"""
Test script to create and verify database tables.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from e1_certification.db import Base, get_engine, init_db  # noqa: E402
from e1_certification.db.models import MODEL_REGISTRY  # noqa: E402
from e1_certification.utils.logging_config import logger  # noqa: E402
from sqlalchemy import inspect  # noqa: E402


def create_tables() -> bool:
    """
    Create all tables in the database.

    Returns:
        bool: True if tables were created successfully, False otherwise.
    """
    logger.info("🔨 Creating database tables...")

    try:
        # Initialize connection
        init_db()

        # Get engine
        engine = get_engine()

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully.")

        # List created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"\n📋 Created {len(tables)} tables:")
        for table in sorted(tables):
            # Get model class name
            model_name = next(
                (name for name, model in MODEL_REGISTRY.items() if name == table),
                "Unknown",  # Add this default
            )
            logger.info(f"  - {table} (Model: {model_name})")

            # Show columns
            columns = inspector.get_columns(table)
            for col in columns:
                logger.info(f"    • {col['name']}: {col['type']}")

    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False

    return True


def verify_relationships() -> None:
    """Verify foreign key relationships."""
    logger.info("\n🔗 Verifying relationships...")

    engine = get_engine()
    inspector = inspect(engine)

    for table_name in sorted(inspector.get_table_names()):
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            logger.info(f"\n  {table_name}:")
            for fk in fks:
                logger.info(
                    f"    → {fk['name']}: {fk['constrained_columns']} "
                    f"references {fk['referred_table']}.{fk['referred_columns']}"
                )


def test_basic_operations() -> bool:
    """Test basic database operations."""
    logger.info("\n🧪 Testing basic operations...")

    from e1_certification.db import get_db_session
    from e1_certification.db.models import Communaute

    try:
        with get_db_session() as session:
            # Test insert
            test_community = Communaute(
                nom="Test Community",
                description="Created by test script",
            )
            session.add(test_community)
            session.commit()

            logger.info(f"✅ ➕ Inserted test record with ID: {test_community.id}")

            # Test query
            result = session.query(Communaute).filter_by(nom="Test Community").first()
            logger.info(f"✅ 📥 Retrieved: {result}")

            # Clean up
            session.delete(result)
            session.commit()
            logger.info("✅ 🗑️ Cleaned up test record.")

    except Exception as e:
        logger.error(f"❌ Operations test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    logger.info("🚀 Starting database model test...\n")

    # Create tables
    if not create_tables():
        sys.exit(1)

    # Verify relationships
    verify_relationships()

    # Test operations
    if not test_basic_operations():
        sys.exit(1)

    logger.info("\n✨ All tests passed successfully!")

    # Ask if user wants to drop tables
    response = input("\n❓ Drop all tables? (y/N): ")
    if response.lower() == "y":
        engine = get_engine()
        Base.metadata.drop_all(bind=engine)
        logger.info("🧹  Tables dropped successfully!")
    else:
        logger.info("📌 Tables kept in database.")
