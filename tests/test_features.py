"""
Unit tests for Feature Engineering pipelines.
Verifies feature structure, temporal logic, and target integrity.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import pytest
import pandas as pd
from src.features.engineering import (
    build_churn_features,
    build_battery_features,
    build_delivery_features,
    build_segmentation_features
)

def test_churn_features():
    """Verify churn feature matrix columns, targets, and non-null values."""
    df = build_churn_features()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "churn_label" in df.columns
    assert "earnings_momentum_ratio" in df.columns
    assert "failure_rate_30d" in df.columns
    assert set(df["churn_label"].unique()).issubset({0, 1})
    assert df["earnings_momentum_ratio"].isna().sum() == 0

def test_battery_features():
    """Verify battery feature matrix columns and SOH target."""
    df = build_battery_features()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "current_soh_pct" in df.columns
    assert "cycle_count" in df.columns
    assert "internal_resistance_m_ohm" in df.columns
    assert df["current_soh_pct"].min() >= 0.0
    assert df["current_soh_pct"].max() <= 100.0

def test_delivery_features():
    """Verify pre-delivery feature matrix."""
    df = build_delivery_features(sample_size=1000)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1000
    assert "target_failure" in df.columns
    assert "start_soc_pct" in df.columns
    assert "distance_km" in df.columns
    # Ensure post-delivery features are NOT in the pre-delivery feature matrix
    assert "delivered_at" not in df.columns
    assert "customer_rating" not in df.columns
    assert "actual_duration_min" not in df.columns

def test_segmentation_features():
    """Verify behavioral clustering feature matrix."""
    df = build_segmentation_features()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "avg_daily_hours" in df.columns
    assert "total_earnings" in df.columns
    assert "failure_rate" in df.columns
    assert df["avg_daily_hours"].isna().sum() == 0
