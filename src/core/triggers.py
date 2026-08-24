"""Decision trigger evaluation engine."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from src.core.models import RaceState, TrackStatus


class DecisionTriggerType(str, Enum):
    HEARTBEAT = "HEARTBEAT"
    RIVAL_PITTED = "RIVAL_PITTED"
    VSC_DEPLOYED = "VSC_DEPLOYED"
    SC_DEPLOYED = "SC_DEPLOYED"
    WEATHER_CHANGED = "WEATHER_CHANGED"
    DEGRADATION_THRESHOLD = "DEGRADATION_THRESHOLD"
    PIT_WINDOW_OPENED = "PIT_WINDOW_OPENED"


class TriggerEvent(BaseModel):
    trigger_type: DecisionTriggerType
    description: str
    urgency: str = "NORMAL"  # LOW, NORMAL, HIGH, IMMEDIATE


class TriggerEvaluator:
    """Evaluates whether the race conditions require an active strategy meeting."""

    @staticmethod
    def evaluate_triggers(
        current_state: RaceState,
        previous_state: Optional[RaceState] = None,
        heartbeat_interval: int = 5,
    ) -> List[TriggerEvent]:
        triggers: List[TriggerEvent] = []

        # 1. Safety Car / VSC Deployed
        if current_state.track_status in (TrackStatus.SAFETY_CAR, TrackStatus.VSC):
            if not previous_state or previous_state.track_status != current_state.track_status:
                triggers.append(
                    TriggerEvent(
                        trigger_type=(
                            DecisionTriggerType.SC_DEPLOYED
                            if current_state.track_status == TrackStatus.SAFETY_CAR
                            else DecisionTriggerType.VSC_DEPLOYED
                        ),
                        description=f"{current_state.track_status.value} deployed! Pit loss reduced to {current_state.pit_loss.current_pit_loss_s:.1f}s.",
                        urgency="IMMEDIATE",
                    )
                )

        # 2. Rain / Weather Forecast change
        rain_prob = current_state.weather_forecast.rain_probability.value
        arrival = current_state.weather_forecast.expected_arrival_laps.value
        if rain_prob >= 0.50 and arrival is not None and arrival <= 3:
            triggers.append(
                TriggerEvent(
                    trigger_type=DecisionTriggerType.WEATHER_CHANGED,
                    description=f"Rain expected in {arrival} laps ({rain_prob*100:.0f}% probability).",
                    urgency="HIGH",
                )
            )

        # 3. Competitor pit stops
        if previous_state:
            prev_competitors = {c.driver: c for c in previous_state.competitors}
            for comp in current_state.competitors:
                prev_comp = prev_competitors.get(comp.driver)
                if prev_comp and not prev_comp.is_in_pit and comp.is_in_pit:
                    triggers.append(
                        TriggerEvent(
                            trigger_type=DecisionTriggerType.RIVAL_PITTED,
                            description=f"Direct rival {comp.driver} pitted from P{comp.position}.",
                            urgency="HIGH",
                        )
                    )

        # 4. Degradation threshold
        deg_rate = current_state.derived_pace.degradation_rate_s_per_lap.value
        if deg_rate > 0.20:
            triggers.append(
                TriggerEvent(
                    trigger_type=DecisionTriggerType.DEGRADATION_THRESHOLD,
                    description=f"High degradation detected: {deg_rate:.2f} s/lap drop.",
                    urgency="NORMAL",
                )
            )

        # 5. Periodic Heartbeat
        if current_state.current_lap % heartbeat_interval == 0:
            triggers.append(
                TriggerEvent(
                    trigger_type=DecisionTriggerType.HEARTBEAT,
                    description=f"Routine lap {current_state.current_lap} heartbeat check.",
                    urgency="LOW",
                )
            )

        return triggers
