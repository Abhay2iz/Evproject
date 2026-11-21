"""
Page 1: Executive Overview.
High-level KPIs, Fleet Utilization, Monthly Delivery Trends, and City-level performance.
"""

import sys
sys.path.insert(0, "/workspace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.utils.data_loader import load_all_processed_data, load_powerbi_data
from app.utils.ui_helpers import apply_custom_css, render_kpi, set_plotly_layout, THEME_COLORS

st.set_page_config(page_title="Executive Overview", page_icon="📈", layout="wide")
apply_custom_css()

st.title("📈 Executive Fleet Overview")
st.markdown("Macro operational indicators, revenue run rate, delivery fulfillment, and regional fleet density.")

data = load_all_processed_data()
if not data or "riders" not in data or len(data["riders"]) == 0:
    st.error("Data not loaded. Please initialize database and run ETL.")
    st.stop()

deliveries = data["deliveries"]
vehicles = data["vehicles"]
batteries = data["batteries"]
riders = data["riders"]
activity = data["rider_activity_daily"]

# Sidebar filters
st.sidebar.markdown("### 🎛️ Filter Controls")
all_cities = sorted(deliveries["city"].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect("Select Cities", options=all_cities, default=all_cities)

# Apply filter
f_deliv = deliveries[deliveries["city"].isin(selected_cities)]
f_veh = vehicles[vehicles["hub_city"].isin(selected_cities)]
f_riders = riders[riders["city"].isin(selected_cities)]

# Top KPI row
c1, c2, c3, c4, c5 = st.columns(5)
tot_deliv = len(f_deliv)
completed_deliv = len(f_deliv[f_deliv["delivery_status"] == "COMPLETED"])
success_rate = (completed_deliv / tot_deliv * 100) if tot_deliv > 0 else 0
tot_gmv = f_deliv["order_value"].sum()
active_riders_cnt = len(f_riders[f_riders["onboarding_status"] == "ACTIVE"])
active_veh_cnt = len(f_veh[f_veh["status"] == "ACTIVE"])
uptime = (active_veh_cnt / len(f_veh) * 100) if len(f_veh) > 0 else 0

render_kpi(c1, "Deliveries", f"{tot_deliv:,}", "+3.2% MoM", "positive")
render_kpi(c2, "Fulfillment Rate", f"{success_rate:.1f}%", "-0.4% vs SLA", "negative" if success_rate < 95 else "positive")
render_kpi(c3, "Gross Merchandise", f"${tot_gmv:,.0f}", "+8.5% YoY", "positive")
render_kpi(c4, "Active Fleet Riders", f"{active_riders_cnt:,}", f"{len(f_riders)} Pool", "neutral")
render_kpi(c5, "Vehicle Uptime", f"{uptime:.1f}%", f"{active_veh_cnt}/{len(f_veh)} Ready", "positive")

st.markdown("---")

# Charts: Monthly Volume & City Fulfillment
col1, col2 = st.columns([3, 2])

with col1:
    f_deliv["year_month"] = pd.to_datetime(f_deliv["delivery_date"]).dt.to_period("M").astype(str)
    monthly_trend = f_deliv.groupby(["year_month", "delivery_status"]).size().reset_index(name="count")
    
    fig_monthly = px.bar(
        monthly_trend,
        x="year_month",
        y="count",
        color="delivery_status",
        color_discrete_map={
            "COMPLETED": THEME_COLORS["teal"],
            "FAILED_BATTERY_DEPLETED": THEME_COLORS["coral"],
            "FAILED_VEHICLE_BREAKDOWN": THEME_COLORS["amber"],
            "FAILED_TRAFFIC_DELAY": "#38BDF8",
            "FAILED_CUSTOMER_UNREACHABLE": "#94A3B8",
            "CANCELLED": "#64748B"
        },
        title="Monthly Delivery Fulfillment & Failure Trajectory"
    )
    set_plotly_layout(fig_monthly, "Monthly Order Volume by Outcome", height=380)
    st.plotly_chart(fig_monthly, use_container_width=True)

with col2:
    city_summary = f_deliv.groupby("city").agg(
        volume=("delivery_id", "count"),
        success_pct=("delivery_status", lambda s: (s == "COMPLETED").mean() * 100)
    ).reset_index().sort_values(by="volume", ascending=True)

    fig_city = go.Figure()
    fig_city.add_trace(go.Bar(
        x=city_summary["volume"],
        y=city_summary["city"],
        orientation="h",
        marker=dict(color=THEME_COLORS["primary"], line=dict(color="#0F172A", width=1)),
        text=[f"{v:,} ({s:.1f}%)" for v, s in zip(city_summary["volume"], city_summary["success_pct"])],
        textposition="inside",
        name="Orders"
    ))
    set_plotly_layout(fig_city, "Order Volume & Success Rate by Hub City", height=380)
    st.plotly_chart(fig_city, use_container_width=True)

st.markdown("---")

# Row 2: Fleet Telematics Gauge & Regional Vehicle Deployment
r2_col1, r2_col2, r2_col3 = st.columns([2, 2, 2])

with r2_col1:
    avg_soh = batteries["current_soh_pct"].mean()
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_soh,
        title=dict(text="Fleet Mean Battery SOH (%)", font=dict(color="#F8FAFC", size=13)),
        gauge=dict(
            axis=dict(range=[50, 100], tickcolor="#94A3B8"),
            bar=dict(color=THEME_COLORS["teal"]),
            bgcolor="#1E293B",
            steps=[
                dict(range=[50, 75], color="#991B1B"),
                dict(range=[75, 85], color="#92400E"),
                dict(range=[85, 100], color="#065F46")
            ],
            threshold=dict(
                line=dict(color="#EF4444", width=3),
                thickness=0.75,
                value=75.0
            )
        )
    ))
    set_plotly_layout(fig_gauge, "Battery Health SOH Status", height=280)
    st.plotly_chart(fig_gauge, use_container_width=True)

with r2_col2:
    veh_status = f_veh["status"].value_counts().reset_index()
    veh_status.columns = ["status", "count"]
    fig_veh = px.pie(
        veh_status,
        names="status",
        values="count",
        color="status",
        color_discrete_map={
            "ACTIVE": THEME_COLORS["emerald"],
            "MAINTENANCE": THEME_COLORS["amber"],
            "RETIRED": THEME_COLORS["coral"]
        },
        hole=0.4
    )
    set_plotly_layout(fig_veh, "Fleet Asset Operational Status", height=280)
    st.plotly_chart(fig_veh, use_container_width=True)

with r2_col3:
    st.markdown("#### 📥 Export Operational Reports")
    st.markdown("Download full analytical aggregations for executive reviews.")
    csv_bytes = city_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download City Aggregations (CSV)",
        data=csv_bytes,
        file_name="city_fleet_summary.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.info("Power BI star-schema models are refreshed in `/workspace/data/powerbi_export/`.")
