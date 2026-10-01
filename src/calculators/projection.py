"""Deterministic shared-scenario race-time projection alongside the legacy scorer."""
from dataclasses import dataclass
from math import isfinite
from random import Random
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.calculators.pace_model import PaceModel
from src.calculators.pit_loss_model import PitLossModel
from src.calculators.tyre_model import TyreModel
from src.calculators.weather_model import WeatherModel
from src.core.models import RaceState, TireCompound, TrackStatus

DRY = frozenset({TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD})
WET = frozenset({TireCompound.INTERMEDIATE, TireCompound.WET})


class Stop(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    lap: int = Field(ge=0, description="Stop boundary, after this completed lap")
    compound: TireCompound


class Policy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(min_length=1)
    label: str
    dry_stops: tuple[Stop, ...] = ()
    react_to_weather: bool = True
    max_stops: int = Field(default=2, ge=0, le=2)

    @model_validator(mode="after")
    def ordered_stops(self):
        if len(self.dry_stops) > self.max_stops or any(
                b.lap <= a.lap for a, b in zip(self.dry_stops, self.dry_stops[1:])):
            raise ValueError("Stops must be strictly ordered and fit the two-stop budget")
        if any(stop.compound not in DRY for stop in self.dry_stops):
            raise ValueError("Scheduled stops must use dry compounds; wet stops are reactive")
        return self


class ProjectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)
    seed: int = 18
    samples_per_weather_branch: int = Field(default=32, ge=1, le=256)
    rain_eta_spread_laps: int = Field(default=2, ge=0, le=20)
    pit_loss_spread_s: float = Field(default=1.5, ge=0)
    wetness_ramp_laps: float = Field(default=2.0, gt=0)
    light_rain_wetness: float = Field(default=0.7, gt=0, le=1)
    fuel_effect_s_per_lap: float = Field(default=0.05, ge=0)
    cliff_rate_s: float = Field(default=0.15, ge=0)
    degradation_scale: float | None = Field(default=None, ge=0)
    base_pace_s: float | None = Field(default=None, gt=0)
    slick_wet_penalty_s: float = Field(default=18.0, ge=0)
    inter_dry_penalty_s: float = Field(default=8.0, ge=0)
    wet_dry_penalty_s: float = Field(default=14.0, ge=0)
    heavy_inter_penalty_s: float = Field(default=8.0, ge=0)
    traffic_gap_s: float = Field(default=1.0, gt=0)
    traffic_penalty_s: float = Field(default=0.4, ge=0)
    dry_grid_step_laps: int = Field(default=4, ge=1)
    max_policies: int = Field(default=6, ge=2, le=20)
    safety_car_lap: int | None = Field(default=None, ge=1)
    safety_car_duration_laps: int = Field(default=2, ge=1)
    rain_sweep_offsets: tuple[int, ...] = tuple(range(1, 35))
    rain_probability_sweep: tuple[float, ...] = tuple(v / 10 for v in range(11))
    pit_loss_sweep_s: tuple[float, ...] = tuple(float(v) for v in range(5, 46, 5))
    safety_car_sweep_offsets: tuple[int, ...] = tuple(range(1, 13))

    @model_validator(mode="after")
    def valid_sweep_ranges(self):
        if any(not 0 <= p <= 1 for p in self.rain_probability_sweep):
            raise ValueError("Rain probability sweep values must be between zero and one")
        if any(p < 0 for p in self.pit_loss_sweep_s):
            raise ValueError("Pit loss sweep values must be nonnegative")
        return self


@dataclass(frozen=True)
class Scenario:
    rain_lap: int | None
    pit_offset_s: float
    weight: float


@dataclass
class Trace:
    times: list[float]
    positions: list[int]
    stops: list[dict]
    legal: bool


