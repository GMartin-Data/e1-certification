"""
Unit tests for SQLAlchemy models.
Tests model creation, relationships, and basic operations.
"""

from datetime import date

from e1_certification.db.models import Communaute, DataColonne, DataTable, Domaine


class TestCommunaute:
    """Test Communaute model."""

    def test_create_communaute(self, db_session):
        """Test creating a Communaute."""
        communaute = Communaute(nom="Test Community", description="Test description")
        db_session.add(communaute)
        db_session.commit()

        assert communaute.id is not None
        assert communaute.nom == "Test Community"  # type: ignore[comparison-overlap]
        assert communaute.description == "Test description"  # type: ignore[comparison-overlap]

    def test_communaute_repr(self, sample_communaute):
        """Test Communaute string representation."""
        repr_str = repr(sample_communaute)
        assert "Communaute" in repr_str
        assert "Test Business Domain" in repr_str

    def test_communaute_to_dict(self, sample_communaute):
        """Test converting Communaute to dictionary."""
        data = sample_communaute.to_dict()
        assert data["nom"] == "Test Business Domain"
        assert "id" in data
        assert "description" in data


class TestDomaine:
    """Test Domaine model."""

    def test_create_domaine(self, db_session, sample_communaute):
        """Test creating a Domaine."""
        domaine = Domaine(
            id="DOM-TEST", nom="Test Domain", communaute_id=sample_communaute.id
        )
        db_session.add(domaine)
        db_session.commit()

        assert domaine.id == "DOM-TEST"  # type: ignore[comparison-overlap]
        assert domaine.nom == "Test Domain"  # type: ignore[comparison-overlap]
        assert domaine.communaute_id == sample_communaute.id

    def test_domaine_communaute_relationship(self, sample_domaine, sample_communaute):
        """Test Domaine-Communaute relationship."""
        assert sample_domaine.communaute == sample_communaute
        assert sample_domaine in sample_communaute.domaines


class TestDataTable:
    """Test DataTable model."""

    def test_create_data_table(self, db_session, sample_domaine):
        """Test creating a DataTable."""
        table = DataTable(
            id="TBL-TEST",
            nom="Test Table",
            description="Test table description",
            date_creation=date(2024, 1, 1),
            date_derniere_modification=date(2024, 1, 15),
            domaine_id=sample_domaine.id,
        )
        db_session.add(table)
        db_session.commit()

        assert table.id == "TBL-TEST"  # type: ignore[comparison-overlap]
        assert table.nom == "Test Table"  # type: ignore[comparison-overlap]
        assert table.date_creation == date(2024, 1, 1)  # type: ignore[comparison-overlap]
        assert table.domaine_id == sample_domaine.id

    def test_table_domaine_relationship(self, sample_data_table, sample_domaine):
        """Test DataTable-Domaine relationship."""
        assert sample_data_table.domaine == sample_domaine
        assert sample_data_table in sample_domaine.data_tables


class TestDataColonne:
    """Test DataColonne model."""

    def test_create_data_colonne(self, db_session, sample_data_table):
        """Test creating a DataColonne."""
        colonne = DataColonne(
            id="COL-TEST",
            nom="test_column",
            description="Test column description",
            data_type="VARCHAR(255)",
            date_creation=date(2024, 1, 1),
            data_table_id=sample_data_table.id,
        )
        db_session.add(colonne)
        db_session.commit()

        assert colonne.id == "COL-TEST"  # type: ignore[comparison-overlap]
        assert colonne.nom == "test_column"  # type: ignore[comparison-overlap]
        assert colonne.data_type == "VARCHAR(255)"  # type: ignore[comparison-overlap]
        assert colonne.data_table_id == sample_data_table.id

    def test_colonne_table_relationship(self, db_session, sample_data_table):
        """Test DataColonne-DataTable relationship."""
        colonne = DataColonne(
            id="COL-REL-TEST",
            nom="relationship_test",
            data_table_id=sample_data_table.id,
        )
        db_session.add(colonne)
        db_session.commit()

        assert colonne.data_table == sample_data_table
        assert colonne in sample_data_table.data_colonnes


class TestModelRegistry:
    """Test MODEL_REGISTRY functionality."""

    def test_registry_contains_all_models(self):
        """Test that MODEL_REGISTRY contains all models."""
        from e1_certification.db.models import MODEL_REGISTRY

        assert "communautes" in MODEL_REGISTRY
        assert "domaines" in MODEL_REGISTRY
        assert "data_tables" in MODEL_REGISTRY
        assert "data_colonnes" in MODEL_REGISTRY

        assert MODEL_REGISTRY["communautes"] == Communaute
        assert MODEL_REGISTRY["domaines"] == Domaine
        assert MODEL_REGISTRY["data_tables"] == DataTable
        assert MODEL_REGISTRY["data_colonnes"] == DataColonne
