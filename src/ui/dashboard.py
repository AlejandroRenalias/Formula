"""Main Streamlit Dashboard application for F1 Pit Wall Strategy System (Presentation-Only)."""
import streamlit as st
import pandas as pd

from src.core.models import (
    TrackStatus,
    TireCompound,
    StrategyObjective,
    RiskProfile,
)
from src.adapters.scenarios import SCENARIOS, ScenarioConfig
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.orchestrator.pipeline import StrategyPipeline
from src.ui.components.decision_card import render_decision_card
from src.ui.components.factor_breakdown import render_factor_breakdown
from src.ui.components.specialist_cards import render_specialist_cards
from src.ui.components.telemetry_charts import render_telemetry_charts
from src.ui.components.llm_resolution import render_llm_resolution


def run_dashboard():
    st.set_page_config(
        page_title="Formula | AI Pit Wall Strategy",
        page_icon="🏎️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom styling
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        div[data-testid="stMetricValue"] { font-size: 1.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🏎️ F1 Pit Wall Strategy System")
    st.caption("Hybrid Deterministic & Multi-Agent Race Strategy Room")

    # 1. Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Race Configuration")
        scenario_key = st.selectbox(
            "Select Scenario",
            options=list(SCENARIOS.keys()),
            format_func=lambda k: SCENARIOS[k].title,
        )
        scenario: ScenarioConfig = SCENARIOS[scenario_key]

        driver = st.selectbox("Managed Driver", options=scenario.available_drivers, index=0)

        # Strategic Goals
        st.subheader("🎯 Strategic Objectives")
        objective = st.selectbox(
            "Team Objective",
            options=list(StrategyObjective),
            format_func=lambda o: o.value.replace("_", " ").title(),
            index=0,
        )
        risk_profile = st.selectbox(
            "Risk Profile",
            options=list(RiskProfile),
            format_func=lambda r: r.value.title(),
            index=1,
        )

        st.subheader("⏱️ Race Lap")
        lap = st.slider("Select Lap Number", min_value=2, max_value=scenario.total_laps, value=scenario.key_decision_laps[0] if scenario.key_decision_laps else 20)

        # Custom controls if in synthetic sandbox
        track_status = TrackStatus.GREEN
        is_raining = False
        rain_prob = 0.0
        rain_arrival = None
        stint_len = lap - 1
        is_sandbox = (scenario_key == "synthetic_sandbox")

        if is_sandbox:
            st.subheader("🧪 Sandbox Injectors")
            track_status = st.selectbox("Track Status", options=list(TrackStatus), index=0)
            custom_rain = st.checkbox("Simulate Imminent Rain Forecast", value=False)
            if custom_rain:
                rain_prob = st.slider("Rain Probability", 0.0, 1.0, 0.85)
                rain_arrival = st.slider("Rain Arrival (Laps)", 0, 5, 1)
            stint_len = st.slider("Current Tyre Stint Age (Laps)", 1, 40, 22)

        # Trigger analysis
        st.button("⚡ ANALYZE PIT WALL STRATEGY", type="primary", use_container_width=True)

    # 2. Build RaceState snapshot via Adapter
    if not is_sandbox:
        timeline_entry = scenario.forecast_timeline.get(lap, {})
        rain_prob = float(timeline_entry.get("rain_prob", 0.0))
        rain_arrival = timeline_entry.get("arrival_laps")
        rain_intensity = str(timeline_entry.get("intensity", "DRY"))
        is_raining = (rain_prob >= 0.95 and rain_arrival == 0)
    else:
        rain_intensity = "MODERATE" if rain_prob > 0.5 else "DRY"

    with st.spinner(f"Building Lap {lap} RaceState for {driver}..."):
        state = SyntheticRaceAdapter.create_race_state(
            current_lap=lap,
            total_laps=scenario.total_laps,
            subject_driver=driver,
            current_compound=TireCompound.MEDIUM if lap < 35 else TireCompound.HARD,
            stint_length_laps=stint_len,
            track_status=track_status,
            is_raining=is_raining,
            rain_probability=rain_prob,
            rain_arrival_laps=rain_arrival,
            rain_intensity=rain_intensity,
            objective=objective,
            risk_profile=risk_profile,
            is_sandbox_override=is_sandbox,
        )

    # 3. Execute Strategy Pipeline (All decisions calculated by domain engine)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)

    # 4. Render Top Metrics Strip with Provenance Badges
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Position", f"P{state.subject_driver.position}", f"{state.subject_driver.driver} ({state.subject_driver.team})")
    m2.metric("Tyre Compound", state.subject_driver.current_compound.value, f"{state.subject_driver.stint_length_laps} Laps Old")
    m3.metric("Track Status", state.track_status.value, f"Pit Loss: {state.pit_loss.current_pit_loss_s:.1f}s")
    
    track_temp_src = f"[{state.observed_weather.track_temp_c.source.value}]"
    m4.metric("Track Temp", f"{state.observed_weather.track_temp_c.value:.1f}°C", track_temp_src)
    
    forecast_src = f"[{state.weather_forecast.rain_probability.source.value}]"
    rain_txt = f"{rain_prob*100:.0f}% (in {rain_arrival}L)" if rain_arrival is not None else "0%"
    m5.metric("Rain Forecast", rain_txt, forecast_src)

    st.markdown("---")

    # 5. Top Primary Decision Card
    render_decision_card(decision)
    render_llm_resolution(decision)

    # 6. Factor Breakdown & Telemetry Charts
    c1, c2 = st.columns([1, 1])
    with c1:
        render_factor_breakdown(decision)
    with c2:
        render_telemetry_charts(state)

    st.markdown("---")

    # 7. Specialist Agent Cards
    render_specialist_cards(decision)

    # 8. Candidate Comparison Table (Presentation of precomputed all_candidates)
    with st.expander("📋 All Generated Strategic Candidates (Comparison Matrix)", expanded=False):
        cand_rows = []
        for cand in decision.all_candidates:
            cand_rows.append({
                "ID": cand.candidate_id,
                "Label": f"Candidate {cand.ui_label}",
                "Action": cand.pit_action.value,
                "Target Compound": cand.target_compound.value if cand.target_compound else "—",
                "Pace Mode": cand.pace_mode.value,
                "Intent": cand.intent.value,
                "Precomputed Strategy Score": f"{cand.candidate_strategy_score:+.2f}",
                "Selection": "✅ SELECTED" if cand.candidate_id == decision.selected_candidate.candidate_id else "—",
            })
        st.dataframe(pd.DataFrame(cand_rows), use_container_width=True)


if __name__ == "__main__":
    run_dashboard()