def _snapshot(state: RaceState, config: ProjectionConfig) -> RaceState:
    if state.timestamp != state.knowledge_cutoff:
        raise ValueError("Projection requires a snapshot timestamp equal to its cutoff")
    if not 0 <= state.current_lap < state.total_laps:
        raise ValueError("Cutoff must precede the finish")
    if not 0 <= state.weather_forecast.rain_probability.value <= 1:
        raise ValueError("Rain probability must be between zero and one")
    if state.weather_forecast.expected_arrival_laps.value is not None and state.weather_forecast.expected_arrival_laps.value < 0:
        raise ValueError("Rain ETA must not be negative")
    if any(v < 0 or not isfinite(v) for v in (state.pit_loss.green_pit_loss_s,
            state.pit_loss.vsc_pit_loss_s, state.pit_loss.sc_pit_loss_s)):
        raise ValueError("Pit losses must be finite and nonnegative")
    if (not isfinite(state.subject_driver.last_lap_time_s) or state.subject_driver.last_lap_time_s <= 0
            or any(not isfinite(r.gap_to_subject_s) or (r.last_lap_time_s is not None and
                   (not isfinite(r.last_lap_time_s) or r.last_lap_time_s <= 0)) for r in state.competitors)):
        raise ValueError("Snapshot gaps and pace must be finite; lap times must be positive")
    history = [lap for lap in state.lap_history if lap.lap_number <= state.current_lap
               and (lap.timestamp is None or lap.timestamp <= state.knowledge_cutoff)]
    # Recompute metrics after physically excluding future rows.
    metrics = PaceModel.calculate_pace_metrics(history, fuel_correction_s_per_lap=config.fuel_effect_s_per_lap)
    return state.model_copy(deep=True, update={"lap_history": history, "derived_pace": metrics})


def default_policies(state: RaceState, config: ProjectionConfig) -> tuple[Policy, ...]:
    compound = TireCompound.HARD if state.subject_driver.current_compound != TireCompound.HARD else TireCompound.MEDIUM
    policies = [Policy(id="box_now", label=f"BOX now for {compound.value}; switch at crossover",
                       dry_stops=(Stop(lap=state.current_lap, compound=compound),))]
    last = state.total_laps - 1
    for lap in range(state.current_lap + config.dry_grid_step_laps, last + 1, config.dry_grid_step_laps):
        policies.append(Policy(id=f"wait_to_{lap}", label=f"STAY; crossover or dry stop after lap {lap}",
                               dry_stops=(Stop(lap=lap, compound=compound),)))
        if len(policies) >= max(2, config.max_policies - 1):
            break
    first = state.current_lap + config.dry_grid_step_laps
    second = first + 4 * config.dry_grid_step_laps
    if len(policies) < config.max_policies and second < state.total_laps:
        other = TireCompound.MEDIUM if compound == TireCompound.HARD else TireCompound.HARD
        policies.append(Policy(id=f"two_stop_{first}_{second}", label=f"Two dry stops after laps {first} and {second}; react to rain",
                               dry_stops=(Stop(lap=first, compound=compound), Stop(lap=second, compound=other))))
    if len(policies) == 1:
        policies.append(Policy(id="stay", label="STAY; switch at crossover", dry_stops=()))
    return tuple(policies)


def sample_scenarios(state: RaceState, config: ProjectionConfig) -> tuple[Scenario, ...]:
    # Seeded simulation draws are intentionally non-cryptographic.
    rng = Random(config.seed)  # nosec B311
    probability = 1.0 if state.observed_weather.rainfall.value else state.weather_forecast.rain_probability.value
    eta = state.weather_forecast.expected_arrival_laps.value
    if probability > 0 and eta is None and not state.observed_weather.rainfall.value:
        raise ValueError("Positive rain probability requires an ETA")
    scenarios = []
    # Stratified branches retain exactly the forecast probability, not a noisy
    # Bernoulli estimate. Seeded conditional ETA and pit draws are shared.
    draws = [(rng.randint(-config.rain_eta_spread_laps, config.rain_eta_spread_laps),
              rng.uniform(-config.pit_loss_spread_s, config.pit_loss_spread_s))
             for _ in range(config.samples_per_weather_branch)]
    for rains, mass in ((False, 1 - probability), (True, probability)):
        if mass <= 0:
            continue
        for offset, pit_offset in draws:
            rain_lap = (state.current_lap if state.observed_weather.rainfall.value else
                        max(state.current_lap + 1, state.current_lap + int(eta) + offset)) if rains else None
            scenarios.append(Scenario(rain_lap, pit_offset, mass / len(draws)))
    return tuple(scenarios)


