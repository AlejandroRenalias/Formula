"""Offline cutoff-map coordinates using a fixed reference lap time profile.

Gap is positive behind the leader. Unwrapped distance preserves lap deficits;
wrapped distance is only a drawing coordinate. No future telemetry is consumed.
"""
from bisect import bisect_right
import json
import math
from pathlib import Path

from src.adapters.scenarios import TrackScenarioConfig

TRACK_FILE = Path(__file__).resolve().parents[2] / "data/tracks/silverstone.json"


def _interpolate(value, xs, ys):
    index = min(max(bisect_right(xs, value) - 1, 0), len(xs) - 2)
    fraction = (value - xs[index]) / (xs[index + 1] - xs[index])
    return ys[index] + fraction * (ys[index + 1] - ys[index])


class CircuitMap:
    def __init__(self, asset):
        self.asset = asset
        self.length = float(asset["lap_length_m"])
        self.duration = float(asset["reference_lap_time_s"])
        self.distances = [p["distance_m"] for p in asset["time_profile"]]
        self.times = [p["time_s"] for p in asset["time_profile"]]
        self.line_distances = [p["distance_m"] for p in asset["polyline"]]
        self.x = [p["x"] for p in asset["polyline"]]
        self.y = [p["y"] for p in asset["polyline"]]
        for values in (self.distances, self.times, self.line_distances):
            if len(values) < 2 or not all(math.isfinite(v) for v in values) or any(b <= a for a, b in zip(values, values[1:])):
                raise ValueError("Track distances and times must be finite and strictly increasing")
        if not all(math.isfinite(v) for v in self.x + self.y):
            raise ValueError("Track coordinates must be finite")
        if self.length <= 0 or self.duration <= 0 or not all((
            self.distances[0] == 0, self.times[0] == 0, self.line_distances[0] == 0,
            math.isclose(self.distances[-1], self.length), math.isclose(self.times[-1], self.duration),
            math.isclose(self.line_distances[-1], self.length),
        )):
            raise ValueError("Profiles must span a complete reference lap")

    def position(self, leader_distance_m, gap_s):
        if not math.isfinite(leader_distance_m) or not math.isfinite(gap_s):
            raise ValueError("Position inputs must be finite")
        leader_turn, leader_distance = divmod(leader_distance_m, self.length)
        leader_time = leader_turn * self.duration + _interpolate(leader_distance, self.distances, self.times)
        turns, clock = divmod(leader_time - gap_s, self.duration)
        distance = _interpolate(clock, self.times, self.distances)
        return {"gap_to_leader_s": gap_s, "distance_m": distance,
                "unwrapped_distance_m": turns * self.length + distance, "lap_offset": int(turns),
                "x": _interpolate(distance, self.line_distances, self.x),
                "y": _interpolate(distance, self.line_distances, self.y)}

    def rejoin(self, leader_distance_m, driver, cars, pit_loss_s):
        if not math.isfinite(pit_loss_s) or pit_loss_s < 0:
            raise ValueError("Pit loss must be finite and non-negative")
        subject = next(c for c in cars if c["driver"] == driver)
        gap = subject["gap_to_leader_s"] + pit_loss_s
        others = [c for c in cars if c["driver"] != driver]
        ahead = [c for c in others if c["gap_to_leader_s"] < gap]
        behind = [c for c in others if c["gap_to_leader_s"] >= gap]
        previous = max(ahead, key=lambda c: c["gap_to_leader_s"], default=None)
        following = min(behind, key=lambda c: c["gap_to_leader_s"], default=None)
        ahead_gap = gap - previous["gap_to_leader_s"] if previous else None
        behind_gap = following["gap_to_leader_s"] - gap if following else None
        return {"driver": driver, **self.position(leader_distance_m, gap), "pit_loss_s": pit_loss_s,
                "position": len(ahead) + 1, "car_ahead": previous["driver"] if previous else None,
                "car_behind": following["driver"] if following else None,
                "gap_to_car_ahead_s": ahead_gap, "gap_to_car_behind_s": behind_gap,
                "display": {"pit_loss_s": round(pit_loss_s, 1),
                            "gap_to_car_ahead_s": round(ahead_gap, 1) if ahead_gap is not None else None,
                            "gap_to_car_behind_s": round(behind_gap, 1) if behind_gap is not None else None},
                "kind": "projection", "field_complete": False}


def build_cutoff_track(state, config=None, asset=None):
    config = config or TrackScenarioConfig()
    asset = asset if asset is not None else json.loads(TRACK_FILE.read_text(encoding="utf-8"))
    if asset["id"] != config.track_id:
        raise ValueError("Scenario track does not match asset")
    circuit = CircuitMap(asset)
    leader_distance = config.leader_distance_m
    if leader_distance is None:
        leader_distance = (asset["pit_entry"]["distance_m"] - config.leader_before_pit_entry_m) % circuit.length
    # Adapter convention is positive ahead of subject, negative behind subject.
    cars = [{"driver": state.subject_driver.driver, "team": state.subject_driver.team, "gap_to_leader_s": 0.0}]
    cars += [{"driver": c.driver, "team": c.team, "gap_to_leader_s": -c.gap_to_subject_s} for c in state.competitors]
    minimum_gap = min(c["gap_to_leader_s"] for c in cars)
    for car in cars:
        car["gap_to_leader_s"] -= minimum_gap
        car.update(circuit.position(leader_distance, car["gap_to_leader_s"]))
        car["team_colour"] = config.team_colours.get(car["team"], "#B9C7D6")
        car["kind"] = "synthetic"  # this fixture entry point is for synthetic cutoff state
    eta = state.weather_forecast.expected_arrival_laps.value
    sector = next(s for s in asset["sectors"] if s["sector"] == config.rain_first_sector)
    return {**asset, "cutoff_lap": state.current_lap,
            "leader": {"driver": min(cars, key=lambda c: c["gap_to_leader_s"])["driver"],
                       "distance_m": leader_distance, "kind": "config"},
            "cars": sorted(cars, key=lambda c: c["gap_to_leader_s"]),
            "ghost_rejoin": circuit.rejoin(leader_distance, state.subject_driver.driver, cars,
                                          state.pit_loss.current_pit_loss_s),
            "rain_overlay": {"kind": "forecast", "source": "synthetic scenario forecast",
                             "first_sector": config.rain_first_sector,
                             "start_distance_m": sector["start_distance_m"], "end_distance_m": sector["end_distance_m"],
                             "location_basis": "configured illustrative first-arrival sector; not radar",
                             "eta_laps": eta, "arrival_lap": state.current_lap + eta if eta is not None else None,
                             "probability": state.weather_forecast.rain_probability.value}}
