# Formula strategy models

## Frozen development model

Local annotated tag: `frozen-development-model`. Active default evaluation profile:
**pit+wear** (`wear`), reproducing the configuration evaluated at `02341a7`.
The explicit freeze record is `data/evaluation/frozen_model.json`; candidate
profiles remain available by name but are not the default. This freeze does not
authorize running held-out or wet races; they remain unrun.

Final predeclared ablation, equal-race pooled conditional green MAE:

| Configuration | 10-lap MAE s | Finish MAE s | Per-prediction finish bias s | Eligible |
| --- | ---: | ---: | ---: | --- |
| Pit+wear | 3.829 | 14.597 | -2.343 | yes |
| Current offsets | 3.840 | 13.545 | -6.172 | reference only |
| A: fit trend, project fixed fuel | 3.693 | 12.897 | -5.421 | no |
| B: fit/project fixed fuel | 3.623 | 12.760 | -5.238 | no |

A and B improve both MAE horizons but fail the finish-bias gate. The absolute
and signed interpretations of no-worse bias select the same fallback, pit+wear.
No shrinkage or interval parameter was adjusted. Removing extrapolated trend
improves MAE, but does not remove the optimistic pooled bias; the ablation does
not establish that linear trend extrapolation alone caused the remaining errors.

Known limitations of the frozen profile:

- Spain SOFT remains too fast: no-stop finish mean error about -1.067 s/lap.
  No-stop finish errors average -0.278 s/lap in Bahrain and -0.762 in Spain.
- Pooling hides opposing race biases: green finish mean bias +7.270 s Bahrain,
  -9.935 s Spain. The aggregate gate passing does not imply either race is unbiased.
- Green intervals under-cover: per-prediction coverage 52.35% at 10 laps and
  37.94% at finish. No uncertainty or interval-width tuning was performed.
- Compound offsets remain fixed, and within-stint wear uses the fixed 0.05
  fuel correction, so fuel, management and track evolution can still confound it.
  Cliff shape, traffic and pace after stops remain approximations.
- Neutralisation priors are unchanged; three development races are too few to
  judge their calibration. Green finish statistics include only Bahrain/Spain.
- Predictions condition on the actual future subject stop plan. This is a
  prediction-layer evaluation, not evidence of strategy/agreement performance.

220 tests pass with the frozen default. All 1,400 saved states/parameters and
31 representative horizon predictions match the selected pit+wear run exactly,
with networking blocked. Reverify using python -m tools.verify_frozen_model.

Full per-race/pooled pit/no-pit and compound/age tables against pit+wear and
offsets: `docs/evaluation/development_ablation/REPORT.md`. Candidate/source hashes,
selection inputs and causal checks are retained alongside the report. Replays
use only hashed local caches with networking blocked. Historical sections below
record experiments; this frozen default supersedes their active configurations.


## Bahrain-only conditional evaluation

The baseline is committed independently in `1597011`. Evaluation uses exact
subject crossing cutoffs, causal raw timing/tyre/weather/status observations,
and the explicitly labelled same-lap rival crossing gap proxy. The subject's
actual future stop schedule is a conditional outcome treatment, never a state
feature. Rivals retain the engine's own causal stop assumptions. All runs load
hash-verified local Bahrain 2021 data with network connections blocked. The initial
Bahrain slices left other races unrun. The authorized development extension
now includes Spain 2022 and France 2022; held-out and wet races remain unrun.

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

Median anchor result (same 429 snapshots / 1,666 predictions): mean bias at 1/5/10/finish = +0.774 / -0.090 / -0.666 / -1.687 s; median error = -0.068 / -0.728 / -0.668 / -2.342 s; MAE = 1.205 / 2.823 / 4.166 / 8.413 s. Baseline MAE was 1.337 / 3.823 / 6.139 / 13.338 s. This controlled change supports the anchor diagnosis without eliminating pit timing or long-horizon modeling errors.

### Controlled fix 2: causal pace uncertainty

