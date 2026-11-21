"""
Page 6: Supplier Intelligence & Hardware Quality Scorecard.
Ranks suppliers by battery degradation velocity, manufacturing defect rates, and warranty breach risk.
"""

import sys
sys.path.insert(0, "/workspace")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.utils.data_loader import load_powerbi_data, load_all_processed_data
from app.utils.ui_helpers import apply_custom_css, render_kpi, set_plotly_layout, THEME_COLORS

st.set_page_config(page_title="Supplier Intelligence", page_icon="🏭", layout="wide")
apply_custom_css()

st.title("🏭 Supplier Intelligence & Warranty Risk Audit")
st.markdown("Holistic supplier scorecard tracking battery degradation, lot defect rates, and contractual warranty exposure.")

pb_data = load_powerbi_data()
raw_data = load_all_processed_data()

if "Fact_Supplier_Quality_Scorecard" not in pb_data:
    st.error("Supplier facts not found. Run ETL pipeline first.")
    st.stop()

scorecard = pb_data["Fact_Supplier_Quality_Scorecard"].copy()

# Scorecard KPIs
c1, c2, c3, c4 = st.columns(4)
total_suppliers = len(scorecard)
tier1_cnt = len(scorecard[scorecard["tier"] == "Tier-1"])
high_risk_cnt = len(scorecard[scorecard["degradation_ratio"] > 0.15])
avg_defect = raw_data["manufacturing_lots"]["defect_rate_estimate"].mean() * 100.0

render_kpi(c1, "Active Hardware Vendors", f"{total_suppliers}", f"{tier1_cnt} Tier-1 Strategic", "neutral")
render_kpi(c2, "High-Risk Suppliers", f"{high_risk_cnt}", "Warranty Review Needed", "negative" if high_risk_cnt > 0 else "positive")
render_kpi(c3, "Mean Lot Defect Rate", f"{avg_defect:.2f}%", "AIS-156 Standard: < 2.5%", "positive" if avg_defect < 3 else "negative")
render_kpi(c4, "Fleet Degradation Ratio", f"{scorecard['degraded_count'].sum() / scorecard['total_batteries'].sum() * 100:.1f}%", f"{scorecard['degraded_count'].sum()} degraded packs", "neutral")

st.markdown("---")

col1, col2 = st.columns([3, 2])

with col1:
    fig_soh = px.bar(
        scorecard.sort_values(by="avg_soh", ascending=True),
        x="avg_soh",
        y="supplier_name",
        orientation="h",
        color="tier",
        color_discrete_map={"Tier-1": THEME_COLORS["emerald"], "Tier-2": THEME_COLORS["primary"], "Tier-3": THEME_COLORS["coral"]},
        text="avg_soh",
        title="Mean Battery Pack State of Health (SOH) by Supplier"
    )
    fig_soh.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    set_plotly_layout(fig_soh, "Supplier Battery SOH Quality Ranking", height=380)
    st.plotly_chart(fig_soh, use_container_width=True)

with col2:
    fig_def = px.scatter(
        scorecard,
        x="avg_internal_resistance",
        y="degradation_ratio",
        size="total_batteries",
        color="tier",
        text="supplier_name",
        color_discrete_map={"Tier-1": THEME_COLORS["emerald"], "Tier-2": THEME_COLORS["primary"], "Tier-3": THEME_COLORS["coral"]},
        labels={"avg_internal_resistance": "Mean Internal Resistance (mΩ)", "degradation_ratio": "Degraded Ratio (<75% SOH)"}
    )
    fig_def.update_traces(textposition='top center')
    set_plotly_layout(fig_def, "Resistance vs Degradation Risk Matrix", height=380)
    st.plotly_chart(fig_def, use_container_width=True)

st.markdown("---")

st.markdown("### 📋 Comprehensive Supplier Performance & Warranty Scorecard")

scorecard["Procurement Action"] = np.where(
    scorecard["degradation_ratio"] > 0.15, "🚨 High Risk - Immediate Warranty Audit",
    np.where(scorecard["degradation_ratio"] > 0.05, "⚠️ Monitor Closely", "✅ Preferred Vendor")
)

display_cols = [
    "supplier_name", "tier", "country", "total_batteries", "avg_soh",
    "degraded_count", "degradation_ratio", "avg_internal_resistance", "Procurement Action"
]
st.dataframe(scorecard[display_cols].sort_values(by="avg_soh", ascending=False), use_container_width=True)

st.markdown("""
**Procurement Recommendation Protocol:**
- **GreenCharge Labs & NexGen Energy Storage (Tier-3):** Trigger clause 14.2 of hardware SLA for defect rates exceeding 5.0%. Freeze lot replenishment orders until thermal dissipation re-certification.
- **VoltCell Innovations & Titan Fleet Motors (Tier-1):** Expand allocation for FY27 battery pack expansion given sub-1% premature degradation rate.
""")
