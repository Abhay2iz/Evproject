"""
Data loader and cache utility for EV Fleet Streamlit application.
"""

import os
import json
import joblib
import pandas as pd
import streamlit as st

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT_DIR / "data" / "processed"
POWERBI_DIR = ROOT_DIR / "data" / "powerbi_export"
ARTIFACTS_DIR = ROOT_DIR / "models_artifacts"

@st.cache_data(ttl=3600)
def load_all_processed_data():
    """Loads all processed datasets into memory with caching."""
    tables = [
        "suppliers", "manufacturing_lots", "batteries",
        "vehicles", "riders", "trips", "deliveries",
        "transactions", "rider_activity_daily"
    ]
    data = {}
    for t in tables:
        path = os.path.join(DATA_DIR, f"{t}.csv")
        if os.path.exists(path):
            data[t] = pd.read_csv(path)
        else:
            data[t] = pd.DataFrame()
    return data

@st.cache_data(ttl=3600)
def load_powerbi_data():
    """Loads Power BI semantic fact and dimension tables."""
    data = {}
    if os.path.exists(POWERBI_DIR):
        for f in os.listdir(POWERBI_DIR):
            if f.endswith(".csv"):
                key = f.replace(".csv", "")
                data[key] = pd.read_csv(os.path.join(POWERBI_DIR, f))
    return data

@st.cache_resource
def load_model_artifacts():
    """Loads trained ML model artifacts into memory."""
    models = {}
    for m in ["churn_model", "battery_model", "delivery_model", "segmentation_model"]:
        p = os.path.join(ARTIFACTS_DIR, f"{m}.joblib")
        if os.path.exists(p):
            models[m] = joblib.load(p)
    return models

@st.cache_data(ttl=3600)
def load_model_metadata():
    """Loads model training metadata JSON."""
    meta_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)
    return {}
