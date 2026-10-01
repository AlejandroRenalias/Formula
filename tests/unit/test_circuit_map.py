import copy
import json

import pytest

from src.adapters.scenarios import SYNTHETIC_LAP18_SCENARIO, TrackScenarioConfig
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.calculators.circuit_map import CircuitMap, TRACK_FILE, build_cutoff_track


@pytest.fixture
def track():
    # Two halves cover equal distance but take 20 s / 80 s: speed matters.
    return CircuitMap({"lap_length_m": 1000, "reference_lap_time_s": 100,
                       "time_profile": [{"distance_m": 0, "time_s": 0},
                                        {"distance_m": 500, "time_s": 20},
                                        {"distance_m": 1000, "time_s": 100}],
                       "polyline": [{"distance_m": 0, "x": 0, "y": 0},
                                    {"distance_m": 500, "x": 1, "y": 1},
                                    {"distance_m": 1000, "x": 0, "y": 0}]})


def test_gap_positions_are_monotonic_even_across_multiple_laps(track):
    distances = [track.position(900, gap)["unwrapped_distance_m"] for gap in (0, 1, 20, 80, 100, 120, 220)]
    assert all(b < a for a, b in zip(distances, distances[1:]))


def test_zero_gap_matches_leader_and_profile_accounts_for_speed(track):
    assert track.position(900, 0)["distance_m"] == pytest.approx(900)
    assert track.position(500, 10)["distance_m"] == pytest.approx(250)
    assert track.position(900, 10)["distance_m"] == pytest.approx(837.5)


def test_full_lap_wrap_preserves_gap_and_unwrapped_distance(track):
    first, wrapped = track.position(900, 3.5), track.position(900, 203.5)
    assert wrapped["distance_m"] == pytest.approx(first["distance_m"])
    assert wrapped["unwrapped_distance_m"] == pytest.approx(first["unwrapped_distance_m"] - 2000)
    assert wrapped["lap_offset"] == first["lap_offset"] - 2
    assert wrapped["gap_to_leader_s"] == 203.5


def test_ghost_zero_loss_matches_driver_and_larger_loss_moves_back(track):
    cars = [{"driver": "NOR", "gap_to_leader_s": 0}, {"driver": "HAM", "gap_to_leader_s": 18}]
    zero = track.rejoin(900, "NOR", cars, 0)
    assert zero["distance_m"] == pytest.approx(track.position(900, 0)["distance_m"])
    assert track.rejoin(900, "NOR", cars, 30)["unwrapped_distance_m"] < track.rejoin(900, "NOR", cars, 20)["unwrapped_distance_m"]


def test_rejoin_neighbours_and_gap_for_nonleader(track):
    cars = [{"driver": "NOR", "gap_to_leader_s": 0}, {"driver": "VER", "gap_to_leader_s": 3.5},
            {"driver": "HAM", "gap_to_leader_s": 18}, {"driver": "LEC", "gap_to_leader_s": 30}]
    ghost = track.rejoin(900, "VER", cars, 21.5)
    assert ghost["gap_to_leader_s"] == 25
    assert ghost["position"] == 3
    assert ghost["car_ahead"] == "HAM" and ghost["car_behind"] == "LEC"
    assert ghost["gap_to_car_ahead_s"] == 7 and ghost["gap_to_car_behind_s"] == 5


def test_committed_track_fixture_cutoff_and_rain():
    state = SyntheticRaceAdapter.create_race_state(current_lap=18, total_laps=52, subject_driver="NOR",
        stint_length_laps=17, rain_probability=.7, rain_arrival_laps=4, rain_intensity="LIGHT")
    block = build_cutoff_track(state, SYNTHETIC_LAP18_SCENARIO.track)
    assert len(block["polyline"]) == 301
    assert block["source"]["driver"] == "RUS"
    assert [c["gap_to_leader_s"] for c in block["cars"]] == [0, 3.5, 18]
    assert [c["driver"] for c in block["cars"]] == ["NOR", "VER", "HAM"]
    ghost = block["ghost_rejoin"]
    assert ghost["position"] == 3 and ghost["car_ahead"] == "HAM" and ghost["car_behind"] is None
    assert ghost["gap_to_car_ahead_s"] == 3.5 and ghost["pit_loss_s"] == 21.5
    assert block["leader"]["distance_m"] == pytest.approx(block["pit_entry"]["distance_m"] - 25)
    assert block["rain_overlay"]["kind"] == "forecast"
    assert block["rain_overlay"]["arrival_lap"] == 22
    assert block["rain_overlay"]["probability"] == .7
    json.dumps(block, allow_nan=False)
    # Map ignores lap history entirely: adding future observations changes nothing.
    mutated = state.model_copy(deep=True)
    future = mutated.lap_history[-1].model_copy(update={"lap_number": 52, "lap_time_s": 1})
    mutated.lap_history.append(future)
    assert build_cutoff_track(mutated, SYNTHETIC_LAP18_SCENARIO.track) == block


def test_leader_position_override():
    state = SyntheticRaceAdapter.create_race_state()
    assert build_cutoff_track(state, TrackScenarioConfig(leader_distance_m=123))["cars"][0]["distance_m"] == pytest.approx(123)


def test_asset_profile_validation_and_invalid_inputs(track):
    asset = json.loads(TRACK_FILE.read_text(encoding="utf-8"))
    CircuitMap(asset)
    malformed = copy.deepcopy(asset)
    malformed["time_profile"][1]["time_s"] = 0
    with pytest.raises(ValueError):
        CircuitMap(malformed)
    with pytest.raises(ValueError):
        track.position(1, float("nan"))
    with pytest.raises(ValueError):
        track.rejoin(900, "NOR", [{"driver": "NOR", "gap_to_leader_s": 0}], -1)
