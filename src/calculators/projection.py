"""Deterministic shared-scenario race-time projection alongside the legacy scorer."""
from dataclasses import dataclass
from math import isfinite, ceil
from random import Random

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
    pit_in_lap_fraction: float = Field(default=1.0, ge=0, le=1)
    degradation_spread_fraction: float = Field(default=0.15, ge=0, le=1)
    call_tolerance_s: float = Field(default=1.0, ge=0)
    wetness_ramp_laps: float = Field(default=2.0, gt=0)
    light_rain_wetness: float = Field(default=0.7, gt=0, le=1)
    fuel_effect_s_per_lap: float = Field(default=0.05, ge=0)
    race_trend_s_per_lap: float | None = None
    cliff_rate_s: float = Field(default=0.15, ge=0)
    degradation_rates_s_per_lap: dict[str, float] = Field(default_factory=dict)
    compound_offsets_s: dict[str, float] = Field(default_factory=dict)
    degradation_scale: float | None = Field(default=None, ge=0)
    base_pace_s: float | None = Field(default=None, gt=0)
    base_pace_sigma_s: float = Field(default=0.0, ge=0)
    lap_noise_sigma_s: float = Field(default=0.0, ge=0)
    base_pace_uncertainty_multiplier: float = Field(default=1.0, gt=0)
    lap_noise_uncertainty_multiplier: float = Field(default=1.0, gt=0)
    slick_wet_penalty_s: float = Field(default=18.0, ge=0)
    inter_dry_penalty_s: float = Field(default=8.0, ge=0)
    wet_dry_penalty_s: float = Field(default=14.0, ge=0)
    heavy_inter_penalty_s: float = Field(default=8.0, ge=0)
    traffic_gap_s: float = Field(default=1.0, gt=0)
    traffic_penalty_s: float = Field(default=0.4, ge=0)
    dry_grid_step_laps: int = Field(default=4, ge=1)
    max_policies: int = Field(default=9, ge=2, le=20)
    future_sc_probability: float = Field(default=0.0, ge=0, le=1)
    future_vsc_probability: float = Field(default=0.0, ge=0, le=1)
    sc_duration_prior_s: tuple[float, ...] = ()
    vsc_duration_prior_s: tuple[float, ...] = ()
    sc_pace_multiplier: float = Field(default=1.0, ge=1)
    vsc_pace_multiplier: float = Field(default=1.0, ge=1)
    ongoing_neutralization_laps: int | None = Field(default=None, ge=0)
    safety_car_lap: int | None = Field(default=None, ge=1)
    safety_car_duration_laps: int = Field(default=2, ge=1)
    safety_car_pack_gap_s: float = Field(default=0.5, ge=0)
    safety_car_pace_delay_s: float = Field(default=20.0, ge=0)
    safety_car_min_benefit_s: float = Field(default=0.5, ge=0)
    rain_sweep_offsets: tuple[int, ...] = tuple(range(1, 35))
    rain_probability_sweep: tuple[float, ...] = tuple(v / 10 for v in range(11))
    pit_loss_sweep_s: tuple[float, ...] = (5., 6., 7., 8., 10., 15., 20., 25., 30., 35., 40., 45.)
    safety_car_sweep_offsets: tuple[int, ...] = tuple(range(1, 13))

    @model_validator(mode="after")
    def valid_sweep_ranges(self):
        if any(c not in {x.value for x in DRY} or not isfinite(v) for c,v in self.compound_offsets_s.items()):
            raise ValueError("Compound offsets require dry compounds and finite values")
        if self.race_trend_s_per_lap is not None and not isfinite(self.race_trend_s_per_lap):
            raise ValueError("Race trend must be finite")
        if any(c not in {x.value for x in DRY} or not isfinite(v) or v < 0
               for c,v in self.degradation_rates_s_per_lap.items()):
            raise ValueError("Compound wear overrides require dry compounds and finite nonnegative rates")
        if self.future_sc_probability + self.future_vsc_probability > 1:
            raise ValueError("Combined neutralization probability exceeds one")
        for probability, durations in ((self.future_sc_probability, self.sc_duration_prior_s),
                                       (self.future_vsc_probability, self.vsc_duration_prior_s)):
            if probability and not durations or any(not isfinite(d) or d <= 0 for d in durations):
                raise ValueError("Positive neutralization risk requires positive finite durations")
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
    degradation_multiplier: float = 1.0
    base_pace_offset_s: float = 0.0
    lap_noise_s: tuple[float, ...] = ()
    neutralization_events: tuple[tuple[int, str, int], ...] = ()


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
        if len(policies) >= min(5, config.max_policies):
            break
    first = state.current_lap + config.dry_grid_step_laps
    second = first + 4 * config.dry_grid_step_laps
    other = TireCompound.MEDIUM if compound == TireCompound.HARD else TireCompound.HARD
    # Add matched variants as pairs: neither immediate action gets a larger
    # second-stop search space just because its initial stop is earlier/later.
    for later in (second, second - config.dry_grid_step_laps):
        if len(policies) + 2 <= config.max_policies and first < later < state.total_laps:
            for initial, pid in ((state.current_lap, f"box_two_stop_{later}"),
                                 (first, f"two_stop_{first}_{later}")):
                policies.append(Policy(id=pid, label=f"Two dry stops after laps {initial} and {later}; react to rain",
                    dry_stops=(Stop(lap=initial, compound=compound), Stop(lap=later, compound=other))))
    if len(policies) == 1:
        policies.append(Policy(id="stay", label="STAY; switch at crossover", dry_stops=()))
    used = set(state.subject_driver.used_compounds) | {state.subject_driver.current_compound}
    if used & WET or len(used & DRY) >= 2:
        # One reserved extra slot: never displace an existing search candidate.
        policies.append(Policy(id="stay_to_finish", label="STAY to the finish",
                               react_to_weather=False, max_stops=0))
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
    # Separate stream preserves paired weather/pit draws when wear spread changes.
    wear_rng = Random(config.seed + 1)  # nosec B311
    wear_draws = [wear_rng.uniform(1 - config.degradation_spread_fraction,
                                  1 + config.degradation_spread_fraction) for _ in draws]
    # Independent streams preserve the existing weather, pit and wear samples.
    # Antithetic normal pairs center the added finite sample at zero; the same
    # subject realization is shared across policies and weather branches.
    def normal_draws(seed, sigma, length):
        random = Random(seed)  # nosec B311
        values = []
        for _ in range((len(draws) + 1) // 2):
            vector = tuple(random.gauss(0, sigma) for _ in range(length))
            values.extend((vector, tuple(-v for v in vector)))
        return values[:len(draws)]

    pace_draws = normal_draws(config.seed + 2, config.base_pace_sigma_s, 1)
    noise_draws = (normal_draws(config.seed + 3, config.lap_noise_sigma_s,
                              state.total_laps - state.current_lap)
                   if config.lap_noise_sigma_s else [() for _ in draws])
    event_draws = [_sample_neutralizations(state, config, i) for i in range(len(draws))]
    for rains, mass in ((False, 1 - probability), (True, probability)):
        if mass <= 0:
            continue
        for (offset, pit_offset), wear, pace, noise, events in zip(draws, wear_draws, pace_draws, noise_draws, event_draws):
            rain_lap = (state.current_lap if state.observed_weather.rainfall.value else
                        max(state.current_lap + 1, state.current_lap + int(eta) + offset)) if rains else None
            scenarios.append(Scenario(rain_lap, pit_offset, mass / len(draws), wear,
                pace[0] * config.base_pace_uncertainty_multiplier,
                tuple(v * config.lap_noise_uncertainty_multiplier for v in noise), events))
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


def _sample_neutralizations(state, config, index):
    """Independent shared-policy timeline; only frozen priors and cutoff inputs."""
    if not (config.future_sc_probability or config.future_vsc_probability):
        return ()
    rng = Random(config.seed + 1000 + index)  # nosec B311
    events = []
    lap = state.current_lap + 1
    green_pace = (config.base_pace_s or state.subject_driver.last_lap_time_s) + TyreModel.lap_delta_s(
        state.subject_driver.current_compound, state.subject_driver.stint_length_laps,
        degradation_rate_s_per_lap=config.degradation_rates_s_per_lap.get(state.subject_driver.current_compound.value),
        compound_offset_s=config.compound_offsets_s.get(state.subject_driver.current_compound.value))
    while lap <= state.total_laps:
        if _status(state, lap, config) in (TrackStatus.SAFETY_CAR, TrackStatus.VSC):
            lap += 1
            continue
        draw = rng.random()
        kind = ('SC' if draw < config.future_sc_probability else
                'VSC' if draw < config.future_sc_probability + config.future_vsc_probability else None)
        if kind:
            durations = config.sc_duration_prior_s if kind == 'SC' else config.vsc_duration_prior_s
            factor = config.sc_pace_multiplier if kind == 'SC' else config.vsc_pace_multiplier
            duration = max(1, ceil(rng.choice(durations) / (green_pace * factor)))
            events.append((lap, kind, duration))
            lap += duration
        else:
            lap += 1
    return tuple(events)


def _status(state, boundary, config, scenario=None):
    if scenario is not None:
        for start, kind, duration in scenario.neutralization_events:
            if start <= boundary < start + duration:
                return TrackStatus.SAFETY_CAR if kind == 'SC' else TrackStatus.VSC
    if config.safety_car_lap is None:
        if (config.ongoing_neutralization_laps is not None and state.track_status in
                (TrackStatus.SAFETY_CAR, TrackStatus.VSC)):
            return state.track_status if boundary <= state.current_lap+config.ongoing_neutralization_laps else TrackStatus.GREEN
        return state.track_status
    return (TrackStatus.SAFETY_CAR if config.safety_car_lap <= boundary <
            config.safety_car_lap + config.safety_car_duration_laps else TrackStatus.GREEN)


def _pit_loss(state, scenario, lap, config):
    status = state.track_status
    if config.future_sc_probability or config.future_vsc_probability:
        status = _status(state, lap, config, scenario)
    # Stop at boundary 18 is committed before hypothetical SC onset 19.
    elif lap > state.current_lap + 1:
        status = _status(state, lap - 1, config)
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
            "call_margin_s": abs(means[stay] - means[box]) if stay and box else None}


