"""
Authentication utilities for the API.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from e1_certification.config import settings
from e1_certification.utils.logging_config import logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any]) -> str:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token (usually: {"sub": username})

    Returns:
        Encoded JWT token as a string
    """
    to_encode = data.copy()

    # Add expiration time
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiration_minutes)
    to_encode.update({"exp": expire})

    # Create the token
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    logger.debug(f"🔐 Created JWT token expiring at {expire}")
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode a JWT access token

    Args:
        token: JWT token to decode

    Returns:
        Decoded token data as a dictionary or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        logger.warning(f"⚠️ JWT decode error: {e}")
        return None


# Mock user database (for demo purposes)
# In production, this would come from a real database
MOCK_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),  # Password: admin123
        "is_active": True,
    },
    "demo": {
        "username": "demo",
        "hashed_password": get_password_hash("demo123"),  # Password: demo123
        "is_active": True,
    },
}


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    """
    Authenticate a user.

    Args:
        username: Username to authenticate
        password: Plain text password

    Returns:
        User dict if authenticated, None otherwise
    """
    user = MOCK_USERS_DB.get(username)
    if not user:
        logger.warning(f"🚫 Authentication failed: User {username} not found")
        return None

    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"🚫 Authentication failed: Invalid password for {username}")
        return None

    logger.info(f"✅ User {username} authenticated successfully")
    return user