def _wetness(state, scenario, lap, config):
    if scenario.rain_lap is None:
        return 0.0
    maximum = config.light_rain_wetness if state.weather_forecast.intensity.value == "LIGHT" else 1.0
    return maximum * min(1.0, max(0.0, (lap - scenario.rain_lap + 1) / config.wetness_ramp_laps))


def _weather_delta(compound, wetness, state, config):
    return WeatherModel.projection_penalty_s(compound, wetness, state.weather_forecast.intensity.value,
        config.slick_wet_penalty_s, config.inter_dry_penalty_s,
        config.wet_dry_penalty_s, config.heavy_inter_penalty_s)


def _wet_compound(state, wetness, config):
    # Choose a fresh wet compound only when it beats fresh HARD at the current
    # wetness. This uses observed simulated wetness, never the sampled future ETA.
    def cost(c):
        return TyreModel.get_compound_specs(c).base_pace_delta_s + _weather_delta(c, wetness, state, config)
    best = min((TireCompound.INTERMEDIATE, TireCompound.WET), key=cost)
    return best if cost(best) < cost(TireCompound.HARD) else None


def _pit_loss(state, scenario, lap, config):
    status = state.track_status
    if config.safety_car_lap is not None:
        status = (TrackStatus.SAFETY_CAR if config.safety_car_lap <= lap <
                  config.safety_car_lap + config.safety_car_duration_laps else TrackStatus.GREEN)
    return PitLossModel.calculate_pit_loss(status,
        green_loss_s=max(0, state.pit_loss.green_pit_loss_s + scenario.pit_offset_s),
        vsc_loss_s=max(0, state.pit_loss.vsc_pit_loss_s + scenario.pit_offset_s),
        sc_loss_s=max(0, state.pit_loss.sc_pit_loss_s + scenario.pit_offset_s)).current_pit_loss_s


def _cutoff_target(state, policy, config):
    """Commit the initial action using only weather observed at the cutoff."""
    if policy.max_stops == 0:
        return None
    wetness = _wetness(state, Scenario(state.current_lap, 0, 1), state.current_lap, config) if state.observed_weather.rainfall.value else 0
    crossover = _wet_compound(state, wetness, config) if policy.react_to_weather else None
    compound = state.subject_driver.current_compound
    if crossover is not None:
        return crossover if compound != crossover else None
    return next((s.compound for s in policy.dry_stops if s.lap == state.current_lap and compound not in WET), None)


def _call_summary(state, policies, means, ranking, config):
    actions = {p.id: "BOX_NOW" if _cutoff_target(state, p, config) is not None else "STAY_OUT" for p in policies}
    best = {action: next((pid for pid in ranking if actions[pid] == action), None)
            for action in ("STAY_OUT", "BOX_NOW")}
    stay, box = best["STAY_OUT"], best["BOX_NOW"]
    return {"call": actions[ranking[0]], "best_policies_by_call": best,
            "call_margin_s": round(abs(means[stay] - means[box]), 4) if stay and box else None}


