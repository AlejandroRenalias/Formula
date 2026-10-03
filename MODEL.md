# Formula strategy models

## Bahrain-only conditional evaluation

The baseline is committed independently in `1597011`. Evaluation uses exact
subject crossing cutoffs, causal raw timing/tyre/weather/status observations,
and the explicitly labelled same-lap rival crossing gap proxy. The subject's
actual future stop schedule is a conditional outcome treatment, never a state
feature. Rivals retain the engine's own causal stop assumptions. All runs load
hash-verified local Bahrain 2021 data with network connections blocked. Spain
2022, France 2022, held-out and wet races remain unrun in this slice.

### Diagnostics without changing predictions

`docs/evaluation/bahrain_2021_diagnostics` reuses the exact baseline prediction
values. It adds median signed error alongside mean bias; every metric is also
split by actual subject pit entry inside `(cutoff, target]`. Error per lap is
computed separately for each row using its actual horizon length and then
mean/median-aggregated; finish rows have unequal lengths. Reports retain counts,
MAE, mean/median error, coverage, interval width, miss counts, interval score,
and mean/median/absolute error per lap for each stratum.

Baseline one-lap mean bias +0.397s conceals median error −0.428s. No-stop bias is
−0.432s (409 cases); pit-entry bias is +17.354s (20 cases), consistent with the
existing single-lap stop-charge approximation. All 324 actuals above p90 are
no-stop cases. Mean no-stop error per lap is −0.432/−0.493/−0.475 at 1/5/10 laps,
but −0.826 to finish (overall finish −0.567). A roughly constant short-horizon
pace error supports the anchor hypothesis, but finish/cohort variation means
wear, cliff and fuel errors are not ruled out by this diagnostic alone.

Baseline defaults remain frozen here: degradation scale 1, nominal compound
wear/cliff, fuel 0.05s/lap, existing pit losses and traffic/SC assumptions. Only
the recent six-clean-lap minimum supplies the base-pace anchor. No outcomes are
used to adjust these values or to widen uncertainty intervals.

### Controlled fix 1: median anchor

The evaluation builder now replaces the minimum of the same last six available
clean lap times with their median. For an even window, the two central raw lap
observations contribute their average; each retains the baseline's nominal
compound/wear subtraction and fixed fuel advance to cutoff. For an odd window
the single central observation is used. The clean window, rival inputs, tyre
model, pit losses, fuel, traffic and existing random samples do not change.
The snapshot records the central lap numbers, method and latest source timestamp.
The normal projection's unconfigured last-lap anchor remains its existing
behavior; historical evaluation supplies an explicit base_pace_s override.

`docs/evaluation/bahrain_2021_anchor_median` compares the matched cohort against
the unchanged minimum baseline/diagnostics. This is a development-race
experiment; the median has not been selected using held-out race outcomes.

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
  matching BOX/STAY two-stop variants on second-stop boundaries 34 and 38 in the
  lap-18 fixture. The default set is capped at nine; paired variants are added
  together so a smaller configured cap cannot favour one action. Every policy has at
  most two more stops, including reactive stops. No exhaustive strategy search
  or tyre inventory is modelled. A policy exhausting its stop budget keeps its
  existing tyres and pays their continuing weather/wear costs.
- Finish legality requires two distinct dry compounds across past and projected
  use, or actual use of INTERMEDIATE/WET. Forecast rain alone grants no exemption.
  A policy illegal in any positive-probability scenario is excluded from ranking;
  its series and `invalid_probability` remain visible. No legal policy raises an
  explicit error. These are the project's existing simplified rule semantics,
  not a complete sporting-regulations implementation.
- Schema version 3 separates the immediate `call` (STAY_OUT / BOX_NOW) from the
  winning policy. `best_policies_by_call` identifies the lowest expected-time
  legal policy in each action group. `call_margin_s` is the nonnegative expected
  time advantage of the winning action over the best opposite-action policy.
  `call_win_rate` is the probability-weighted share in which best STAY beats best
  BOX by **more than** `call_tolerance_s` (default 1.0s), even when BOX wins on
  expected time. `call_confidence` reports STAY clearly better, BOX clearly better,
  and too close; margins exactly at either tolerance boundary are too close.
  These shares describe model samples, not calibrated real-world confidence.
  `scenario_group_margins` reports conditional expected BOX-minus-STAY time for
  rain and no-rain branches (positive favours STAY), their p10/p90 and shares.
  Missing action groups
  yield null call margin, win rate, and comparison; the available action wins.
  Policies are selected by expected time once, not re-optimized in each sample.
- The initial action is committed using scheduled cutoff stops and weather
  already observed at the cutoff. Sampled future rain cannot trigger an initial
  stop. Subsequent weather reactions retain the coarse per-lap crossover model.