For each snapshot, normalize the same driver's last six available clean lap
times by the unchanged nominal tyre/wear cost and 0.05s/lap fuel advance to
cutoff. Their sample standard deviation is s, with n observations. The subject
receives a persistent Normal(0, (s/sqrt(n))^2) base pace offset in each simulation
sample, plus independent Normal(0, s^2) noise on each future lap. One available
clean observation gives zero scatter; no floor, cross-driver borrowing or
outcome-residual fitting is added. This split is a modeling assumption, not
an empirical decomposition of systematic and random pace errors.

Offsets and noise use independent seed streams (seed+2 and seed+3), shared
across policies/weather branches. Antithetic pairs center these additional
draws at zero for the even 32-sample evaluation. Existing weather, pit-loss and
wear draws retain their original values. Subject noise can change modeled
traffic interactions; rival base paces and future strategy assumptions are
unchanged. Config defaults for both new sigmas are zero, preserving existing
non-evaluation behavior. No UI code changes are required.

Without traffic/SC/pit/wear interactions, added elapsed-time variance at h laps
is h^2*s^2/n + h*s^2. The persistent term therefore prevents uncertainty from
averaging away at long horizons. Noise is added before existing traffic/SC
handling. Each snapshot records normalized observations, sample count, both
sigmas and their latest source timestamp; all parameter sources must be no
later than the cutoff. Forecasts and actual future outcomes never size them.

The matched report is `docs/evaluation/bahrain_2021_uncertainty/REPORT.md`.
This was a Bahrain-only development experiment before the separately
authorized three-race extension below.

Coverage at 1/5/10/finish rises from 11.9/11.7/16.6/15.9% to
61.3/46.6/45.1/47.3%; mean interval width rises from
0.219/0.965/1.655/3.636 s to 1.063/3.279/5.940/15.745 s.
MAE is 1.208/2.823/4.165/8.514 s, nearly unchanged from the median-only run.
The 80% target remains unmet; no further tuning is performed. Both reports
include all metrics split by actual subject pit entry. The unchanged one-lap
pit-charge approximation remains a separate source of large errors.

### Controlled fix 3: frozen pit-loss allocation

Bahrain and subsequent authorized dry development evaluations use a frozen
50% in-lap / 50% out-lap share. This neutral default is not estimated from any
race, including Bahrain, Spain or France. The stop's sampled total, status
basis and pit uncertainty are fixed at entry. Half is charged on the entry lap
and the exact remainder is carried to the next lap; it is not resampled or
repriced. The same allocation applies to modeled rival stops. Consecutive
stops accumulate any already-due out-lap cost. A stop on the final projected
lap charges all its loss there, preserving the race total without a nonexistent
out-lap. Tests verify conservation across varying pit offsets and terminal
stops. Traffic interactions can change after reallocating temporal costs.

Compound reset and tyre age timing retain the existing entry-lap approximation;
no tyre wear, pace, fuel, rival stop rules or uncertainty sources are changed.
ProjectionConfig defaults to the original fraction 1.0 for compatibility with
existing UI fixtures and non-evaluation callers; evaluation explicitly sets
pit_in_lap_fraction=0.5. The UI and its fixture files remain untouched.

Report: `docs/evaluation/bahrain_2021_pit_split/REPORT.md`, compared with the
previous causal-uncertainty run on identical cutoffs and targets.

Pit-entry-only 1-lap mean bias falls from +17.683 to +6.968 s; pit-entry 5-lap MAE changes from 5.935 to 3.736 s. No-stop errors are nearly unchanged. The unestimated 50/50 share reduces,
but does not eliminate, the in-lap mismatch; it is retained without tuning.

### Authorized development extension

The unchanged pit-split model is evaluated on Bahrain 2021 (56 scheduled laps),
Spain 2022 (66) and France 2022 (53), with fixed pre-declared distances and an
explicit acquisition/evaluation allowlist. Spain 2023, Bahrain 2024, Russia
2021, Netherlands 2023 and Canada 2024 remain denied and unrun. Each race uses
top-ten finishers, cutoffs lap 5 through distance minus 5, and the same four
horizons, exclusions, parameter defaults, causal state builder and gap proxy.
Acquisition populates both local FastF1 and hash-verified normalized caches;
evaluation and aggregation block network connections. Legacy Bahrain CLI names
are retained, with an explicit --race acquisition option and --dataset replay.

