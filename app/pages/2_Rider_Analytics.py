"""
Page 2: Rider Analytics.
Rider Onboarding Funnel, Cohort Retention Curves, Daily Activity & Earnings Distribution.
"""

import sys
sys.path.insert(0, "/workspace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.utils.data_loader import load_all_processed_data
from app.utils.ui_helpers import apply_custom_css, render_kpi, set_plotly_layout, THEME_COLORS

st.set_page_config(page_title="Rider Analytics", page_icon="👥", layout="wide")
apply_custom_css()

st.title("👥 Rider Operations & Lifecycle Analytics")
st.markdown("Onboarding conversion funnel, retention cohorts, operational intensity, and rider tier comparisons.")

data = load_all_processed_data()
if "riders" not in data or len(data["riders"]) == 0:
    st.error("Data unavailable. Run ETL first.")
    st.stop()

riders = data["riders"]
activity = data["rider_activity_daily"]

# Top KPIs
c1, c2, c3, c4 = st.columns(4)
total_signups = len(riders)
activated = len(riders[riders["is_activated"] == 1])
active = len(riders[riders["onboarding_status"] == "ACTIVE"])
churned = len(riders[riders["is_churned"] == 1])
act_rate = (activated / total_signups * 100)
churn_rate = (churned / activated * 100) if activated > 0 else 0

render_kpi(c1, "Total Signups", f"{total_signups:,}", "Top of Funnel", "neutral")
render_kpi(c2, "Activation Rate", f"{act_rate:.1f}%", f"{activated:,} Activated", "positive")
render_kpi(c3, "Currently Active", f"{active:,}", f"{active/total_signups*100:.1f}% of Pool", "positive")
render_kpi(c4, "Cohort Churn Rate", f"{churn_rate:.1f}%", f"{churned:,} Riders Churned", "negative")

st.markdown("---")

col1, col2 = st.columns([3, 2])

with col1:
    # Monthly Cohort Retention Bar
    riders["cohort_month"] = pd.to_datetime(riders["signup_date"]).dt.to_period("M").astype(str)
    cohort_df = riders.groupby("cohort_month").agg(
        Signups=("rider_id", "count"),
        Activated=("is_activated", "sum"),
        Retained=("onboarding_status", lambda s: (s == "ACTIVE").sum()),
        Churned=("is_churned", "sum")
    ).reset_index()

    fig_cohort = go.Figure()
    fig_cohort.add_trace(go.Bar(x=cohort_df["cohort_month"], y=cohort_df["Signups"], name="Signups", marker_color="#334155"))
    fig_cohort.add_trace(go.Bar(x=cohort_df["cohort_month"], y=cohort_df["Activated"], name="Activated", marker_color=THEME_COLORS["primary"]))
    fig_cohort.add_trace(go.Bar(x=cohort_df["cohort_month"], y=cohort_df["Retained"], name="Active Retained", marker_color=THEME_COLORS["teal"]))
    fig_cohort.add_trace(go.Scatter(x=cohort_df["cohort_month"], y=cohort_df["Churned"], name="Churned", mode="lines+markers", marker=dict(color=THEME_COLORS["coral"], size=7), line=dict(width=2)))
    set_plotly_layout(fig_cohort, "Signup Cohorts: Activation, Retention, and Churn", height=380)
    st.plotly_chart(fig_cohort, use_container_width=True)

with col2:
    # Onboarding Status Funnel
    status_counts = riders["onboarding_status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig_funnel = go.Figure(go.Funnel(
        y=status_counts["status"],
        x=status_counts["count"],
        textinfo="value+percent initial",
        marker=dict(color=[THEME_COLORS["teal"], THEME_COLORS["coral"], THEME_COLORS["amber"], "#64748B"])
    ))
    set_plotly_layout(fig_funnel, "Rider Status Distribution Funnel", height=380)
    st.plotly_chart(fig_funnel, use_container_width=True)

st.markdown("---")

# Row 2: Daily Hours vs Earnings Distribution by Tier
r2_col1, r2_col2 = st.columns(2)

with r2_col1:
    # Sample daily activity for clean scatter
    act_sample = activity.sample(n=min(5000, len(activity)), random_state=42)
    fig_scatter = px.scatter(
        act_sample,
        x="hours_online",
        y="total_earnings",
        color="peak_hour_ratio",
        color_continuous_scale=["#38BDF8", "#0284C7", "#0D9488", "#10B981"],
        opacity=0.6,
        labels={"hours_online": "Daily Hours Online", "total_earnings": "Total Daily Earnings ($)", "peak_hour_ratio": "Peak Ratio"}
    )
    set_plotly_layout(fig_scatter, "Rider Daily Engagement vs Earnings Velocity", height=350)
    st.plotly_chart(fig_scatter, use_container_width=True)

with r2_col2:
    tier_stats = riders.groupby("tier").agg(
        Riders=("rider_id", "count"),
        AvgRating=("rating_avg", "mean"),
        AvgDeliveries=("lifetime_deliveries", "mean"),
        AvgEarnings=("lifetime_earnings", "mean")
    ).reset_index()

    fig_tier = go.Figure()
    fig_tier.add_trace(go.Bar(
        x=tier_stats["tier"],
        y=tier_stats["AvgEarnings"],
        marker_color=[THEME_COLORS["primary"], THEME_COLORS["teal"], THEME_COLORS["emerald"]],
        text=[f"${e:,.0f}" for e in tier_stats["AvgEarnings"]],
        textposition="inside"
    ))
    set_plotly_layout(fig_tier, "Mean Lifetime Earnings by Rider Tier ($)", height=350)
    st.plotly_chart(fig_tier, use_container_width=True)

# Data Table
with st.expander("🔍 View Raw Rider Cohort Table"):
    st.dataframe(riders[["rider_id", "city", "tier", "signup_date", "activation_date", "onboarding_status", "rating_avg", "lifetime_deliveries", "lifetime_earnings"]].head(100), use_container_width=True)
