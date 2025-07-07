"""
API router configuration.
"""

from fastapi import APIRouter

from e1_certification.utils.logging_config import logger

api_router = APIRouter()


# We'll add actual endpoints here in step 5
@api_router.get("/test", summary="🧪 Test Endpoint")
async def test_endpoint():
    """Test endpoint to verify routing works."""
    logger.info("🧪 Test endpoint for router")
    return {"message": "API router is working!"}
