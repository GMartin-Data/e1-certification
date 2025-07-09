"""
API router configuration.
"""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from e1_certification.api.auth import authenticate_user, create_access_token
from e1_certification.api.dependencies import get_current_user, get_db
from e1_certification.api.schemas import (
    CommunauteListResponse,
    CommunauteResponse,
    DataColonneCreate,
    DataColonneListResponse,
    DataColonneResponse,
    DataColonneUpdate,
    DataTableCreate,
    DataTableListResponse,
    DataTableResponse,
    DataTableUpdate,
    DomaineListResponse,
    DomaineResponse,
    PaginationInfo,
    TokenResponse,
)
from e1_certification.config import settings
from e1_certification.db.models import (
    Communaute,
    DataColonne,
    DataTable,
    Domaine,
)
from e1_certification.utils.logging_config import logger


class ExampleIDs:
    """Real IDs from database for testing."""

    COMMUNITY_ID = 6
    DOMAIN_ID = "01929505-432d-7f75-a3f1-9aecc9464478"
    TABLE_ID = "018e80b4-9a34-74cf-aabc-3972e0070cc3"
    COLUMN_ID = "01aa6d4f-5207-4d85-8006-29c311f5c5bb"

    # For filters
    COMMUNITY_WITH_MANY_DOMAINS = 2  # Has 50+ domains
    DOMAIN_WITH_MANY_TABLES = "3ba5be8f-98cc-4179-9c9f-df720a664784"  # Has 150+ tables
    TABLE_WITH_MANY_COLUMNS = (
        "2c986526-ecf4-43d7-90f1-da0dca3e2b05"  # Has about 1900 columns
    )


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
    community_id: int = Path(
        ..., description="Community ID", example=ExampleIDs.COMMUNITY_ID
    ),
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
    communaute_id: int | None = Query(
        None,
        description="Filter by community ID",
        example=ExampleIDs.COMMUNITY_WITH_MANY_DOMAINS,
    ),
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
    domain_id: str = Path(..., description="Domain ID", example=ExampleIDs.DOMAIN_ID),
    db: Session = Depends(get_db),
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
    domain_id: str = Path(
        ..., description="Domain ID", example=ExampleIDs.DOMAIN_WITH_MANY_TABLES
    ),
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
    table_id: str = Path(..., description="Table ID", example=ExampleIDs.TABLE_ID),
    db: Session = Depends(get_db),
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