- All policies also use a safety-car opportunity rule, within the same two-stop
  budget. While an SC is observed, compare a dry HARD/MEDIUM stop or a wet stop
  against continuing, using forecast-weighted remaining own-car time. Advance
  and consume a matching future dry stop; do not repeat it at the old deadline.
  Stop only for a predicted gain greater than 0.5s (configurable). The local
  calculation uses cutoff forecast probability/ETA and nominal degradation/pit
  loss, not the sampled future rain arrival or latent wear/pit draws. It allows
  a later cheap wet switch in forecast branches where rain has become observable,
  and charges pre-emptive inters' dry costs outside neutralized laps. It enforces
  the remaining stop budget and finish compound legality in forecast branches.
  Fresh-tyre pace gains are zero on neutralized laps in this local check.
  It does not optimize traffic or rival
  responses in this local check; complete policies are still ranked by the full
  shared-scenario simulation. Future SC duration is an assumed config value.

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
  offsets are uniform within +/-1.5s. Independent seeded wear multipliers are
  uniform in [0.85, 1.15], shared across policies and rivals, scaling both linear
  and cliff wear. Pace remains anchored to the last cutoff lap in each draw.
  This creates modest dry variation without inventing post-cutoff measurements.
  There are 32 draws per nonzero branch. Each
  policy sees the same draws and weights. This is stratified Monte Carlo, not
  repeated independent weather draws per policy. The probability itself is a
  fixed forecast input, not a separately sampled probability estimate.
- For ETA four laps out, the arrival distribution covers 2-6 laps ahead (laps
  20-24 in the fixture), with five equally likely support values before sampling.
  This is a transparent +/-50% timing sensitivity assumption, not a claim about
  measured radar accuracy. Keep it configurable; no calibration data is available.
  Earlier than next-lap arrivals are clamped to the next lap, accumulating mass
  there. A +/-4-lap sensitivity run retains STAY but changes expected call margin
  from about 10.4s to 9.5s; the default remains +/-2. The finite seeded draw sets
  have sampling noise, including other unchanged-distribution random inputs.
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
  a two-lap SC window and otherwise green. Onset 19 means SC is first observed
  during lap 19: a cutoff stop after 18 pays green 21.5s; a reactive stop after
  19 pays SC 9.5s. SC boundaries 19 and 20 are eligible with duration two. The
  existing pit model also supplies VSC 12.5s; sampled offsets affect each cost.
  The duration, costs, and pack assumptions are configurable.
- At SC onset, modeled cars compress instantly in time order to 0.5s gaps from
  the modeled leader, before that lap's running and stop costs. Lost time already
  incurred before onset can be recovered by bunching. Unknown cars retain the
  existing anonymous count; no invented gaps are compressed. SC running laps
  use a common pace equal to the slowest modeled free pace plus 20s, with no
  traffic penalty. Cumulative offsets include a synthetic reduction of time lost
  to the leader at compression; this is a race-time comparison, not a literal
  subject stopwatch. No pit-lane queues, gradual pack catch-up, lapped-car rules,
  restart dynamics, or stochastic SC duration are modeled. A duration of two
  means neutralized running laps 19/20 and cheap stops at boundaries 19/20.
- Moving SC onset from 19 (STAY +13.6s) to 20 (BOX +1.8s) lets BOX's already-paid
  green-stop loss be mostly recovered by bunching before STAY pays its later SC
  stop; those signs depend on this instant-compression timing assumption.

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
  units, complete evaluated grid, and whether no rain is included. Every point
  includes call, expected call margin, conditional rain/dry margins, tolerance
  shares, and zero-offset representative scenario margins. The pit grid adds
  6/7/8s to the original 5s grid to inspect the cheap-stop crossover. Inserting the
  current value may create a smaller local interval. The probability sweep
  cannot undo already-observed rainfall, which forces occurrence in the model.
  With no forecast ETA and no observed rain it is explicitly unavailable;
  positive rain probabilities cannot be tested without inventing arrival data.
- Seconds in raw output retain floating-point precision. Every object with
  user-facing seconds also has a `display` object rounded to 0.1s, including
  per-lap arrays, stop losses, group margins, and every sweep point. Rounding
  never affects ranking, tolerance classification, or flips.
- Parameters and cutoff-derived inputs are serialized under `assumptions`.
  The `measured` kind includes metrics derived from measured/synthetic snapshot
  inputs; it does not imply real-world provenance. The fixture also stores its
  full source state, provenance, config, and generation command. No live services
  or paid models are used by this projection.

This model is intentionally small and uncalibrated. Sanity cases validate its
internal mechanics and expected qualitative behaviour, not race prediction accuracy.

## Fixture-driven workspace

The fixture generator adds `ui.display` presentation fields for the custom view.
All displayed numbers, chart ticks, narratives, table cells, and slider point
labels come from these fields. Browser sliders select a precomputed single-input
sweep point; they do not combine assumptions or rerun the engine. Off-base points
dim the base chart and disclose that its assumptions have not changed.

