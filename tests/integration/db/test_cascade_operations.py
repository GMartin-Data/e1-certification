"""
Integration tests for cascade delete operations.
Tests that deleting parent objects properly cascades to children.
"""

import pytest
from e1_certification.db.models import Communaute, DataColonne, DataTable, Domaine


@pytest.mark.integration
class TestCascadeDeletes:
    """Test cascade delete operations across the model hierarchy."""

    def test_delete_communaute_cascades(self, db_session, complete_hierarchy):
        """Test that deleting a Communaute deletes all related objects."""
        # Get the created objects
        communaute = complete_hierarchy["communaute"]
        domaine = complete_hierarchy["domaine"]
        table = complete_hierarchy["table"]
        colonnes = complete_hierarchy["colonnes"]

        # Get IDs for verification
        communaute_id = communaute.id
        domaine_id = domaine.id
        table_id = table.id
        colonne_ids = [col.id for col in colonnes]

        # Delete the community
        db_session.delete(communaute)
        db_session.commit()

        # Verify everything is deleted
        assert db_session.get(Communaute, communaute_id) is None
        assert db_session.get(Domaine, domaine_id) is None
        assert db_session.get(DataTable, table_id) is None

        for col_id in colonne_ids:
            assert db_session.get(DataColonne, col_id) is None

    def test_delete_domaine_cascades(self, db_session, complete_hierarchy):
        """Test that deleting a Domaine deletes related tables and columns."""
        # Get objects
        communaute = complete_hierarchy["communaute"]
        domaine = complete_hierarchy["domaine"]
        table = complete_hierarchy["table"]
        colonnes = complete_hierarchy["colonnes"]

        domaine_id = domaine.id
        table_id = table.id
        colonne_ids = [col.id for col in colonnes]

        # Delete the domain
        db_session.delete(domaine)
        db_session.commit()

        # Community should still exist
        assert db_session.get(Communaute, communaute.id) is not None

        # Domain and its children should be deleted
        assert db_session.get(Domaine, domaine_id) is None
        assert db_session.get(DataTable, table_id) is None

        for col_id in colonne_ids:
            assert db_session.get(DataColonne, col_id) is None

    def test_delete_table_cascades(self, db_session, complete_hierarchy):
        """Test that deleting a DataTable deletes related columns only."""
        # Get objects
        communaute = complete_hierarchy["communaute"]
        domaine = complete_hierarchy["domaine"]
        table = complete_hierarchy["table"]
        colonnes = complete_hierarchy["colonnes"]

        table_id = table.id
        colonne_ids = [col.id for col in colonnes]

        # Delete the table
        db_session.delete(table)
        db_session.commit()

        # Community and Domain should still exist
        assert db_session.get(Communaute, communaute.id) is not None
        assert db_session.get(Domaine, domaine.id) is not None

        # Table and columns should be deleted
        assert db_session.get(DataTable, table_id) is None

        for col_id in colonne_ids:
            assert db_session.get(DataColonne, col_id) is None


@pytest.mark.integration
class TestComplexQueries:
    """Test complex queries across relationships."""

    def test_query_full_hierarchy(self, db_session, complete_hierarchy):
        """Test querying through the full hierarchy."""
        # Query community with all relationships
        result = (
            db_session.query(Communaute)
            .filter_by(nom="Complete Test Community")
            .first()
        )

        assert result is not None
        assert len(result.domaines) == 1
        assert len(result.domaines[0].data_tables) == 1
        assert len(result.domaines[0].data_tables[0].data_colonnes) == 3

    def test_count_objects_in_hierarchy(self, db_session, complete_hierarchy):
        """Test counting objects at each level."""
        # Count all objects
        communaute_count = db_session.query(Communaute).count()
        domaine_count = db_session.query(Domaine).count()
        table_count = db_session.query(DataTable).count()
        colonne_count = db_session.query(DataColonne).count()

        assert communaute_count >= 1
        assert domaine_count >= 1
        assert table_count >= 1
        assert colonne_count >= 3
