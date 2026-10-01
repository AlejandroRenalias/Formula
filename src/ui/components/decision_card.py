"""Top Decision Banner component for Streamlit Pit Wall UI."""
import streamlit as st
from src.core.models import StrategyDecision, PitAction, ConfidenceLevel


def render_decision_card(decision: StrategyDecision):
    """Renders the primary top decision banner."""
    cand = decision.selected_candidate
    is_box = decision.pit_action == PitAction.BOX_NOW

    # Banner Styling based on action
    banner_color = "#E10600" if is_box else "#00D2BE"  # F1 Red for Box, Turquoise for Stay Out
    bg_gradient = "linear-gradient(135deg, #1E1E2E 0%, #2A2A3E 100%)"

    conf_color = "#00FF66" if decision.confidence == ConfidenceLevel.HIGH else (
        "#FFCC00" if decision.confidence == ConfidenceLevel.MEDIUM else "#FF3366"
    )

    st.markdown(
        f"""
        <div style="background: {bg_gradient}; border-left: 8px solid {banner_color}; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 0.9em; text-transform: uppercase; letter-spacing: 2px; color: #8888AA;">LAP {decision.lap} FINAL PIT WALL CALL</span>
                    <h1 style="margin: 5px 0; color: white; font-size: 2.2em; font-weight: 800;">
                        {'🛑 ' + decision.pit_action.value if is_box else '🟢 ' + decision.pit_action.value}
                        <span style="font-size: 0.6em; color: {banner_color}; padding-left: 10px;">
                            {'→ ' + decision.target_compound.value if decision.target_compound else f'({decision.pace_mode.value})'}
                        </span>
                    </h1>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.4em; font-weight: 700; color: white;">
                        Score Delta: <span style="color: #00FF66;">+{decision.score_margin:.1f} pts</span>
                    </div>
                    <div style="margin-top: 5px;">
                        Confidence: <span style="color: {conf_color}; font-weight: 700;">{decision.confidence.value}</span>
                    </div>
                </div>
            </div>
            <div style="margin-top: 15px; color: #DDDDFF; font-size: 1.05em; line-height: 1.5; border-top: 1px solid #3A3A4E; padding-top: 12px;">
                <strong>Strategic Rationale:</strong> {decision.rationale}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Next Triggers section
    if decision.next_triggers:
        with st.expander("⏱️ Next Strategy Review Triggers", expanded=False):
            for t in decision.next_triggers:
                st.markdown(f"- **{t.trigger_type}**: {t.condition_description}")
