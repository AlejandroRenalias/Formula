# Formula strategy models

## Legacy specialist scorer

The scorer produces dimensionless heuristic points, not predicted race time.
`score_margin` is the winner's score minus the runner-up's score. It replaces
the misleading name `expected_advantage_s`; the JSON contract uses the new name.
Weights remain unchanged. Scorer output is retained for specialist explanations.

Known limitations:

- Green-flag pit loss is available in seconds but contributes zero scoring points.
  STAY receives +1 raw point for preserving track position. SC/VSC rewards are
  fixed points, not a time calculation.
- Rejoin gaps below 1.5s receive -2 traffic points; above 4s receive +1.2
  clean-air points. Between these thresholds, including a P1-to-P3 rejoin at
  3.5s, there is no traffic score. Position loss is not directly scored.
- Rain at probability >=60% and ETA <=2 laps enters an imminent-rain branch.
  ETA >=3 receives the dry baseline despite forecast rain. Dry baseline weather
  is the same offset for all slick/STAY candidates. Pre-emptive intermediates
  receive a fixed reward without simulating their dry-running time cost.
- Compound progress receives +2 raw points only for a new dry compound or a
  wet compound establishing the existing exemption semantics. This remains an
  immediate-compliance heuristic, not a calculation of a later stop's cost.

The separate projection must enforce compound compliance through the finish,
charge stop losses in seconds, and evaluate weather-reactive policies.

## Projection and decision contract

`src.calculators.projection.project` projects policies to `state.total_laps`.
`src.orchestrator.projection_pipeline.run_projection_cycle` is the engine entry
point for the new decision contract: `recommended` is the finish-legal policy
with the lowest probability-weighted remaining race time. `plan_margin_s` is its
expected-time advantage over the second policy, not a score or a difference
between medians. The existing StrategyPipeline remains usable for compatibility;
its serialized output is attached under `scorer` as reasoning only. The
`disagreement` object compares initial actions and compounds across scenarios;
it includes their probability distribution and the probability of disagreeing
with the scorer. Neither module changes the UI.

### Lap boundary and policies

- The cutoff is the end of the completed lap. Every time series starts at zero
  there. A stop with `lap=18` occurs after lap 18 and its entire cost is charged
  to projected lap 19. There is no fictitious elapsed-time drop at the cutoff.
- A policy has scheduled **dry** stops and an optional weather reaction. At each
  projected lap it sees current simulated wetness, not the sampled future ETA.
  It switches when a fresh wet compound beats fresh HARD on compound plus
  weather loss. Weather overrides that lap's scheduled dry stop; once on wet
  tyres, later dry stops are skipped because rain persists in this model.
- Default policies: BOX now; four alternative dry deadlines on a four-lap grid;
  one two-stop dry alternative. The set is capped at six. Every policy has at
  most two more stops, including reactive stops. No exhaustive strategy search
  or tyre inventory is modelled. A policy exhausting its stop budget keeps its
  existing tyres and pays their continuing weather/wear costs.
- Finish legality requires two distinct dry compounds across past and projected
  use, or actual use of INTERMEDIATE/WET. Forecast rain alone grants no exemption.
  A policy illegal in any positive-probability scenario is excluded from ranking;
  its series and `invalid_probability` remain visible. No legal policy raises an
  explicit error. These are the project's existing simplified rule semantics,
  not a complete sporting-regulations implementation.
- Schema version 2 separates the immediate `call` (STAY_OUT / BOX_NOW) from the
  winning policy. `best_policies_by_call` identifies the lowest expected-time
  legal policy in each action group. `call_margin_s` is the nonnegative expected
  time advantage of the winning action over the best opposite-action policy.
  `call_win_rate` is always the probability-weighted share of paired samples in
  which that best STAY policy beats that best BOX policy, even when BOX wins on
  expected time. Exact ties do not count as STAY wins. Missing action groups
  yield null call margin, win rate, and comparison; the available action wins.
  Policies are selected by expected time once, not re-optimized in each sample.
- The initial action is committed using scheduled cutoff stops and weather
  already observed at the cutoff. Sampled future rain cannot trigger an initial
  stop. Subsequent weather reactions retain the coarse per-lap crossover model.

### Lap times

`lap_time = base_pace + compound_offset + linear_wear + cliff_wear
            - fuel_effect * laps_since_cutoff + traffic + weather + stop_loss`

- Compound offsets, wear rates, life, and cliff ages come from existing
  `TyreModel` specifications. `TyreModel.lap_delta_s` applies linear wear and a
  configurable extra 0.15s per lap beyond the cliff. Age is measured at the start
  of the running segment; a new set starts at zero and ages after each lap.
- Unless explicitly configured, the current compound's degradation rate is
  re-estimated with `PaceModel` from physically cutoff-filtered clean laps. The
  ratio to that compound's default rate scales all compounds. This is a simple
  cross-compound assumption, not an independently fitted rate for each tyre.
- Base pace is the last known subject lap time minus its modelled compound/wear
  loss, or a configured value. No extra future data is loaded. A traffic-affected
  or pit-affected last lap can distort this anchor; no robust pace fit is claimed.
  Fuel gain defaults to 0.05s per projected lap and is common across policies.
