"""
API router configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from e1_certification.api.dependencies import get_db
from e1_certification.api.schemas import (
    CommunauteListResponse,
    CommunauteResponse,
    DataColonneListResponse,
    DataColonneResponse,
    DataTableListResponse,
    DataTableResponse,
    DomaineListResponse,
    DomaineResponse,
    PaginationInfo,
)
from e1_certification.db.models import (
    Communaute,
    DataColonne,
    DataTable,
    Domaine,
)
from e1_certification.utils.logging_config import logger

api_router = APIRouter()


# ========== Testing Endpoints ==========
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


# ========== Community Endpoints ==========
@api_router.get(
    "/communities",
    response_model=CommunauteListResponse,
    tags=["Communities"],
    summary="📋 List All Communities",
    status_code=status.HTTP_200_OK,
)
async def get_communities(db: Session = Depends(get_db)):
    """
    Get all communities.

    No pagination needed, as there are only ~20 communities.
    """
    logger.info("🏛️ Fetching all communities")

    communities = db.query(Communaute).order_by(Communaute.nom).all()

    logger.info(f"✅ Found {len(communities)} communities")

    # Convert SQLAlchemy objects to Pydantic models
    community_responses = [
        CommunauteResponse.model_validate(comm) for comm in communities
    ]
    return CommunauteListResponse(data=community_responses)


@api_router.get(
    "/communities/{community_id}",
    response_model=CommunauteResponse,
    tags=["Communities"],
    summary="🔎 Get Community by ID",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Community not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def get_community(
    community_id: int = Path(..., description="Community ID"),
    db: Session = Depends(get_db),
):
    """Get a specific community by ID"""
    logger.info(f"🏛️ Fetching community with ID {community_id}")

    community = db.query(Communaute).filter(Communaute.id == community_id).first()

    if not community:
        logger.warning(f"⚠️ Community with ID {community_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Community not found"
        )

    return community


# ========== Domain Endpoints ==========
@api_router.get(
    "/domains",
    response_model=DomaineListResponse,
    tags=["Domains"],
    summary="📋 List Domains",
)
async def get_domains(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    communaute_id: int | None = Query(None, description="Filter by community ID"),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of domains.

    Can optionally filter by community ID.
    """
    logger.info(
        f"📁 Fetching domains (page={page}, per_page={per_page}, communaute_id={communaute_id})"
    )

    # Base query
    query = db.query(Domaine).order_by(Domaine.nom)

    # Apply filter if provided
    if communaute_id is not None:
        query = query.filter(Domaine.communaute_id == communaute_id)

    # Get total count
    total = query.count()

    # Calculate pagination
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Get paginated results
    domains = query.offset(offset).limit(per_page).all()
    logger.info(f"✅ Found {len(domains)} domains (page {page}/{pages})")

    # Convert SQLAlchemy objects to Pydantic models
    domain_responses = [DomaineResponse.model_validate(dom) for dom in domains]

    return DomaineListResponse(
        data=domain_responses,
        pagination=PaginationInfo(
            total=total, page=page, per_page=per_page, pages=pages
        ),
    )


@api_router.get(
    "/domains/{domain_id}",
    response_model=DomaineResponse,
    tags=["Domains"],
    summary="🔎 Get Domain by ID",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Domain not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def get_domain(
    domain_id: str = Path(..., description="Domain ID"), db: Session = Depends(get_db)
):
    """Get a specific domain by ID."""
    logger.info(f"📁 Fetching domain with ID {domain_id}")

    domain = db.query(Domaine).filter(Domaine.id == domain_id).first()

    if not domain:
        logger.warning(f"⚠️ Domain with ID {domain_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {domain_id} not found",
        )

    return domain


# ========== Table Endpoints ==========
@api_router.get(
    "/domains/{domain_id}/tables",
    response_model=DataTableListResponse,
    tags=["Tables"],
    summary="📋 List Tables by Domain",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Domain not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def get_tables_by_domain(
    domain_id: str = Path(..., description="Domain ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of tables for a specific domain.

    Tables must be filtered by domain ID (no GET all endpoint).
    """
    logger.info(
        f"📅 Fetching tables for domain with ID: {domain_id} (page={page}, per_page={per_page})"
    )

    # Check domain exists
    domain = db.query(Domaine).filter(Domaine.id == domain_id).first()
    if not domain:
        logger.warning(f"⚠️ Domain with ID {domain_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {domain_id} not found",
        )

    # Query tables
    query = (
        db.query(DataTable)
        .filter(DataTable.domaine_id == domain_id)
        .order_by(DataTable.nom)
    )

    # Get total count
    total = query.count()

    # Calculate pagination
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Get paginated results
    tables = query.offset(offset).limit(per_page).all()

    logger.info(
        f"✅ Found {len(tables)} tables in domain {domain_id} (page {page}/{pages})"
    )

    # Convert SQLAlchemy objects to Pydantic models
    table_responses = [DataTableResponse.model_validate(table) for table in tables]

    return DataTableListResponse(
        data=table_responses,
        pagination=PaginationInfo(
            total=total, page=page, per_page=per_page, pages=pages
        ),
    )


@api_router.get(
    "/tables/{table_id}",
    response_model=DataTableResponse,
    tags=["Tables"],
    summary="🔍 Get Table by ID",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Table not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def get_table(
    table_id: str = Path(..., description="Table ID"), db: Session = Depends(get_db)
):
    """Get a specific table by ID."""
    logger.info(f"📅 Fetching table with ID {table_id}")

    table = db.query(DataTable).filter(DataTable.id == table_id).first()

    if not table:
        logger.warning(f"⚠️ Table with ID {table_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID {table_id} not found",
        )

    return table


# ========== Column Endpoints ==========
@api_router.get(
    "/tables/{table_id}/columns",
    response_model=DataColonneListResponse,
    tags=["Columns"],
    summary="📋 List Columns by Table",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Table not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def get_columns_by_table(
    table_id: str = Path(..., description="Table ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of columns for a specific table.

    Columns must be filtered by table (no GET all endpoint).
    Some tables have 500+ columns, so pagination is essential.
    """
    logger.info(
        f"📏 Fetching columns for table {table_id} (page={page}, per_page={per_page})"
    )

    # Check table exists
    table = db.query(DataTable).filter(DataTable.id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Table {table_id} not found"
        )

    # Query columns
    query = (
        db.query(DataColonne)
        .filter(DataColonne.data_table_id == table_id)
        .order_by(DataColonne.nom)
    )

    # Get total count
    total = query.count()

    # Calculate pagination
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page

    # Get paginated results
    columns = query.offset(offset).limit(per_page).all()

    logger.info(
        f"✅ Found {len(columns)} columns in table {table_id} (page {page}/{pages})"
    )

    # Convert SQLAlchemy objects to Pydantic models
    column_responses = [DataColonneResponse.model_validate(col) for col in columns]

    return DataColonneListResponse(
        data=column_responses,
        pagination=PaginationInfo(
            total=total, page=page, per_page=per_page, pages=pages
        ),
    )


@api_router.get(
    "/columns/{column_id}",
    response_model=DataColonneResponse,
    tags=["Columns"],
    summary="🔍 Get Column by ID",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Column not found"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)
async def get_column(
    column_id: str = Path(..., description="Column ID"), db: Session = Depends(get_db)
):
    """Get a specific column by ID."""
    logger.info(f"📏 Fetching column with ID {column_id}")

    column = db.query(DataColonne).filter(DataColonne.id == column_id).first()

    if not column:
        logger.warning(f"⚠️ Column with ID {column_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with ID {column_id} not found",
        )

    return column
