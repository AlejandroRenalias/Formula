"""Unit tests for adapter layers and scenarios."""
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from src.adapters.scenarios import SCENARIOS
from src.adapters.fastf1_adapter import FastF1Adapter, FastF1AdapterError
from src.core.models import TrackStatus, TireCompound, StrategyObjective, RiskProfile
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.orchestrator.pipeline import StrategyPipeline


class _FakeSession:
    date = datetime(2024, 7, 7, 13, 0, tzinfo=timezone.utc)
    total_laps = 3

    def __init__(self):
        self.laps = pd.DataFrame([
            {"Driver": "NOR", "LapNumber": 1, "Time": timedelta(seconds=90), "LapTime": timedelta(seconds=90), "Compound": "MEDIUM", "TyreLife": 1, "Position": 2, "Team": "McLaren", "PitInTime": pd.NaT, "PitOutTime": pd.NaT, "TrackStatus": "1"},
            {"Driver": "NOR", "LapNumber": 2, "Time": timedelta(seconds=180), "LapTime": timedelta(seconds=90), "Compound": "MEDIUM", "TyreLife": 2, "Position": 2, "Team": "McLaren", "PitInTime": pd.NaT, "PitOutTime": pd.NaT, "TrackStatus": "1"},
            {"Driver": "NOR", "LapNumber": 3, "Time": timedelta(seconds=270), "LapTime": timedelta(seconds=90), "Compound": "SOFT", "TyreLife": 1, "Position": 1, "Team": "McLaren", "PitInTime": pd.NaT, "PitOutTime": pd.NaT, "TrackStatus": "1"},
            {"Driver": "VER", "LapNumber": 1, "Time": timedelta(seconds=88), "LapTime": timedelta(seconds=88), "Compound": "HARD", "TyreLife": 1, "Position": 1, "Team": "Red Bull", "PitInTime": pd.NaT, "PitOutTime": pd.NaT, "TrackStatus": "1"},
            {"Driver": "VER", "LapNumber": 2, "Time": timedelta(seconds=178), "LapTime": timedelta(seconds=90), "Compound": "HARD", "TyreLife": 2, "Position": 1, "Team": "Red Bull", "PitInTime": pd.NaT, "PitOutTime": pd.NaT, "TrackStatus": "1"},
            # This future row must not affect a lap-2 snapshot.
            {"Driver": "VER", "LapNumber": 3, "Time": timedelta(seconds=268), "LapTime": timedelta(seconds=90), "Compound": "SOFT", "TyreLife": 1, "Position": 10, "Team": "Red Bull", "PitInTime": timedelta(seconds=267), "PitOutTime": pd.NaT, "TrackStatus": "4"},
        ])
        self.weather_data = pd.DataFrame([
            {"Time": timedelta(seconds=180), "TrackTemp": 30, "AirTemp": 21, "Rainfall": False, "Humidity": 55},
            {"Time": timedelta(seconds=270), "TrackTemp": 99, "AirTemp": 99, "Rainfall": True, "Humidity": 99},
        ])


def test_fastf1_load_session_configures_cache_only_when_loading(monkeypatch):
    calls = []

    class _CacheDir:
        def mkdir(self, **kwargs):
            calls.append(("mkdir", kwargs))

        def __str__(self):
            return "offline-cache"

    class _Cache:
        @staticmethod
        def enable_cache(path):
            calls.append(("cache", path))

    class _FastF1:
        Cache = _Cache

        @staticmethod
        def get_session(*args):
            calls.append(("get", args))
            return type("LoadedSession", (), {"load": lambda self, **kwargs: calls.append(("load", kwargs))})()

    monkeypatch.setattr("src.adapters.fastf1_adapter.fastf1", _FastF1)
    monkeypatch.setattr("src.adapters.fastf1_adapter.CACHE_DIR", _CacheDir())
    FastF1Adapter.load_session(2024, "Test GP")
    assert calls == [
        ("mkdir", {"parents": True, "exist_ok": True}),
        ("cache", "offline-cache"),
        ("get", (2024, "Test GP", "R")),
        ("load", {"telemetry": False, "weather": True, "laps": True}),
    ]


def test_fastf1_load_session_wraps_acquisition_failures(monkeypatch):
    class _FastF1:
        class Cache:
            @staticmethod
            def enable_cache(path):
                pass

        @staticmethod
        def get_session(*args):
            raise OSError("network unavailable")

    monkeypatch.setattr("src.adapters.fastf1_adapter.fastf1", _FastF1)
    with pytest.raises(FastF1AdapterError, match="2024.*network unavailable"):
        FastF1Adapter.load_session(2024, "Test GP")


