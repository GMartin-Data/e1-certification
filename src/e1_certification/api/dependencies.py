"""
FastAPI dependencies for the API.

Provides reusable dependencies for database sessions,
authentication, and other cross-cutting concerns.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from e1_certification.db import get_db_session
from e1_certification.utils.logging_config import logger


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Automatically handles session lifecycle:
    - Creates session when endpoint is called
    - Yields it to the endpoint function
    - Coses it after the request completes (even on error)

    Usage in endpoint:
        @app.get("/items/")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    logger.debug("🌱 Creating database session for request")

    with get_db_session() as session:
        try:
            yield session
            logger.debug("✅ Database session completed successfully")
        except Exception as e:
            logger.error(f"❌ Database error in request: {e}")
            raise
        finally:
            logger.debug("🔒 Closing database session")


# Future auth dependency will go here
