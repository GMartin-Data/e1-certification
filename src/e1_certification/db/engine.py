"""
Database connection management for lambda Environment.
Handles connection pooling and lifecycle for serverless execution.
"""

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from e1_certification.config import settings
from e1_certification.utils.logging_config import logger

# Global engine instance (reused across Lambda invocations)
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def create_db_engine(
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
    pool_recycle: int = 3_600,
) -> Engine:
    """
    Create SQLAlchemy engine optimized for Lambda.

    Args:
        pool_size: Number of persistent connections
        max_overflow: Maximum overflow connections
        pool_timeout: Timeout in seconds for getting connection from pool
        pool_recycle: Recycle connections after this many seconds

    Returns:
        Configured SQLAlchemy engine
    """
    if not settings.database_url:
        raise ValueError(
            "Database URL not configured. "
            "Please set DB_HOST, DB_USER, and DB_PASSWORD environment variables."
        )

    # Base config
    engine_config: dict[str, Any] = {
        "pool_pre_ping": True,  # Verify connections before use
        "echo": settings.log_level == "DEBUG",  # SQL logging in debug mode
    }

    # For Lambda, use Nullpool wihout pool parameters to prevent connection leaks
    if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        logger.info("📡 Detected Lambda environment, using NullPool")
        engine_config["poolclass"] = pool.NullPool
    else:
        # Only add pool settings for non-Lambda environments
        engine_config.update(
            {
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_timeout": pool_timeout,
                "pool_recycle": pool_recycle,
            }
        )

    engine = create_engine(settings.database_url, **engine_config)

    # Add connection event listeners for debugging
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.debug("🟢 Database connection established")

    @event.listens_for(engine, "close")
    def receive_close(dbapi_connection, connection_record):
        logger.debug("🔴 Database connection closed")

    return engine


def get_engine() -> Engine:
    """
    Get or create the global engine instance.

    Returns:
        SQLAlchemy engine
    """
    global _engine
    if _engine is None:
        logger.info("🚂 Creating new database engine")
        _engine = create_db_engine()
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the global session factory.

    Returns:
        SQLAlchemy session factory
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,  # Require explicit commit() calls (safer)
            autoflush=False,  # Don't auto-send changes before queries
            expire_on_commit=False,  # Don't refetch data after commit (Lambda optimization)
        )
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Ensures proper cleanup even if lambda times out.

    Yields:
        SQLAlchemy session

    Example:
        with get_db_session() as session:
            result = session.query(Model).all()
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("❌ Database session error, rolling back")
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database connection.
    Useful for Lambda cold starts to fail fast if DB is unreachable.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"✅ Database connection test successful: {result.scalar()}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database connection: {e}")
        raise


def close_db_connections() -> None:
    """
    Close all database connections.
    Useful for cleanup in Lambda environment.
    """
    global _engine, _SessionLocal
    if _engine is not None:
        logger.info("🧹 Disposing database engine")
        _engine.dispose()
        _engine = None
        _SessionLocal = None
