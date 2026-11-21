"""
Page 5: Delivery Analytics & Pre-Dispatch Failure Risk Prediction.
Root cause breakdowns, hourly peak vulnerability, and live failure prediction form.
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

st.set_page_config(page_title="Delivery Analytics", page_icon="📦", layout="wide")
apply_custom_css()

st.title("📦 Delivery Analytics & Pre-Dispatch Risk Engine")
st.markdown("Analyze delivery success rates, bottleneck root causes, and predict order failure risk prior to dispatch.")

data = load_all_processed_data()
models = load_model_artifacts()

if "deliveries" not in data or len(data["deliveries"]) == 0:
    st.error("Delivery records not found. Please run ETL first.")
    st.stop()

deliveries = data["deliveries"]
delivery_artifact = models.get("delivery_model")

# High-level KPIs
c1, c2, c3, c4 = st.columns(4)
total_deliv = len(deliveries)
completed = len(deliveries[deliveries["delivery_status"] == "COMPLETED"])
failed = total_deliv - completed
fail_rate = (failed / total_deliv) * 100.0 if total_deliv > 0 else 0
avg_time = deliveries["actual_duration_min"].dropna().mean()
ontime_rate = (deliveries["is_ontime"].sum() / total_deliv) * 100.0 if "is_ontime" in deliveries else 0

render_kpi(c1, "Total Order Volume", f"{total_deliv:,}", "Last 12 Months", "neutral")
render_kpi(c2, "Overall Failure Rate", f"{fail_rate:.2f}%", f"{failed:,} Failed Orders", "negative" if fail_rate > 5 else "positive")
render_kpi(c3, "On-Time SLA Rate", f"{ontime_rate:.1f}%", "Target >= 90%", "positive" if ontime_rate >= 90 else "negative")
render_kpi(c4, "Average Delivery Time", f"{avg_time:.1f} min", "Promised: ~30 min", "neutral")

st.markdown("---")

tab1, tab2 = st.tabs(["⚡ Pre-Dispatch Failure Predictor", "📊 Operational Bottlenecks & Root Causes"])

with tab1:
    st.markdown("### 🎛️ Pre-Dispatch Order Risk Scoring Form")
    st.markdown("Input pre-delivery parameters (trip distance, vehicle battery status, ambient temperature, timing) to evaluate order failure probability.")

    with st.form("delivery_risk_form"):
        d1, d2, d3 = st.columns(3)
        with d1:
            distance_km = st.slider("Delivery Route Distance (km)", min_value=1.0, max_value=35.0, value=7.5, step=0.5)
            promised_min = st.number_input("Promised Delivery Duration (min)", min_value=10, max_value=120, value=35, step=5)
            order_val = st.number_input("Order Value ($)", min_value=5.0, max_value=300.0, value=45.0, step=5.0)
            city = st.selectbox("Dispatch Hub City", options=["Bangalore", "Delhi-NCR", "Hyderabad", "Mumbai", "Pune"], index=0)
        with d2:
            start_soc = st.slider("Vehicle Starting Battery SOC (%)", min_value=5.0, max_value=100.0, value=65.0, step=1.0)
            current_soh = st.slider("Battery State of Health (%)", min_value=60.0, max_value=100.0, value=88.0, step=1.0)
            internal_res = st.slider("Battery Internal Resistance (mΩ)", min_value=18.0, max_value=55.0, value=25.0, step=0.5)
            chem_type = st.selectbox("Battery Chemistry", options=["LFP", "NMC"], index=0)
        with d3:
            hour_of_day = st.slider("Dispatch Hour of Day (0-23)", min_value=8, max_value=22, value=19)
            day_of_week = st.selectbox("Day of Week", options=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday"), (5, "Saturday"), (6, "Sunday")], format_func=lambda x: x[1])
            ambient_temp = st.slider("Ambient Temperature (°C)", min_value=15.0, max_value=48.0, value=34.0, step=0.5)

        submit_risk = st.form_submit_button("⚡ Score Pre-Dispatch Failure Risk", use_container_width=True)

    if submit_risk and delivery_artifact:
        pipe = delivery_artifact["pipeline"]
        is_weekend = 1 if day_of_week[0] >= 5 else 0
        is_peak = 1 if hour_of_day in [12, 13, 14, 19, 20, 21] else 0

        input_df = pd.DataFrame([{
            "distance_km": distance_km,
            "promised_duration_min": promised_min,
            "order_value": order_val,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week[0],
            "is_weekend": is_weekend,
            "is_peak_hour": is_peak,
            "start_soc_pct": start_soc,
            "ambient_temp_c": ambient_temp,
            "current_soh_pct": current_soh,
            "internal_resistance_m_ohm": internal_res,
            "chemistry_type": chem_type,
            "city": city
        }])

        prob_fail = pipe.predict_proba(input_df)[0, 1]

        st.markdown("---")
        st.markdown("### 🎯 Predicted Order Risk Output")
        res1, res2 = st.columns([1, 2])
        with res1:
            fig_fail_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=prob_fail * 100.0,
                number={'suffix': "%"},
                title=dict(text="Failure Probability", font=dict(color="#F8FAFC", size=14)),
                gauge=dict(
                    axis=dict(range=[0, 30], tickcolor="#94A3B8"),
                    bar=dict(color=THEME_COLORS["coral"] if prob_fail > 0.08 else THEME_COLORS["teal"]),
                    bgcolor="#1E293B",
                    steps=[
                        dict(range=[0, 5], color="#065F46"),
                        dict(range=[5, 12], color="#92400E"),
                        dict(range=[12, 30], color="#991B1B")
                    ]
                )
            ))
            set_plotly_layout(fig_fail_g, "Pre-Dispatch Risk Score", height=280)
            st.plotly_chart(fig_fail_g, use_container_width=True)

        with res2:
            if prob_fail >= 0.12 or start_soc < 18.0:
                st.error(f"🚨 **HIGH FAILURE RISK ({prob_fail*100:.1f}%)**")
                st.markdown("""
                **Root Risk Factors:**
                - Low battery SOC relative to route distance introduces severe mid-route depletion hazard.
                - Peak congestion window coupled with elevated ambient temperature stresses thermal throttling.
                - **Dispatch Safeguard Action:** Re-route assignment to an EV with SOC >= 50% or execute a mandatory 2-minute battery swap prior to order pickup.
                """)
            elif prob_fail >= 0.06:
                st.warning(f"⚠️ **ELEVATED VULNERABILITY ({prob_fail*100:.1f}%)**")
                st.markdown("Order requires proactive rider notification to monitor remaining range.")
            else:
                st.success(f"✅ **SAFE DISPATCH VERIFIED ({prob_fail*100:.1f}%)**")
                st.markdown("Battery buffer is ample for distance. Delivery has high confidence of timely completion.")

with tab2:
    st.markdown("### 📊 Failure Root Cause Distribution & Peak Hour Dynamics")
    p1, p2 = st.columns(2)

    with p1:
        failed_records = deliveries[deliveries["delivery_status"] != "COMPLETED"]
        fail_reasons = failed_records["failure_reason"].fillna("Other").value_counts().reset_index()
        fail_reasons.columns = ["reason", "count"]

        fig_reasons = px.bar(
            fail_reasons,
            x="count",
            y="reason",
            orientation="h",
            color="count",
            color_continuous_scale=["#F59E0B", "#EF4444"],
            title="Delivery Failure Breakdown by Cause"
        )
        set_plotly_layout(fig_reasons, "Primary Failure Drivers", height=350)
        st.plotly_chart(fig_reasons, use_container_width=True)

    with p2:
        deliveries["hour"] = pd.to_datetime(deliveries["start_time"]).dt.hour
        hourly_perf = deliveries.groupby("hour").agg(
            Volume=("delivery_id", "count"),
            Failures=("is_failed", "sum")
        ).reset_index()
        hourly_perf["FailPct"] = (hourly_perf["Failures"] / hourly_perf["Volume"]) * 100.0

        fig_hour = go.Figure()
        fig_hour.add_trace(go.Bar(x=hourly_perf["hour"], y=hourly_perf["Volume"], name="Volume", marker_color="#334155"))
        fig_hour.add_trace(go.Scatter(x=hourly_perf["hour"], y=hourly_perf["FailPct"], name="Failure Rate (%)", yaxis="y2", marker_color=THEME_COLORS["coral"], line=dict(width=2)))
        fig_hour.update_layout(
            yaxis2=dict(title="Failure Rate (%)", overlaying="y", side="right", showgrid=False, font=dict(color=THEME_COLORS["coral"]))
        )
        set_plotly_layout(fig_hour, "Hourly Order Dispatch vs Failure Spike", height=350)
        st.plotly_chart(fig_hour, use_container_width=True)
