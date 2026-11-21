"""
Unit tests for Streamlit application utility helpers and data loaders.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import pytest
import pandas as pd
from app.utils.data_loader import load_all_processed_data, load_model_metadata, load_model_artifacts

def test_data_loader_processed_tables():
    """Verify processed data loader pulls cached tables."""
    data = load_all_processed_data()
    assert isinstance(data, dict)
    assert "riders" in data
    assert "batteries" in data
    assert len(data["riders"]) > 0

def test_metadata_loader():
    """Verify model metadata loader retrieves structured dictionary."""
    meta = load_model_metadata()
    assert isinstance(meta, dict)
    assert "models" in meta
    assert "rider_churn" in meta["models"]
    assert "battery_degradation" in meta["models"]

def test_artifacts_loader():
    """Verify all 4 model artifacts load successfully."""
    artifacts = load_model_artifacts()
    assert "churn_model" in artifacts
    assert "battery_model" in artifacts
    assert "delivery_model" in artifacts
    assert "segmentation_model" in artifacts
