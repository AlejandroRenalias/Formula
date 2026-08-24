"""Telemetry charts and telemetry gauges for Streamlit Pit Wall UI."""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from src.core.models import RaceState


def render_telemetry_charts(state: RaceState):
    """Renders lap time history, pace regression, and competitor gaps."""
    st.subheader("📈 Telemetry & Track Insights")

    col1, col2 = st.columns(2)

    with col1:
        # Lap time trace with clean vs unusable laps
        laps = state.lap_history
        if laps:
            lap_nums = [l.lap_number for l in laps]
            lap_times = [l.lap_time_s for l in laps]
            clean_flags = [l.usable_for_pace_model for l in laps]

            fig_lap = go.Figure()
            # Clean laps
            clean_nums = [n for n, c in zip(lap_nums, clean_flags) if c]
            clean_times = [t for t, c in zip(lap_times, clean_flags) if c]
            fig_lap.add_trace(
                go.Scatter(
                    x=clean_nums,
                    y=clean_times,
                    mode="lines+markers",
                    name="Clean Lap Time",
                    line=dict(color="#00D2BE", width=2),
                    marker=dict(size=6),
                )
            )

            # Unusable / caution laps
            unclean_nums = [n for n, c in zip(lap_nums, clean_flags) if not c]
            unclean_times = [t for t, c in zip(lap_times, clean_flags) if not c]
            if unclean_nums:
                fig_lap.add_trace(
                    go.Scatter(
                        x=unclean_nums,
                        y=unclean_times,
                        mode="markers",
                        name="SC/VSC/Pit (Excluded)",
                        marker=dict(color="#FF3366", size=8, symbol="x"),
                    )
                )

            fig_lap.update_layout(
                title="Driver Lap Pace Evolution",
                xaxis_title="Lap Number",
                yaxis_title="Lap Time (s)",
                height=260,
                margin=dict(l=10, r=10, t=35, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#DDDDDD"),
                xaxis=dict(showgrid=True, gridcolor="#333344"),
                yaxis=dict(showgrid=True, gridcolor="#333344"),
            )
            st.plotly_chart(fig_lap, use_container_width=True)

    with col2:
        # Competitor Gap Landscape
        comps = state.competitors[:6]
        if comps:
            drivers = [c.driver for c in comps]
            gaps = [c.gap_to_subject_s for c in comps]
            colors = ["#00FF66" if g > 0 else "#FFAA00" for g in gaps]

            fig_gap = go.Figure(
                go.Bar(
                    x=gaps,
                    y=drivers,
                    orientation="h",
                    marker_color=colors,
                    text=[f"{g:+.1f}s" for g in gaps],
                    textposition="auto",
                )
            )

            # Add pit loss line
            fig_gap.add_vline(
                x=-state.pit_loss.current_pit_loss_s,
                line_dash="dash",
                line_color="#FF3366",
                annotation_text=f"Pit Window ({state.pit_loss.current_pit_loss_s:.1f}s)",
                annotation_position="top left",
            )

            fig_gap.update_layout(
                title=f"Gap to Rivals (Rejoin P{state.pit_loss.expected_rejoin_position})",
                xaxis_title="Gap to Subject (s) [Positive = Ahead, Negative = Behind]",
                height=260,
                margin=dict(l=10, r=10, t=35, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#DDDDDD"),
                xaxis=dict(showgrid=True, gridcolor="#333344"),
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_gap, use_container_width=True)
