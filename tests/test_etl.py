"""
Unit tests for ETL pipeline, extraction, transformation, and load functions.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import pytest
import pandas as pd
import numpy as np
from src.etl.extract import extract_data_from_db, extract_table
from src.etl.transform import transform_all

def test_extract_tables_exist():
    """Verify core tables can be extracted and contain data."""
    data = extract_data_from_db()
    assert "riders" in data
    assert "batteries" in data
    assert "deliveries" in data
    assert "trips" in data
    assert len(data["riders"]) > 0
    assert len(data["batteries"]) > 0

def test_extract_single_table():
    """Verify single table extraction."""
    suppliers_df = extract_table("suppliers")
    assert isinstance(suppliers_df, pd.DataFrame)
    assert len(suppliers_df) >= 8
    assert "supplier_id" in suppliers_df.columns

def test_transform_enrichments():
    """Verify derived columns in transformation module."""
    raw_sample = {
        "suppliers": pd.DataFrame([{
            "supplier_id": "SUP-001", "supplier_name": "Test", "country": "India",
            "rating": 4.5, "tier": "Tier-1", "contract_start_date": "2024-01-01"
        }]),
        "manufacturing_lots": pd.DataFrame([{
            "lot_id": "LOT-001", "supplier_id": "SUP-001", "component_type": "BATTERY",
            "production_date": "2024-01-10", "defect_rate_estimate": 0.02, "certification_standard": "ISO-9001"
        }]),
        "batteries": pd.DataFrame([{
            "battery_id": "BAT-001", "supplier_id": "SUP-001", "lot_id": "LOT-001",
            "serial_number": "SN-001", "chemistry_type": "LFP", "nominal_capacity_kwh": 3.2,
            "cycle_count": 500, "current_soh_pct": 78.0, "max_temp_celsius_recorded": 42.0,
            "internal_resistance_m_ohm": 31.0, "status": "ACTIVE", "manufactured_date": "2024-01-15",
            "last_swap_timestamp": "2024-06-01 12:00:00"
        }]),
        "vehicles": pd.DataFrame([{
            "vehicle_id": "VEH-001", "lot_id": "LOT-001", "model_name": "VoltCruiser",
            "vin": "VIN001", "registration_date": "2024-02-01", "total_odometer_km": 12000.0,
            "current_battery_id": "BAT-001", "status": "ACTIVE", "hub_city": "Bangalore"
        }]),
        "riders": pd.DataFrame([{
            "rider_id": "RDR-001", "full_name": "Test Rider", "email": "rider@test.com",
            "city": "Bangalore", "signup_date": "2024-01-01", "activation_date": "2024-01-03",
            "onboarding_status": "ACTIVE", "vehicle_assigned_id": "VEH-001", "tier": "PRO",
            "rating_avg": 4.8, "lifetime_deliveries": 100, "lifetime_earnings": 5000.0, "churn_date": None
        }]),
        "trips": pd.DataFrame([{
            "trip_id": "TRP-001", "rider_id": "RDR-001", "vehicle_id": "VEH-001",
            "battery_id": "BAT-001", "start_time": "2024-06-01 10:00:00", "end_time": "2024-06-01 10:30:00",
            "distance_km": 10.0, "energy_consumed_kwh": 0.32, "start_soc_pct": 90.0, "end_soc_pct": 80.0,
            "avg_speed_kmh": 20.0, "max_speed_kmh": 40.0, "ambient_temp_c": 30.0, "city": "Bangalore"
        }]),
        "deliveries": pd.DataFrame([{
            "delivery_id": "DEL-001", "trip_id": "TRP-001", "rider_id": "RDR-001",
            "merchant_id": "M-1", "customer_id": "C-1", "order_value": 50.0,
            "distance_km": 10.0, "promised_duration_min": 35, "actual_duration_min": 28.0,
            "delivery_status": "COMPLETED", "failure_reason": None,
            "start_time": "2024-06-01 10:00:00", "delivered_at": "2024-06-01 10:28:00",
            "customer_rating": 5.0, "city": "Bangalore"
        }]),
        "transactions": pd.DataFrame([{
            "transaction_id": "TXN-001", "rider_id": "RDR-001", "transaction_type": "EARNING",
            "amount": 55.0, "transaction_time": "2024-06-01 10:30:00", "payment_status": "SUCCESS", "notes": ""
        }]),
        "rider_activity_daily": pd.DataFrame([{
            "activity_id": "ACT-001", "rider_id": "RDR-001", "activity_date": "2024-06-01",
            "hours_online": 6.0, "trips_completed": 8, "deliveries_completed": 10,
            "deliveries_failed": 0, "distance_km": 65.0, "battery_swaps_count": 1,
            "total_earnings": 120.0, "peak_hour_ratio": 0.6
        }])
    }

    res = transform_all(raw_sample)
    
    # Check battery degradation calculation
    assert "degradation_rate_per_100_cycles" in res["batteries"].columns
    assert res["batteries"]["is_degraded"].iloc[0] == 0  # 78% SOH is > 75%
    
    # Check trips energy Wh/km
    assert "energy_wh_per_km" in res["trips"].columns
    assert res["trips"]["energy_wh_per_km"].iloc[0] == 32.0  # 0.32 kWh * 1000 / 10 km = 32 Wh/km
    
    # Check delivery on-time indicator
    assert "is_ontime" in res["deliveries"].columns
    assert res["deliveries"]["is_ontime"].iloc[0] == 1  # 28 <= 35 and COMPLETED
    assert res["deliveries"]["is_failed"].iloc[0] == 0
