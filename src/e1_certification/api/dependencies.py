"""
FastAPI dependencies for the API.

Provides reusable dependencies for database sessions,
authentication, and other cross-cutting concerns.
"""

from collections.abc import Generator
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from e1_certification.api.auth import decode_access_token
from e1_certification.db import get_db_session
from e1_certification.utils.logging_config import logger


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Automatically handles session lifecycle:
    - Creates session when endpoint is called
    - Yields it to the endpoint function
    - Closes it after the request completes (even on error)

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


# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    """
    Validate JWT token and return current user.

    This dependency will:
        1. Extract token from Authorization header
        2. Decode and validate the token
        3. Return user info or raise 401

    Args:
        token: JWT token from Authorization header

    Returns:
        User information from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Decode token
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract username from token
    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    logger.debug(f"✅ Authenticated user: {username}")
    return {"username": username}
