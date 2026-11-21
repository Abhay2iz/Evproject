"""
Unit tests for Data Quality Validation suite.
Tests both clean data and intentionally corrupted edge cases.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import pytest
import pandas as pd
from src.etl.validator import DataValidator

def test_validator_clean_data():
    """Verify clean dataset passes validation with zero errors."""
    clean_data = {
        "suppliers": pd.DataFrame([{"supplier_id": "SUP-1", "supplier_name": "Volt"}]),
        "manufacturing_lots": pd.DataFrame([{"lot_id": "LOT-1", "supplier_id": "SUP-1"}]),
        "batteries": pd.DataFrame([{"battery_id": "BAT-1", "supplier_id": "SUP-1", "chemistry_type": "LFP", "current_soh_pct": 85.0}]),
        "vehicles": pd.DataFrame([{"vehicle_id": "VEH-1", "vin": "VIN1", "model_name": "VoltCruiser"}]),
        "riders": pd.DataFrame([{"rider_id": "RDR-1", "email": "r1@test.com", "signup_date": "2024-01-01", "onboarding_status": "ACTIVE"}]),
        "trips": pd.DataFrame([{
            "trip_id": "TRP-1", "rider_id": "RDR-1", "vehicle_id": "VEH-1", "battery_id": "BAT-1",
            "start_time": "2024-06-01 10:00:00", "end_time": "2024-06-01 10:30:00",
            "distance_km": 8.0, "start_soc_pct": 90.0, "end_soc_pct": 80.0
        }]),
        "deliveries": pd.DataFrame([{
            "delivery_id": "DEL-1", "rider_id": "RDR-1", "delivery_status": "COMPLETED", "start_time": "2024-06-01 10:00:00"
        }]),
        "transactions": pd.DataFrame([{
            "transaction_id": "TXN-1", "rider_id": "RDR-1", "amount": 25.0, "transaction_time": "2024-06-01 10:30:00"
        }])
    }

    validator = DataValidator()
    report = validator.validate_all(clean_data)
    assert report["passed"] is True
    assert len(report["errors"]) == 0

def test_validator_catches_null_pk():
    """Verify validator flags null primary keys."""
    bad_data = {
        "suppliers": pd.DataFrame([{"supplier_id": None, "supplier_name": "Volt"}]),
        "batteries": pd.DataFrame([{"battery_id": "BAT-1", "supplier_id": "SUP-1", "chemistry_type": "LFP", "current_soh_pct": 85.0}])
    }
    validator = DataValidator()
    report = validator.validate_all(bad_data)
    assert report["passed"] is False
    assert any("nulls" in err for err in report["errors"])

def test_validator_catches_invalid_soh_range():
    """Verify validator flags SOH outside [0, 100]."""
    bad_data = {
        "suppliers": pd.DataFrame([{"supplier_id": "SUP-1", "supplier_name": "Volt"}]),
        "batteries": pd.DataFrame([{"battery_id": "BAT-1", "supplier_id": "SUP-1", "chemistry_type": "LFP", "current_soh_pct": 115.0}])
    }
    validator = DataValidator()
    report = validator.validate_all(bad_data)
    assert report["passed"] is False
    assert any("SOH outside [0, 100]" in err for err in report["errors"])

def test_validator_catches_orphan_foreign_keys():
    """Verify validator flags orphan rider IDs in trips."""
    orphan_data = {
        "suppliers": pd.DataFrame([{"supplier_id": "SUP-1", "supplier_name": "Volt"}]),
        "batteries": pd.DataFrame([{"battery_id": "BAT-1", "supplier_id": "SUP-1", "chemistry_type": "LFP", "current_soh_pct": 85.0}]),
        "vehicles": pd.DataFrame([{"vehicle_id": "VEH-1", "vin": "VIN1", "model_name": "VoltCruiser"}]),
        "riders": pd.DataFrame([{"rider_id": "RDR-VALID", "email": "r1@test.com", "signup_date": "2024-01-01", "onboarding_status": "ACTIVE"}]),
        "trips": pd.DataFrame([{
            "trip_id": "TRP-1", "rider_id": "RDR-ORPHAN", "vehicle_id": "VEH-1", "battery_id": "BAT-1",
            "start_time": "2024-06-01 10:00:00", "end_time": "2024-06-01 10:30:00",
            "distance_km": 8.0, "start_soc_pct": 90.0, "end_soc_pct": 80.0
        }]),
        "deliveries": pd.DataFrame([{"delivery_id": "DEL-1", "rider_id": "RDR-VALID", "delivery_status": "COMPLETED", "start_time": "2024-06-01 10:00:00"}]),
        "transactions": pd.DataFrame([{"transaction_id": "TXN-1", "rider_id": "RDR-VALID", "amount": 25.0, "transaction_time": "2024-06-01 10:30:00"}])
    }
    validator = DataValidator()
    report = validator.validate_all(orphan_data)
    assert report["passed"] is False
    assert any("orphan rider_ids" in err for err in report["errors"])
