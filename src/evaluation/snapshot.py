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

from src.evaluation.races import DEVELOPMENT_RACES, race_key
from src.evaluation.neutralization_prior import ongoing_inputs, load_prior
from src.evaluation.pit_parameters import pit_inputs
from src.evaluation.wear_parameters import estimate_wear
from src.evaluation.joint_parameters import estimate_joint
from src.evaluation.model_configurations import resolve_configuration, frozen_uncertainty_multipliers

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
    key = race_key(data)
    if data.get("schema_version") != 1 or data.get("scheduled_laps") != DEVELOPMENT_RACES[key]["scheduled_laps"]:
        raise ValueError("Unsupported schema or pre-declared scheduled race distance")
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


def median_pace_anchor(clean, current_lap, wear_rates=None, race_trend=-.05, compound_offsets=None):
    """Use the raw median, retaining baseline nominal wear/fuel corrections."""
    ordered = sorted(clean, key=lambda r: r.lap_time_s)
    middle = ordered[(len(ordered) - 1) // 2:len(ordered) // 2 + 1]
    base = statistics.mean(r.lap_time_s - TyreModel.lap_delta_s(r.compound, r.tyre_age_laps,
                               degradation_rate_s_per_lap=(wear_rates or {}).get(r.compound.value),
                               compound_offset_s=(compound_offsets or {}).get(r.compound.value))
                           + race_trend * (current_lap - r.lap_number) for r in middle)
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


def build_snapshot(data, driver, lap, *, cutoff_s=None, gap_proxy=None, fit_wear=None, fit_trend=None, fit_offsets=None, configuration=None):
    """Only coordinate/proxy channels may read corrected crossing Times."""
    calibration = frozen_uncertainty_multipliers() if configuration is None else {}
    configuration, settings = resolve_configuration(configuration)
    profile_wear, profile_joint, profile_offsets, estimate_trend, extrapolate_trend = settings
    fit_wear = profile_wear if fit_wear is None else fit_wear
    fit_trend = profile_joint if fit_trend is None else fit_trend
    fit_offsets = profile_offsets if fit_offsets is None else fit_offsets
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
    config = ProjectionConfig(degradation_scale=1.0, base_pace_s=base_pace, pit_in_lap_fraction=0.5,
                              base_pace_sigma_s=uncertainty["base_pace_sigma_s"],
                              lap_noise_sigma_s=uncertainty["lap_noise_sigma_s"], **calibration)
    uncertainty["multipliers"] = {
        "base_pace_uncertainty_multiplier": config.base_pace_uncertainty_multiplier,
        "lap_noise_uncertainty_multiplier": config.lap_noise_uncertainty_multiplier}
    uncertainty["calibration_basis"] = "frozen development profile" if calibration else "unit multipliers"
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
    prefixes = {driver: subject}
    for rival in sorted(driver_map):
        if rival == driver:
            continue
        prefix = driver_prefix(data, rival, cutoff)
        prefixes[rival] = prefix
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
    ongoing_laps, ongoing_audit = ongoing_inputs(track, cutoff, status, base_pace + TyreModel.lap_delta_s(compound, age))
    prior, _ = load_prior()
    config = config.model_copy(update={"ongoing_neutralization_laps":ongoing_laps,
        "future_sc_probability":prior["sc_probability_per_green_lap"],
        "future_vsc_probability":prior["vsc_probability_per_green_lap"],
        "sc_duration_prior_s":tuple(prior["sc_durations_s"]),
        "vsc_duration_prior_s":tuple(prior["vsc_durations_s"]),
        "sc_pace_multiplier":prior["sc_pace_multiplier"],
        "vsc_pace_multiplier":prior["vsc_pace_multiplier"]})
    green_loss, in_fraction, pit_audit = pit_inputs(data, prefixes, cutoff)
    config = config.model_copy(update={"pit_in_lap_fraction":in_fraction})
    wear_rates, wear_audit = estimate_wear(data, prefixes, cutoff) if fit_wear else ({},{})
    trend, trend_audit = -.05, {}
    offsets, offset_audit = {}, {}
    if fit_wear and fit_trend:
        fitted = estimate_joint(data, prefixes, cutoff, fit_offsets=fit_offsets, fit_race_trend=estimate_trend)
        wear_rates, wear_audit, trend, trend_audit = fitted[:4]
        if fit_offsets:offsets, offset_audit = fitted[4:]
    projection_trend = trend if extrapolate_trend else -.05
    if fit_wear:
        # Keep the existing ongoing-event conversion and noise sizing unchanged.
        base_pace, observed_median, anchor_laps = median_pace_anchor(clean, lap, wear_rates, trend, offsets)
        config = config.model_copy(update={"base_pace_s":base_pace,
            "degradation_rates_s_per_lap":wear_rates, "race_trend_s_per_lap":projection_trend if fit_trend else None, "compound_offsets_s":offsets})
        metrics = metrics.model_copy(update={"degradation_rate_s_per_lap":ProvenanceMetric(
            value=wear_rates[compound.value], source=DataSource.USER_DEFINED if wear_audit[compound.value]["fallback_used"] else DataSource.DERIVED_MODEL,
            quality=DataQuality.LOW if wear_audit[compound.value]["fallback_used"] else DataQuality.MEDIUM,
            notes=f"Causal compound-pooled within-stint slope; n={wear_audit[compound.value]['sample_count']}; fallback={wear_audit[compound.value]['fallback_used']}")})
    loss = PitLossModel.calculate_pit_loss(status, green_loss_s=green_loss).current_pit_loss_s
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
        pit_loss=PitLossModel.calculate_pit_loss(status, pos, gap, green_loss_s=green_loss))
    timestamps = {"frozen_defaults": 0., "base_pace": max((r.timestamp - EPOCH).total_seconds() for r in anchor_laps),
                  "subject_timing": subject["latest_source_s"], "subject_tyres": tyre_source,
                  "rival_inputs": max(rival_sources, default=0.),
                  "weather": w["Time"], "track_status": track[-1]["Time"]}
    for c, estimate in offset_audit.items():
        timestamps["compound_offset_"+c] = estimate["latest_source_session_s"]
    if trend_audit:
        timestamps["race_trend"] = trend_audit["latest_source_session_s"]
    for c, estimate in wear_audit.items():
        timestamps["tyre_wear_"+c] = estimate["latest_source_session_s"]
    if fit_wear:
        timestamps["base_pace"] = max(timestamps["base_pace"],
            timestamps.get("race_trend",0.),
            *(wear_audit[r.compound.value]["latest_source_session_s"] for r in anchor_laps),
            *(offset_audit.get(r.compound.value,{}).get("latest_source_session_s",0.) for r in anchor_laps))
    timestamps["pit_loss_estimate"] = pit_audit["latest_source_session_s"]
    timestamps["pit_loss_prior"] = 0.
    timestamps["pace_uncertainty"] = uncertainty["source_session_s"]
    timestamps["neutralization_onset"] = ongoing_audit["source_session_s"]
    timestamps["neutralization_prior"] = 0.
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
             "configuration":configuration, "projected_race_trend_s_per_lap":projection_trend, "base_pace_method": "median", "compound_offset_estimates":offset_audit, "race_trend_estimate":trend_audit, "wear_estimates":wear_audit, "wear_enabled":fit_wear, "pit_loss_estimate":pit_audit, "pace_uncertainty": uncertainty, "ongoing_neutralization":ongoing_audit,
             "parameters": "causal pit components and compound wear; recent six clean laps median anchor; unchanged nominal driver-local noise sizing"}
    return Snapshot(state, config, audit)
