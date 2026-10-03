"""Causal packet replay with an isolated, explicitly permitted gap proxy."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
import statistics

from src.calculators.pace_model import PaceModel
from src.calculators.pit_loss_model import PitLossModel
from src.calculators.projection import ProjectionConfig
from src.calculators.traffic_model import TrafficModel
from src.calculators.tyre_model import TyreModel
from src.core.models import (CompetitorState, DerivedPaceMetrics, LapObservation,
                             ObservedWeather, RaceState, SubjectDriverState,
                             TireCompound, TrackStatus, WeatherForecast)
from src.core.provenance import DataQuality, DataSource, ProvenanceMetric

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
STATUS = {"1": TrackStatus.GREEN, "2": TrackStatus.YELLOW,
          "4": TrackStatus.SAFETY_CAR, "5": TrackStatus.RED_FLAG,
          "6": TrackStatus.VSC, "7": TrackStatus.VSC}


class ExcludedSnapshot(ValueError):
    """An explicit data/model limitation, counted in the report."""


def clock(seconds):
    """Encode exact session-relative time; deliberately NOT a wall-clock date."""
    return EPOCH + timedelta(seconds=seconds)


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def lap_seconds(value):
    if not value:
        return None
    parts = str(value).split(":")
    try:
        result = sum(float(v) * 60 ** i for i, v in enumerate(reversed(parts)))
    except ValueError:
        return None
    return result if isfinite(result) and result > 0 else None


def load_dataset(path):
    path = Path(path)
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != path.with_suffix(".sha256").read_text(encoding="utf-8").strip():
        raise ValueError("Normalized session hash mismatch")
    data = json.loads(blob)
    if (data.get("schema_version"), data.get("year"), data.get("race")) != (1, 2021, "Bahrain"):
        raise ValueError("Slice 1 permits Bahrain 2021 only")
    return data, digest


def crossings(data, driver):
    # Coordinates/outcome labels only. Never read pace, tyres or stops here.
    return {int(r["NumberOfLaps"]): r["Time"] for r in data["laps"]
            if r["Driver"] == driver and number(r["Time"]) and r["NumberOfLaps"] > 0}


def at_time(rows, cutoff, driver=None):
    return sorted((r for r in rows if number(r["Time"]) and r["Time"] <= cutoff
                   and (driver is None or r["Driver"] == driver)), key=lambda r: r["Time"])


def tyre_at(data, driver, cutoff, completed_lap):
    rows = at_time(data["tyres"], cutoff, driver)
    rows = [r for r in rows if number(r.get("Stint"))]
    if not rows:
        raise ExcludedSnapshot("missing_causal_tyre_metadata")
    stint = max(r["Stint"] for r in rows)
    current = [r for r in rows if r["Stint"] == stint]
    compounds = [r for r in current if r.get("Compound")]
    starts = [r for r in current if number(r.get("StartLaps"))]
    if not compounds or not starts:
        raise ExcludedSnapshot("incomplete_causal_tyre_metadata")
    try:
        compound = TireCompound(compounds[-1]["Compound"])
    except ValueError as exc:
        raise ExcludedSnapshot("unknown_compound") from exc
    if compound in (TireCompound.INTERMEDIATE, TireCompound.WET):
        raise ExcludedSnapshot("wet_compound_outside_slice")
    # Tyre age at fit + completed race laps since the previous observed pit-in.
    # This avoids late corrections to full-session TyreLife and app counter lag.
    pit_entries = [r for r in at_time(data["events"], current[0]["Time"], driver)
                   if r.get("InPit") is True]
    boundary = 0
    if stint > 0:
        if not pit_entries:
            raise ExcludedSnapshot("tyre_change_without_observed_pit")
        entry = pit_entries[-1]["Time"]
        seen = [r for r in at_time(data["events"], entry, driver) if number(r.get("NumberOfLaps"))]
        boundary = int(seen[-1]["NumberOfLaps"]) + 1 if seen else 0
    age = int(starts[-1]["StartLaps"]) + max(0, completed_lap - boundary)
    used = sorted({r["Compound"] for r in rows if r.get("Compound") in {c.value for c in TireCompound}})
    return compound, age, int(stint), [TireCompound(c) for c in used], max(
        compounds[-1]["Time"], starts[-1]["Time"])


def driver_prefix(data, driver, cutoff):
    """Reduce only earlier raw timing packets; no full-session corrections."""
    position, retired, in_pit = None, False, False
    n, last_crossing, pit_count = 0, None, 0
    history, source_times = [], []
    statuses = at_time(data["track_status"], cutoff)
    for event in at_time(data["events"], cutoff, driver):
        time = event["Time"]
        source_times.append(time)
        if str(event.get("Position", "")).isdigit() and int(event["Position"]) > 0:
            position = int(event["Position"])
        if "Retired" in event:
            retired = bool(event["Retired"])
        if "InPit" in event:
            if event["InPit"] and not in_pit and time >= data.get("session_start_s", 0.):
                pit_count += 1
            in_pit = bool(event["InPit"])
        if number(event.get("NumberOfLaps")):
            updated = int(event["NumberOfLaps"])
            if updated > n:
                n, last_crossing = updated, time
        duration = lap_seconds(event.get("LastLapTime", {}).get("Value"))
        if duration is None or n == 0 or last_crossing is None:
            continue
        # LastLapTime packet is usable only once received, including corrections.
        start = last_crossing - duration
        status_rows = [r for r in statuses if r["Time"] <= last_crossing]
        initial = next((r["Status"] for r in reversed(status_rows) if r["Time"] <= start), "1")
        affected = initial != "1" or any(r["Status"] != "1" for r in status_rows if r["Time"] > start)
        lap_events = at_time(data["events"], last_crossing, driver)
        pit_lap = any("InPit" in r for r in lap_events if r["Time"] >= start)
        try:
            compound, age, _, _, _ = tyre_at(data, driver, time, n)
        except ExcludedSnapshot:
            continue
        observation = LapObservation(lap_number=n, lap_time_s=duration,
            compound=compound, tyre_age_laps=age,
            track_status=TrackStatus.YELLOW if affected else TrackStatus.GREEN,
            is_pit_in_lap=pit_lap, usable_for_pace_model=not affected and not pit_lap,
            timestamp=clock(time))
        history = [r for r in history if r.lap_number != n] + [observation]
    return {"position": position, "retired": retired, "in_pit": in_pit,
            "pit_count": pit_count, "completed_lap": n, "history": history,
            "latest_source_s": max(source_times, default=0)}


@dataclass(frozen=True)
class Snapshot:
    state: RaceState
    config: ProjectionConfig
    audit: dict


def median_pace_anchor(clean, current_lap):
    """Use the raw median, retaining baseline nominal wear/fuel corrections."""
    ordered = sorted(clean, key=lambda r: r.lap_time_s)
    middle = ordered[(len(ordered) - 1) // 2:len(ordered) // 2 + 1]
    base = statistics.mean(r.lap_time_s - TyreModel.lap_delta_s(r.compound, r.tyre_age_laps)
                           - 0.05 * (current_lap - r.lap_number) for r in middle)
    return base, statistics.median(r.lap_time_s for r in clean), middle


def pace_uncertainty(clean, current_lap):
    """Driver-local nominally normalized scatter; no outcome residual fitting."""
    values = [r.lap_time_s - TyreModel.lap_delta_s(r.compound, r.tyre_age_laps)
              - 0.05 * (current_lap - r.lap_number) for r in clean]
    scatter = statistics.stdev(values) if len(values) > 1 else 0.0
    return {"clean_lap_numbers": [r.lap_number for r in clean],
            "normalized_pace_samples_s": values, "sample_count": len(values),
            "clean_lap_scatter_s": scatter,
            "base_pace_sigma_s": scatter / len(values)**0.5,
            "lap_noise_sigma_s": scatter,
            "source_session_s": max((r.timestamp - EPOCH).total_seconds() for r in clean),
            "assumption": "normal persistent offset SD=s/sqrt(n); independent lap noise SD=s; one observation gives zero"}


def build_snapshot(data, driver, lap, *, cutoff_s=None, gap_proxy=None):
    """Only coordinate/proxy channels may read corrected crossing Times."""
    driver_map = {r["DriverNumber"]: r for r in data["drivers"]}
    own_crossings = crossings(data, driver)
    cutoff = own_crossings.get(lap) if cutoff_s is None else cutoff_s
    if not number(cutoff):
        raise ExcludedSnapshot("missing_cutoff_crossing")
    if not 5 <= lap <= data["scheduled_laps"] - 5:
        raise ExcludedSnapshot("cutoff_outside_slice")
    subject = driver_prefix(data, driver, cutoff)
    if subject["in_pit"]:
        raise ExcludedSnapshot("subject_stop_straddles_cutoff")
    if subject["position"] is None or not subject["history"]:
        raise ExcludedSnapshot("missing_causal_subject_timing")
    compound, age, stint, used, tyre_source = tyre_at(data, driver, cutoff, lap)
    history = subject["history"]
    # Only compounds observed on completed racing laps/current set count as
    # used. Old-stint metadata corrections are not evidence of racing on them.
    used = sorted({r.compound for r in history} | {compound}, key=lambda c: c.value)
    clean = PaceModel.filter_clean_laps(history)[-6:]
    if not clean:
        raise ExcludedSnapshot("no_recent_clean_pace")
    base_pace, observed_median, anchor_laps = median_pace_anchor(clean, lap)
    uncertainty = pace_uncertainty(clean, lap)
    config = ProjectionConfig(degradation_scale=1.0, base_pace_s=base_pace,
                              base_pace_sigma_s=uncertainty["base_pace_sigma_s"],
                              lap_noise_sigma_s=uncertainty["lap_noise_sigma_s"])
    metrics = DerivedPaceMetrics(
        recent_pace_trend_s_per_lap=ProvenanceMetric(value=0., source=DataSource.USER_DEFINED,
                                                   notes="Frozen: no pace regression"),
        degradation_rate_s_per_lap=ProvenanceMetric(
            value=TyreModel.get_compound_specs(compound).degradation_base_rate_s_per_lap,
            source=DataSource.USER_DEFINED, notes="Frozen compound defaults; config scale=1"),
        clean_air_potential_lap_time_s=ProvenanceMetric(value=observed_median,
                                                      source=DataSource.DERIVED_MODEL))
    own = SubjectDriverState(driver=driver_map[driver]["Abbreviation"],
        team=driver_map[driver]["TeamName"], position=subject["position"],
        current_compound=compound, stint_length_laps=age,
        total_pit_stops=subject["pit_count"], used_compounds=used,
        last_lap_time_s=history[-1].lap_time_s)
    rivals, gap_audit, rival_sources, omitted = [], [], [], []
    for rival in sorted(driver_map):
        if rival == driver:
            continue
        prefix = driver_prefix(data, rival, cutoff)
        if prefix["retired"] or not prefix["history"] or prefix["position"] is None:
            omitted.append({"driver": rival, "reason": "causal_retired_or_no_completed_timing"})
            continue
        try:
            c, a, _, _, source = tyre_at(data, rival, cutoff, prefix["completed_lap"])
        except ExcludedSnapshot:
            omitted.append({"driver": rival, "reason": "missing_causal_tyres"})
            continue
        crossing = (gap_proxy or {}).get(rival) if gap_proxy is not None else crossings(data, rival).get(lap)
        basis = "live_timing_proxy_same_lap_crossing"
        if not number(crossing):
            # Causal fallback for missing same-lap crossing: most recent common
            # completed lap. Its gap is stale, disclosed, never invented by rank.
            rc = {k: v for k, v in crossings(data, rival).items() if v <= cutoff}
            common = sorted(k for k in rc if k in own_crossings and own_crossings[k] <= cutoff)
            if not common:
                omitted.append({"driver": rival, "reason": "no_causal_gap_or_proxy"})
                continue
            k = common[-1]
            crossing = rc[k]
            gap = own_crossings[k] - crossing
            basis = "stale_pre_cutoff_common_lap_crossing"
        else:
            gap = cutoff - crossing
        rivals.append(CompetitorState(driver=driver_map[rival]["Abbreviation"],
            team=driver_map[rival]["TeamName"], position=prefix["position"],
            current_compound=c, tyre_age_laps=a, gap_to_subject_s=gap,
            last_lap_time_s=prefix["history"][-1].lap_time_s,
            is_in_pit=prefix["in_pit"], pit_stop_count=prefix["pit_count"]))
        gap_audit.append({"driver": rival, "basis": basis, "crossing_session_s": crossing,
                          "after_cutoff_exception": crossing > cutoff, "gap_s": gap})
        rival_sources.extend([source, prefix["latest_source_s"]])
    weather = at_time(data["weather"], cutoff)
    track = at_time(data["track_status"], cutoff)
    if not weather or not track:
        raise ExcludedSnapshot("missing_weather_or_track_status")
    w = weather[-1]
    if any(w.get(k) is None for k in ("TrackTemp", "AirTemp", "Rainfall", "Humidity")):
        raise ExcludedSnapshot("incomplete_weather")
    if w["Rainfall"]:
        raise ExcludedSnapshot("observed_rain_outside_slice")
    status = STATUS.get(str(track[-1]["Status"]))
    if status is None or status == TrackStatus.RED_FLAG:
        raise ExcludedSnapshot("unsupported_track_status")
    loss = PitLossModel.calculate_pit_loss(status).current_pit_loss_s
    pos, gap = TrafficModel.predict_rejoin(own, rivals, loss)
    def measured(value):
        return ProvenanceMetric(value=value, source=DataSource.REAL_FASTF1)
    state = RaceState(current_lap=lap, total_laps=data["scheduled_laps"],
        timestamp=clock(cutoff), knowledge_cutoff=clock(cutoff), subject_driver=own,
        competitors=rivals, track_status=status, observed_weather=ObservedWeather(
            track_temp_c=measured(w["TrackTemp"]), air_temp_c=measured(w["AirTemp"]),
            rainfall=measured(w["Rainfall"]), humidity_pct=measured(w["Humidity"]),
            wind_speed_kmh=measured(w["WindSpeed"] * 3.6) if number(w.get("WindSpeed")) else None),
        weather_forecast=WeatherForecast(
            rain_probability=ProvenanceMetric(value=0., source=DataSource.USER_DEFINED,
                                             quality=DataQuality.LOW, notes="No forecast; dry persistence"),
            expected_arrival_laps=ProvenanceMetric(value=None, source=DataSource.USER_DEFINED),
            intensity=ProvenanceMetric(value="DRY", source=DataSource.USER_DEFINED),
            confidence=DataQuality.LOW), derived_pace=metrics, lap_history=history,
        pit_loss=PitLossModel.calculate_pit_loss(status, pos, gap))
    timestamps = {"frozen_defaults": 0., "base_pace": max((r.timestamp - EPOCH).total_seconds() for r in anchor_laps),
                  "subject_timing": subject["latest_source_s"], "subject_tyres": tyre_source,
                  "rival_inputs": max(rival_sources, default=0.),
                  "weather": w["Time"], "track_status": track[-1]["Time"]}
    timestamps["pace_uncertainty"] = uncertainty["source_session_s"]
    if any(t > cutoff for t in timestamps.values()):
        raise ValueError("Future parameter/input source timestamp")
    audit = {"cutoff_session_s": cutoff, "clock": "session-relative epoch encoding; not wall UTC",
             "parameter_source_session_s": timestamps, "gaps": gap_audit,
             "weather_sample_age_s": cutoff - w["Time"], "omitted_rivals": omitted,
             "subject_stint_index": stint, "subject_tyre_age": age,
             "subject_completed_stint_laps": age - int(next(
                 r["StartLaps"] for r in reversed(at_time(data["tyres"], cutoff, driver))
                 if r.get("Stint") == stint and number(r.get("StartLaps")))),
             "base_pace_anchor_lap": max(r.lap_number for r in anchor_laps),
             "base_pace_anchor_laps": [r.lap_number for r in anchor_laps],
             "base_pace_method": "median", "pace_uncertainty": uncertainty,
             "parameters": "frozen defaults; recent six clean laps median pace and driver-local scatter"}
    return Snapshot(state, config, audit)
