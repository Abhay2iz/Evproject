"""
Page 4: Battery Intelligence & State of Health (SOH) Regressor.
Degradation physics, thermal impact, high-risk pack queue, and live SOH prediction.
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

st.set_page_config(page_title="Battery Intelligence", page_icon="🔋", layout="wide")
apply_custom_css()

st.title("🔋 Battery Fleet Telematics & Degradation Intelligence")
st.markdown("Track battery State of Health (SOH), impedance growth, thermal stress, and forecast battery degradation.")

data = load_all_processed_data()
models = load_model_artifacts()

if "batteries" not in data or len(data["batteries"]) == 0:
    st.error("Battery data not found. Run ETL first.")
    st.stop()

batteries = data["batteries"]
battery_artifact = models.get("battery_model")

# Top KPI row
c1, c2, c3, c4 = st.columns(4)
total_bats = len(batteries)
mean_soh = batteries["current_soh_pct"].mean()
degraded_count = (batteries["current_soh_pct"] < 75.0).sum()
avg_ir = batteries["internal_resistance_m_ohm"].mean()

render_kpi(c1, "Total Battery Fleet", f"{total_bats:,}", "Active & Swapping", "neutral")
render_kpi(c2, "Mean State of Health", f"{mean_soh:.1f}%", "-0.2% vs baseline", "positive")
render_kpi(c3, "Degraded (<75% SOH)", f"{degraded_count}", f"{degraded_count/total_bats*100:.1f}% of Fleet", "negative" if degraded_count > 50 else "positive")
render_kpi(c4, "Mean Resistance", f"{avg_ir:.1f} mΩ", "Nominal: 22 - 38 mΩ", "neutral")

st.markdown("---")

tab1, tab2 = st.tabs(["⚡ Live SOH Regressor", "📈 Fleet Physics & Replacement Queue"])

with tab1:
    st.markdown("### 🎛️ Live Battery SOH % Prediction Form")
    st.markdown("Predict the current State of Health (SOH %) of an EV battery pack given its thermal, cycling, and manufacturing characteristics.")

    with st.form("battery_soh_form"):
        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            cycle_count = st.slider("Cumulative Cycle Count", min_value=10, max_value=2500, value=750, step=10)
            battery_age_days = st.slider("Battery Age (Days Since Production)", min_value=30, max_value=730, value=280, step=10)
            chemistry_type = st.selectbox("Battery Chemistry", options=["LFP", "NMC"], index=0)
        with b_col2:
            max_temp = st.slider("Max Recorded Cell Temp (°C)", min_value=25.0, max_value=60.0, value=41.5, step=0.5)
            internal_resistance = st.slider("Internal Resistance (mΩ)", min_value=18.0, max_value=65.0, value=32.0, step=0.5)
            nominal_capacity = st.number_input("Nominal Capacity (kWh)", min_value=2.0, max_value=5.0, value=3.2, step=0.1)
        with b_col3:
            supplier_tier = st.selectbox("Supplier Quality Tier", options=["Tier-1", "Tier-2", "Tier-3"], index=0)
            supplier_rating = st.slider("Supplier Audit Rating", min_value=1.0, max_value=5.0, value=4.5, step=0.1)
            defect_rate = st.slider("Lot Defect Rate Estimate", min_value=0.001, max_value=0.120, value=0.025, step=0.005)

        submit_soh = st.form_submit_button("⚡ Predict Current SOH %", use_container_width=True)

    if submit_soh and battery_artifact:
        pipe = battery_artifact["pipeline"]
        input_bat = pd.DataFrame([{
            "cycle_count": cycle_count,
            "battery_age_days": battery_age_days,
            "nominal_capacity_kwh": nominal_capacity,
            "chemistry_type": chemistry_type,
            "max_temp_celsius_recorded": max_temp,
            "internal_resistance_m_ohm": internal_resistance,
            "supplier_tier": supplier_tier,
            "supplier_rating": supplier_rating,
            "defect_rate_estimate": defect_rate
        }])

        pred_soh = float(pipe.predict(input_bat)[0])
        pred_soh = round(np.clip(pred_soh, 45.0, 99.5), 2)

        st.markdown("---")
        st.markdown("### 🎯 Predicted Battery Health Output")
        out1, out2 = st.columns([1, 2])
        with out1:
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pred_soh,
                number={'suffix': "%"},
                title=dict(text="Predicted SOH", font=dict(color="#F8FAFC", size=14)),
                gauge=dict(
                    axis=dict(range=[50, 100], tickcolor="#94A3B8"),
                    bar=dict(color=THEME_COLORS["teal"]),
                    bgcolor="#1E293B",
                    steps=[
                        dict(range=[50, 75], color="#991B1B"),
                        dict(range=[75, 85], color="#92400E"),
                        dict(range=[85, 100], color="#065F46")
                    ]
                )
            ))
            set_plotly_layout(fig_g, "Predicted State of Health", height=280)
            st.plotly_chart(fig_g, use_container_width=True)

        with out2:
            if pred_soh < 75.0:
                st.error(f"🚨 **BATTERY RETIREMENT RECOMMENDED (SOH: {pred_soh}%)**")
                st.markdown("""
                - Pack has breached the 75% End-of-Life operational threshold.
                - Severe impedance degradation causes sudden mid-route voltage collapse.
                - **Prescribed Action:** Schedule decommissioning and transition pack to secondary stationary ESS storage.
                """)
            elif pred_soh < 82.0:
                st.warning(f"⚠️ **ATTENTION REQUIRED (SOH: {pred_soh}%)**")
                st.markdown("Battery is experiencing accelerated cyclic aging. Restrict to short-haul inner city routes (< 5 km).")
            else:
                st.success(f"✅ **NOMINAL OPERATIONAL HEALTH (SOH: {pred_soh}%)**")
                st.markdown("Battery pack is in optimal condition with healthy thermal profile and low internal resistance.")

with tab2:
    st.markdown("### 📈 SOH Degradation vs Cycling & Thermal Stress")
    col_plot1, col_plot2 = st.columns(2)

    with col_plot1:
        fig_deg = px.scatter(
            batteries,
            x="cycle_count",
            y="current_soh_pct",
            color="chemistry_type",
            color_discrete_map={"LFP": THEME_COLORS["teal"], "NMC": THEME_COLORS["amber"]},
            opacity=0.6,
            labels={"cycle_count": "Cycle Count", "current_soh_pct": "Current SOH (%)"}
        )
        fig_deg.add_hline(y=75.0, line_dash="dash", line_color=THEME_COLORS["coral"], annotation_text="75% EOL Cutoff")
        set_plotly_layout(fig_deg, "SOH Degradation Trajectory (LFP vs NMC)", height=350)
        st.plotly_chart(fig_deg, use_container_width=True)

    with col_plot2:
        fig_temp = px.scatter(
            batteries,
            x="max_temp_celsius_recorded",
            y="internal_resistance_m_ohm",
            color="current_soh_pct",
            color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
            labels={"max_temp_celsius_recorded": "Peak Temp (°C)", "internal_resistance_m_ohm": "Internal Resistance (mΩ)"}
        )
        set_plotly_layout(fig_temp, "Thermal Stress vs Internal Cell Resistance", height=350)
        st.plotly_chart(fig_temp, use_container_width=True)

    st.markdown("### 🚨 Urgent Replacement Queue (SOH < 75% or Resistance > 40 mΩ)")
    urgent = batteries[(batteries["current_soh_pct"] < 75.0) | (batteries["internal_resistance_m_ohm"] > 40.0)].sort_values(
        by=["current_soh_pct", "internal_resistance_m_ohm"], ascending=[True, False]
    )
    st.dataframe(urgent[["battery_id", "supplier_id", "chemistry_type", "cycle_count", "current_soh_pct", "max_temp_celsius_recorded", "internal_resistance_m_ohm", "status"]].head(50), use_container_width=True)
