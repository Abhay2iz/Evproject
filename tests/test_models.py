"""
Unit tests for Machine Learning model inference, serialization, and edge cases.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import pytest
import joblib
import numpy as np
import pandas as pd

ARTIFACTS_DIR = "/workspace/models_artifacts"

def test_churn_model_inference():
    """Verify Churn prediction pipeline loads and produces valid probabilities."""
    path = os.path.join(ARTIFACTS_DIR, "churn_model.joblib")
    assert os.path.exists(path), "Churn model artifact missing."
    artifact = joblib.load(path)
    pipe = artifact["pipeline"]

    test_input = pd.DataFrame([{
        "tenure_days_at_cutoff": 45,
        "active_days_30d": 12,
        "avg_hours_daily": 4.5,
        "total_deliveries_30d": 60,
        "avg_daily_earnings": 50.0,
        "battery_swaps_30d": 10,
        "earnings_momentum_ratio": 0.70,
        "hours_momentum_ratio": 0.80,
        "failure_rate_30d": 0.05,
        "hourly_earnings_rate": 11.1,
        "rating_avg": 4.5,
        "swaps_per_delivery": 0.16,
        "tier": "STANDARD",
        "city": "Bangalore"
    }])

    prob = pipe.predict_proba(test_input)[0, 1]
    assert 0.0 <= prob <= 1.0, f"Probability out of range: {prob}"

def test_churn_model_edge_case_zeroes():
    """Verify Churn prediction on extreme zero values."""
    artifact = joblib.load(os.path.join(ARTIFACTS_DIR, "churn_model.joblib"))
    pipe = artifact["pipeline"]

    edge_input = pd.DataFrame([{
        "tenure_days_at_cutoff": 0,
        "active_days_30d": 0,
        "avg_hours_daily": 0.0,
        "total_deliveries_30d": 0,
        "avg_daily_earnings": 0.0,
        "battery_swaps_30d": 0,
        "earnings_momentum_ratio": 0.0,
        "hours_momentum_ratio": 0.0,
        "failure_rate_30d": 1.0,
        "hourly_earnings_rate": 0.0,
        "rating_avg": 3.0,
        "swaps_per_delivery": 0.0,
        "tier": "STANDARD",
        "city": "Mumbai"
    }])

    prob = pipe.predict_proba(edge_input)[0, 1]
    assert 0.0 <= prob <= 1.0
    # Zero activity rider should have very high churn probability
    assert prob >= 0.50

def test_battery_regressor_inference():
    """Verify Battery SOH regressor loads and predicts within physical bounds."""
    path = os.path.join(ARTIFACTS_DIR, "battery_model.joblib")
    assert os.path.exists(path), "Battery model artifact missing."
    artifact = joblib.load(path)
    pipe = artifact["pipeline"]

    test_input = pd.DataFrame([{
        "cycle_count": 800,
        "battery_age_days": 300,
        "nominal_capacity_kwh": 3.2,
        "chemistry_type": "LFP",
        "max_temp_celsius_recorded": 42.0,
        "internal_resistance_m_ohm": 32.0,
        "supplier_tier": "Tier-1",
        "supplier_rating": 4.7,
        "defect_rate_estimate": 0.015
    }])

    soh_pred = pipe.predict(test_input)[0]
    assert 40.0 <= soh_pred <= 100.0, f"SOH prediction unreasonable: {soh_pred}"

def test_delivery_risk_inference():
    """Verify Delivery failure risk model runs on pre-delivery features."""
    path = os.path.join(ARTIFACTS_DIR, "delivery_model.joblib")
    assert os.path.exists(path), "Delivery model artifact missing."
    artifact = joblib.load(path)
    pipe = artifact["pipeline"]

    test_input = pd.DataFrame([{
        "distance_km": 12.0,
        "promised_duration_min": 40,
        "order_value": 75.0,
        "hour_of_day": 20,
        "day_of_week": 4,
        "is_weekend": 0,
        "is_peak_hour": 1,
        "start_soc_pct": 25.0,
        "ambient_temp_c": 36.0,
        "current_soh_pct": 82.0,
        "internal_resistance_m_ohm": 34.0,
        "chemistry_type": "LFP",
        "city": "Delhi-NCR"
    }])

    prob = pipe.predict_proba(test_input)[0, 1]
    assert 0.0 <= prob <= 1.0

def test_segmentation_inference():
    """Verify K-Means clustering predicts cluster within [0, 3]."""
    path = os.path.join(ARTIFACTS_DIR, "segmentation_model.joblib")
    assert os.path.exists(path), "Segmentation artifact missing."
    artifact = joblib.load(path)
    scaler = artifact["scaler"]
    km = artifact["kmeans"]

    sample_vec = np.array([[120, 6.5, 300, 85.0, 4.7, 1.2, 0.6, 0.03, 1.5]])
    scaled = scaler.transform(sample_vec)
    cluster = km.predict(scaled)[0]
    assert cluster in [0, 1, 2, 3]
