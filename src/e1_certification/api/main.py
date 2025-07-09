"""
FastAPI application for E1 certification REST API.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from e1_certification.api.router import api_router
from e1_certification.utils.logging_config import logger

# Create FastAPI instance
app = FastAPI(
    title="E1 Certification API - Collibra Data Catalog",
    description="""
    ## 🎯 Overview

    REST API for accessing Collibra data catalog metadata.
    Provides read access to communities, domains, tables, and columns,
    with authentication-protected write operations.

    ## 🔐 Authentication

    Use `/api/v1/auth/login` with test credentials:
    - Username: `admin`, Password: `admin123`
    - Username: `demo`, Password: `demo123`

    ## 📚 Key Features

    - **Smart filtering**: Tables/columns must be filtered by parent
    - **Pagination**: For large result sets (domains, tables, columns)
    - **JWT Auth**: Secure endpoints for modifications
    - **ETL Integration**: Data synced from Collibra daily

    ## ⚠️ Note

    All modifications will be overwritten by the next ETL run.
    This API is primarily for read access and temporary updates.
    """,
    version="1.0.0",
    root_path=os.environ.get("API_GATEWAY_STAGE", ""),  # For AWS Lambda
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    openapi_tags=[
        {"name": "Testing", "description": "🧪 Test endpoints for development"},
        {"name": "Communities", "description": "🏛️ Community operations"},
        {"name": "Domains", "description": "📁 Domain operations"},
        {
            "name": "Tables",
            "description": "📅 Table operations (auth required for modifications)",
        },
        {
            "name": "Columns",
            "description": "📏 Column operations (auth required for modifications)",
        },
        {"name": "Authentication", "description": "🔐 Login and token management"},
    ],
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

logger.info("🚀 E1 Certification API initialized")


# Health check endpoint
@app.get("/health", summary="❤️ Health Check")
async def health_check():
    """Health check endpoint."""
    logger.info("❤️ Health check requested")
    return {"status": "healthy", "service": "e1-certification-api", "version": "1.0.0"}


# Create Lambda handler
handler = Mangum(app)
