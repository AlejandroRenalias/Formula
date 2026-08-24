"""Specialist Agent Cards component for Streamlit Pit Wall UI."""
import streamlit as st
from src.core.models import StrategyDecision


def render_specialist_cards(decision: StrategyDecision):
    """Renders side-by-side cards for each specialist agent."""
    st.subheader("👥 Specialist Agent Assessments")

    cols = st.columns(len(decision.specialist_evaluations))

    icons = {
        "Pace & Tyre Specialist": "🏎️",
        "Weather Specialist": "🌧️",
        "Race Control Specialist": "🚩",
    }

    for col, report in zip(cols, decision.specialist_evaluations):
        icon = icons.get(report.agent_name, "👤")
        with col:
            st.markdown(
                f"""
                <div style="background: #181824; border: 1px solid #2E2E3E; border-radius: 8px; padding: 15px; height: 100%;">
                    <div style="font-size: 1.1em; font-weight: 700; color: #FFFFFF;">
                        {icon} {report.agent_name}
                    </div>
                    <div style="font-size: 0.85em; color: #8888AA; margin-bottom: 8px;">
                        {report.role}
                    </div>
                    <div style="background: #252538; padding: 6px 10px; border-radius: 5px; margin: 8px 0;">
                        <strong>Preferred:</strong> <span style="color: #00FF66;">Candidate {report.recommended_candidate_id}</span>
                        <span style="float: right; color: #FFAA00;">Conf: {report.confidence.value}</span>
                    </div>
                    <div style="font-size: 0.9em; color: #CCCCCC; line-height: 1.4; margin-top: 8px;">
                        {report.rationale}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
