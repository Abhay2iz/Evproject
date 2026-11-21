"""
Main ETL Pipeline Runner.
Orchestrates Extraction, Validation, Transformation, and Loading.
"""

import sys
import os
sys.path.insert(0, "/workspace")
from src.etl.extract import extract_data_from_db
from src.etl.validator import DataValidator
from src.etl.transform import transform_all
from src.etl.load import load_processed_data

def run_pipeline():
    print("=" * 60)
    print("STARTING EV FLEET ETL PIPELINE EXECUTION")
    print("=" * 60)
    
    # Step 1: Extract
    print("[1/4] Extracting tables from SQLite database...")
    raw_data = extract_data_from_db()
    for tbl, df in raw_data.items():
        print(f"      - {tbl}: {len(df):,} rows")
        
    # Step 2: Validate
    print("\n[2/4] Running Data Quality & Referential Integrity Validations...")
    validator = DataValidator()
    val_report = validator.validate_all(raw_data)
    print(f"      - Total checks performed: {val_report['total_checks']}")
    print(f"      - Validation passed: {val_report['passed']}")
    if not val_report["passed"]:
        print("      - ERRORS FOUND:")
        for err in val_report["errors"]:
            print(f"        * {err}")
        sys.exit(1)
    else:
        print("      - All Data Quality checks passed cleanly!")
        
    # Step 3: Transform
    print("\n[3/4] Running Data Transformations & Feature Engineering...")
    transformed_data = transform_all(raw_data)
    
    # Step 4: Load
    print("\n[4/4] Loading to processed storage & Power BI export layer...")
    load_processed_data(transformed_data)
    
    print("\n" + "=" * 60)
    print("ETL PIPELINE EXECUTED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
