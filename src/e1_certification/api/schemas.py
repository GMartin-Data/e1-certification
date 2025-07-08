"""
Pydantic schemas for API requests and responses.

Endpoint Design Philosophy:
- Communities: Return all (only 20)
- Domains: Paginated, can filter by community
- Tables: MUST filter by domain (no GET all endpoint)
- Columns: MUST filter by table (no GET all endpoint)
"""

from datetime import date

from pydantic import BaseModel, ConfigDict

# ========== Response Models ==========


class CommunauteResponse(BaseModel):
    """
    Community response model.

    Represents a top-level organizational unit in the data catalog.
    Used when returning community data from endpoints like GET /communautes/{id}
    """

    # This allows Pydantic to read attributes from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)

    id: int  # integer auto-incremented primary key
    nom: str
    description: str | None = None


class DomaineResponse(BaseModel):
    """
    Domain response model.

    Represents a domain within a community
    """

    model_config = ConfigDict(from_attributes=True)

    id: str  # String primary key (from Collibra)
    nom: str
    communaute_id: int  # Foreign key to community


class DataTableResponse(BaseModel):
    """
    Data table response model.

    Represents a database table in the catalog.
    Between 1,000 and 2,000 tables; hence always filtered by domain.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str  # String primary key (from Collibra)
    nom: str
    description: str | None = None
    date_creation: date | None = None
    date_derniere_modification: date | None = None
    domaine_id: str  # Foreign key to domain


class DataColonneResponse(BaseModel):
    """
    Data column response model.

    Represents a column within a table.
    The simplest entity in our hierarchy.
    Between 50,000 and 100,000 columns; hence always filtered by data_table.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str  # String primary key (from Collibra)
    nom: str
    description: str | None = None
    data_type: str | None = None
    date_creation: date | None = None
    date_derniere_modification: date | None = None
    data_table_id: str  # Foreign key to data_table


# ========== Pagination Models ==========


class PaginationInfo(BaseModel):
    """
    Pagination metadata.

    Provides clients with navigation information:
    - total: Total items across all pages
    - page: Current page number
    - per_page: Items per page (default 50)
    - pages: Total number of pages
    """

    total: int
    page: int = 1
    per_page: int = 50
    pages: int


# ========== List Response Models ==========
# Different approaches based on data volume


class CommunauteListResponse(BaseModel):
    """
    List of all communities.

    No pagination needed - only 20 communities total.
    Response for GET /communities
    """

    data: list[CommunauteResponse]


class DomaineListResponse(BaseModel):
    """
    Paginated list of domains.

    Between 100 and 200 domains total, paginated at 50 per page.
    Response for GET /domains or GET /domains?communaute_id=X
    """

    data: list[DomaineResponse]
    pagination: PaginationInfo


class DataTableListResponse(BaseModel):
    """
    Paginated list of tables (always filtered by domain).

    Between 1,000 and 2,000 tables total - too many for a single response.
    Response for GET /domains/{domain_id}/tables
    """

    data: list[DataTableResponse]
    pagination: PaginationInfo


class DataColonneListResponse(BaseModel):
    """
    Paginated list of columns (always filtered by table).

    Between 50,000 and 100,000 columns total - must be filtered.
    Response for GET /tables/{table_id}/columns
    Some tables have 500+ columns, so pagination is essential.
    """

    data: list[DataColonneResponse]
    pagination: PaginationInfo


# ========== Request Models ==========
# These models validate data coming INTO our API.
# They ensure we receive properly formatted data from clients.


class LoginRequest(BaseModel):
    """
    Login request model.

    Used by POST /auth/login
    We'll validate these credentials against a user store.
    """

    username: str  # Could be email or username
    password: str  # Will be hashed before comparison


class TokenResponse(BaseModel):
    """
    JWT token response.

    Returned after successful login.
    Follows OAuth2 conventions for compatibility with tools/libraries.
    """

    access_token: str  # The actual JWT token
    token_type: str = "bearer"  # Always "bearer" for JWT
    expires_in: int = 3600  # Token lifetime in seconds (1 hour default)


# ========== Error Models ==========
# Consistent error responses make debugging easier for API consumers.


class ErrorResponse(BaseModel):
    """
    Standard error response.

    Provides consistent error format across all endpoints:
    - error: Machine-readable error code (e.g., "validation_error")
    - message: Human-readable explanation
    - status_code: HTTP status code for reference
    - detail: Optional additional context (e.g., field-specific errors)
    """

    error: str
    message: str
    status_code: int
    detail: dict | None = None
