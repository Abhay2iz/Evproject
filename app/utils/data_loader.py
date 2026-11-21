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
    """Load all processed CSV tables into a dictionary."""
    
    # Temporary debug (will show on the app)
    st.write("DEBUG → ROOT_DIR:", ROOT_DIR)
    st.write("DEBUG → DATA_DIR:", DATA_DIR)
    st.write("DEBUG → DATA_DIR exists?:", DATA_DIR.exists())
    
    data = {}

    if not DATA_DIR.exists():
        st.error("data/processed folder not found!")
        return data

    files = list(DATA_DIR.iterdir())
    st.write("DEBUG → Files found:", [f.name for f in files])

    for f in files:
        if f.suffix.lower() == ".csv":
            key = f.stem
            try:
                df = pd.read_csv(f)
                data[key] = df
                st.write(f"Loaded {key}: {len(df)} rows")
            except Exception as e:
                st.error(f"Failed to load {f.name}: {e}")

    return data


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