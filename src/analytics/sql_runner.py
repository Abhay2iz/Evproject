"""
SQL Runner and Benchmark Module.
Executes advanced analytical SQL scripts, benchmark query performance, and exports outputs.
"""

import os
import re
import sqlite3
import time
import pandas as pd

DB_PATH = "/workspace/database/ev_fleet.db"
SQL_DIR = "/workspace/sql"
OUTPUT_DIR = "/workspace/reports/sql_results"

def clean_sql_statement(stmt: str) -> str:
    # Remove single-line comments
    lines = [line for line in stmt.split("\n") if not line.strip().startswith("--")]
    cleaned = "\n".join(lines).strip()
    return cleaned

def run_sql_file(filepath: str, conn: sqlite3.Connection):
    with open(filepath, "r") as f:
        full_sql = f.read()

    raw_statements = full_sql.split(";")
    results = []
    
    for idx, raw_stmt in enumerate(raw_statements, 1):
        stmt = clean_sql_statement(raw_stmt)
        if not stmt:
            continue
        first_word = stmt.split()[0].upper() if stmt.split() else ""
        if first_word not in ["WITH", "SELECT"]:
            continue
            
        start_t = time.time()
        try:
            df = pd.read_sql_query(stmt, conn)
            elapsed = (time.time() - start_t) * 1000
            results.append({
                "statement_index": idx,
                "elapsed_ms": round(elapsed, 2),
                "row_count": len(df),
                "dataframe": df
            })
        except Exception as e:
            print(f"Error executing statement #{idx} in {filepath}: {e}")
            
    return results

def execute_all_sql():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    sql_files = sorted([f for f in os.listdir(SQL_DIR) if f.endswith(".sql")])
    
    print(f"Executing {len(sql_files)} SQL analytical suites against {DB_PATH}...\n")
    
    summary = []
    for sf in sql_files:
        path = os.path.join(SQL_DIR, sf)
        print(f"Running: {sf}")
        res = run_sql_file(path, conn)
        for r in res:
            print(f"  [Stmt #{r['statement_index']}] Returned {r['row_count']} rows in {r['elapsed_ms']} ms")
            out_csv = os.path.join(OUTPUT_DIR, f"{os.path.splitext(sf)[0]}_stmt{r['statement_index']}.csv")
            r["dataframe"].to_csv(out_csv, index=False)
            summary.append({
                "file": sf,
                "statement": r["statement_index"],
                "rows": r["row_count"],
                "elapsed_ms": r["elapsed_ms"]
            })
            
    conn.close()
    print("\nAll SQL suites executed and exported to reports/sql_results/.")
    return pd.DataFrame(summary)

if __name__ == "__main__":
    execute_all_sql()