# ========== Protected Table Endpoints (CUD) ==========
@api_router.post(
    "/tables",
    response_model=DataTableResponse,
    tags=["Tables"],
    summary="➕ Create Table",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Domain not found"},
    },
)
async def create_table(
    table: DataTableCreate = Body(
        ...,
        example={
            "nom": "Test Table API Demo",
            "description": "Table created via API for testing",
            "domaine_id": ExampleIDs.DOMAIN_ID,
        },
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new table.

    **Requires authentication**

    Note: Changes will be overwritten by next ETL run.
    """
    logger.info(f"➕ User {current_user['username']} creating table: {table.nom}")

    # NOTE: The table ID can't already exist, due to algorithm choice to generate it

    # Check domain exists
    domain = db.query(Domaine).filter(Domaine.id == table.domaine_id).first()
    if not domain:
        logger.warning(f"⚠️ Domain with ID {table.domaine_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {table.domaine_id} not found",
        )

    # Create new table with generated IDs and dates
    new_table = DataTable(
        id=str(uuid.uuid4()),
        **table.model_dump(),
        date_creation=date.today(),
        date_derniere_modification=date.today(),
    )

    db.add(new_table)
    db.commit()
    db.refresh(new_table)

    logger.info(f"✅ Table {new_table.id} created by {current_user['username']}")
    return new_table


@api_router.put(
    "/tables/{table_id}",
    response_model=DataTableResponse,
    tags=["Tables"],
    summary="✏️ Update Table",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Table not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid update data"},
    },
)
async def update_table(
    table_id: str = Path(..., description="Table ID"),
    table_update: DataTableUpdate = Body(
        ...,
        example={
            "nom": "Updated Table Name",
            "description": "Updated description via API",
            "domaine_id": ExampleIDs.DOMAIN_WITH_MANY_TABLES,  # Different domain than for CREATE
        },
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing table.

    **Requires authentication**

    Only provided fields will be updated.
    The modification date will be automatically set.

    Note: Changes will be overwritten by next ETL run.
    """
    logger.info(f"✏️ User {current_user['username']} updating table: {table_id}")

    # Get existing table
    table = db.query(DataTable).filter(DataTable.id == table_id).first()
    if not table:
        logger.warning(f"⚠️ Table with ID {table_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID {table_id} not found",
        )

    # Update only provided fields
    update_data = table_update.model_dump(exclude_unset=True)

    # If domain_id is being updated, verify it exists
    if "domaine_id" in update_data:
        domain = (
            db.query(Domaine).filter(Domaine.id == update_data["domaine_id"]).first()
        )
        if not domain:
            logger.warning(f"⚠️ Domain with ID {update_data['domaine_id']} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain with ID {update_data['domaine_id']} not found",
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(table, field, value)

    # Update modification date
    table.date_derniere_modification = date.today()  # type: ignore[assignment]

    db.commit()
    db.refresh(table)

    logger.info(f"✅ Table {table_id} updated by {current_user['username']}")
    return table


@api_router.delete(
    "/tables/{table_id}",
    tags=["Tables"],
    summary="🗑️ Delete Table",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Table not found"},
    },
)
async def delete_table(
    table_id: str = Path(..., description="Table ID"),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a table.

    **Requires authentication**

    ⚠️ **WARNING**: This will also delete all columns belonging to this table!

    Note: Table will be restored on next ETL run.
    """
    logger.info(f"🗑️ User {current_user['username']} deleting table: {table_id}")

    # Get existing table
    table = db.query(DataTable).filter(DataTable.id == table_id).first()
    if not table:
        logger.warning(f"⚠️ Table with ID {table_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID {table_id} not found",
        )

    # Count columns that will be deleted (for logging)
    column_count = (
        db.query(DataColonne).filter(DataColonne.data_table_id == table_id).count()
    )

    # Delete table (cascades to columns)
    db.delete(table)
    db.commit()

    logger.info(
        f"✅ Table with ID: {table_id} and its {column_count} columns deleted by {current_user['username']}"
    )

    # 204 No Content - successful deletion returns no body
    return None


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
    table_id: str = Path(
        ..., description="Table ID", example=ExampleIDs.TABLE_WITH_MANY_COLUMNS
    ),
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
    column_id: str = Path(..., description="Column ID", example=ExampleIDs.COLUMN_ID),
    db: Session = Depends(get_db),
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


# ========== Protected Column Endpoints (CUD) ==========
@api_router.post(
    "/columns",
    response_model=DataColonneResponse,
    tags=["Columns"],
    summary="➕ Create Column",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Table not found"},
    },
)
async def create_column(
    column: DataColonneCreate = Body(
        ...,
        example={
            "nom": "test_column_api",
            "description": "Column created via API for testing",
            "data_type": "VARCHAR(255)",
            "data_table_id": ExampleIDs.TABLE_ID,
        },
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new column.

    **Requires authentication**

    Note: Changes will be overwritten by next ETL run.
    """
    logger.info(f"➕ User {current_user['username']} creating column: {column.nom}")

    # Check table exists
    table = db.query(DataTable).filter(DataTable.id == column.data_table_id).first()
    if not table:
        logger.warning(f"⚠️ Table with ID {column.data_table_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID {column.data_table_id} not found",
        )

    # Create new column with generated ID and dates
    new_column = DataColonne(
        id=str(uuid.uuid4()),
        **column.model_dump(),
        date_creation=date.today(),
        date_derniere_modification=date.today(),
    )

    db.add(new_column)
    db.commit()
    db.refresh(new_column)

    logger.info(
        f"✅ Column {new_column.id} created in table {column.data_table_id} by {current_user['username']}"
    )
    return new_column


@api_router.put(
    "/columns/{column_id}",
    response_model=DataColonneResponse,
    tags=["Columns"],
    summary="✏️ Update Column",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Column not found"},
    },
)
async def update_column(
    column_id: str = Path(..., description="Column ID"),
    column_update: DataColonneUpdate = Body(
        ...,
        example={
            "nom": "updated_column_name",
            "description": "Updated column description",
            "data_type": "INTEGER",
            "data_table_id": ExampleIDs.TABLE_WITH_MANY_COLUMNS,  # Different table than for CREATE column
        },
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing column.

    **Requires authentication**

    Only provided fields will be updated.
    The modification date will be automatically set.

    Note: Change will be overwritten by next ETL run.
    """
    logger.info(f"✏️ User {current_user['username']} updating column: {column_id}")

    # Get existing column
    column = db.query(DataColonne).filter(DataColonne.id == column_id).first()
    if not column:
        logger.warning(f"⚠️ Column with ID {column_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with ID {column_id} not found",
        )

    # Update only provided fields
    update_data = column_update.model_dump(exclude_unset=True)

    # If data_table_id is being updated, verify it exists
    if "data_table_id" in update_data:
        table = (
            db.query(DataTable)
            .filter(DataTable.id == update_data["data_table_id"])
            .first()
        )
        if not table:
            logger.warning(f"⚠️ Table with ID {update_data['data_table_id']} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table with ID {update_data['data_table_id']} not found",
            )

    # Apply updates
    for field, value in update_data.items():
        setattr(column, field, value)

    # Update modification date
    column.date_derniere_modification = date.today()  # type: ignore[assignment]

    db.commit()
    db.refresh(column)

    logger.info(f"✅ Column {column_id} updated by {current_user['username']}")
    return column


@api_router.delete(
    "/columns/{column_id}",
    tags=["Columns"],
    summary="🗑️ Delete Column",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_404_NOT_FOUND: {"description": "Column not found"},
    },
)
async def delete_column(
    column_id: str = Path(..., description="Column ID"),
    current_user: dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a column.

    **Requires authentication**

    Note: Column will be restored on next ETL run.
    """
    logger.info(f"🗑️ User {current_user['username']} deleting column: {column_id}")

    # Get existing column
    column = db.query(DataColonne).filter(DataColonne.id == column_id).first()
    if not column:
        logger.warning(f"⚠️ Column with ID {column_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with ID {column_id} not found",
        )

    # Store table ID for logging
    table_id = column.data_table_id

    # Delete column
    db.delete(column)
    db.commit()

    logger.info(
        f"✅ Column {column_id} deleted from table {table_id} by {current_user['username']}"
    )

    # 204 No Content - successful deletion returns no body
    return None


# ========== Authentication Endpoints ==========
@api_router.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["Authentication"],
    summary="🔐 Login",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
    },
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with username and password to get JWT token.

    Test credentials:
    - Username: `admin`, Password: `admin123`
    - Username: `demo`, Password: `demo123`

    Returns:
        JWT access token valid for 30 minutes.
    """
    logger.info(f"🔐 Login attempt for user: {form_data.username}")

    # Authenticate user
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"⚠️ Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": user["username"]})

    logger.info(f"✅ Logging successful for user: {form_data.username}")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60,  # Convert minutes to seconds
    )


@api_router.get(
    "/auth/me",
    tags=["Authentication"],
    summary="🙋 Current User",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
    },
)
async def get_current_user_info(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    Get current authenticated user info.

    Requires valid JWT token in Authorization header.
    """
    logger.info(f"📋 User {current_user['username']} requested their info")
    return {
        "username": current_user["username"],
        "message": "Authentication is working",
    }
