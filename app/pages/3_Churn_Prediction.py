"""
Page 3: Rider Churn Prediction & Risk Inference.
Interactive ML inference form, risk scoring, and at-risk rider queue.
"""

import sys
sys.path.insert(0, "/workspace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.utils.data_loader import load_model_artifacts, load_all_processed_data
from app.utils.ui_helpers import apply_custom_css, render_kpi, set_plotly_layout, THEME_COLORS
from src.features.engineering import build_churn_features

st.set_page_config(page_title="Churn Prediction", page_icon="🔮", layout="wide")
apply_custom_css()

st.title("🔮 Rider Churn Prediction & Early Warning System")
st.markdown("Proactively identify at-risk riders before departure using our trained Random Forest Classifier.")

# Load models
models = load_model_artifacts()
churn_artifact = models.get("churn_model")

if not churn_artifact:
    st.error("Churn model artifact not found. Please train models first: `python3 src/models/train_all.py`")
    st.stop()

pipeline = churn_artifact["pipeline"]
metrics = churn_artifact["metrics"]
feat_importances = churn_artifact["feature_importance"]

# Tabs for Inference and Analytics
tab1, tab2 = st.tabs(["⚡ Live Prediction Sandbox", "📊 Risk Queue & Model Drivers"])

with tab1:
    st.markdown("### 🎛️ Live Rider Risk Inference Form")
    st.markdown("Adjust the operational parameters below to evaluate real-time churn hazard for an individual rider.")
    
    with st.form("churn_prediction_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tenure_days = st.slider("Rider Fleet Tenure (Days)", min_value=5, max_value=365, value=90, step=5)
            active_days_30d = st.slider("Active Days in Last 30 Days", min_value=0, max_value=30, value=18)
            avg_hours_daily = st.slider("Average Daily Hours Online", min_value=0.5, max_value=12.0, value=5.5, step=0.5)
            tier = st.selectbox("Rider Contract Tier", options=["STANDARD", "PREMIUM", "PRO"], index=0)
            
        with col2:
            total_deliveries_30d = st.number_input("Deliveries Completed (Last 30 Days)", min_value=0, max_value=500, value=110, step=5)
            avg_daily_earnings = st.number_input("Average Daily Earnings ($)", min_value=0.0, max_value=300.0, value=75.0, step=5.0)
            earnings_momentum = st.slider("Earnings Momentum (Last 7d vs Prior 7d)", min_value=0.1, max_value=3.0, value=0.85, step=0.05, 
                                          help="Value < 1.0 indicates declining weekly earnings trend")
            city = st.selectbox("Operating Hub City", options=["Bangalore", "Delhi-NCR", "Hyderabad", "Mumbai", "Pune"], index=0)
            
        with col3:
            hours_momentum = st.slider("Hours Momentum (Last 7d vs Prior 7d)", min_value=0.1, max_value=3.0, value=0.90, step=0.05)
            failure_rate_30d = st.slider("Delivery Failure Rate (Last 30 Days)", min_value=0.0, max_value=0.40, value=0.04, step=0.01)
            rating_avg = st.slider("Customer Average Rating", min_value=3.0, max_value=5.0, value=4.7, step=0.1)
            battery_swaps_30d = st.number_input("Battery Swaps Performed (Last 30 Days)", min_value=0, max_value=80, value=22)

        submit_btn = st.form_submit_button("⚡ Evaluate Churn Risk Score", use_container_width=True)

    if submit_btn:
        # Compute derived features
        hourly_earnings_rate = round(avg_daily_earnings / (avg_hours_daily + 0.1), 2)
        swaps_per_delivery = round(battery_swaps_30d / (total_deliveries_30d + 1.0), 3)

        input_data = pd.DataFrame([{
            "tenure_days_at_cutoff": tenure_days,
            "active_days_30d": active_days_30d,
            "avg_hours_daily": avg_hours_daily,
            "total_deliveries_30d": total_deliveries_30d,
            "avg_daily_earnings": avg_daily_earnings,
            "battery_swaps_30d": battery_swaps_30d,
            "earnings_momentum_ratio": earnings_momentum,
            "hours_momentum_ratio": hours_momentum,
            "failure_rate_30d": failure_rate_30d,
            "hourly_earnings_rate": hourly_earnings_rate,
            "rating_avg": rating_avg,
            "swaps_per_delivery": swaps_per_delivery,
            "tier": tier,
            "city": city
        }])

        # Predict
        churn_prob = pipeline.predict_proba(input_data)[0, 1]
        is_churn = churn_prob >= 0.50

        st.markdown("---")
        st.markdown("### 🎯 Inference Results")
        res_col1, res_col2 = st.columns([1, 2])
        
        with res_col1:
            fig_pred_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=churn_prob * 100.0,
                number={'suffix': "%"},
                title=dict(text="Predicted Churn Hazard", font=dict(color="#F8FAFC", size=14)),
                gauge=dict(
                    axis=dict(range=[0, 100], tickcolor="#94A3B8"),
                    bar=dict(color=THEME_COLORS["coral"] if is_churn else THEME_COLORS["emerald"]),
                    bgcolor="#1E293B",
                    steps=[
                        dict(range=[0, 30], color="#065F46"),
                        dict(range=[30, 60], color="#92400E"),
                        dict(range=[60, 100], color="#991B1B")
                    ]
                )
            ))
            set_plotly_layout(fig_pred_gauge, "Model Probability Output", height=280)
            st.plotly_chart(fig_pred_gauge, use_container_width=True)

        with res_col2:
            if churn_prob >= 0.65:
                st.error("🚨 **HIGH CHURN HAZARD DETECTED**")
                st.markdown(f"**Estimated Probability:** `{churn_prob*100:.1f}%`")
                st.markdown("**Key Risk Factors Identified:**")
                st.markdown("""
                - Declining weekly earnings momentum (< 1.0) indicates driver disengagement.
                - Drop in active days over the last 30 days is a primary churn precursor.
                - High failure rate or low swap availability friction.
                """)
                st.markdown("**Recommended Operational Action:** Issue immediate $25 weekend retention quest incentive and dispatch proactive fleet manager outreach.")
            elif churn_prob >= 0.35:
                st.warning("⚠️ **MODERATE RETENTION RISK**")
                st.markdown(f"**Estimated Probability:** `{churn_prob*100:.1f}%`")
                st.markdown("Rider activity is softening. Add to 14-day supervisor check-in watchlist.")
            else:
                st.success("✅ **STABLE / LOW CHURN RISK**")
                st.markdown(f"**Estimated Probability:** `{churn_prob*100:.1f}%`")
                st.markdown("Rider exhibits strong engagement velocity and steady earning momentum.")

