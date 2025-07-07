"""
FastAPI application for E1 certification REST API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from e1_certification.api.router import api_router
from e1_certification.utils.logging_config import logger

# Create FastAPI instance
app = FastAPI(
    title="E1 Certification API",
    description="REST API for Collibra data catalog metadata",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
)

# Add CORS middleware (to configure properly later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, configure later
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods for now, configure later
    allow_headers=["*"],  # Allow all headers for now, configure later
)

# Include routers
app.include_router(api_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", summary="❤️ Health Check")
async def health_check():
    """Health check endpoint."""
    logger.info("❤️ Health check requested")
    return {"status": "healthy", "service": "e1-certification-api", "version": "1.0.0"}


# Create Lambda handler
handler = Mangum(app)
