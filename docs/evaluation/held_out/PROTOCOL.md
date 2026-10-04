# One held-out evaluation

User-authorized acquisition/evaluation: Spain 2023 (66 scheduled laps) and
Bahrain 2024 (57). Use exactly tag `frozen-development-model-calibrated`
(`0878c4d093bf5b2b0e901b17ea8887fa42b7bbe8`): pit+wear default profile,
persistent pace uncertainty multiplier 3.0 and per-lap multiplier 1.0.

No model, prior, parameter-estimation, calibration or exclusion changes.
Confirm tracked model/profile files match the tag, hash them before/after each
run, and assert the selected profile/scales on each snapshot. Authorization of
these two datasets is scoped to the runner; the original default dataset guard
remains unchanged. Wet races remain unauthorized.

Acquisition is a separate network-enabled operation using the existing FastF1
exporter and local cache. All evaluation and reporting runs block networking.
Use the existing exact completed-lap cutoff, permitted labelled live-gap proxy,
causal parameter estimation, actual subject plan treatment and causal rival
policies. Top ten finishers, cutoffs from 5 to scheduled distance minus 5;
horizons 1/5/10 laps and driver finish. Retain existing exclusions. Benchmark a
few snapshots; retain every lap unless the original 30-minute-per-race runtime
rule requires stride 2. Reuse benchmark predictions rather than simulating the
same held-out snapshot again. Persist a start ledger and refuse repeat runs.

Report full and conditional-green views, per race, per-prediction pooled and
equal-race pooled, including pit/no-pit strata. Same definitions/tables as
development: MAE, mean bias, median signed error, error per lap, coverage, width,
below-p10/above-p90 counts and interval score. Green outcomes require GREEN at
cutoff and no actual SC/VSC in the horizon; quantiles use only draws with no
neutralisation in that horizon. Outcome labels never enter inputs. Missing
race/horizon groups receive no weight; pit strata normalize independently.

Compare side by side with the three development races under the identical
calibrated profile. Existing calibration artifacts supply the green reference;
replay saved frozen development states/configs/plans to obtain the full view,
changing only their uncertainty multipliers to the already selected values.
Verify resulting green metrics against the saved calibration metrics.

Save dataset/exclusion counts, prediction records, manifests/hashes, runtime,
plots, worst errors and limitations. Unexpected acquisition/evaluation/parity
failure is reported and stops the run; no corrective model/data changes or
second held-out evaluation. Poor predictive performance is reported as observed,
with no tuning. Stop for user review after the report.
