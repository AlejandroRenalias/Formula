"""Factor Breakdown component for Streamlit Pit Wall UI."""
import streamlit as st
import plotly.graph_objects as go
from typing import Dict
from src.core.models import StrategyDecision


def render_factor_breakdown(decision: StrategyDecision):
    """Renders horizontal bar chart of scoring sub-factors."""
    st.subheader("📊 Decision Factor Breakdown")

    factors: Dict[str, float] = decision.score_breakdown
    if not factors:
        st.info("No detailed factor breakdown available.")
        return

    # Clean factor labels
    labels = [f.replace("_", " ").title() for f in factors.keys()]
    values = list(factors.values())
    colors = ["#00FF66" if v >= 0 else "#FF3366" for v in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.1f}" for v in values],
            textposition="auto",
        )
    )

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#DDDDDD"),
        xaxis=dict(title="Factor Score Contribution", showgrid=True, gridcolor="#333344"),
        yaxis=dict(autorange="reversed"),
    )

    st.plotly_chart(fig, use_container_width=True)
