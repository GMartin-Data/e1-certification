"""
SQLAlchemy models for Collibra asset tables.

This module defines the 4 table models corresponding to
Collibra asset exports. These models will be populated
from Excel files and accessed via the REST API.
"""

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from e1_certification.db.base import Base


class Communaute(Base):
    """Community model - top level organizational unit."""

    # Fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(255), unique=True, nullable=False)
    description = Column(Text)

    # Relationships - One-to-Many: Many domains may belong to one community
    domaines = relationship(
        "Domaine",
        back_populates="communaute",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Domaine(Base):
    """Domain model - groups related data tables."""

    # Fields
    id = Column(String(255), primary_key=True)
    nom = Column(String(255), nullable=False)
    communaute_id = Column(
        Integer, ForeignKey("communautes.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    # Many-to-One: Many domains may belong to one community
    communaute = relationship("Communaute", back_populates="domaines")
    # One-to-Many: One domain may have many data_tables
    data_tables = relationship(
        "DataTable",
        back_populates="domaine",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DataTable(Base):
    """Data table model - represents a database table."""

    # Fields
    id = Column(String(255), primary_key=True)
    nom = Column(String(255), nullable=False)
    description = Column(Text)
    date_creation = Column(Date)
    date_derniere_modification = Column(Date)
    domaine_id = Column(
        String(255), ForeignKey("domaines.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    # Many-to-One: Many data_tables may belong to one domain
    domaine = relationship("Domaine", back_populates="data_tables")
    # One-to-Many: One data_table may have many data_columns
    data_colonnes = relationship(
        "DataColonne",
        back_populates="data_table",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DataColonne(Base):
    """Data column model - represents a column in a table."""

    # Fields
    id = Column(String(255), primary_key=True)
    nom = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(String(50))
    date_creation = Column(Date)
    date_derniere_modification = Column(Date)
    data_table_id = Column(
        String(255), ForeignKey("data_tables.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    # Many-to-One: Many data_columns may belong to one data_table
    data_table = relationship("DataTable", back_populates="data_colonnes")


# Model registry for easy access
MODEL_REGISTRY = {
    "communautes": Communaute,
    "domaines": Domaine,
    "data_tables": DataTable,
    "data_colonnes": DataColonne,
}
