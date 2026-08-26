"""Presentation-only component for optional LLM Chief resolution metadata."""
import streamlit as st

from src.core.models import StrategyDecision


def render_llm_resolution(decision: StrategyDecision) -> None:
    """Render the LLM Chief result without recalculating or selecting strategy."""
    resolution = decision.llm_chief_resolution
    if resolution is None:
        return

    deterministic_id = decision.selected_candidate.candidate_id
    outcome = "CONFIRMED" if not resolution.overridden else "OVERRIDDEN"
    st.subheader("🧠 LLM Chief Resolution")
    st.write(f"Deterministic recommendation: `{deterministic_id}`")
    st.write(f"LLM Chief outcome: **{outcome}** — `{resolution.confirmed_candidate_id}`")
    if resolution.overridden and resolution.override_reason:
        st.write(f"Override reason: {resolution.override_reason}")
    st.write(f"Chief rationale: {resolution.strategic_rationale}")
    if resolution.cited_evidence_ids:
        st.caption("Cited evidence: " + ", ".join(resolution.cited_evidence_ids))