def simulate_policy(state: RaceState, policy: Policy, scenario: Scenario,
                    config: ProjectionConfig) -> Trace:
    """Project from the completed-lap boundary to the finish; no scored bonuses."""
    subject = state.subject_driver
    scale = config.degradation_scale
    if scale is None:
        scale = state.derived_pace.degradation_rate_s_per_lap.value / TyreModel.get_compound_specs(subject.current_compound).degradation_base_rate_s_per_lap
    if not isfinite(scale):
        raise ValueError("Degradation must be finite")
    delta = lambda c, age: TyreModel.lap_delta_s(c, age, scale, config.cliff_rate_s)
    base = config.base_pace_s if config.base_pace_s is not None else subject.last_lap_time_s - delta(subject.current_compound, subject.stint_length_laps)
    rivals = [{"time": -r.gap_to_subject_s, "compound": r.current_compound, "age": r.tyre_age_laps,
               "base": (r.last_lap_time_s if r.last_lap_time_s is not None else subject.last_lap_time_s)
                       - delta(r.current_compound, r.tyre_age_laps), "stops": 0} for r in state.competitors]
    # Missing competitors retain an anonymous fixed count ahead, not invented pace.
    missing_ahead = max(0, subject.position - 1 - sum(r.gap_to_subject_s > 0 for r in state.competitors))
    compound, age = subject.current_compound, subject.stint_length_laps
    used = set(subject.used_compounds) | {compound}
    times, positions, stops = [0.0], [subject.position], []
    total = 0.0
    for lap in range(state.current_lap + 1, state.total_laps + 1):
        wetness = _wetness(state, scenario, lap, config)
        crossover = _wet_compound(state, wetness, config) if policy.react_to_weather else None
        scheduled = next((stop.compound for stop in policy.dry_stops if stop.lap == lap - 1), None)
        target = crossover if crossover is not None and compound != crossover else (
            scheduled if crossover is None and compound not in WET else None)
        if lap == state.current_lap + 1:
            target = _cutoff_target(state, policy, config)
        loss = 0.0
        if target is not None and len(stops) < policy.max_stops:
            compound, age = target, 0
            used.add(compound)
            loss = _pit_loss(state, scenario, lap, config)
            stops.append({"lap": lap - 1, "charged_on_lap": lap, "compound": compound.value, "pit_loss_s": loss})
        fuel = config.fuel_effect_s_per_lap * (lap - state.current_lap)
        own_pace = base + delta(compound, age) - fuel + _weather_delta(compound, wetness, state, config)
        # Rival policies are explicit model assumptions: crossover or a tyre-life stop.
        rival_paces, rival_losses = [], []
        for rival in rivals:
            c = rival["compound"]
            target_rival = _wet_compound(state, wetness, config)
            if target_rival is None and c in DRY and rival["age"] >= TyreModel.get_compound_specs(c).expected_life_laps:
                target_rival = TireCompound.HARD if c != TireCompound.HARD else TireCompound.MEDIUM
            rival_loss = 0.0
            if target_rival is not None and target_rival != c and rival["stops"] < 2:
                rival["compound"], rival["age"] = target_rival, 0
                rival["stops"] += 1
                rival_loss = _pit_loss(state, scenario, lap, config)
            rival_paces.append(rival["base"] + delta(rival["compound"], rival["age"]) - fuel
                               + _weather_delta(rival["compound"], wetness, state, config))
            rival_losses.append(rival_loss)
        traffic = 0.0
        for rival, rival_pace, rival_loss in zip(rivals, rival_paces, rival_losses):
            # Gap at the start of the running segment, after this lap's stop costs.
            gap = total + loss - (rival["time"] + rival_loss)
            if 0 < gap <= config.traffic_gap_s and rival_pace <= own_pace:
                traffic = config.traffic_penalty_s
                break
        total += own_pace + traffic + loss
        age += 1
        for rival, pace, rival_loss in zip(rivals, rival_paces, rival_losses):
            rival["time"] += pace + rival_loss
            rival["age"] += 1
        times.append(total)
        positions.append(1 + missing_ahead + sum(r["time"] < total for r in rivals))
    legal = bool(used & WET) or len(used & DRY) >= 2
    return Trace(times, positions, stops, legal)


def _quantile(values, weights, q):
    pairs = sorted(zip(values, weights))
    threshold, cumulative = q * sum(weights), 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= threshold - 1e-12:
            return value
    return pairs[-1][0]


