"""
Database Initialization Script for EV Fleet & Rider Intelligence System.
Initializes SQLite database using database/schema.sql and loads data from CSVs into SQLite tables.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = "/workspace/database/ev_fleet.db"
SCHEMA_PATH = "/workspace/database/schema.sql"
DATA_DIR = "/workspace/data/raw"

def init_database():
    print(f"Connecting to SQLite database at {DB_PATH}...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Read and apply schema
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
    
    cursor.executescript(schema_sql)
    conn.commit()
    print("Schema applied successfully.")
    
    tables_order = [
        ("suppliers", "suppliers.csv"),
        ("manufacturing_lots", "manufacturing_lots.csv"),
        ("batteries", "batteries.csv"),
        ("vehicles", "vehicles.csv"),
        ("riders", "riders.csv"),
        ("trips", "trips.csv"),
        ("deliveries", "deliveries.csv"),
        ("transactions", "transactions.csv"),
        ("rider_activity_daily", "rider_activity_daily.csv")
    ]
    
    for table_name, csv_filename in tables_order:
        csv_path = os.path.join(DATA_DIR, csv_filename)
        if os.path.exists(csv_path):
            print(f"Loading {csv_filename} into {table_name}...")
            # Load in chunks for large tables to maintain low memory profile
            chunk_size = 50000
            for chunk in pd.read_csv(csv_path, chunksize=chunk_size):
                chunk.to_sql(table_name, conn, if_exists="append", index=False)
            count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"-> {table_name}: {count:,} records.")
        else:
            print(f"WARNING: {csv_path} not found.")
            
    conn.commit()
    conn.close()
    print("Database initialization and population complete!")

if __name__ == "__main__":
    init_database()