Per-race and pooled metrics include mean bias, median signed error, MAE,
row-normalized mean/median/absolute error per lap and coverage, split by actual
subject pit entry in the horizon. Pooling concatenates valid prediction rows,
so longer races and fewer exclusions receive greater weight; snapshots are
correlated. No-stop breakdowns use causal cutoff compound and tyre age, in
fixed 0-9, 10-19, 20-29 and 30+ bins, plus joint compound/age and cutoff-status
groups. They do not feed model fitting. Finish-horizon length, traffic, fuel,
status and survivor selection can confound associations with tyre age.

New races have no previous same-race runs. Comparisons to the previous Bahrain
pit-split report are explicitly unmatched population references, not controlled
model improvements. Calculator source hashes are identical across all three
races. The snapshot loader changes only its allowed dataset identities and
pre-declared-distance validation; no input-building formulas change.

Report: `docs/evaluation/development_2021_2022/REPORT.md`, with individual
race reports and pooled prediction/metric/breakdown artifacts.

Across 1,400 valid snapshots and 5,446 predictions, pooled coverage at
1/5/10/finish is 62.4/43.0/39.3/29.9%. Finish MAE is 8.519 s in Bahrain,
16.702 s in Spain and 130.620 s in France; France finish coverage is zero.
France has 11 SC cutoff snapshots producing a very large positive error tail,
while every scored France finish horizon contains a real later neutralization.
The report adds an explicitly outcome-only SC/VSC horizon label and a
GREEN-cutoff/no-actual-neutralization tyre diagnostic. These labels are created
only after predictions, never used by the state builder or parameter sizing.

In the filtered no-stop finish subset, Bahrain HARD and Spain SOFT show more
negative error per lap at higher cutoff ages; Spain MEDIUM and France short
horizons do not show a uniform monotonic age pattern. Wear remains plausible,
but SC/VSC modeling, fuel, horizon lengths and selection prevent attribution
to a single wear coefficient. No parameters are changed after these results.

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


## Structural neutralization correction 1: ongoing events end

The external prior is built only from 2019 races, before all evaluation years.
Germany was omitted in advance; sessions with any rain station sample are
excluded. The included 18 races and raw status/episode evidence are committed
in data/priors/neutralization_2019.json with a SHA-256 sidecar. Acquisition reads
only 2019 public timing/status/weather and caches it locally; no projection is
run on those prior races. Held-out and wet evaluation races remain untouched.

Green-lap exposure is green/yellow race-running seconds divided by each race's
median driver clean-lap pace; red flags and SC/VSC seconds are not exposure.
There are 9 SC and 6 VSC onsets over 1019.026 green-lap equivalents. Total-duration
observations ending at race finish are right-censored: count their onset but
exclude their unfinished duration from the completed-duration distribution.
Full-lap pace ratios exclude pit laps, lap 1/2, and mixed-status laps and are
normalized to the same driver's median green pace within that prior race.
This small dry-only prior has selection and censoring limitations; VSC pace has
only two qualifying observations. No evaluation outcomes enter any estimate.

For an ongoing event, use the prefix's most recent uninterrupted SC (code 4)
or VSC (codes 6/7 together) onset. Elapsed time is cutoff minus that onset.
Expected remaining seconds is the mean of D-elapsed among external completed
durations D greater than elapsed. Beyond the largest observed duration, use an
explicit untuned remaining-duration assumption: 90 s SC / 30 s VSC. Convert to
remaining whole laps by ceil(seconds / (cutoff nominal green pace * external
pace multiplier)), at least one lap. These multipliers are 1.34175 SC and
1.35539 VSC; in this first correction they only convert clock duration to laps.
Existing SC running pace/pack behavior and VSC running pace remain unchanged.
The event ends at that predicted boundary, never at its actual future ending.
Onset timestamp must be <= cutoff; the frozen prior is available before session
start and records latest source year 2019 and its hash. Default engine behavior
outside evaluation remains compatible via ongoing_neutralization_laps=None.