def _evaluate(state, policies, scenarios, config):
    traces = {p.id: [simulate_policy(state, p, s, config) for s in scenarios] for p in policies}
    means = {p.id: sum(t.times[-1] * s.weight for t, s in zip(traces[p.id], scenarios))
             for p in policies if all(t.legal for t in traces[p.id])}
    ranking = sorted(means, key=lambda pid: (means[pid], pid))
    if not ranking:
        raise ValueError("No policy is compound-compliant in every positive-probability scenario")
    return traces, means, ranking


def project(state: RaceState, policies: tuple[Policy, ...] | None = None,
            config: ProjectionConfig | None = None, include_flips: bool = True) -> dict:
    config = config or ProjectionConfig()
    state = _snapshot(state, config)
    policies = policies if policies is not None else default_policies(state, config)
    if not policies or len(policies) > config.max_policies or len({p.id for p in policies}) != len(policies):
        raise ValueError("Policy IDs must be unique and set size must fit max_policies")
    if any(stop.lap < state.current_lap or stop.lap >= state.total_laps for p in policies for stop in p.dry_stops):
        raise ValueError("Scheduled stop boundaries must be between cutoff and finish")
    scenarios = sample_scenarios(state, config)
    traces, means, ranking = _evaluate(state, policies, scenarios, config)
    call = _call_summary(state, policies, means, ranking, config)
    stay, box = (call["best_policies_by_call"][a] for a in ("STAY_OUT", "BOX_NOW"))
    reference = box or policies[0].id
    weights = [s.weight for s in scenarios]
    plans = []
    laps = list(range(state.current_lap, state.total_laps + 1))
    for policy in policies:
        differences = [[trace.times[i] - traces[reference][j].times[i]
                        for j, trace in enumerate(traces[policy.id])] for i in range(len(laps))]
        representative = min(range(len(scenarios)), key=lambda j: abs(traces[policy.id][j].times[-1]
                             - _quantile([t.times[-1] for t in traces[policy.id]], weights, .5)))
        plans.append({"id": policy.id, "label": policy.label, "policy": policy.model_dump(mode="json"),
            "stops": traces[policy.id][representative].stops, "stops_kind": "representative_scenario",
            "laps": laps, "median": [round(_quantile(v, weights, .5), 4) for v in differences],
            "p10": [round(_quantile(v, weights, .1), 4) for v in differences],
            "p90": [round(_quantile(v, weights, .9), 4) for v in differences],
            "mean_time_to_finish_s": round(means[policy.id], 4) if policy.id in means else None,
            "invalid_probability": round(sum(s.weight for t, s in zip(traces[policy.id], scenarios) if not t.legal), 6),
            "median_position": [_quantile([t.positions[i] for t in traces[policy.id]], weights, .5) for i in range(len(laps))],
            "scenario_stops": [{"rain_lap": s.rain_lap, "weight": s.weight, "stops": t.stops}
                               for t, s in zip(traces[policy.id], scenarios)]})
    comparison = None
    win_rate = None
    if stay and box:
        differences = [[a.times[i] - b.times[i] for a, b in zip(traces[stay], traces[box])]
                       for i in range(len(laps))]
        comparison = {"stay_policy_id": stay, "box_policy_id": box, "laps": laps,
            "sign": "STAY minus BOX; negative means STAY is faster",
            "median": [round(_quantile(v, weights, .5), 4) for v in differences],
            "p10": [round(_quantile(v, weights, .1), 4) for v in differences],
            "p90": [round(_quantile(v, weights, .9), 4) for v in differences]}
        win_rate = round(sum(s.weight for s, a, b in zip(scenarios, traces[stay], traces[box])
                             if a.times[-1] < b.times[-1]), 6)
    result = {"schema_version": 2, "cutoff_lap": state.current_lap, "horizon_lap": state.total_laps,
        "reference": {"id": reference, "units": "seconds", "sign": "positive means slower than reference",
                      "comparison": "paired difference within the same weather scenario"},
        "plans": plans, "ranking": ranking, "recommended": ranking[0],
        "plan_margin_s": round(means[ranking[1]] - means[ranking[0]], 4) if len(ranking) > 1 else None,
        **call, "call_win_rate": win_rate, "call_comparison": comparison,
        "scenarios": _representative_scenarios(state, policies, call, config),
        "decision_basis": "minimum probability-weighted remaining race time among finish-legal policies",
        "flip_thresholds": [], "policy_flip_thresholds": [], "assumptions": _assumptions(state, config), "seed": config.seed}
    if include_flips:
        result["flip_thresholds"], result["policy_flip_thresholds"] = _flips(state, policies, config, ranking[0], call["call"])
    return result