The observed trace is the cumulative lap-time residual versus the average known
lap pace, centered to zero at cutoff. The example future chart uses a shared
running reference: the mean of the two example cumulative times after stripping
their pit costs. Subtract each actual example time from that reference; higher is
faster and stops are visible drops. This is a display coordinate transformation,
not a new strategy model. Exact example paths and sampled group expected margins
can differ; the chart explicitly labels the bracket as sampled group statistics.
No observed trace is historical telemetry in this synthetic fixture.

The custom workspace is the default app view. Historical and legacy data tools
remain available with `?view=legacy`. The standalone preview runs with
`python -m tools.serve_projection`, reading the same canonical fixture without
copying it. The old static scorer study is preserved separately for reference.

## Offline circuit map

`scripts/build_track.py` exports the fastest accurate non-pit lap from the 2024
British GP qualifying session (RUS, lap 25). FastF1 is only needed to rebuild this
committed asset, not to load or compute the map. Use `--offline` after caching the
session. The JSON records the source, reference lap duration and integrated
telemetry distance. This is a static reference asset, not telemetry from the
synthetic cutoff or a source of later race outcomes.

The line is resampled to 301 equally spaced distance stations. X/Y are centered
and scaled together to preserve aspect ratio; the endpoint is closed to the
start to remove the positional timing-line seam. The independent, denser time
profile preserves measured speed changes. Sector boundaries interpolate the
reference sector times into distance. Integrated lap distance is approximate
and is not forced to the circuit's official length.

Pit entry/exit default to 96% / 4% of the reference distance, explicitly tagged
`config`, approximate and uncalibrated. Override with the exporter's marker
fraction arguments; these are not actual surveyed pit markers. The synthetic
scenario's leader position defaults to 25 m before that pit-entry marker, with
an explicit distance override available in `TrackScenarioConfig`.

All cars share the reference lap's distance-to-time profile. Convert the leader
distance to reference clock time, subtract each positive gap behind the leader,
then interpolate clock time back to distance. Keep unwrapped distance and lap
offset alongside wrapped drawing coordinates: large gaps must not look like
overtakes. The adapter's positive-ahead/negative-behind gaps are converted and
normalized against the leader, including when the selected driver is not leading.
This depicts synthetic timing gaps, not measured car telemetry or predicted pace.

The ghost uses the existing `current_pit_loss_s`, adding it to the selected car's
leader gap; it is an equivalent race-progress position on the racing line, not
a physical pit-lane trajectory or a future timestamp at pit exit. Neighbours
are ranked in time-gap space, so lap wrap never changes order. Rivals keep their
cutoff gaps during this illustration; no future pace, stops or field compression
are simulated. The fixture has only three cars: P3 and neighbour gaps refer to
that supplied field, explicitly marked incomplete (`field_complete: false`).

The synthetic rain forecast first reaches sector 2 (configured illustrative
location, not radar or wind direction), with probability and ETA read from the
cutoff weather forecast: 70%, four laps, lap 22. The entire overlay is tagged
`forecast`; location basis is disclosed. No drifting rain-cell trajectory is
invented. Runtime map computation uses no FastF1, network or future lap history.

The cutoff track block scales every qualifying-profile time by race-reference
duration / qualifying duration before converting race gaps. The scenario may
override `reference_race_lap_time_s`; otherwise the synthetic subject's last lap
known at cutoff is used (91.5 s here). Qualifying duration (85.819 s), scale and
timing provenance remain serialized. Geometry, distance stations and sector
distances do not change. This assumes the race lap has the same relative speed
shape as qualifying, with a uniform time multiplier, not section-specific wear.

The map view rotates the source by -90 degrees and converts positive Y to screen
Y, matching the standard orientation shown at
https://www.formula1.com/en/racing/2025/great-britain (start/finish upper left,
Stowe left, Luffield upper right). No logo or official font is used. The call uses
locally bundled Barlow Condensed ExtraBold Italic under its included OFL licence;
only the call is italic. The tyre health arc uses the existing TyreModel estimate,
not measured tread wear. Map labels occupy separate packed side rails. Browser
pit-loss changes use the fixture's scaled profile and fixed cutoff gaps to redraw
the equivalent-progress ghost and neighbours; they do not simulate the pit lane
or change the precomputed recommendation. The forecast sector is a soft static
overlay; no rain motion or wind vector is inferred.

Median anchor result (same 429 snapshots / 1,666 predictions): mean bias at 1/5/10/finish = +0.774 / -0.090 / -0.666 / -1.687 s; median error = -0.068 / -0.728 / -0.668 / -2.342 s; MAE = 1.205 / 2.823 / 4.166 / 8.413 s. Baseline MAE was 1.337 / 3.823 / 6.139 / 13.338 s. This controlled change supports the anchor diagnosis without eliminating pit timing or long-horizon modeling errors.