def test_fastf1_snapshot_uses_exact_completed_lap_and_historical_cutoff():
    state = FastF1Adapter.create_race_state_at_lap(_FakeSession(), 2, subject_driver="NOR")

    assert state.timestamp == datetime(2024, 7, 7, 13, 3, tzinfo=timezone.utc)
    assert state.knowledge_cutoff == state.timestamp
    assert [lap.lap_number for lap in state.lap_history] == [1, 2]
    assert state.subject_driver.position == 2
    assert state.observed_weather.track_temp_c.value == 30
    assert state.competitors[0].position == 1


def test_fastf1_stint_fallback_uses_pit_boundary_when_history_stint_is_missing():
    session = _FakeSession()
    subject_rows = session.laps[session.laps["Driver"] == "NOR"]
    session.laps["Stint"] = pd.NA
    session.laps["PitInTime"] = session.laps["PitInTime"].astype(object)
    session.laps.loc[subject_rows.index[1], "PitInTime"] = pd.Timedelta(seconds=179)
    session.laps.loc[subject_rows.index[1], "Stint"] = 2

    state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")

    assert state.lap_history[-1].is_pit_in_lap is True
    assert state.subject_driver.stint_length_laps == 2


def test_fastf1_snapshot_weather_ignores_future_observations():
    session = _FakeSession()
    state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")

    session.weather_data.loc[len(session.weather_data)] = {
        "Time": timedelta(seconds=181), "TrackTemp": 101, "AirTemp": 101,
        "Rainfall": True, "Humidity": 1,
    }
    future_state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")

    assert future_state.observed_weather == state.observed_weather


def test_fastf1_snapshot_track_status_ignores_future_status():
    session = _FakeSession()
    state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")
    session.laps.loc[session.laps["LapNumber"] == 3, "TrackStatus"] = "5"

    future_state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")

    assert state.track_status == TrackStatus.GREEN
    assert future_state.track_status == TrackStatus.GREEN


@pytest.mark.parametrize("track_status", ["245", "456", "267", "27", "12"])
def test_fastf1_snapshot_track_status_concatenated_codes_use_precedence(track_status):
    session = _FakeSession()
    session.laps.loc[
        (session.laps["Driver"] == "NOR") & (session.laps["LapNumber"] == 2),
        "TrackStatus",
    ] = track_status

    state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")

    expected = {
        "245": TrackStatus.RED_FLAG,
        "456": TrackStatus.RED_FLAG,
        "267": TrackStatus.VSC,
        "27": TrackStatus.VSC,
        "12": TrackStatus.YELLOW,
    }[track_status]
    assert state.track_status == expected


def test_fastf1_snapshot_handles_red_flag_status():
    session = _FakeSession()
    session.laps.loc[
        (session.laps["Driver"] == "NOR") & (session.laps["LapNumber"] == 2),
        "TrackStatus",
    ] = "5"

    state = FastF1Adapter.create_race_state_at_lap(session, 2, subject_driver="NOR")

    assert state.track_status == TrackStatus.RED_FLAG
    assert state.lap_history[-1].track_status == TrackStatus.RED_FLAG


def test_fastf1_snapshot_requires_exact_completed_lap():
    with pytest.raises(ValueError, match="No completed lap 4"):
        FastF1Adapter.create_race_state_at_lap(_FakeSession(), 4, subject_driver="NOR")

    with pytest.raises(ValueError, match="Driver 'HAM' not found"):
        FastF1Adapter.create_race_state_at_lap(_FakeSession(), 2, subject_driver="HAM")


def test_scenarios_catalog():
    """Verify scenario catalog configuration."""
    assert "silverstone_2024" in SCENARIOS
    assert "synthetic_sandbox" in SCENARIOS

    silverstone = SCENARIOS["silverstone_2024"]
    assert silverstone.total_laps == 52
    assert "NOR" in silverstone.available_drivers
    assert 18 in silverstone.forecast_timeline
    assert silverstone.forecast_timeline[18]["rain_prob"] == 0.70


def test_scenario_execution_across_laps():
    """Verify strategy pipeline runs properly across different race laps."""
    pipeline = StrategyPipeline()

    # Lap 15 (Dry, rain far away) -> Stay out
    state_l15 = SyntheticRaceAdapter.create_race_state(
        current_lap=15,
        stint_length_laps=14,
        rain_probability=0.20,
        rain_arrival_laps=5,
    )
    decision_l15 = pipeline.run_strategy_cycle(state_l15)
    assert decision_l15.selected_candidate is not None

    # Lap 19 (Rain imminent in 1 lap) -> Box for Inters
    state_l19 = SyntheticRaceAdapter.create_race_state(
        current_lap=19,
        stint_length_laps=18,
        rain_probability=0.90,
        rain_arrival_laps=1,
    )
    decision_l19 = pipeline.run_strategy_cycle(state_l19)
    assert decision_l19.selected_candidate.target_compound == TireCompound.INTERMEDIATE