def _representative_scenarios(state, policies, call, config):
    probability = 1.0 if state.observed_weather.rainfall.value else state.weather_forecast.rain_probability.value
    eta = state.weather_forecast.expected_arrival_laps.value
    rain_lap = state.current_lap if state.observed_weather.rainfall.value else (
        max(state.current_lap + 1, state.current_lap + int(eta)) if eta is not None else None)
    definitions = [("rain_at_eta", "Rain at forecast ETA", probability, rain_lap),
                   ("stays_dry", "Stays dry", 1 - probability, None)]
    selected = set(pid for pid in call["best_policies_by_call"].values() if pid)
    results = []
    for sid, label, mass, arrival in definitions:
        if sid == "rain_at_eta" and arrival is None:
            continue
        projected = []
        for policy in policies:
            if policy.id not in selected:
                continue
            trace = simulate_policy(state, policy, Scenario(arrival, 0, 1), config)
            projected.append({"policy_id": policy.id, "laps": list(range(state.current_lap, state.total_laps + 1)),
                "cumulative_time": [round(t, 4) for t in trace.times], "stops": trace.stops,
                "finish_legal": trace.legal})
        results.append({"id": sid, "label": label, "probability": round(mass, 12),
            "probability_kind": "weather branch mass, not probability of this exact ETA",
            "rain_lap": arrival, "pit_offset_s": 0, "plans": projected})
    return results


def _assumptions(state, config):
    values = [("rain_probability", state.weather_forecast.rain_probability.value, "forecast"),
              ("rain_arrival_lap", state.current_lap + state.weather_forecast.expected_arrival_laps.value
               if state.weather_forecast.expected_arrival_laps.value is not None else None, "forecast"),
              ("rain_intensity", state.weather_forecast.intensity.value, "forecast"),
              ("current_rainfall", state.observed_weather.rainfall.value, "measured"),
              ("subject_last_lap_s", state.subject_driver.last_lap_time_s, "measured"),
              ("subject_compound", state.subject_driver.current_compound.value, "measured"),
              ("subject_tyre_age", state.subject_driver.stint_length_laps, "measured"),
              ("previously_used_compounds", [c.value for c in state.subject_driver.used_compounds], "measured"),
              ("track_status_at_cutoff", state.track_status.value, "measured"),
              ("rivals_at_cutoff", [r.model_dump(mode="json") for r in state.competitors], "measured"),
              ("derived_degradation_s_per_lap", state.derived_pace.degradation_rate_s_per_lap.value, "measured"),
              ("green_pit_loss_s", state.pit_loss.green_pit_loss_s, "config"),
              ("vsc_pit_loss_s", state.pit_loss.vsc_pit_loss_s, "config"),
              ("sc_pit_loss_s", state.pit_loss.sc_pit_loss_s, "config"),
              ("tyre_specs", {c.value: TyreModel.get_compound_specs(c).model_dump(mode="json") for c in TireCompound}, "config")]
    values.extend((name, value, "config") for name, value in config.model_dump(mode="json").items())
    return [{"name": name, "value": value, "kind": kind} for name, value, kind in values]


