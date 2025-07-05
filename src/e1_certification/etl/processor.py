"""
ETL processor for Collibra Excel files.
Optimized for Lambda execution with S3 integration.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e1_certification.db import get_db_session
from e1_certification.db.models import MODEL_REGISTRY
from e1_certification.etl.mappings import (
    COLS_MAPPING,
    DOMS_MAPPING,
    TABS_MAPPING,
)
from e1_certification.utils.logging_config import logger


class CollibraETLProcessor:
    """Process Collibra Excel exports and load to database."""

    def __init__(self, file_paths: dict[str, Path]):
        """
        Initialize processor with file paths.

        Args:
            file_paths: Dict mapping entity name to file path
                        (e.g. {"communautes": Path("/.../communities.xlsx")})
        """
        self.file_paths = file_paths
        self.stats = {"processed": 0, "errors": 0}

    @staticmethod
    def handle_text_col(df: pd.DataFrame, colname: str) -> pd.Series:
        """
        Clean text column: strip whitespace and convert NaN to None.

        Args:
            df: DataFrame containing the column
            colname: Name of column to clean

        Returns:
            Cleaned series
        """
        return (
            df[colname]
            .replace(np.nan, None)
            .apply(lambda x: x.strip() if isinstance(x, str) else x)
        )

    @staticmethod
    def handle_date_col(df: pd.DataFrame, colname: str) -> pd.Series:
        """
        Clean date column: convert to date objects and NaT to None.

        Args:
            df: DataFrame containing the column
            colname: Name of column to clean

        Returns:
            Cleaned series with date objects
        """
        return pd.to_datetime(df[colname], errors="coerce").dt.date.apply(
            lambda d: None if pd.isna(d) else d
        )

    def process_communautes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process communities DataFrame."""
        logger.info("🏛️ Processing communities...")

        return df.rename(
            columns={"Community": "nom", "Description": "description"}
        ).assign(
            id=lambda df_: range(1, len(df_) + 1),  # type: ignore[arg-type]
            nom=lambda df_: self.handle_text_col(df_, "nom"),
            description=lambda df_: self.handle_text_col(df_, "description"),
        )[["id", "nom", "description"]]

    def process_domaines(self, df: pd.DataFrame, coms_dict: dict) -> pd.DataFrame:
        """Process domains dataframe."""
        logger.info("📁 Processing domains...")

        return (
            df[list(DOMS_MAPPING.keys())]
            .rename(columns=DOMS_MAPPING)
            .query("asset_type == 'Schema'")  # Filter only schemas
            .assign(
                nom=lambda df_: self.handle_text_col(df_, "nom"),
                communaute_id=lambda df_: df_.communaute.map(coms_dict),
            )
            .drop(columns=["asset_type", "communaute"])
            .drop_duplicates()
            .reset_index(drop=True)
        )

    def process_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process tables dataframe."""
        logger.info("📅 Processing tables...")

        return (
            df[list(TABS_MAPPING.keys())]
            .rename(columns=TABS_MAPPING)
            .drop_duplicates()
            .reset_index(drop=True)
            .assign(
                nom=lambda df_: self.handle_text_col(df_, "nom"),
                description=lambda df_: self.handle_text_col(df_, "description"),
                date_creation=lambda df_: self.handle_date_col(df_, "date_creation"),
                date_derniere_modification=lambda df_: self.handle_date_col(
                    df_, "date_derniere_modification"
                ),
            )
        )

    def process_colonnes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process columns dataframe."""
        logger.info("📏 Processing columns...")

        return (
            df[list(COLS_MAPPING.keys())]
            .rename(columns=COLS_MAPPING)
            .drop_duplicates()
            .reset_index(drop=True)
            .assign(
                nom=lambda df_: self.handle_text_col(df_, "nom"),
                description=lambda df_: self.handle_text_col(df_, "description"),
                data_type=lambda df_: self.handle_text_col(df_, "data_type"),
                date_creation=lambda df_: self.handle_date_col(df_, "date_creation"),
                date_derniere_modification=lambda df_: self.handle_date_col(
                    df_, "date_derniere_modification"
                ),
            )
        )

    def load_to_database(self, df: pd.DataFrame, model_name: str) -> int:
        """
        Load DataFrame to database using SQLAlchemy model.

        Args:
            df: DataFrame to load
            model_name: Name of model in MODEL_REGISTRY

        Returns:
            Number of records loaded
        """
        model = MODEL_REGISTRY[model_name]
        records_loaded = 0

        with get_db_session() as session:
            for _, row in df.iterrows():
                instance = model(**row.to_dict())
                session.add(instance)
                records_loaded += 1

            session.commit()
            logger.info(f"✅ Loaded {records_loaded} {model_name} records")

        return records_loaded

    def process_all(self) -> dict[str, Any]:
        """
        Process all Excel files in the correct order.

        Returns:
            Processing statistics
        """
        stats = {
            "communautes": {"read": 0, "loaded": 0},
            "domaines": {"read": 0, "loaded": 0},
            "data_tables": {"read": 0, "loaded": 0},
            "data_colonnes": {"read": 0, "loaded": 0},
            "errors": [],
        }

        # Initialize lookup dictionary
        coms_dict = {}

        try:
            # 1. Process communities first (no dependencies)
            if "communautes" in self.file_paths:
                df_coms = pd.read_excel(self.file_paths["communautes"])
                stats["communautes"]["read"] = len(df_coms)

                df_coms = self.process_communautes(df_coms)
                stats["communautes"]["loaded"] = self.load_to_database(
                    df_coms, "communautes"
                )

                # Create lookup dict for domains
                coms_dict = dict(zip(df_coms.nom, df_coms.id, strict=False))

            # 2. Process domains (depends on communities)
            if "domaines" in self.file_paths:
                df_doms = pd.read_excel(self.file_paths["domaines"])
                stats["domaines"]["read"] = len(df_doms)

                df_doms = self.process_domaines(df_doms, coms_dict)
                stats["domaines"]["loaded"] = self.load_to_database(df_doms, "domaines")

            # 3. Process tables (depends on domains)
            if "data_tables" in self.file_paths:
                df_tabs = pd.read_excel(self.file_paths["data_tables"])
                stats["data_tables"]["read"] = len(df_tabs)

                df_tabs = self.process_tables(df_tabs)
                stats["data_tables"]["loaded"] = self.load_to_database(
                    df_tabs, "data_tables"
                )

            # 4. Process columns (depends on tables)
            if "data_colonnes" in self.file_paths:
                df_cols = pd.read_excel(self.file_paths["data_colonnes"])
                stats["data_colonnes"]["read"] = len(df_cols)

                df_cols = self.process_colonnes(df_cols)
                stats["data_colonnes"]["loaded"] = self.load_to_database(
                    df_cols, "data_colonnes"
                )

        except Exception as e:
            logger.error(f"❌ ETL processing failed: {e}")
            stats["errors"].append(str(e))
            raise

        return stats