def _sc_opportunity(state, policy, scenario, config, lap, compound, age, stops, remaining, wetness, scale):
    """Local forecast-based cost check, never given the sampled future rain lap."""
    if len(stops) >= policy.max_stops:
        return None
    crossover = _wet_compound(state, wetness, config) if policy.react_to_weather else None
    candidates = [crossover] if crossover is not None else [TireCompound.HARD, TireCompound.MEDIUM]
    if policy.react_to_weather and crossover is None:
        candidates.append(TireCompound.INTERMEDIATE)
    probability = 1.0 if wetness > 0 else state.weather_forecast.rain_probability.value
    eta = state.weather_forecast.expected_arrival_laps.value
    arrival = lap if wetness > 0 else max(lap, state.current_lap + eta) if eta is not None else None
    branches = [(None, 1 - probability), (arrival, probability)]
    cheap = _pit_loss(state, Scenario(None, 0, 1), lap, config)
    green = state.pit_loss.green_pit_loss_s
    known_scale = scale / scenario.degradation_multiplier if scenario.degradation_multiplier else 0

    def cost(target):
        expected = 0.0
        for rain_lap, weight in branches:
            if weight == 0:
                continue
            c, tyre_age, count = compound, age, len(stops)
            used = set(state.subject_driver.used_compounds) | {state.subject_driver.current_compound, compound}
            used.update(TireCompound(s["compound"]) for s in stops)
            scheduled = list(remaining)
            total = 0.0
            if target is not None:
                c, tyre_age, count, total = target, 0, count + 1, cheap
                used.add(target)
                if scheduled and scheduled[0].compound == target:
                    scheduled.pop(0)  # Advance that dry stop rather than add one.
            for future in range(lap, state.total_laps + 1):
                w = _wetness(state, Scenario(rain_lap, 0, 1), future, config)
                wet = _wet_compound(state, w, config) if policy.react_to_weather else None
                dry = next((s.compound for s in scheduled if s.lap == future - 1), None)
                change = wet if wet is not None and c != wet else (dry if wet is None and c not in WET else None)
                future_loss = _pit_loss(state, Scenario(None, 0, 1), future, config)
                # In a forecast branch with rain already observed, reserve the
                # cheap SC stop for a wet switch if its early-running cost is less
                # than the SC discount. Otherwise a slick stop can look beneficial
                # only because the rollout incorrectly prices the next wet stop green.
                if (future > lap and change is None and policy.react_to_weather and w > 0 and c in DRY
                        and _status(state, future - 1, config) == TrackStatus.SAFETY_CAR):
                    early_cost = 0.0
                    for ahead in range(future, state.total_laps + 1):
                        ahead_w = _wetness(state, Scenario(rain_lap, 0, 1), ahead, config)
                        if _wet_compound(state, ahead_w, config) is not None:
                            break
                        if _status(state, ahead, config) == TrackStatus.SAFETY_CAR:
                            continue
                        early_cost += max(0, TyreModel.get_compound_specs(TireCompound.INTERMEDIATE).base_pace_delta_s
                            + _weather_delta(TireCompound.INTERMEDIATE, ahead_w, state, config)
                            - TyreModel.get_compound_specs(c).base_pace_delta_s - _weather_delta(c, ahead_w, state, config))
                    if green - future_loss > early_cost:
                        change = TireCompound.INTERMEDIATE
                if future == lap and target is not None:
                    change = None
                if change is not None and count < policy.max_stops:
                    c, tyre_age, count = change, 0, count + 1
                    used.add(change)
                    total += future_loss
                if _status(state, future, config) != TrackStatus.SAFETY_CAR:
                    total += TyreModel.lap_delta_s(c, tyre_age, known_scale,
                        config.cliff_rate_s, config.degradation_rates_s_per_lap.get(c.value), config.compound_offsets_s.get(c.value)) + _weather_delta(c, w, state, config)
                tyre_age += 1
            if not (used & WET) and len(used & DRY) < 2:
                return float("inf")
            expected += total * weight
        return expected

    baseline = cost(None)
    costs = {candidate: cost(candidate) for candidate in candidates}
    best = min(costs, key=costs.get)
    return best if isfinite(costs[best]) and baseline - costs[best] > config.safety_car_min_benefit_s else None


