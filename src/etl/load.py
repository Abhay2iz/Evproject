"""
ETL Load Module - Exports processed datasets and Power BI semantic layer.
"""

import os
from typing import Dict
import pandas as pd

PROCESSED_DIR = "/workspace/data/processed"
POWERBI_DIR = "/workspace/data/powerbi_export"

def load_processed_data(transformed_data: Dict[str, pd.DataFrame]):
    """Persists transformed data to CSV and Parquet formats for analytics & BI."""
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(POWERBI_DIR, exist_ok=True)
    
    print("Exporting processed data and Power BI dimension/fact tables...")
    
    # Save standard processed tables
    for name, df in transformed_data.items():
        csv_file = os.path.join(PROCESSED_DIR, f"{name}.csv")
        # Save as CSV
        df.to_csv(csv_file, index=False)
        
    # Build Power BI star-schema export layer
    # 1. Dim_Riders
    riders = transformed_data["riders"]
    activity = transformed_data["rider_activity_daily"]
    
    act_agg = activity.groupby("rider_id").agg(
        total_hours_online=("hours_online", "sum"),
        total_trips=("trips_completed", "sum"),
        total_deliveries=("deliveries_completed", "sum"),
        failed_deliveries=("deliveries_failed", "sum"),
        total_swaps=("battery_swaps_count", "sum"),
        avg_daily_earnings=("total_earnings", "mean")
    ).reset_index()
    
    dim_riders = riders.merge(act_agg, on="rider_id", how="left").fillna(0)
    dim_riders.to_csv(os.path.join(POWERBI_DIR, "Dim_Riders.csv"), index=False)
    
    # 2. Dim_Batteries
    batteries = transformed_data["batteries"]
    suppliers = transformed_data["suppliers"][["supplier_id", "supplier_name", "tier", "country"]]
    dim_batteries = batteries.merge(suppliers, on="supplier_id", how="left")
    dim_batteries.to_csv(os.path.join(POWERBI_DIR, "Dim_Batteries.csv"), index=False)
    
    # 3. Dim_Vehicles
    dim_vehicles = transformed_data["vehicles"]
    dim_vehicles.to_csv(os.path.join(POWERBI_DIR, "Dim_Vehicles.csv"), index=False)
    
    # 4. Dim_Suppliers
    transformed_data["suppliers"].to_csv(os.path.join(POWERBI_DIR, "Dim_Suppliers.csv"), index=False)
    
    # 5. Fact_Daily_Rider_Performance
    activity.to_csv(os.path.join(POWERBI_DIR, "Fact_Daily_Rider_Performance.csv"), index=False)
    
    # 6. Fact_Deliveries_Monthly_Summary
    deliv = transformed_data["deliveries"]
    deliv["year_month"] = pd.to_datetime(deliv["delivery_date"]).dt.to_period("M").astype(str)
    monthly_deliv = deliv.groupby(["year_month", "city", "delivery_status"]).agg(
        delivery_count=("delivery_id", "count"),
        total_order_value=("order_value", "sum"),
        avg_actual_duration=("actual_duration_min", "mean"),
        avg_promised_duration=("promised_duration_min", "mean"),
        avg_rating=("customer_rating", "mean")
    ).reset_index()
    monthly_deliv.to_csv(os.path.join(POWERBI_DIR, "Fact_Deliveries_Monthly_Summary.csv"), index=False)
    
    # 7. Fact_Supplier_Quality_Scorecard
    # Combine battery and lot data per supplier
    lots = transformed_data["manufacturing_lots"]
    sup_score = batteries.groupby("supplier_id").agg(
        total_batteries=("battery_id", "count"),
        avg_soh=("current_soh_pct", "mean"),
        degraded_count=("is_degraded", "sum"),
        avg_internal_resistance=("internal_resistance_m_ohm", "mean"),
        avg_max_temp=("max_temp_celsius_recorded", "mean"),
        avg_cycles=("cycle_count", "mean")
    ).reset_index()
    sup_score = sup_score.merge(suppliers, on="supplier_id", how="left")
    sup_score["degradation_ratio"] = (sup_score["degraded_count"] / sup_score["total_batteries"]).round(3)
    sup_score.to_csv(os.path.join(POWERBI_DIR, "Fact_Supplier_Quality_Scorecard.csv"), index=False)
    
    print("Power BI data layer exported successfully.")