Correction 1 results: Bahrain and Spain metrics are unchanged. France finish MAE falls from 130.620 to 67.441 s; mean bias moves from +2.818 to -60.361 s, median error remains -36.519 s, and coverage remains 0% (11 below p10 / 418 above p90). See docs/evaluation/development_ongoing/REPORT.md for all horizons and pit strata. Full verification: 179 tests passed, including real SC-cutoff future poisoning; offline source hashes and parameter timestamps verified.

## Structural neutralization correction 2: future event risk and pace

The same frozen 2019 evidence supplies constant, non-track-specific per-green-lap
onset probabilities: SC 0.00883196 and VSC 0.00588797. A categorical draw permits
at most one onset on an eligible lap. No onset is sampled while the ongoing
expected event or a sampled event is active. Each Monte Carlo draw has an
independent seed+1000+index stream, shared across policies and weather branches;
the existing weather, pit, wear and driver pace draws are unchanged.

For a new event, sample uniformly from the external completed durations (8 SC,
6 VSC). Convert seconds to whole laps with ceil(duration / (cutoff nominal green
pace * prior pace multiplier)), minimum one lap. Events can extend past finish;
the simulated trace clips there. Rates and distributions are not adjusted using
Bahrain/Spain/France coverage. Whole-lap discretization particularly coarsens
short VSC episodes. Ongoing expected duration remains deterministic from step 1.

SC running pace uses cutoff nominal subject green pace, fuel progression and
existing subject pace uncertainty, multiplied by 1.3417544; rivals share that
pace. VSC multiplies each car's projected green pace by 1.3553914 without pack
compression. These external pace effects apply to both sampled and ongoing
events. This replaces the old SC maximum-of-cutoff-rival-pace plus 20 seconds,
which can double count a rival's neutralised or pit lap. Under this enabled
model, SC compression changes relative rival gaps but preserves subject elapsed
time: pack rearrangement cannot move the subject's clock backward. Traffic
penalties are disabled while neutralised. This is a coarse whole-lap model,
not a reconstruction of the actual restart or SC train.

Actual-plan entry laps active under a sampled/ongoing event use existing SC/VSC
pit losses and the same frozen 50/50 allocation. The out-lap retains the entry
price; no extra pit draw or later repricing occurs. Entry-lap status replaces
boundary status only in this enabled risk model, as needed for a stop falling
under a sampled event. Rivals retain causal tyre-life/weather assumptions. A
policy may react to an event already active at its boundary, but never receives
the sampled future schedule in its stop-opportunity forecast. Legacy configs
have zero risk and preserve fixture numbers. No degradation fitting or interval
tuning is performed; 32 draws per branch remain unchanged.

Correction 2 finish results (ongoing -> future risk): Bahrain MAE 8.519 ->
12.697 s, coverage 47.6% -> 71.6%; Spain MAE 16.702 -> 16.007 s, coverage
39.7% -> 77.7%; France MAE 67.441 -> 57.359 s, coverage 0% -> 85.1%.
France misses change from 11/418 below/above to 10/54; width 13.650 ->
140.470 s. Prediction-pooled finish coverage is 78.1%, with 184 below / 123
above among 1,400 predictions. France finish median error remains -34.581 s:
the prior models risk, not the observed future event schedule. Bahrain point
accuracy worsens while coverage improves. No rates or intervals were tuned.
All horizons, pit strata and matched metrics: docs/evaluation/development_future/REPORT.md.
Verification: 183 full-suite tests plus the added SC subject-clock regression
passed; all three offline manifests/source hashes and cutoff timestamps checked.

## Outcome-only reporting views and race weighting

Green-only rows have a GREEN cutoff and no actual SC/VSC status (4/6/7) at
any point through the target crossing. These post-prediction labels never
enter state, parameters or event sampling. Both pit and no-pit rows remain;
every metric keeps the subject-stop split. Equal-race pooling assigns each
available race total weight 1/R, then each row within its race weight 1/(R*N).
Pit strata normalize separately within contributing races. Medians are weighted
medians of individual errors; counts remain raw integer misses, with balanced
miss rates reported separately. Missing cells are unavailable, never zeros.
France contributes no green-only finish rows, so that cell uses two races.

