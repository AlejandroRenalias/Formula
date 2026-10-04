# Frozen development model: interval calibration protocol

Predeclared before any calibration evaluation. Mean-model reference: commit
2646808, tag `frozen-development-model`, profile `wear` (pit+wear).

## Search and selection

Independently multiply the existing persistent per-sample base pace offset SD
and independent per-lap noise SD. Both API defaults are 1.0. Each grid axis is
1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75, 4.0:
169 candidates, including the unchanged (1.0, 1.0) reference.

Use Bahrain 2021, Spain 2022 and France 2022 only, the frozen saved snapshots,
actual subject plans, seeds, and outcome/exclusion cohorts. No subsampling.
Use conditional green sample quantiles, evaluated only where the cutoff is
GREEN and no actual SC/VSC occurs within the horizon. Outcome filters and
actual plans remain in the scoring/treatment channel, never in causal inputs.

For each of 1, 5, 10 laps and finish, give each available race equal weight and
each eligible prediction within that race equal weight. Missing race/horizon
cells have no weight (France has no green finish outcomes). Compute:

`objective = mean_horizon(abs(equal_race_coverage[horizon] - 0.80))`.

Choose the smallest objective. Break exact numerical ties by smaller
`mean_horizon(equal_race_mean_interval_width[horizon])`. If both are exactly
tied, choose the lexicographically smaller (persistent, per-lap) multipliers.
The four horizons have equal weight. Pit strata are diagnostic, not selection
objectives. Flag either multiplier on either grid boundary (1.0 or 4.0);
do not extend the search or retune the grid after seeing results.

## Invariants and computation

Keep raw causal scatter estimates, mean pace, wear, fuel, offsets, pit model,
weather, rival strategy assumptions and neutralisation priors unchanged. Reuse
the same normal, pit, wear and event draws across candidates. Zero estimated
scatter remains zero. Scaling may change traffic interactions and Monte Carlo
medians; these must be simulated, not approximated by scaling saved intervals.

An accelerated green-prefix calculation may replay engine-recorded lap inputs
across the grid, including traffic thresholds. Verify it against ordinary
simulation at baseline and multiple grid cells, and verify the selected cell
on every eligible snapshot. Fail on mismatch; do not silently approximate.
All reads/runs are local, with networking blocked and hashed input files.
Existing cutoff leakage tests remain applicable; calibration constants are
explicit development-set tuning, not per-cutoff observations or held-out data.

## Evidence and reporting

Save all 169 objective/width results, selected multipliers, input hashes,
runtime and parity checks. Report baseline versus selected conditional green
coverage, mean width, integer below-p10/above-p90 counts and 80% interval score
per horizon, per race and both pooling schemes, including pit/no-pit strata.
Equal-race miss rates accompany raw counts. Interval score is
`width + 10*max(p10-actual,0) + 10*max(actual-p90,0)`.

Record the selection in the frozen profile and MODEL.md; create the local tag
`frozen-development-model-calibrated`. Preserve the original mean-model tag.
Development coverage after selecting on these same races is in-sample and
does not establish held-out calibration. No new races, UI changes, additional
model changes or interval tuning. Stop for review.
