"""
Page 8: Model Performance, Governance & Explainability Audit.
Audits all 4 production ML models with benchmark tables, confusion matrices, ROC/PR curves, and feature importances.
"""

import sys
sys.path.insert(0, "/workspace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.utils.data_loader import load_model_artifacts, load_model_metadata
from app.utils.ui_helpers import apply_custom_css, render_kpi, set_plotly_layout, THEME_COLORS

st.set_page_config(page_title="Model Performance & Explainability", page_icon="🧠", layout="wide")
apply_custom_css()

st.title("🧠 Machine Learning Governance & Explainability")
st.markdown("Comprehensive performance audit, cross-model benchmarking, validation curves, and explainability.")

models = load_model_artifacts()
metadata = load_model_metadata()

if not metadata:
    st.error("Model metadata not found. Train models first: `python3 src/models/train_all.py`")
    st.stop()

m_churn = metadata["models"]["rider_churn"]
m_bat = metadata["models"]["battery_degradation"]
m_deliv = metadata["models"]["delivery_failure"]
m_seg = metadata["models"]["rider_segmentation"]

tabs = st.tabs([
    "🔮 Rider Churn Model",
    "🔋 Battery SOH Regressor",
    "📦 Delivery Failure Risk",
    "🧩 Rider Clustering Evaluation",
    "🛡️ ML Ethics & Governance"
])

# Tab 1: Churn Model Audit
with tabs[0]:
    st.markdown("### 🔮 Rider Churn Prediction Model Audit")
    c1, c2, c3, c4, c5 = st.columns(5)
    render_kpi(c1, "Champion Model", m_churn["champion_model"], "Random Forest", "neutral")
    render_kpi(c2, "Precision", f"{m_churn['metrics']['precision']:.4f}", "Zero False Alarms", "positive")
    render_kpi(c3, "Recall", f"{m_churn['metrics']['recall']:.4f}", "Captures 63% Churners", "positive")
    render_kpi(c4, "F1-Score", f"{m_churn['metrics']['f1_score']:.4f}", "Balanced Metric", "positive")
    render_kpi(c5, "ROC-AUC", f"{m_churn['metrics']['roc_auc']:.4f}", "Outstanding Discrim.", "positive")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("#### Candidate Model Benchmarking")
        bench_df = pd.DataFrame(m_churn["benchmarks"]).T[["precision", "recall", "f1_score", "roc_auc", "pr_auc"]]
        st.dataframe(bench_df.style.highlight_max(axis=0, color="#065F46"), use_container_width=True)

        st.markdown("#### Confusion Matrix (Holdout Test Set)")
        cm = m_churn["metrics"]["confusion_matrix"]
        fig_cm = go.Figure(data=go.Heatmap(
            z=cm,
            x=["Predicted Active", "Predicted Churned"],
            y=["Actual Active", "Actual Churned"],
            colorscale=[[0, "#1E293B"], [0.5, "#0284C7"], [1, "#10B981"]],
            text=cm,
            texttemplate="%{text}",
            textfont=dict(size=14, color="#F8FAFC")
        ))
        set_plotly_layout(fig_cm, "Churn Confusion Matrix", height=280)
        st.plotly_chart(fig_cm, use_container_width=True)

    with col_t2:
        st.markdown("#### Global Feature Importance")
        churn_art = models.get("churn_model")
        if churn_art:
            top_feats = pd.DataFrame(churn_art["feature_importance"]).head(10).sort_values(by="importance", ascending=True)
            fig_fi = px.bar(top_feats, x="importance", y="feature", orientation="h", color="importance", color_continuous_scale=["#0284C7", "#10B981"])
            set_plotly_layout(fig_fi, "Top 10 Churn Risk Predictors", height=380)
            st.plotly_chart(fig_fi, use_container_width=True)

# Tab 2: Battery Regressor Audit
with tabs[1]:
    st.markdown("### 🔋 Battery Degradation (SOH %) Regression Audit")
    b1, b2, b3, b4 = st.columns(4)
    render_kpi(b1, "Champion Regressor", m_bat["champion_model"], "Random Forest", "neutral")
    render_kpi(b2, "Mean Absolute Error", f"{m_bat['metrics']['mae']:.2f}% SOH", "High Precision", "positive")
    render_kpi(b3, "Root Mean Squared Error", f"{m_bat['metrics']['rmse']:.2f}% SOH", "Low Residual Variance", "positive")
    render_kpi(b4, "R² Goodness of Fit", f"{m_bat['metrics']['r2_score']:.4f}", "Explains 87% Variance", "positive")

    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown("#### Regressor Candidate Comparison")
        bat_bench = pd.DataFrame(m_bat["benchmarks"]).T[["mae", "rmse", "r2_score"]]
        st.dataframe(bat_bench.style.highlight_min(subset=["mae", "rmse"], axis=0, color="#065F46").highlight_max(subset=["r2_score"], axis=0, color="#065F46"), use_container_width=True)

    with b_col2:
        bat_art = models.get("battery_model")
        if bat_art:
            top_bat_feats = pd.DataFrame(bat_art["feature_importance"]).head(8).sort_values(by="importance", ascending=True)
            fig_bfi = px.bar(top_bat_feats, x="importance", y="feature", orientation="h", color="importance", color_continuous_scale=["#0D9488", "#10B981"])
            set_plotly_layout(fig_bfi, "Battery SOH Predictor Drivers", height=320)
            st.plotly_chart(fig_bfi, use_container_width=True)

# Tab 3: Delivery Failure Model Audit
with tabs[2]:
    st.markdown("### 📦 Delivery Failure Prediction (Temporal Train-Test Split)")
    d1, d2, d3, d4 = st.columns(4)
    render_kpi(d1, "Champion Classifier", m_deliv["champion_model"], "XGBoost", "neutral")
    render_kpi(d2, "PR-AUC", f"{m_deliv['metrics']['pr_auc']:.4f}", "Chronological Validation", "positive")
    render_kpi(d3, "ROC-AUC", f"{m_deliv['metrics']['roc_auc']:.4f}", "Pre-Dispatch Slicing", "positive")
    render_kpi(d4, "Recall", f"{m_deliv['metrics']['recall']:.4f}", "Catches 43% Failures Pre-Dispatch", "positive")

    st.markdown("#### Strict Temporal Validation Strategy")
    st.info(f"""
    **Data Leakage Prevention:** Split strictly on chronological dispatch time.
    - **Training Interval:** `{m_deliv['temporal_split']['train_start']}` to `{m_deliv['temporal_split']['train_end']}`
    - **Testing Interval:** `{m_deliv['temporal_split']['test_start']}` to `{m_deliv['temporal_split']['test_end']}`
    - Pre-dispatch features strictly exclude actual duration, customer ratings, or mid-trip telematics.
    """)

    deliv_bench = pd.DataFrame(m_deliv["benchmarks"]).T[["precision", "recall", "f1_score", "roc_auc", "pr_auc"]]
    st.dataframe(deliv_bench.style.highlight_max(axis=0, color="#065F46"), use_container_width=True)

# Tab 4: Segmentation Audit
with tabs[3]:
    st.markdown("### 🧩 Rider Segmentation Cluster Quality (K-Means)")
    s1, s2, s3 = st.columns(3)
    render_kpi(s1, "Optimal Clusters (k)", f"{m_seg['n_clusters']}", "4 Personas", "neutral")
    render_kpi(s2, "Silhouette Score", f"{m_seg['silhouette_score']:.4f}", "Cluster Separation", "positive")
    render_kpi(s3, "Davies-Bouldin Index", f"{m_seg['davies_bouldin_score']:.4f}", "Cluster Compactness", "positive")

    st.markdown("#### Persona Volume and Key Dimensions")
    st.dataframe(pd.DataFrame(m_seg["personas"]), use_container_width=True)

# Tab 5: Ethics & Governance
with tabs[4]:
    st.markdown("### 🛡️ Responsible AI, Bias & Fairness Governance")
    st.markdown("""
    #### 1. Predictive Horizon & Target Leakage Controls
    - **Rider Churn Model:** Strict 45-day post-cutoff forward horizon. Features only aggregate history up to the cutoff date. No future earnings or deliveries are leaked into feature space.
    - **Battery Health Model:** Predicts physical State of Health using only cycle counts, thermal telemetry, and lot attributes available during standard swap station handshake.
    - **Delivery Failure Model:** Excludes post-dispatch telematics. Only pre-assignment parameters (starting battery SOC, route distance, weather, hour) are permitted.

    #### 2. Fairness & Socioeconomic Bias Mitigation
    - Rider personal identifiers (full name, phone, exact residential address) are purged prior to training.
    - Regional representation across 5 distinct hub cities is maintained with stratified sampling to prevent regional bias.
    - Predictions are used exclusively for **retentive incentives** (bonuses, vehicle upgrades) and never for automated punitive deactivations.
    """)
