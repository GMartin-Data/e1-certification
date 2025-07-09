"""Lambda handler fo REST API."""

from typing import Any

from e1_certification.api.main import handler as fastapi_handler
from e1_certification.db import close_db_connections, init_db
from e1_certification.utils.logging_config import logger


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda handler that wraps FastAPI application.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    logger.info(
        f" 🌐API Lambda started: {event.get('httpMethod)')} {event.get('path')}"
    )

    try:
        # Initialize database connection
        init_db()

        # Let FastAPI handle the request
        response = fastapi_handler(event, context)

        return response

    finally:
        # Clean up database connections
        close_db_connections()
