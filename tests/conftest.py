"""
Global pytest fixtures for database testing.
"""

import pytest
from e1_certification.config import settings
from e1_certification.db.base import Base
from e1_certification.db.models import Communaute, DataColonne, DataTable, Domaine
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine.
    Uses the same database but with test isolation.
    """
    # Check database URL is configured
    if not settings.database_url:
        pytest.fail(
            "❌ Database not configured! Please set DB_HOST, DB_USER, and DB_PASSWORD in .env 📝"
        )

    # Use the same database URL from settings
    # In production, you might want a separate test database
    engine = create_engine(
        settings.database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
    )

    # Ensure clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup after all tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Create a database session for each test.
    Rollback after each test for isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Rollback and cleanup
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_communaute(db_session: Session) -> Communaute:
    """Create a sample Communaute for testing."""
    communaute = Communaute(
        nom="Test Business Domain", description="A test community for unit tests"
    )
    db_session.add(communaute)
    db_session.commit()
    db_session.refresh(communaute)
    return communaute


@pytest.fixture
def sample_domaine(db_session: Session, sample_communaute: Communaute) -> Domaine:
    """Create a sample Domaine for testing."""
    domaine = Domaine(
        id="DOM-001", nom="Finance Domain", communaute_id=sample_communaute.id
    )
    db_session.add(domaine)
    db_session.commit()
    db_session.refresh(domaine)
    return domaine


@pytest.fixture
def sample_data_table(db_session: Session, sample_domaine: Domaine) -> DataTable:
    """Create a sample DataTable for testing."""
    from datetime import date

    data_table = DataTable(
        id="TBL-001",
        nom="Customer Transactions",
        description="Table containing customer transaction data",
        date_creation=date(2024, 1, 1),
        date_derniere_modification=date(2024, 1, 15),
        domaine_id=sample_domaine.id,
    )
    db_session.add(data_table)
    db_session.commit()
    db_session.refresh(data_table)
    return data_table


@pytest.fixture
def complete_hierarchy(db_session: Session) -> dict:
    """
    Create a complete hierarchy of test data.
    Returns a dict with all created objects.
    """
    from datetime import date

    # Create community
    communaute = Communaute(
        nom="Complete Test Community",
        description="Full hierarchy for integration tests",
    )
    db_session.add(communaute)
    db_session.flush()

    # Create domain
    domaine = Domaine(id="DOM-TEST-001", nom="Test Domain", communaute_id=communaute.id)
    db_session.add(domaine)
    db_session.flush()

    # Create table
    table = DataTable(
        id="TBL-TEST-001",
        nom="Test Table",
        description="Test table description",
        date_creation=date(2024, 1, 1),
        domaine_id=domaine.id,
    )
    db_session.add(table)
    db_session.flush()

    # Create columns
    columns = []
    for i in range(3):
        col = DataColonne(
            id=f"COL-TEST-{i + 1:03d}",
            nom=f"test_column_{i + 1}",
            description=f"Test column {i + 1}",
            data_type="VARCHAR",
            date_creation=date(2024, 1, 1),
            data_table_id=table.id,
        )
        db_session.add(col)
        columns.append(col)

    db_session.commit()

    return {
        "communaute": communaute,
        "domaine": domaine,
        "table": table,
        "colonnes": columns,
    }