Final full equal-race finish coverage is 78.1%, MAE 28.688 s and bias -15.762 s;
full prediction pooling is 78.1%, MAE 27.664 s and bias -14.384 s. Green-only
equal-race mean error/lap at 1/5/10/finish is +0.065/-0.109/-0.065/-0.019 s.
Report and all matched stage comparisons:
docs/evaluation/development_neutralization_views/REPORT.md and COMPARISONS.md.
This report-only step leaves every saved prediction unchanged. Held-out and
wet evaluation races remain unrun; no UI source or artifact was changed.


## Same-sample conditional green output and onset calibration

No model or parameter change: retain the existing scenarios and traces. Each
horizon also reports conditional median/p10/p90 for samples with no SC/VSC
active anywhere in that projected horizon, using original weights renormalized
within the retained subset. Keep sample count and probability mass. Empty
subsets, including horizons containing a known ongoing event, are unavailable;
never substitute the combined prediction. Evaluate this on the same GREEN
cutoff/no actual SC/VSC outcome view, with pit/no-pit strata and both pooling
schemes. These outcome labels never enter predictions.

Report exact marginal probability of a new onset as 1-(1-p_SC-p_VSC)^K, where
K counts eligible future laps outside the known ongoing-event schedule. Prior
durations after the first onset cannot affect whether any onset occurs. The
sampled onset weight fraction is output separately; the original 32 draws have
no first-lap onsets, so their empirical one-lap estimate is zero despite a
positive model hazard. Computing the exact marginal changes no rate, draw,
trace, median or interval. Calibration uses the exact probability against
actual new status-kind starts in (cutoff time,target crossing]. Already ongoing
events are not new starts; VSC codes 6/7 and repeated same-kind updates are
merged. Brier scores and fixed-decile reliability tables are descriptive only:
three races and strongly correlated driver/cutoff horizons cannot establish
calibration. No tuning or new races were used.

All 5,446 combined predictions and all per-race combined metrics exactly match
the previous future-risk run. Conditional green prediction-pooled finish MAE
is 13.099 s, bias -4.967 s, mean error/lap -0.258 s, coverage 45.5%, and width
19.060 s; France has no green-only finish outcomes. Full per-race, pit-split,
equal-race and calibration tables: docs/evaluation/development_conditional/REPORT.md.

## Causal pit prior and completed-stop updates

The effective green-stop prior comes from Bahrain 2019, Spain 2019 and France
2019 only, outside every evaluation race. Public raw timing/tyre/status/weather
responses are cached locally; no projections are run on those prior races.
Venue-specific medians are recorded in data/priors/pit_2019.json with SHA-256.
France puts its stop mainly before the timing line (entry-heavy); Bahrain and
Spain are exit-heavy. Do not pool those structurally different lap allocations.
This estimates effective elapsed loss including warm-up and local pace effects,
not pure stationary service time. Venue-specific defaults use the earlier 2019 season, never evaluation outcomes.
A pooled fallback is retained only for an unknown venue.

Reduce raw TimingData packets only before the cutoff. Identify entry lap from
completed-lap count at an observed pit entry. Require both entry/out-lap lap-time
packets and a pit exit received before the cutoff. Both full laps must be green.
Counterfactual in-lap pace uses the median of up to three earlier clean laps in
the same stint, at least two and after lap 2, adjusted with frozen nominal
compound/wear and fuel 0.05 s/lap. Out-lap pace uses up to three already observed
clean new-stint laps within five laps of entry, if available; otherwise use the
pre-stop fresh-pace anchor and new nominal compound/age. Never use a following
stint or a clean lap after the cutoff. Physical measurement quality bounds are
0<entry excess<40 s, 0<exit excess<40 s, 5<total<60 s; these quality bounds allow either timing-line allocation and are not tuned
to evaluation errors. Green-only stops are
pooled across all causally observed drivers, without finisher selection.