with tab2:
    st.markdown("### 📊 Churn Drivers & Historical Risk Distribution")
    
    col_feat, col_dist = st.columns([3, 2])
    with col_feat:
        feat_df = pd.DataFrame(feat_importances).head(10).sort_values(by="importance", ascending=True)
        fig_feat = px.bar(
            feat_df,
            x="importance",
            y="feature",
            orientation="h",
            color="importance",
            color_continuous_scale=["#0284C7", "#0D9488", "#10B981"],
            title="Top 10 Churn Feature Importances (Random Forest)"
        )
        set_plotly_layout(fig_feat, "Feature Importance Hierarchy", height=350)
        st.plotly_chart(fig_feat, use_container_width=True)

    with col_dist:
        st.markdown("#### 🏆 Production Model Performance")
        st.markdown(f"""
        - **Champion Architecture:** {churn_artifact['model_name']}
        - **Precision:** `{metrics['precision']:.4f}`
        - **Recall:** `{metrics['recall']:.4f}`
        - **F1-Score:** `{metrics['f1_score']:.4f}`
        - **ROC-AUC:** `{metrics['roc_auc']:.4f}`
        - **PR-AUC:** `{metrics['pr_auc']:.4f}`
        """)
        st.info("Trained strictly on historical cutoffs with 45-day forward inactivity evaluation window.")