def simulate_policy(state: RaceState, policy: Policy, scenario: Scenario,
                    config: ProjectionConfig, *, fixed_schedule: bool = False,
                    green_segments: list | None = None) -> Trace:
    """Project from the completed-lap boundary to the finish; no scored bonuses.

    fixed_schedule disables autonomous SC stops for conditional actual-plan
    evaluation. Weather reactions remain governed by the supplied policy.
    """
    remaining_laps = state.total_laps - state.current_lap
    if scenario.lap_noise_s and len(scenario.lap_noise_s) != remaining_laps:
        raise ValueError("Per-lap noise must cover exactly the remaining race")
    if not all(isfinite(v) for v in (scenario.base_pace_offset_s, *scenario.lap_noise_s)):
        raise ValueError("Pace uncertainty draws must be finite")
    subject = state.subject_driver
    scale = config.degradation_scale
    if scale is None:
        scale = state.derived_pace.degradation_rate_s_per_lap.value / TyreModel.get_compound_specs(subject.current_compound).degradation_base_rate_s_per_lap
    if not isfinite(scale):
        raise ValueError("Degradation must be finite")
    scale *= scenario.degradation_multiplier
    delta = lambda c, age: TyreModel.lap_delta_s(c, age, scale, config.cliff_rate_s * scenario.degradation_multiplier,
                                                   config.degradation_rates_s_per_lap.get(c.value), config.compound_offsets_s.get(c.value))
    base = config.base_pace_s if config.base_pace_s is not None else subject.last_lap_time_s - delta(subject.current_compound, subject.stint_length_laps)
    rivals = [{"time": -r.gap_to_subject_s, "compound": r.current_compound, "age": r.tyre_age_laps,
               "base": (r.last_lap_time_s if r.last_lap_time_s is not None else subject.last_lap_time_s)
                       - delta(r.current_compound, r.tyre_age_laps), "stops": 0, "pending_pit_loss": 0.0} for r in state.competitors]
    # Missing competitors retain an anonymous fixed count ahead, not invented pace.
    missing_ahead = max(0, subject.position - 1 - sum(r.gap_to_subject_s > 0 for r in state.competitors))
    compound, age = subject.current_compound, subject.stint_length_laps
    used = set(subject.used_compounds) | {compound}
    times, positions, stops = [0.0], [subject.position], []
    consumed_dry_laps = set()
    compressed = False
    total = 0.0
    pending_pit_loss = 0.0
    green_prefix = True
    for lap in range(state.current_lap + 1, state.total_laps + 1):
        running_status = _status(state, lap, config, scenario)
        running_sc = running_status == TrackStatus.SAFETY_CAR
        prior_effects = bool(config.future_sc_probability or config.future_vsc_probability)
        if prior_effects and not running_sc:
            compressed = False
        if running_sc and not compressed:
            # Instant pack compression precedes this lap's running/stop costs.
            ordered = sorted([(total, -1)] + [(r["time"], i) for i, r in enumerate(rivals)])
            leader = (total - next(i for i, (_, index) in enumerate(ordered) if index == -1)
                      * config.safety_car_pack_gap_s) if prior_effects else ordered[0][0]
            for position, (_, index) in enumerate(ordered):
                packed = leader + position * config.safety_car_pack_gap_s
                if index == -1:
                    total = packed
                else:
                    rivals[index]["time"] = packed
            compressed = True
        wetness = _wetness(state, scenario, lap, config)
        crossover = _wet_compound(state, wetness, config) if policy.react_to_weather else None
        remaining = [s for s in policy.dry_stops if s.lap >= lap - 1 and s.lap not in consumed_dry_laps]
        scheduled = next((stop.compound for stop in remaining if stop.lap == lap - 1), None)
        target = crossover if crossover is not None and compound != crossover else (
            scheduled if crossover is None and compound not in WET else None)
        if lap == state.current_lap + 1:
            target = _cutoff_target(state, policy, config)
        opportunistic = False
        if (not fixed_schedule and lap > state.current_lap + 1
                and _status(state, lap - 1, config, scenario) == TrackStatus.SAFETY_CAR and target is None):
            target = _sc_opportunity(state, policy, scenario, config, lap, compound, age, stops, remaining, wetness, scale)
            opportunistic = target is not None
            if target is not None and remaining and remaining[0].compound == target:
                consumed_dry_laps.add(remaining[0].lap)
        loss, pending_pit_loss = pending_pit_loss, 0.0
        if target is not None and len(stops) < policy.max_stops:
            compound, age = target, 0
            used.add(compound)
            total_loss = _pit_loss(state, scenario, lap, config)
            # Keep the entry-time sampled total/status. Defer only its allocation,
            # never reprice the out-lap using a later status or a second pit draw.
            share = config.pit_in_lap_fraction if lap < state.total_laps else 1.0
            in_loss = total_loss * share
            pending_pit_loss = total_loss - in_loss
            loss += in_loss
            record = {"lap": lap - 1, "charged_on_lap": lap, "compound": compound.value,
                      "pit_loss_s": total_loss,
                      "reason": "safety_car_opportunity" if opportunistic else "weather_or_schedule"}
            if config.pit_in_lap_fraction != 1.0:
                record.update(in_lap_loss_s=in_loss, out_lap_loss_s=pending_pit_loss,
                              out_lap=lap+1 if pending_pit_loss else None)
            stops.append(record)
        fuel = -(config.race_trend_s_per_lap if config.race_trend_s_per_lap is not None else -config.fuel_effect_s_per_lap) * (lap - state.current_lap)
        noise = scenario.lap_noise_s[lap - state.current_lap - 1] if scenario.lap_noise_s else 0.0
        nominal_pace = base + delta(compound, age) - fuel + _weather_delta(compound, wetness, state, config)
        own_pace = nominal_pace + scenario.base_pace_offset_s + noise
        # Rival policies are explicit model assumptions: crossover or a tyre-life stop.
        rival_paces, rival_losses = [], []
        for rival in rivals:
            c = rival["compound"]
            target_rival = _wet_compound(state, wetness, config)
            if target_rival is None and c in DRY and rival["age"] >= TyreModel.get_compound_specs(c).expected_life_laps:
                target_rival = TireCompound.HARD if c != TireCompound.HARD else TireCompound.MEDIUM
            rival_loss, rival["pending_pit_loss"] = rival["pending_pit_loss"], 0.0
            if target_rival is not None and target_rival != c and rival["stops"] < 2:
                rival["compound"], rival["age"] = target_rival, 0
                rival["stops"] += 1
                total_loss = _pit_loss(state, scenario, lap, config)
                share = config.pit_in_lap_fraction if lap < state.total_laps else 1.0
                in_loss = total_loss * share
                rival["pending_pit_loss"] = total_loss - in_loss
                rival_loss += in_loss
            rival_paces.append(rival["base"] + delta(rival["compound"], rival["age"]) - fuel
                               + _weather_delta(rival["compound"], wetness, state, config))
            rival_losses.append(rival_loss)
        if running_sc:
            # Common neutralized pace prevents fresh-tyre racing under SC.
            neutral_pace = ((base + delta(subject.current_compound, subject.stint_length_laps) - fuel
                             + scenario.base_pace_offset_s + noise) * config.sc_pace_multiplier
                            if prior_effects else max([own_pace] + rival_paces) + config.safety_car_pace_delay_s)
            own_pace = neutral_pace
            rival_paces = [neutral_pace for _ in rivals]
        elif prior_effects and running_status == TrackStatus.VSC:
            own_pace *= config.vsc_pace_multiplier
            rival_paces = [p * config.vsc_pace_multiplier for p in rival_paces]
        green_prefix = green_prefix and running_status not in (TrackStatus.SAFETY_CAR, TrackStatus.VSC)
        if green_segments is not None and green_prefix:
            # Evaluation acceleration observes engine inputs, never changes them.
            # Rival paths are independent of subject noise until a neutralisation.
            green_segments.append((nominal_pace, loss,
                tuple((r['time'], p, cost) for r, p, cost in zip(rivals, rival_paces, rival_losses))))
        traffic = 0.0
        for rival, rival_pace, rival_loss in zip(rivals, rival_paces, rival_losses):
            # Gap at the start of the running segment, after this lap's stop costs.
            gap = total + loss - (rival["time"] + rival_loss)
            if not running_sc and not (prior_effects and running_status == TrackStatus.VSC) and 0 < gap <= config.traffic_gap_s and rival_pace <= own_pace:
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