Update the two component medians with weight n/(n+5), an untuned five-stop prior
strength. Derive total and share from these shrunken components. Record n,
fallback, component values, prior weight/hash/year, every accepted stop and the
latest source timestamp <= cutoff. With no complete stop, use the external prior.
SC/VSC total pit losses stay 9.5/12.5 s; the revised allocation fraction is
shared as in the existing model. No interval-width parameters, event rates,
fuel, degradation, tyre reset timing or UI behavior change in this pit slice.


2019 venue priors (64 stops total): Bahrain 23 stops, total 24.382 s and entry
share 12.05%; Spain 23 stops, total 23.125 s and entry share 15.41%; France
18 stops, total 24.4165 s and entry share 82.46%. The different France split is
observed in the 2019 evidence itself, not selected from its 2022 predictions.
Old car/tyre and service differences remain a limitation of this starting prior;
the already completed current-race stop updates provide causal adaptation.


Pit slice results: one-lap stop MAE changes from 6.968 to 1.048 s Bahrain,
5.303 to 1.767 s Spain, and 13.052 to 4.722 s France (only two cases).
Prediction-pooled one-lap stop MAE falls from 6.279 to 1.598 s; bias changes
from +5.234 to -1.545 s and coverage from 0% to 8%. The remaining entry-lap
fresh-tyre approximation and individual service/pace variations are unchanged.
Pooled conditional finish MAE is 13.099 -> 13.210 s, bias -4.967 -> -3.327 s;
this change primarily fixes entry horizons. No interval parameters were tuned.
All horizons, pit/no-pit and race pools: docs/evaluation/development_parameters_pit/REPORT.md.


## Causal compound wear estimation

For each cutoff, use all drivers' already received raw clean lap observations,
never corrected full-session lap times or future tyre labels. Fit one linear
coefficient per dry compound with a separate intercept for each driver/stint:
demean age and fuel-corrected time within each stint, then sum within-stint
cross-products across drivers. Fuel correction is +0.05 s times race lap number.
Remove the existing fixed 0.15 s/lap post-cliff contribution from the fitted
response, so the unchanged cliff term is not counted twice. Compound offsets,
cliff thresholds, tyre life, fuel and stop timing remain unchanged.

Exclude race laps 1/2, all pit-entry/out laps, non-GREEN/unusable lap flags,
nonfinite times and invalid ages. A stint needs at least three clean laps and
an age span of at least three laps. Clamp a negative empirical slope to zero
(physical constraint), then shrink it toward the existing compound default with
weight n/(n+60), where n is the number of qualifying clean laps. The sixty-lap
prior strength and eligibility rules were chosen before viewing this slice's
outcomes; they are not fitted to its errors. With no qualifying stint, use the exact
existing default. Every compound records used/available counts, stint/driver
counts, raw slope, shrink weight, fallback/clipping flags, within-stint sufficient
statistics, and latest source session time <= cutoff. Defaults for an unused
compound have source 0; thin-data fallback records the latest available evidence
used for that decision. Traffic, driver management and track evolution can still
confound these empirical slopes; they are not a measurement of tyre chemistry.

Projection uses these rates per compound and the original +/-15% wear draws.
The recent-six raw median selects the same anchor lap(s), but removing wear to
recover fresh pace now uses the fitted curve. Record upstream wear timestamps
in the anchor's parameter provenance. Pit-loss estimates keep their step-1
nominal counterfactuals so this wear slice does not refit the pit parameters.
The driver-local noise sigmas deliberately keep their existing nominal-wear
normalization and identical draws; no interval-width sizing or tuning changes.
Known ongoing-event duration conversion remains the previous nominal cutoff
pace calculation, preserving onset probabilities. SC/VSC priors are unchanged.
Future event duration conversion can consume the updated nominal tyre curve,
but this cannot change the probability of any first new onset in a horizon.
The staged CLI can still run pit-only with fit_wear=False.


