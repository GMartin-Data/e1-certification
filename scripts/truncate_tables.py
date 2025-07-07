#!/usr/bin/env python3
"""Truncate all tables in the database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from e1_certification.db import get_engine  # noqa: E402
from sqlalchemy import text  # noqa: E402

with get_engine().connect() as conn:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for table in ["data_colonnes", "data_tables", "domaines", "communautes"]:
        conn.execute(text(f"TRUNCATE TABLE {table}"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    conn.commit()
    print("✂️ All tables truncated")