def _confidence(traces, scenarios, stay, box, tolerance):
    if not stay or not box:
        return None, []
    paired = [(s, b.times[-1] - a.times[-1])
              for s, a, b in zip(scenarios, traces[stay], traces[box])]

    def shares(rows):
        mass = sum(s.weight for s, _ in rows)
        return {"stay_clearly_better": sum(s.weight for s, v in rows if v > tolerance) / mass,
                "box_clearly_better": sum(s.weight for s, v in rows if v < -tolerance) / mass,
                "too_close_to_call": sum(s.weight for s, v in rows if abs(v) <= tolerance) / mass}

    groups = []
    for name, rains in (("rain", True), ("no_rain", False)):
        rows = [(s, v) for s, v in paired if (s.rain_lap is not None) == rains]
        mass = sum(s.weight for s, _ in rows)
        if mass:
            groups.append({"id": name, "probability": mass,
                "expected_stay_advantage_s": sum(s.weight * v for s, v in rows) / mass,
                "p10_stay_advantage_s": _quantile([v for _, v in rows], [s.weight for s, _ in rows], .1),
                "p90_stay_advantage_s": _quantile([v for _, v in rows], [s.weight for s, _ in rows], .9),
                "confidence": shares(rows)})
    return {"tolerance_s": tolerance, **shares(paired)}, groups