Wear-only development result versus the preceding causal-pit run (matched
conditional green cohorts): per-prediction 10-lap MAE 4.041 -> 3.961 s,
coverage 50.0% -> 52.3%; equal-race 10-lap MAE 3.808 -> 3.829 s.
Pooled finish MAE worsens 13.210 -> 14.759 s, coverage 44.5% -> 37.9%.
No-stop finish MAE improves Bahrain 6.196 -> 5.151 s and Spain
9.835 -> 8.648 s, but Spain's signed error/lap worsens -0.723 -> -0.762.
Bahrain's no-stop finish error/lap improves -0.445 -> -0.278. France's
10-lap bias is nearly zero, with worse MAE; no green finish cohort exists there.
Across races no-stop finish HARD/MEDIUM improve, SOFT worsens. No post-result
parameter or interval tuning: this remains an unvalidated, mixed experiment.
Full per-race/pooled pit strata and compound/age before/after tables:
docs/evaluation/development_parameters_wear/REPORT.md. All 205 tests pass;
1,400 snapshots / 5,446 predictions preserve probability/subset invariants.

## Joint race trend and wear (first regression slice)

Fit clean pre-cutoff laps with driver intercepts, fixed default compound offsets,
compound-specific nonnegative linear wear and a signed race-lap trend. Keep the
same clean-lap, pit-lap and three-lap/three-age-span eligibility rules as before.
Subtract the unchanged fixed cliff term. Demean the design and response within
drivers (not stints) to eliminate driver intercepts; different stint start laps
supply the separation between age and race lap. Do not use future tyre labels.

Before viewing outcomes, freeze slope regularization at 60 pseudo-laps with
five-lap standard deviation: ridge precision 60*25=1500 for each wear slope and
race trend. Priors are the existing compound slopes and signed trend -0.05 s/lap
(the existing positive 0.05 fuel effect). This is joint prior-centered ridge,
not the preceding count-weight blend. Solve nonnegative wear by an active set;
allow either sign of race trend. With a rank-deficient driver-demeaned design,
keep the trend exactly at its prior and label fallback; absent compounds also
retain their priors. Regularization does not make unidentifiable trend evidence.
Record counts, design rank, fallback and latest source time for every coefficient.
Jointly fitted coefficients depend on all included rows, so their source timestamp
is the latest included observation, not only rows of their own compound.

Use the fitted curve and trend to reanchor the same recent raw-median lap(s),
and use the trend for future race-lap increments. Preserve pit parameters,
nominal scatter sizing, uncertainty spreads and neutralisation priors/initial
ongoing-duration conversion. The trend absorbs fuel, track evolution and other
race-wide effects; it is not a separate physical fuel estimate. Extrapolating
one linear trend to the finish remains an assumption. No interval tuning.

The next offset slice's prior is also fixed before these replays: 60 pseudo-laps
with one-second offset-design spread (ridge precision 60). Only drivers with
multiple qualifying observed compounds identify offset contrasts; unsupported
compound comparisons retain defaults. No evaluation errors select prior strength.


Trend-only result versus the preceding wear run: pooled green finish MAE
14.759 -> 14.047 s (equal-race 14.597 -> 13.750), but bias
-2.343 -> -6.635 s, coverage 37.9% -> 36.5%. Pooled 10-lap MAE
3.961 -> 3.994 s. Bahrain with-stop finish bias +12.899 -> +2.007;
Spain -10.588 -> -11.030 s. No-stop finish error/lap worsens Bahrain
-0.278 -> -0.649 and Spain -0.762 -> -0.809. Spain SOFT remains poor.
No tuning after these outcomes. 209 tests pass; all 1,400 snapshot and
5,446 prediction provenance/probability invariants verified. Full matched
pit/no-pit and compound/age tables: docs/evaluation/development_parameters_trend/REPORT.md.

## Causal compound offsets (second regression slice)

Add compound-offset adjustments to the same driver-intercept, compound-wear,
race-trend regression; refit shared coefficients jointly. Offsets have prior
precision 60 (60 pseudo-laps with a one-second spread), frozen before either
slice's outcomes. Slopes retain precision 1500; all eligibility rules and
uncertainty sizing stay unchanged. The response subtracts default compound
and cliff contributions; offset-adjustment priors are zero.

