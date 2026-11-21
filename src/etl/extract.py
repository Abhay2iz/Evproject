"""
ETL Extract Module - Extracts raw relational tables from SQLite database.
"""

import sqlite3
import pandas as pd
from typing import Dict

DEFAULT_DB_PATH = "/workspace/database/ev_fleet.db"

def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)

def extract_table(table_name: str, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """Extract a single table into a pandas DataFrame."""
    conn = get_connection(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        return df
    finally:
        conn.close()

def extract_data_from_db(db_path: str = DEFAULT_DB_PATH) -> Dict[str, pd.DataFrame]:
    """Extract all fleet database tables."""
    tables = [
        "suppliers",
        "manufacturing_lots",
        "batteries",
        "vehicles",
        "riders",
        "trips",
        "deliveries",
        "transactions",
        "rider_activity_daily"
    ]
    data = {}
    conn = get_connection(db_path)
    try:
        for t in tables:
            data[t] = pd.read_sql_query(f"SELECT * FROM {t}", conn)
    finally:
        conn.close()
    return data