def _display_fields(value):
    """Attach 0.1s presentation values without rounding raw calculations."""
    if isinstance(value, list):
        for item in value:
            _display_fields(item)
    elif isinstance(value, dict):
        seconds = {key: ([round(v, 1) for v in number] if isinstance(number, list) else
                         round(number, 1) if isinstance(number, (int, float)) else None)
                   for key, number in value.items()
                   if key.endswith("_s") or key in {"median", "p10", "p90", "cumulative_time"}}
        for key, item in list(value.items()):
            if key != "display":
                _display_fields(item)
        if seconds:
            value["display"] = seconds


def project(state: RaceState, policies: tuple[Policy, ...] | None = None,
            config: ProjectionConfig | None = None, include_flips: bool = True) -> dict:
    config = config or ProjectionConfig()
    state = _snapshot(state, config)
    default_search = policies is None
    policies = policies if policies is not None else default_policies(state, config)
    policy_cap = config.max_policies + int(default_search and any(p.id == "stay_to_finish" for p in policies))
    if not policies or len(policies) > policy_cap or len({p.id for p in policies}) != len(policies):
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
            "laps": laps, "median": [_quantile(v, weights, .5) for v in differences],
            "p10": [_quantile(v, weights, .1) for v in differences],
            "p90": [_quantile(v, weights, .9) for v in differences],
            "mean_time_to_finish_s": means.get(policy.id),
            "invalid_probability": round(sum(s.weight for t, s in zip(traces[policy.id], scenarios) if not t.legal), 6),
            "median_position": [_quantile([t.positions[i] for t in traces[policy.id]], weights, .5) for i in range(len(laps))],
            "scenario_stops": [{"rain_lap": s.rain_lap, "weight": s.weight,
                                "degradation_multiplier": s.degradation_multiplier, "stops": t.stops}
                               for t, s in zip(traces[policy.id], scenarios)]})
    comparison = None
    win_rate = None
    if stay and box:
        differences = [[a.times[i] - b.times[i] for a, b in zip(traces[stay], traces[box])]
                       for i in range(len(laps))]
        comparison = {"stay_policy_id": stay, "box_policy_id": box, "laps": laps,
            "sign": "STAY minus BOX; negative means STAY is faster",
            "median": [_quantile(v, weights, .5) for v in differences],
            "p10": [_quantile(v, weights, .1) for v in differences],
            "p90": [_quantile(v, weights, .9) for v in differences]}
    confidence, groups = _confidence(traces, scenarios, stay, box, config.call_tolerance_s)
    win_rate = confidence["stay_clearly_better"] if confidence else None
    result = {"schema_version": 3, "cutoff_lap": state.current_lap, "horizon_lap": state.total_laps,
        "reference": {"id": reference, "units": "seconds", "sign": "positive means slower than reference",
                      "comparison": "paired difference within the same weather scenario"},
        "plans": plans, "ranking": ranking, "recommended": ranking[0],
        "plan_margin_s": means[ranking[1]] - means[ranking[0]] if len(ranking) > 1 else None,
        **call, "call_win_rate": win_rate, "call_comparison": comparison,
        "call_confidence": confidence, "scenario_group_margins": groups,
        "scenarios": _representative_scenarios(state, policies, call, config),
        "decision_basis": "minimum probability-weighted remaining race time among finish-legal policies",
        "flip_thresholds": [], "policy_flip_thresholds": [], "assumptions": _assumptions(state, config), "seed": config.seed}
    if include_flips:
        result["flip_thresholds"], result["policy_flip_thresholds"] = _flips(state, policies, config, ranking[0], call["call"])
    _display_fields(result)
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
                "cumulative_time": trace.times, "stops": trace.stops,
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
            samples = sample_scenarios(trial, cfg)
            traces, means, ranking = _evaluate(trial, policies, samples, cfg)
            summary = _call_summary(trial, policies, means, ranking, cfg)
            stay, box = (summary["best_policies_by_call"][a] for a in ("STAY_OUT", "BOX_NOW"))
            confidence, groups = _confidence(traces, samples, stay, box, cfg.call_tolerance_s)
            illustrative = _representative_scenarios(trial, policies, summary, cfg)
            margins = []
            if stay and box:
                for scenario in illustrative:
                    finish = {p["policy_id"]: p["cumulative_time"][-1] for p in scenario["plans"]}
                    margins.append({"id": scenario["id"], "stay_advantage_s": finish[box] - finish[stay]})
            evaluated.append({"value": value, "recommended": ranking[0], **summary,
                "call_confidence": confidence, "scenario_group_margins": groups,
                "representative_margins": margins})
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