- `PitLossModel` supplies cutoff green/VSC/SC loss, plus a shared sampled offset.
  Defaults are the existing 21.5/12.5/9.5s. No warm-up, pit-lane queue, or split
  in-lap/out-lap cost is modelled. Costs are applied in full at every stop.

### Weather and traffic

- Occurrence branches have exactly forecast probability and its complement.
  Seeded conditional ETA offsets are uniform integers within +/-2 laps; pit
  offsets are uniform within +/-1.5s. There are 32 draws per nonzero branch. Each
  policy sees the same draws and weights. This is stratified Monte Carlo, not
  repeated independent weather draws per policy. The probability itself is a
  fixed forecast input, not a separately sampled probability estimate.
- Wetness rises linearly over two laps from sampled arrival to 0.7 for LIGHT or
  1.0 otherwise. Rain persists to the finish. Already-observed rainfall forces
  occurrence. No drying, spatial rainfall, forecast updates, or rain duration is
  modelled. Arrival outside the horizon produces no in-horizon wetness.
- `WeatherModel.projection_penalty_s` adds 18s * wetness on slicks;
  8s * (1-wetness) on intermediates; 14s * (1-wetness) on wets; and an additional
  8s * wetness on intermediates in HEAVY rain. Existing wet-tyre base offsets
  (6.5/12s) are also charged. These are configurable teaching assumptions,
  not calibrated crossover data. There is no ETA threshold in the projection.
- Rivals start with observed gaps/tyres/ages/last pace; missing last pace uses the
  subject's. Their base pace is anchored similarly. They react to crossover or
  switch dry compound at the existing tyre-life limit, at most twice. These rival
  policies are assumptions, not knowledge of future real stops. Rival compound
  compliance is not checked; rivals do not receive mutual traffic penalties.
- The subject pays 0.4s for a lap when, after stop losses, it is within 1s behind
  a projected rival whose free-running pace is no slower. The penalty is charged
  once, not per car. Sorting cumulative race-time offsets produces positions;
  there is no position bonus, overtaking manoeuvre model, DRS, or pack compression.
  Unknown cars ahead retain a fixed count. Position arrays are illustrative
  consequences, not the optimization objective.
- Cutoff track status persists unless a configured SC scenario replaces it with
  a two-lap SC window and otherwise green. SC affects stop cost only; no pace cap
  or field bunching. This makes SC sweeps stop-cost experiments, not full SC sims.

### Series, thresholds and reproducibility

- `reference` is the best BOX policy when available, otherwise the first supplied
  policy. Each sample's cumulative time is
  differenced against that reference **within the same scenario**, then weighted
  median/p10/p90 are computed. Positive = slower than reference. Reference bands
  are therefore zero. These are model sensitivity bands, not calibrated confidence
  intervals; they need not grow monotonically. Absolute expected finish times
  are also returned. A plotted short window must not change the finish ranking.
- `call_comparison` contains paired STAY-minus-BOX median/p10/p90 time differences
  between the two best action policies, with negative meaning STAY is faster.
  These bands are uncertainty in the difference, not quantiles of separate
  absolute trajectories. `scenarios` supplies distinct rain-at-forecast-ETA and
  stays-dry absolute cumulative-time paths from zero at cutoff, plus exact stops,
  using those same two policies and zero pit-loss offset. Scenario probability
  is the rain/dry branch mass, not the probability of that exact ETA. Zero-mass
  branches remain as hypothetical illustrations. If ETA is unavailable the rain
  illustration is omitted rather than inventing an arrival.
- `stops` is a labelled representative scenario, not the universal stop sequence.
  `policy` contains decision rules; `scenario_stops` records every realized stop
  schedule and weight. Realized stops identify both boundary and charged lap.
- Flip sweeps use the same seed and policies, re-selecting the best policy in each
  action group at each value. Primary `flip_thresholds` reports call changes;
  secondary `policy_flip_thresholds` reports policy changes. Rain arrival defaults
  to cutoff+1 through cutoff+34, bounded by the finish, at one-lap resolution and
  adds an explicit `no rain` endpoint (occurrence probability zero). This endpoint
  overrides current rainfall only for that counterfactual experiment. Probability
  covers 0-1 in 0.1 steps; green pit loss covers 5-45s in 5s steps; SC onset covers
  cutoff+1 to cutoff+12. Current values are included. Other assumptions stay fixed.
  All winner-change brackets are reported. `flips_at` is the nearest **sampled**
  value whose winner differs from the current winner, not an exact root; multiple
  transitions are possible. `no flip in range` says nothing beyond that range.
  Each sweep reports its numeric range, configured resolution (null if irregular),
  units, complete evaluated grid, and whether no rain is included. Inserting the
  current value may create a smaller local interval. The probability sweep
  cannot undo already-observed rainfall, which forces occurrence in the model.
  With no forecast ETA and no observed rain it is explicitly unavailable;
  positive rain probabilities cannot be tested without inventing arrival data.
- Parameters and cutoff-derived inputs are serialized under `assumptions`.
  The `measured` kind includes metrics derived from measured/synthetic snapshot
  inputs; it does not imply real-world provenance. The fixture also stores its
  full source state, provenance, config, and generation command. No live services
  or paid models are used by this projection.

This model is intentionally small and uncalibrated. Sanity cases validate its
internal mechanics and expected qualitative behaviour, not race prediction accuracy.
