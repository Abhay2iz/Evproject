"""
Page 7: Rider Behavioral Segmentation & Personas.
Unsupervised K-Means clustering, cluster profiling, and interactive persona classifier.
"""

import sys
sys.path.insert(0, "/workspace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.utils.data_loader import load_model_artifacts
from app.utils.ui_helpers import apply_custom_css, render_kpi, set_plotly_layout, THEME_COLORS
from src.features.engineering import build_segmentation_features

st.set_page_config(page_title="Rider Segmentation", page_icon="🧩", layout="wide")
apply_custom_css()

st.title("🧩 Rider Behavioral Segmentation & Persona Profiling")
st.markdown("Unsupervised K-Means clustering reveals distinct operational archetypes to tailor retention, incentives, and shift scheduling.")

models = load_model_artifacts()
seg_artifact = models.get("segmentation_model")

if not seg_artifact:
    st.error("Segmentation model artifact not found. Please train models first: `python3 src/models/train_all.py`")
    st.stop()

scaler = seg_artifact["scaler"]
kmeans = seg_artifact["kmeans"]
profiles = seg_artifact["cluster_profiles"]
persona_mapping = seg_artifact["persona_mapping"]

# KPI Cards for Personas
st.markdown("### 👥 Operational Archetypes")
p_cols = st.columns(4)
for idx, p in enumerate(profiles):
    col = p_cols[idx]
    render_kpi(
        col,
        f"Cluster {p['cluster_id']}: {p['persona_name'].split('(')[0]}",
        f"{p['rider_count']:,} Riders",
        f"{p['share_pct']}% of Fleet | ${p['mean_earnings']:.0f}/day",
        "neutral"
    )

st.markdown("---")

tab1, tab2 = st.tabs(["📊 Cluster Distributions & Tradeoffs", "⚡ Live Rider Persona Classifier"])

with tab1:
    df_seg = build_segmentation_features()
    scaled_feats = scaler.transform(df_seg[seg_artifact["feature_cols"]])
    df_seg["cluster"] = kmeans.predict(scaled_feats)
    df_seg["persona"] = df_seg["cluster"].map(persona_mapping)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        fig_clust = px.scatter(
            df_seg,
            x="avg_daily_hours",
            y="total_earnings",
            color="persona",
            color_discrete_sequence=[THEME_COLORS["teal"], THEME_COLORS["primary"], THEME_COLORS["amber"], THEME_COLORS["coral"]],
            opacity=0.7,
            labels={"avg_daily_hours": "Average Daily Hours Online", "total_earnings": "Average Daily Earnings ($)"}
        )
        set_plotly_layout(fig_clust, "Engagement Hours vs Daily Earnings Velocity", height=380)
        st.plotly_chart(fig_clust, use_container_width=True)

    with col_s2:
        # Radar profile of clusters
        prof_df = pd.DataFrame(profiles)
        categories = ["Daily Hours", "Deliveries", "Rating", "Earnings ($)", "Failure Rate (%)"]
        
        fig_radar = go.Figure()
        for idx, row in prof_df.iterrows():
            vals = [
                row["mean_daily_hours"] / 10.0,
                row["mean_deliveries"] / 500.0,
                row["mean_rating"] / 5.0,
                row["mean_earnings"] / 1000.0,
                (1.0 - row["mean_failure_rate"]) # higher is better
            ]
            vals.append(vals[0])
            fig_radar.add_trace(go.Scatterpolar(
                r=vals,
                theta=categories + [categories[0]],
                fill='toself',
                name=f"C{row['cluster_id']}: {row['persona_name'].split('(')[0]}"
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            paper_bgcolor="#1E293B",
            font=dict(color="#94A3B8")
        )
        set_plotly_layout(fig_radar, "Multidimensional Persona Archetypes", height=380)
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("### 📋 Persona Strategy Matrix")
    for p in profiles:
        with st.expander(f"📌 {p['persona_name']} ({p['share_pct']}% of Active Fleet)"):
            st.markdown(f"""
            - **Profile Summary:** Operates **{p['mean_daily_hours']} hours/day** generating average daily earnings of **${p['mean_earnings']:.2f}** with an average customer rating of **{p['mean_rating']:.2f}**.
            - **Delivery Failure Rate:** `{p['mean_failure_rate']*100:.1f}%`
            - **Recommended Engagement Policy:**
                - *Incentive Strategy:* {"Surge tier bonuses for peak hours" if p['cluster_id'] == 0 else ("Guaranteed daily minimum lease subsidies" if p['cluster_id'] == 1 else ("Targeted weekend quests" if p['cluster_id'] == 2 else "Remedial onboarding & vehicle reassignment"))}
                - *Battery Allocation:* {"Priority ultra-fast swap reservation" if p['cluster_id'] in [0, 1] else "Standard swap queue"}
            """)

with tab2:
    st.markdown("### 🎛️ Live Rider Behavioral Classifier")
    st.markdown("Classify any rider into an operational persona using their behavioral parameters.")

    with st.form("persona_classifier_form"):
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            u_days = st.slider("Active Days on Platform", 5, 300, 120)
            u_hours = st.slider("Average Hours Online per Day", 1.0, 12.0, 6.5, 0.5)
            u_deliv = st.number_input("Total Lifetime Deliveries", 10, 2000, 350)
        with pc2:
            u_earn = st.number_input("Average Daily Earnings ($)", 10.0, 250.0, 85.0)
            u_rating = st.slider("Average Customer Rating", 3.0, 5.0, 4.6, 0.1)
            u_swaps = st.slider("Daily Battery Swaps", 0.0, 3.0, 1.2, 0.1)
        with pc3:
            u_peak = st.slider("Peak Hour Delivery Ratio", 0.1, 1.0, 0.65, 0.05)
            u_fail = st.slider("Historical Failure Rate", 0.0, 0.25, 0.04, 0.01)
            u_rate = st.number_input("Deliveries per Hour", 0.5, 4.0, 1.5, 0.1)

        btn_persona = st.form_submit_button("⚡ Classify Persona Archetype", use_container_width=True)

    if btn_persona:
        user_vector = np.array([[u_days, u_hours, u_deliv, u_earn, u_rating, u_swaps, u_peak, u_fail, u_rate]])
        scaled_vec = scaler.transform(user_vector)
        pred_clust = int(kmeans.predict(scaled_vec)[0])
        pred_persona = persona_mapping.get(pred_clust, f"Cluster {pred_clust}")

        st.markdown("---")
        st.success(f"🎯 **Identified Persona Archetype:** `{pred_persona}` (Cluster {pred_clust})")
