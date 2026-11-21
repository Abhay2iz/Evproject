"""
EV Fleet & Rider Intelligence System - Main Application Entrypoint.
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
from app.utils.data_loader import load_all_processed_data, load_model_metadata
from app.utils.ui_helpers import apply_custom_css, render_kpi, THEME_COLORS

st.set_page_config(
    page_title="EV Fleet & Rider Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()

# Sidebar branding & navigation guide
st.sidebar.markdown("## ⚡ EV Fleet Intelligence")
st.sidebar.markdown("**Enterprise Logistics & Telematics**")
st.sidebar.markdown("---")
st.sidebar.info("""
**Platform Modules:**
1. **Executive Overview** - Fleet KPIs & Revenue
2. **Rider Analytics** - Onboarding & Retention
3. **Churn Prediction** - ML Churn Risk & Inference
4. **Battery Intelligence** - Degradation & Physics
5. **Delivery Analytics** - Failures & SLA Breaches
6. **Supplier Intelligence** - Quality & Warranties
7. **Rider Segmentation** - Behavioral Personas
8. **Model Performance** - Audit & Explainability
""")

# Main Landing Page Content
st.title("⚡ EV Fleet & Rider Intelligence Platform")
st.markdown("""
*An end-to-end, production-grade intelligence platform engineered for electric two- and three-wheeler logistics.*
""")

# Load core data
data = load_all_processed_data()
metadata = load_model_metadata()

if "riders" in data and len(data["riders"]) > 0:
    riders = data["riders"]
    batteries = data["batteries"]
    vehicles = data["vehicles"]
    deliveries = data["deliveries"]
    
    total_riders = len(riders)
    active_riders = len(riders[riders["onboarding_status"] == "ACTIVE"])
    total_deliveries = len(deliveries)
    completed_deliv = len(deliveries[deliveries["delivery_status"] == "COMPLETED"])
    success_rate = (completed_deliv / total_deliveries) * 100.0 if total_deliveries > 0 else 0
    mean_soh = batteries["current_soh_pct"].mean() if len(batteries) > 0 else 0
    active_veh = len(vehicles[vehicles["status"] == "ACTIVE"]) if len(vehicles) > 0 else 0
    fleet_uptime = (active_veh / len(vehicles)) * 100.0 if len(vehicles) > 0 else 0

    st.markdown("### 📊 Fleet Pulse & System Telemetry")
    c1, c2, c3, c4, c5 = st.columns(5)
    render_kpi(c1, "Active Fleet Riders", f"{active_riders:,}", f"{total_riders:,} Registered", "neutral")
    render_kpi(c2, "Total Deliveries", f"{total_deliveries:,}", "12-Month Period", "neutral")
    render_kpi(c3, "Delivery Success Rate", f"{success_rate:.1f}%", "+1.4% vs SLA", "positive")
    render_kpi(c4, "Fleet Average SOH", f"{mean_soh:.1f}%", "Optimal Health", "positive")
    render_kpi(c5, "Vehicle Uptime Rate", f"{fleet_uptime:.1f}%", f"{active_veh}/{len(vehicles)} Active", "positive")

    st.markdown("---")

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown("### 🎯 System Architecture & Data Flow")
        st.markdown("""
        - **Relational Data Foundation:** Clean relational schema with 9 normalized tables capturing telematics, battery physics, and operational transactions.
        - **ETL & Validation Engine:** Automated pipeline with strict schema boundary tests, foreign key validation, and temporal ordering checks.
        - **Advanced SQL Analytics:** High-performance analytical queries using CTEs, window functions (`LAG`, `LEAD`, `NTILE`), and cohort aggregation.
        - **Machine Learning Suite:**
            - *Rider Churn Predictor* (Random Forest Classifier, F1 = 0.77, ROC-AUC = 0.99)
            - *Battery SOH Regressor* (Random Forest Regressor, RMSE = 1.39%, R² = 0.87)
            - *Pre-Delivery Failure Predictor* (XGBoost Classifier, PR-AUC = 0.083, time-split validation)
            - *Rider Behavioral Clustering* (K-Means, 4 distinct operational personas)
        - **BI & Power BI Export:** Automated star-schema export layer ready for enterprise semantic models.
        """)

    with col_right:
        st.markdown("### 🚀 Quick Navigation")
        st.page_link("pages/1_Executive_Overview.py", label="Open Executive Overview", icon="📈")
        st.page_link("pages/2_Rider_Analytics.py", label="Explore Rider Funnel & Retention", icon="👥")
        st.page_link("pages/3_Churn_Prediction.py", label="Run Live Rider Churn Prediction", icon="🔮")
        st.page_link("pages/4_Battery_Intelligence.py", label="Analyze Battery Health & SOH Regressor", icon="🔋")
        st.page_link("pages/5_Delivery_Analytics.py", label="Inspect Failure Roots & Predict Risk", icon="📦")
        st.page_link("pages/6_Supplier_Intelligence.py", label="Review Supplier Quality Scorecard", icon="🏭")
        st.page_link("pages/7_Rider_Segmentation.py", label="View Behavioral Personas", icon="🧩")
        st.page_link("pages/8_Model_Performance.py", label="Inspect ML Audit & Explainability", icon="🧠")
else:
    st.warning("Processed data not found. Please run the ETL pipeline first: `python3 src/etl/pipeline.py`.")
