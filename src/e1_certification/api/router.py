"""
API router configuration.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from e1_certification.api.dependencies import get_db
from e1_certification.db.models import Communaute
from e1_certification.utils.logging_config import logger

api_router = APIRouter()


# We'll add actual endpoints here in step 5
@api_router.get("/test", tags=["Testing"], summary="🚚 Test Router")
async def test_endpoint():
    """Test endpoint to verify routing works."""
    logger.info("🧪 Test endpoint for router")
    return {"message": "API router is working!"}


@api_router.get("/test-db", tags=["Testing"], summary="🗄️ Test Database")
async def test_database(db: Session = Depends(get_db)):
    """Test endpoint to verify database dependency works."""
    logger.info("🧪 Test endpoint for database")
    count = db.query(Communaute).count()
    return {"message": "Database connection working!", "communaute_count": count}