def _flips(state, policies, config, current_best, current_call):
    eta = state.weather_forecast.expected_arrival_laps.value
    sweep_definitions = [
        ("rain_arrival_lap", state.current_lap + eta if eta is not None else None,
         [state.current_lap + offset for offset in config.rain_sweep_offsets if 1 <= offset <= state.total_laps - state.current_lap], "laps"),
        ("rain_probability", state.weather_forecast.rain_probability.value,
         list(config.rain_probability_sweep), "probability"),
        ("pit_loss_s", state.pit_loss.green_pit_loss_s, list(config.pit_loss_sweep_s), "seconds"),
        ("safety_car_lap", config.safety_car_lap,
         [state.current_lap + offset for offset in config.safety_car_sweep_offsets if offset >= 1], "laps"),
    ]
    results, policy_results = [], []
    for name, current, grid, units in sweep_definitions:
        configured_grid = sorted(set(grid))
        steps = [round(b - a, 8) for a, b in zip(configured_grid, configured_grid[1:])]
        resolution = steps[0] if steps and len(set(steps)) == 1 else None
        if name == "rain_probability" and eta is None and not state.observed_weather.rainfall.value:
            unavailable = {"assumption": name, "current": current, "flips_at": None, "flips_to": None,
                "status": "unavailable: rain ETA missing", "range": [grid[0], grid[-1]] if grid else [],
                "resolution": resolution, "units": units, "includes_no_rain": False,
                "transitions": [], "sweep": []}
            results.append(unavailable)
            policy_results.append(dict(unavailable))
            continue
        if current is not None:
            grid.append(current)
        grid = sorted(set(grid))
        if name == "rain_arrival_lap":
            grid.append("no rain")
        evaluated = []
        for value in grid:
            trial, cfg = state, config
            if name == "rain_arrival_lap":
                field = "rain_probability" if value == "no rain" else "expected_arrival_laps"
                number = 0 if value == "no rain" else value - state.current_lap
                forecast = state.weather_forecast.model_copy(update={field:
                    getattr(state.weather_forecast, field).model_copy(update={"value": number})})
                trial = state.model_copy(update={"weather_forecast": forecast})
                if value == "no rain":
                    observed = state.observed_weather.model_copy(update={"rainfall":
                        state.observed_weather.rainfall.model_copy(update={"value": False})})
                    trial = trial.model_copy(update={"observed_weather": observed})
            elif name == "rain_probability":
                forecast = state.weather_forecast.model_copy(update={"rain_probability":
                    state.weather_forecast.rain_probability.model_copy(update={"value": value})})
                trial = state.model_copy(update={"weather_forecast": forecast})
            elif name == "pit_loss_s":
                trial = state.model_copy(update={"pit_loss": state.pit_loss.model_copy(update={"green_pit_loss_s": value})})
            else:
                cfg = config.model_copy(update={"safety_car_lap": value})
            _, means, ranking = _evaluate(trial, policies, sample_scenarios(trial, cfg), cfg)
            summary = _call_summary(trial, policies, means, ranking, cfg)
            evaluated.append({"value": value, "recommended": ranking[0], **summary})
        for key, current_winner, destination, level in (
                ("call", current_call, results, "call"),
                ("recommended", current_best, policy_results, "plan")):
            transitions = [{"from_value": a["value"], "to_value": b["value"],
                            f"from_{level}": a[key], f"to_{level}": b[key]}
                           for a, b in zip(evaluated, evaluated[1:]) if a[key] != b[key]]
            changed = [entry for entry in evaluated if entry[key] != current_winner]
            numeric = [entry for entry in changed if isinstance(entry["value"], (int, float))]
            nearest = (min(numeric, key=lambda entry: abs(entry["value"] - current))
                       if numeric and current is not None else (changed[0] if changed else None))
            numeric_grid = [v for v in grid if isinstance(v, (int, float))]
            destination.append({"assumption": name, "current": current,
                "flips_at": nearest["value"] if nearest else None,
                "flips_to": nearest[key] if nearest else None,
                "status": "change found on grid" if nearest else "no flip in range",
                "range": [numeric_grid[0], numeric_grid[-1]] if numeric_grid else [],
                "resolution": resolution, "units": units,
                "includes_no_rain": name == "rain_arrival_lap",
                "transitions": transitions, "sweep": evaluated})
    return results, policy_results