Only drivers with more than one qualifying observed compound supply offset
contrasts. A single-compound driver's compound indicator is constant and drops
out on driver demeaning, while their clean laps can still supply wear/trend
evidence. Form connected compound comparisons from these multi-compound drivers.
An absolute offset cannot be distinguished from driver intercepts, so keep the
first present compound in SOFT/MEDIUM/HARD order at its default for each connected
component. Thus France, without SOFT observations, retains MEDIUM at +0.4 s and
fits HARD relative to it; it cannot estimate an unseen SOFT-to-MEDIUM gap.

Add only contrasts increasing design rank beyond the already identified slopes
and trend. A collinear contrast stays at its default and records that reason;
reference, unused and unsupported compounds also have explicit fallback flags.
Offsets may be signed: no ordering/cap selected from evaluation results. Record
qualifying comparison-lap counts, available comparison counts, driver counts,
reference compound, fallback reason, prior precision and latest source timestamp.
Every fitted coefficient's conservative source time includes all joint regression
rows. Use the fitted offsets both in the median-anchor correction and future
compound transitions. Preserve pit counterfactuals and uncertainty normalization
at their preceding nominal definitions; SC/VSC assumptions are unchanged.


Offset-only result versus trend commit: pooled green finish MAE
14.047 -> 13.844 s (equal-race 13.750 -> 13.545), coverage
36.5% -> 38.5%; pooled 10-lap MAE 3.994 -> 3.955 s. With-stop finish
bias Bahrain +2.007 -> +2.126 and Spain -11.030 -> -10.210 s.
No-stop finish error/lap remains poor: Bahrain -0.618, Spain -0.802;
Spain SOFT -1.060. Both changes versus starting wear baseline reduce
pooled finish MAE 14.759 -> 13.844 s but worsen bias -2.343 -> -6.172 s.
The starting no-stop finish MAE was better in both races. No tuning afterward.
213 tests pass; all 1,400 snapshots / 5,446 predictions retain causal source
and SC/probability/noise invariants. Full incremental and initial-baseline
pit/no-pit and compound/age tables: docs/evaluation/development_parameters_offsets/REPORT.md.
Offline replay commands: python -m tools.evaluate_causal_parameters --stage
offsets --race <development race>, then --stage offsets --report-only;
python -m tools.report_regression_baseline adds the cumulative starting-baseline
tables and JSON artifacts idempotently. Historical slice reproduction should
use that slice's commit so its model-source hashes match.

## Final pre-freeze ablation protocol (fixed before replay)

Candidates keep all existing priors, eligibility, ridge strengths, cliff, pit
parameters, scatter normalization, Monte Carlo draws and SC/VSC priors unchanged.
A: joint wear/offset/trend fitting exactly as the offsets configuration, including
fitted-trend correction from historical median-anchor laps up to the cutoff;
future laps use only signed -0.05 s/lap (fixed fuel). No fitted trend extrapolation.
B: same joint driver-intercept wear/offset regression, but subtract the fixed
-0.05 race-lap effect rather than estimating a trend; future laps also use -0.05.
Neither candidate changes interval sizing. Compare each with wear (02341a7) and
current offsets (e6270ef), using matched conditional green cohorts and both pools.

Selection uses stored, unrounded metrics. Finish-bias gate is per-prediction
pooled green absolute mean bias <= 2.3433399051303514 s, the absolute value
of the wear baseline's stored bias (conservative interpretation of no worse). Rank eligible A/B and the fallback wear configuration by equal-race
pooled green MAE at 10 laps AND at finish; select a candidate only if it attains
the minimum at both horizons. If minima belong to different configurations,
or neither candidate qualifies, retain wear. No post-hoc horizon weighting.
Offsets is a reference, not an eligible new candidate (its bias fails the gate).
France has no qualifying green finish outcomes, so finish equal-race pooling
covers Bahrain and Spain. This development-only selection does not validate
held-out or wet performance. Freeze the chosen default via an explicit recorded
profile and tag after the report; preserve all other profiles for reproduction.
