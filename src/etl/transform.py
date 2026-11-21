"""
ETL Transform Module - Cleans, enriches, and computes analytical features.
"""

from typing import Dict
import pandas as pd
import numpy as np

def transform_all(raw_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Execute all data transformations and feature enrichments."""
    print("Transforming and enriching datasets...")
    transformed = {}

    # 1. Suppliers
    suppliers = raw_data["suppliers"].copy()
    suppliers["contract_start_date"] = pd.to_datetime(suppliers["contract_start_date"])
    transformed["suppliers"] = suppliers

    # 2. Manufacturing Lots
    lots = raw_data["manufacturing_lots"].copy()
    lots["production_date"] = pd.to_datetime(lots["production_date"])
    transformed["manufacturing_lots"] = lots

    # 3. Batteries
    batteries = raw_data["batteries"].copy()
    batteries["manufactured_date"] = pd.to_datetime(batteries["manufactured_date"])
    batteries["last_swap_timestamp"] = pd.to_datetime(batteries["last_swap_timestamp"])
    
    # Calculate degradation rate per 100 cycles
    safe_cycles = batteries["cycle_count"].replace(0, 1)
    batteries["soh_loss_pct"] = 100.0 - batteries["current_soh_pct"]
    batteries["degradation_rate_per_100_cycles"] = np.round(
        (batteries["soh_loss_pct"] / safe_cycles) * 100.0, 3
    )
    batteries["is_degraded"] = (batteries["current_soh_pct"] < 75.0).astype(int)
    transformed["batteries"] = batteries

    # 4. Vehicles
    vehicles = raw_data["vehicles"].copy()
    vehicles["registration_date"] = pd.to_datetime(vehicles["registration_date"])
    transformed["vehicles"] = vehicles

    # 5. Riders
    riders = raw_data["riders"].copy()
    riders["signup_date"] = pd.to_datetime(riders["signup_date"])
    riders["activation_date"] = pd.to_datetime(riders["activation_date"])
    riders["churn_date"] = pd.to_datetime(riders["churn_date"])
    riders["is_activated"] = riders["activation_date"].notna().astype(int)
    riders["days_to_activate"] = (riders["activation_date"] - riders["signup_date"]).dt.days
    riders["is_churned"] = (riders["onboarding_status"] == "CHURNED").astype(int)
    transformed["riders"] = riders

    # 6. Trips
    trips = raw_data["trips"].copy()
    trips["start_time"] = pd.to_datetime(trips["start_time"])
    trips["end_time"] = pd.to_datetime(trips["end_time"])
    trips["duration_min"] = (trips["end_time"] - trips["start_time"]).dt.total_seconds() / 60.0
    safe_dist = trips["distance_km"].replace(0, 0.1)
    trips["energy_wh_per_km"] = np.round((trips["energy_consumed_kwh"] * 1000.0) / safe_dist, 2)
    trips["soc_drop_pct"] = trips["start_soc_pct"] - trips["end_soc_pct"]
    trips["trip_date"] = trips["start_time"].dt.date
    trips["trip_hour"] = trips["start_time"].dt.hour
    transformed["trips"] = trips

    # 7. Deliveries
    deliveries = raw_data["deliveries"].copy()
    deliveries["start_time"] = pd.to_datetime(deliveries["start_time"])
    deliveries["delivered_at"] = pd.to_datetime(deliveries["delivered_at"])
    deliveries["is_failed"] = (deliveries["delivery_status"] != "COMPLETED").astype(int)
    deliveries["is_ontime"] = (
        (deliveries["actual_duration_min"] <= deliveries["promised_duration_min"]) & 
        (deliveries["delivery_status"] == "COMPLETED")
    ).astype(int)
    deliveries["delivery_date"] = deliveries["start_time"].dt.date
    deliveries["delivery_hour"] = deliveries["start_time"].dt.hour
    transformed["deliveries"] = deliveries

    # 8. Transactions
    transactions = raw_data["transactions"].copy()
    transactions["transaction_time"] = pd.to_datetime(transactions["transaction_time"])
    transactions["txn_date"] = transactions["transaction_time"].dt.date
    transformed["transactions"] = transactions

    # 9. Rider Daily Activity
    activity = raw_data["rider_activity_daily"].copy()
    activity["activity_date"] = pd.to_datetime(activity["activity_date"])
    activity["earnings_per_hour"] = np.where(
        activity["hours_online"] > 0,
        np.round(activity["total_earnings"] / activity["hours_online"], 2),
        0.0
    )
    transformed["rider_activity_daily"] = activity

    print("Data transformations and enrichments completed.")
    return transformed
