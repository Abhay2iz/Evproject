"""
UI Helpers and custom styling for EV Fleet Intelligence Streamlit dashboard.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Theme Colors (High contrast solid scheme - strictly no purple gradients)
THEME_COLORS = {
    "bg_dark": "#0B1120",
    "card_bg": "#1E293B",
    "border": "#334155",
    "text_primary": "#F8FAFC",
    "text_muted": "#94A3B8",
    "primary": "#0284C7",   # Deep Ocean Blue
    "teal": "#0D9488",      # Rich Teal
    "emerald": "#10B981",   # Green Success
    "amber": "#F59E0B",     # Amber Warning
    "coral": "#EF4444"      # Crimson Danger
}

def apply_custom_css():
    """Injects custom high-contrast CSS styling."""
    st.markdown("""
        <style>
        /* General page layout */
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.5rem;
            max-width: 96%;
        }
        
        /* Metric Card styling */
        .kpi-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 18px 20px;
            margin-bottom: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .kpi-title {
            color: #94A3B8;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .kpi-value {
            color: #F8FAFC;
            font-size: 1.85rem;
            font-weight: 700;
            line-height: 1.2;
        }
        .kpi-delta {
            font-size: 0.82rem;
            font-weight: 600;
            margin-top: 6px;
        }
        .delta-pos { color: #10B981; }
        .delta-neg { color: #EF4444; }
        .delta-neutral { color: #0284C7; }

        /* Badge Pills */
        .badge-healthy {
            background-color: #065F46;
            color: #A7F3D0;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-warning {
            background-color: #92400E;
            color: #FDE68A;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .badge-danger {
            background-color: #991B1B;
            color: #FECACA;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

def render_kpi(col, title, value, delta=None, delta_direction="positive"):
    """Renders a styled KPI card into a Streamlit column."""
    delta_html = ""
    if delta:
        delta_class = "delta-pos" if delta_direction == "positive" else ("delta-neg" if delta_direction == "negative" else "delta-neutral")
        icon = "▲" if delta_direction == "positive" else ("▼" if delta_direction == "negative" else "●")
        delta_html = f'<div class="kpi-delta {delta_class}">{icon} {delta}</div>'

    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    col.markdown(html, unsafe_allow_html=True)

def set_plotly_layout(fig, title="", height=400):
    """Applies high-contrast dark palette layout to Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#F8FAFC", family="Arial")),
        paper_bgcolor="#1E293B",
        plot_bgcolor="#1E293B",
        font=dict(color="#94A3B8", size=11),
        height=height,
        margin=dict(l=40, r=30, t=50, b=40),
        xaxis=dict(
            gridcolor="#334155",
            zerolinecolor="#334155",
            showline=True,
            linecolor="#334155"
        ),
        yaxis=dict(
            gridcolor="#334155",
            zerolinecolor="#334155",
            showline=True,
            linecolor="#334155"
        ),
        legend=dict(
            font=dict(color="#F8FAFC"),
            bgcolor="rgba(30, 41, 59, 0.8)",
            bordercolor="#334155",
            borderwidth=1
        )
    )
    return fig
