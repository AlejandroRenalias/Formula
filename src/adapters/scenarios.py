"""Preconfigured race scenarios and forecast timelines."""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class TrackScenarioConfig(BaseModel):
    track_id: str = "silverstone"
    reference_race_lap_time_s: Optional[float] = None
    leader_distance_m: Optional[float] = None
    leader_before_pit_entry_m: float = 25.0
    rain_first_sector: int = 2
    team_colours: Dict[str, str] = {"McLaren": "#FF8000", "Red Bull": "#3671C6", "Mercedes": "#27F4D2"}


class ScenarioConfig(BaseModel):
    scenario_id: str
    title: str
    year: int
    grand_prix: str
    default_driver: str
    available_drivers: List[str]
    total_laps: int
    key_decision_laps: List[int]
    description: str
    forecast_timeline: Dict[int, Dict[str, Any]] = {}
    track: Optional[TrackScenarioConfig] = None


SYNTHETIC_LAP18_SCENARIO = ScenarioConfig(
        scenario_id="synthetic_lap18", title="Synthetic Silverstone cutoff", year=2024,
        grand_prix="Synthetic scenario", default_driver="NOR", available_drivers=["NOR", "VER", "HAM"],
        total_laps=52, key_decision_laps=[18], description="Projection fixture; fictional gaps and weather.",
        track=TrackScenarioConfig(),
        forecast_timeline={18: {"rain_prob": .70, "arrival_laps": 4, "intensity": "LIGHT"}},
    )


SCENARIOS: Dict[str, ScenarioConfig] = {
    "silverstone_2024": ScenarioConfig(
        scenario_id="silverstone_2024",
        title="🇬🇧 British GP 2024 (Silverstone Rain Chaos)",
        year=2024,
        grand_prix="British Grand Prix",
        default_driver="NOR",
        available_drivers=["NOR", "HAM", "VER", "PIA", "RUS"],
        total_laps=52,
        key_decision_laps=[15, 18, 20, 27, 34, 38, 40],
        description="Rain approaches the circuit around lap 18-20. The pit wall must time the crossover from slicks to Intermediates.",
        forecast_timeline={
            15: {"rain_prob": 0.20, "arrival_laps": 5, "intensity": "LIGHT"},
            18: {"rain_prob": 0.70, "arrival_laps": 2, "intensity": "LIGHT"},
            19: {"rain_prob": 0.90, "arrival_laps": 1, "intensity": "MODERATE"},
            20: {"rain_prob": 1.00, "arrival_laps": 0, "intensity": "MODERATE"},
            38: {"rain_prob": 0.05, "arrival_laps": None, "intensity": "DRY"},
        },
    ),
    "synthetic_sandbox": ScenarioConfig(
        scenario_id="synthetic_sandbox",
        title="🧪 Synthetic Grand Prix (Interactive Sandbox)",
        year=2024,
        grand_prix="Sandbox GP",
        default_driver="NOR",
        available_drivers=["NOR", "VER", "HAM", "LEC", "PIA"],
        total_laps=57,
        key_decision_laps=[10, 20, 25, 30, 40, 50],
        description="A sandbox scenario where you can test any custom race condition, VSC, Safety Car, or sudden rainstorm.",
        forecast_timeline={},
    ),
}
