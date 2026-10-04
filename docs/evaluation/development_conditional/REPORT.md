# Same-sample conditional green predictions and neutralization probability

Bahrain 2021, Spain 2022 and France 2022 only. No model changes, parameter changes, tuning or new races. All combined median/p10/p90 values reproduce the previous future-risk run exactly. Predictions come from the same 32 samples per branch and saved snapshots/plans, offline.

## Pooled green-only result

Prediction-weighted pooling; finish uses Bahrain and Spain because France has no green-only finish outcomes.

| Horizon | N | MAE s | Bias s | Error/lap s | Coverage | Mean width s | Brier score (all outcomes) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1365 | 0.650 | +0.068 | +0.068 | 63.6% | 1.059 | 0.01269 |
| 5 | 1284 | 2.365 | -0.763 | -0.153 | 47.7% | 3.629 | 0.06454 |
| 10 | 1085 | 4.206 | -1.404 | -0.140 | 47.9% | 6.821 | 0.10365 |
| finish | 970 | 13.099 | -4.967 | -0.258 | 45.5% | 19.060 | 0.24758 |

The conditional pace distribution still under-covers and is too fast on average at longer horizons. The combined distribution remains unchanged and continues to reflect both worlds. Three race histories and overlapping snapshots cannot establish calibration.

## Definitions

- **If it stays green:** median/p10/p90 conditional on no SC/VSC active in the projected horizon, using the retained samples and their original weights, renormalized within that subset. This is not a new all-green simulation or a change to the base pace model. Retained sample count and probability mass are output for every horizon. If none remain (including known ongoing neutralization inside the horizon), the conditional prediction is unavailable, never replaced by the combined prediction.
- **Green-only outcome:** GREEN at cutoff and no actual SC/VSC through target, matching the existing reporting definition. Yellow cutoffs are excluded. Actual future status is an outcome-side filter only. Both pit and no-pit horizons remain; signed error is prediction minus actual.
- **New-event probability:** exact marginal probability from the unchanged frozen rates: 1-(1-p_SC-p_VSC)^K, where K is the number of eligible future laps after the known ongoing-event schedule. Until the first new start, event duration cannot affect this probability. The sampled onset fraction is also output separately, without changing any draw. An already ongoing event does not count as a start. Observed starts use actual status transitions during (exact cutoff time, target crossing time]. VSC codes 6/7 are one continuous kind; repeated same-kind messages do not count as new starts. All scored snapshots, including ongoing-event cutoffs, enter calibration. Calibration uses the exact marginal probability; the green quantiles still use the original finite 32-draw subset. Whole-lap simulation and sampling remain unchanged.

**Three races are far too few to judge calibration.** Driver snapshots and overlapping horizons share the same few race-wide episodes. The thousands of rows are not independent trials. Brier scores and bin frequencies are descriptive development diagnostics; no calibration fitting is performed. Empty bins are unavailable. Probability bins are fixed deciles, chosen before viewing results.

## Dataset and availability

| Race | Snapshots | Predictions | Green-only outcomes | Conditional available on green outcomes | Unavailable on green outcomes |
| --- | ---: | ---: | ---: | ---: | ---: |
| bahrain_2021 | 429 | 1666 | 1662 | 1662 | 0 |
| spain_2022 | 542 | 2114 | 2114 | 2114 | 0 |
| france_2022 | 429 | 1666 | 928 | 928 | 0 |

Exclusions remain those of the previous replay; no new cutoff/target exclusions or stride changes. France has no eligible green-only finish outcomes. Equal-race pooling normalizes each contributing race, and each pit stratum, separately; missing cells have no weight.

# If it stays green, evaluated on green-only outcomes

## bahrain_2021

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 428 | 0.710 | +0.261 | -0.087 | +0.261 | -0.087 | 0.710 | 61.2% | 1.021 | 78 | 88 | 5.218 |
| 1 | without_stop | 408 | 0.403 | -0.068 | -0.104 | -0.068 | -0.104 | 0.403 | 64.2% | 1.005 | 58 | 88 | 2.329 |
| 1 | with_stop | 20 | 6.968 | +6.968 | +7.063 | +6.968 | +7.063 | 6.968 | 0.0% | 1.348 | 20 | 0 | 64.145 |
| 5 | all | 428 | 2.288 | -0.527 | -0.707 | -0.105 | -0.141 | 0.458 | 47.2% | 3.396 | 72 | 154 | 15.054 |
| 5 | without_stop | 325 | 1.843 | -0.420 | -0.433 | -0.084 | -0.087 | 0.369 | 53.5% | 3.383 | 49 | 102 | 11.242 |
| 5 | with_stop | 103 | 3.692 | -0.864 | -1.666 | -0.173 | -0.333 | 0.738 | 27.2% | 3.437 | 23 | 52 | 27.081 |
| 10 | all | 378 | 3.811 | -0.744 | -0.356 | -0.074 | -0.036 | 0.381 | 48.7% | 6.541 | 76 | 118 | 24.171 |
| 10 | without_stop | 203 | 3.635 | -0.419 | -0.508 | -0.042 | -0.051 | 0.364 | 51.7% | 6.735 | 44 | 54 | 21.930 |
| 10 | with_stop | 175 | 4.015 | -1.121 | -0.275 | -0.112 | -0.027 | 0.401 | 45.1% | 6.315 | 32 | 64 | 26.772 |
| finish | all | 428 | 8.885 | -0.248 | -1.016 | -0.152 | -0.051 | 0.391 | 51.4% | 16.394 | 54 | 154 | 51.196 |
| finish | without_stop | 157 | 6.198 | -4.588 | -4.633 | -0.445 | -0.487 | 0.530 | 36.9% | 8.031 | 11 | 88 | 40.569 |
| finish | with_stop | 271 | 10.441 | +2.267 | +1.707 | +0.018 | +0.054 | 0.311 | 59.8% | 21.240 | 43 | 66 | 57.353 |

## spain_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 542 | 0.781 | +0.049 | -0.142 | +0.049 | -0.142 | 0.781 | 62.7% | 1.183 | 73 | 129 | 5.399 |
| 1 | without_stop | 514 | 0.535 | -0.237 | -0.165 | -0.237 | -0.165 | 0.535 | 66.1% | 1.168 | 45 | 129 | 3.112 |
| 1 | with_stop | 28 | 5.303 | +5.303 | +5.401 | +5.303 | +5.401 | 5.303 | 0.0% | 1.472 | 28 | 0 | 47.381 |
| 5 | all | 540 | 2.854 | -1.225 | -1.296 | -0.245 | -0.259 | 0.571 | 41.9% | 4.030 | 81 | 233 | 18.343 |
| 5 | without_stop | 400 | 2.555 | -1.172 | -1.120 | -0.234 | -0.224 | 0.511 | 46.5% | 4.116 | 53 | 161 | 15.510 |
| 5 | with_stop | 140 | 3.708 | -1.378 | -1.672 | -0.276 | -0.334 | 0.742 | 28.6% | 3.786 | 28 | 72 | 26.437 |
| 10 | all | 490 | 4.985 | -2.306 | -2.433 | -0.231 | -0.243 | 0.498 | 43.3% | 7.332 | 61 | 217 | 31.382 |
| 10 | without_stop | 234 | 5.485 | -1.948 | -2.254 | -0.195 | -0.225 | 0.549 | 40.2% | 7.940 | 46 | 94 | 32.926 |
| 10 | with_stop | 256 | 4.527 | -2.634 | -2.542 | -0.263 | -0.254 | 0.453 | 46.1% | 6.776 | 15 | 123 | 29.970 |
| finish | all | 542 | 16.427 | -8.693 | -5.631 | -0.343 | -0.256 | 0.560 | 40.8% | 21.165 | 59 | 262 | 106.909 |
| finish | without_stop | 127 | 9.829 | -7.839 | -6.320 | -0.722 | -0.651 | 0.867 | 37.0% | 10.415 | 7 | 73 | 63.365 |
| finish | with_stop | 415 | 18.446 | -8.955 | -5.264 | -0.226 | -0.176 | 0.466 | 41.9% | 24.455 | 52 | 189 | 120.235 |

## france_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 395 | 0.406 | -0.116 | -0.056 | -0.116 | -0.056 | 0.406 | 67.3% | 0.929 | 60 | 69 | 2.460 |
| 1 | without_stop | 393 | 0.341 | -0.050 | -0.055 | -0.050 | -0.055 | 0.341 | 67.7% | 0.928 | 60 | 67 | 1.830 |
| 1 | with_stop | 2 | 13.052 | -13.052 | -13.052 | -13.052 | -13.052 | 13.052 | 0.0% | 1.060 | 0 | 2 | 126.316 |
| 5 | all | 316 | 1.633 | -0.292 | -0.095 | -0.058 | -0.019 | 0.327 | 58.2% | 3.258 | 57 | 75 | 10.135 |
| 5 | without_stop | 309 | 1.382 | -0.011 | -0.048 | -0.002 | -0.010 | 0.276 | 59.5% | 3.266 | 57 | 68 | 7.673 |
| 5 | with_stop | 7 | 12.683 | -12.683 | -13.715 | -2.537 | -2.743 | 2.537 | 0.0% | 2.934 | 0 | 7 | 118.777 |
| 10 | all | 217 | 3.135 | -0.517 | -0.521 | -0.052 | -0.052 | 0.313 | 57.1% | 6.158 | 41 | 52 | 19.862 |
| 10 | without_stop | 208 | 2.631 | +0.101 | -0.347 | +0.010 | -0.035 | 0.263 | 59.6% | 6.208 | 41 | 43 | 14.986 |
| 10 | with_stop | 9 | 14.792 | -14.792 | -15.011 | -1.479 | -1.501 | 1.479 | 0.0% | 4.996 | 0 | 9 | 132.557 |

Finish: N=0, unavailable.

## pooled_prediction

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.650 | +0.068 | -0.091 | +0.068 | -0.091 | 0.650 | 63.6% | 1.059 | 211 | 286 | 4.492 |
| 1 | without_stop | 1315 | 0.436 | -0.129 | -0.114 | -0.129 | -0.114 | 0.436 | 66.0% | 1.046 | 163 | 284 | 2.486 |
| 1 | with_stop | 50 | 6.279 | +5.234 | +5.921 | +5.234 | +5.921 | 6.279 | 0.0% | 1.406 | 48 | 2 | 57.244 |
| 5 | all | 1284 | 2.365 | -0.763 | -0.682 | -0.153 | -0.136 | 0.473 | 47.7% | 3.629 | 210 | 462 | 15.226 |
| 5 | without_stop | 1034 | 1.981 | -0.588 | -0.508 | -0.118 | -0.102 | 0.396 | 52.6% | 3.632 | 159 | 331 | 11.827 |
| 5 | with_stop | 250 | 3.953 | -1.483 | -1.810 | -0.297 | -0.362 | 0.791 | 27.2% | 3.618 | 51 | 131 | 29.288 |
| 10 | all | 1085 | 4.206 | -1.404 | -1.118 | -0.140 | -0.112 | 0.421 | 47.9% | 6.821 | 178 | 387 | 26.566 |
| 10 | without_stop | 645 | 3.982 | -0.806 | -0.787 | -0.081 | -0.079 | 0.398 | 50.1% | 7.002 | 131 | 191 | 23.680 |
| 10 | with_stop | 440 | 4.533 | -2.281 | -1.782 | -0.228 | -0.178 | 0.453 | 44.8% | 6.557 | 47 | 196 | 30.797 |
| finish | all | 970 | 13.099 | -4.967 | -3.288 | -0.258 | -0.159 | 0.485 | 45.5% | 19.060 | 113 | 416 | 82.326 |
| finish | without_stop | 284 | 7.822 | -6.042 | -5.322 | -0.569 | -0.546 | 0.681 | 37.0% | 9.097 | 18 | 161 | 50.763 |
| finish | with_stop | 686 | 15.284 | -4.522 | -1.644 | -0.130 | -0.051 | 0.405 | 49.0% | 23.185 | 95 | 255 | 95.394 |

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.632 | +0.065 | -0.087 | +0.065 | -0.087 | 0.632 | 63.8% | 1.044 | 211 | 286 | 4.359 |
| 1 | without_stop | 1315 | 0.426 | -0.118 | -0.112 | -0.118 | -0.112 | 0.426 | 66.0% | 1.034 | 163 | 284 | 2.424 |
| 1 | with_stop | 50 | 8.441 | -0.260 | +5.401 | -0.260 | +5.401 | 8.441 | 0.0% | 1.293 | 48 | 2 | 79.281 |
| 5 | all | 1284 | 2.258 | -0.681 | -0.589 | -0.136 | -0.118 | 0.452 | 49.1% | 3.562 | 210 | 462 | 14.510 |
| 5 | without_stop | 1034 | 1.927 | -0.534 | -0.472 | -0.107 | -0.094 | 0.385 | 53.2% | 3.588 | 159 | 331 | 11.475 |
| 5 | with_stop | 250 | 6.694 | -4.975 | -3.316 | -0.995 | -0.663 | 1.339 | 18.6% | 3.385 | 51 | 131 | 57.432 |
| 10 | all | 1085 | 3.977 | -1.189 | -0.868 | -0.119 | -0.087 | 0.398 | 49.7% | 6.677 | 178 | 387 | 25.138 |
| 10 | without_stop | 645 | 3.917 | -0.755 | -0.692 | -0.076 | -0.069 | 0.392 | 50.5% | 6.961 | 131 | 191 | 23.280 |
| 10 | with_stop | 440 | 7.778 | -6.182 | -5.010 | -0.618 | -0.501 | 0.778 | 30.4% | 6.029 | 47 | 196 | 63.100 |
| finish | all | 970 | 12.656 | -4.471 | -3.059 | -0.247 | -0.131 | 0.475 | 46.1% | 18.780 | 113 | 416 | 79.053 |
| finish | without_stop | 284 | 8.013 | -6.214 | -5.478 | -0.583 | -0.554 | 0.698 | 37.0% | 9.223 | 18 | 161 | 51.967 |
| finish | with_stop | 686 | 14.444 | -3.344 | -0.354 | -0.104 | -0.010 | 0.388 | 50.9% | 22.847 | 95 | 255 | 88.794 |

# Full combined metrics: unchanged reference

## bahrain_2021

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 429 | 0.709 | +0.260 | -0.087 | +0.260 | -0.087 | 0.709 | 61.3% | 1.020 | 78 | 88 | 5.207 |
| 1 | without_stop | 409 | 0.402 | -0.068 | -0.106 | -0.068 | -0.106 | 0.402 | 64.3% | 1.004 | 58 | 88 | 2.325 |
| 1 | with_stop | 20 | 6.968 | +6.968 | +7.063 | +6.968 | +7.063 | 6.968 | 0.0% | 1.348 | 20 | 0 | 64.145 |
| 5 | all | 429 | 2.265 | -0.402 | -0.582 | -0.080 | -0.116 | 0.453 | 49.9% | 3.715 | 81 | 134 | 14.350 |
| 5 | without_stop | 326 | 1.826 | -0.291 | -0.205 | -0.058 | -0.041 | 0.365 | 55.5% | 3.692 | 56 | 89 | 10.803 |
| 5 | with_stop | 103 | 3.655 | -0.755 | -1.627 | -0.151 | -0.325 | 0.731 | 32.0% | 3.786 | 25 | 45 | 25.577 |
| 10 | all | 379 | 3.818 | -0.245 | +0.106 | -0.024 | +0.011 | 0.382 | 78.4% | 35.290 | 82 | 0 | 41.525 |
| 10 | without_stop | 204 | 3.639 | +0.126 | +0.136 | +0.013 | +0.014 | 0.364 | 77.0% | 35.417 | 47 | 0 | 42.539 |
| 10 | with_stop | 175 | 4.027 | -0.677 | +0.106 | -0.068 | +0.011 | 0.403 | 80.0% | 35.143 | 35 | 0 | 40.343 |
| finish | all | 429 | 12.697 | +7.125 | +2.861 | +0.053 | +0.103 | 0.475 | 71.6% | 139.221 | 81 | 41 | 156.780 |
| finish | without_stop | 158 | 5.965 | -3.340 | -4.134 | -0.370 | -0.408 | 0.503 | 69.0% | 68.725 | 13 | 36 | 79.535 |
| finish | with_stop | 271 | 16.622 | +13.226 | +11.175 | +0.300 | +0.323 | 0.459 | 73.1% | 180.321 | 68 | 5 | 201.816 |

## spain_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 542 | 0.781 | +0.049 | -0.142 | +0.049 | -0.142 | 0.781 | 62.7% | 1.183 | 73 | 129 | 5.399 |
| 1 | without_stop | 514 | 0.535 | -0.237 | -0.165 | -0.237 | -0.165 | 0.535 | 66.1% | 1.168 | 45 | 129 | 3.112 |
| 1 | with_stop | 28 | 5.303 | +5.303 | +5.401 | +5.303 | +5.401 | 5.303 | 0.0% | 1.472 | 28 | 0 | 47.381 |
| 5 | all | 540 | 2.811 | -1.063 | -1.146 | -0.213 | -0.229 | 0.562 | 46.9% | 4.377 | 89 | 198 | 17.208 |
| 5 | without_stop | 400 | 2.503 | -1.002 | -0.962 | -0.200 | -0.192 | 0.501 | 50.2% | 4.462 | 61 | 138 | 14.383 |
| 5 | with_stop | 140 | 3.689 | -1.237 | -1.568 | -0.247 | -0.314 | 0.738 | 37.1% | 4.134 | 28 | 60 | 25.277 |
| 10 | all | 490 | 4.888 | -1.683 | -1.760 | -0.168 | -0.176 | 0.489 | 85.3% | 32.865 | 72 | 0 | 37.510 |
| 10 | without_stop | 234 | 5.365 | -1.270 | -1.530 | -0.127 | -0.153 | 0.537 | 78.2% | 33.036 | 51 | 0 | 40.175 |
| 10 | with_stop | 256 | 4.452 | -2.061 | -1.930 | -0.206 | -0.193 | 0.445 | 91.8% | 32.709 | 21 | 0 | 35.074 |
| finish | all | 542 | 16.007 | +1.313 | -1.174 | -0.092 | -0.054 | 0.544 | 77.7% | 174.074 | 93 | 28 | 189.499 |
| finish | without_stop | 127 | 8.608 | -6.198 | -4.811 | -0.612 | -0.455 | 0.792 | 71.7% | 53.100 | 8 | 28 | 71.753 |
| finish | with_stop | 415 | 18.271 | +3.612 | +3.748 | +0.067 | +0.135 | 0.468 | 79.5% | 211.095 | 85 | 0 | 225.532 |

## france_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 429 | 1.455 | -1.181 | -0.083 | -1.181 | -0.083 | 1.455 | 62.9% | 0.937 | 62 | 97 | 12.753 |
| 1 | without_stop | 418 | 0.950 | -0.669 | -0.075 | -0.669 | -0.075 | 0.950 | 64.6% | 0.933 | 62 | 86 | 7.762 |
| 1 | with_stop | 11 | 20.664 | -20.664 | -18.451 | -20.664 | -18.451 | 20.664 | 0.0% | 1.083 | 0 | 11 | 202.391 |
| 5 | all | 429 | 15.288 | -11.448 | -0.573 | -2.290 | -0.115 | 3.058 | 45.5% | 3.477 | 82 | 152 | 144.502 |
| 5 | without_stop | 374 | 6.928 | -2.523 | -0.173 | -0.505 | -0.035 | 1.386 | 52.1% | 3.581 | 82 | 97 | 61.313 |
| 5 | with_stop | 55 | 72.138 | -72.138 | -94.720 | -14.428 | -18.944 | 14.428 | 0.0% | 2.766 | 0 | 55 | 710.187 |
| 10 | all | 379 | 31.957 | -26.862 | -2.576 | -2.686 | -0.258 | 3.196 | 55.7% | 35.392 | 61 | 107 | 221.262 |
| 10 | without_stop | 269 | 9.579 | -2.401 | -0.128 | -0.240 | -0.013 | 0.958 | 71.4% | 35.319 | 61 | 16 | 66.391 |
| 10 | with_stop | 110 | 86.682 | -86.682 | -99.939 | -8.668 | -9.994 | 8.668 | 17.3% | 35.572 | 0 | 91 | 599.994 |
| finish | all | 429 | 57.359 | -55.723 | -34.581 | -2.341 | -2.316 | 2.389 | 85.1% | 140.470 | 10 | 54 | 181.476 |
| finish | without_stop | 278 | 30.810 | -28.687 | -30.924 | -2.158 | -1.815 | 2.221 | 77.3% | 110.088 | 9 | 54 | 171.654 |
| finish | with_stop | 151 | 106.238 | -105.499 | -113.780 | -2.678 | -2.630 | 2.699 | 99.3% | 196.405 | 1 | 0 | 199.559 |

## pooled_prediction

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1400 | 0.965 | -0.263 | -0.110 | -0.263 | -0.110 | 0.965 | 62.4% | 1.058 | 213 | 314 | 7.594 |
| 1 | without_stop | 1341 | 0.624 | -0.320 | -0.117 | -0.320 | -0.117 | 0.624 | 65.1% | 1.045 | 165 | 303 | 4.322 |
| 1 | with_stop | 59 | 8.731 | +1.026 | +5.629 | +1.026 | +5.629 | 8.731 | 0.0% | 1.357 | 48 | 11 | 81.964 |
| 5 | all | 1398 | 6.472 | -4.047 | -0.743 | -0.809 | -0.149 | 1.294 | 47.4% | 3.897 | 252 | 484 | 55.393 |
| 5 | without_stop | 1100 | 3.807 | -1.308 | -0.446 | -0.262 | -0.089 | 0.761 | 52.5% | 3.934 | 199 | 324 | 29.278 |
| 5 | with_stop | 298 | 16.310 | -14.156 | -2.241 | -2.831 | -0.448 | 3.262 | 28.5% | 3.761 | 53 | 160 | 151.790 |
| 10 | all | 1248 | 12.783 | -8.893 | -1.303 | -0.889 | -0.130 | 1.278 | 74.2% | 34.369 | 215 | 107 | 94.532 |
| 10 | without_stop | 707 | 6.470 | -1.297 | -0.406 | -0.130 | -0.041 | 0.647 | 75.2% | 34.592 | 159 | 16 | 50.832 |
| 10 | with_stop | 541 | 21.034 | -18.819 | -2.739 | -1.882 | -0.274 | 2.103 | 72.8% | 34.078 | 56 | 91 | 151.642 |
| finish | all | 1400 | 27.664 | -14.384 | -5.677 | -0.737 | -0.335 | 1.088 | 78.1% | 153.097 | 184 | 123 | 177.015 |
| finish | without_stop | 563 | 18.829 | -16.501 | -15.116 | -1.308 | -0.877 | 1.416 | 73.7% | 85.625 | 30 | 118 | 123.266 |
| finish | with_stop | 837 | 33.607 | -12.960 | +1.977 | -0.353 | +0.054 | 0.868 | 81.0% | 198.481 | 154 | 5 | 213.168 |

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1400 | 0.982 | -0.291 | -0.102 | -0.291 | -0.102 | 0.982 | 62.3% | 1.047 | 213 | 314 | 7.787 |
| 1 | without_stop | 1341 | 0.629 | -0.325 | -0.115 | -0.325 | -0.115 | 0.629 | 65.0% | 1.035 | 165 | 303 | 4.400 |
| 1 | with_stop | 59 | 10.978 | -2.798 | +5.401 | -2.798 | +5.401 | 10.978 | 0.0% | 1.301 | 48 | 11 | 104.639 |
| 5 | all | 1398 | 6.788 | -4.304 | -0.711 | -0.861 | -0.142 | 1.358 | 47.4% | 3.856 | 252 | 484 | 58.687 |
| 5 | without_stop | 1100 | 3.752 | -1.272 | -0.439 | -0.254 | -0.088 | 0.750 | 52.6% | 3.912 | 199 | 324 | 28.833 |
| 5 | with_stop | 298 | 26.494 | -24.710 | -3.106 | -4.942 | -0.621 | 5.299 | 23.1% | 3.562 | 53 | 160 | 253.680 |
| 10 | all | 1248 | 13.554 | -9.597 | -1.271 | -0.960 | -0.127 | 1.355 | 73.1% | 34.516 | 215 | 107 | 100.099 |
| 10 | without_stop | 707 | 6.194 | -1.182 | -0.348 | -0.118 | -0.035 | 0.619 | 75.5% | 34.591 | 159 | 16 | 49.702 |
| 10 | with_stop | 541 | 31.720 | -29.807 | -4.523 | -2.981 | -0.452 | 3.172 | 63.0% | 34.474 | 56 | 91 | 225.137 |
| finish | all | 1400 | 28.688 | -15.762 | -6.219 | -0.793 | -0.390 | 1.136 | 78.1% | 151.255 | 184 | 123 | 175.918 |
| finish | without_stop | 563 | 15.128 | -12.742 | -8.660 | -1.047 | -0.707 | 1.172 | 72.7% | 77.304 | 30 | 118 | 107.647 |
| finish | with_stop | 837 | 47.044 | -29.554 | -3.405 | -0.770 | -0.111 | 1.209 | 84.0% | 195.941 | 154 | 5 | 208.969 |

# Neutralization-start calibration


## bahrain_2021

| Horizon | N | Brier score | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 429 | 0.00022 | 0.015 | 0.000 | 0 |
| 5 | 429 | 0.00511 | 0.071 | 0.000 | 0 |
| 10 | 379 | 0.01899 | 0.138 | 0.000 | 0 |
| finish | 429 | 0.11653 | 0.315 | 0.000 | 0 |

### Reliability: 1

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 429 | 0.015 | 0.000 | 0 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 5

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 429 | 0.071 | 0.000 | 0 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 10

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 0 | — | — | 0 |
| [0.1, 0.2) | 379 | 0.138 | 0.000 | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: finish

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 30 | 0.085 | 0.000 | 0 |
| [0.1, 0.2) | 80 | 0.156 | 0.000 | 0 |
| [0.2, 0.3) | 83 | 0.255 | 0.000 | 0 |
| [0.3, 0.4) | 96 | 0.355 | 0.000 | 0 |
| [0.4, 0.5) | 110 | 0.450 | 0.000 | 0 |
| [0.5, 0.6) | 30 | 0.509 | 0.000 | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

## spain_2022

| Horizon | N | Brier score | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 542 | 0.00022 | 0.015 | 0.000 | 0 |
| 5 | 540 | 0.00511 | 0.071 | 0.000 | 0 |
| 10 | 490 | 0.01899 | 0.138 | 0.000 | 0 |
| finish | 542 | 0.15765 | 0.366 | 0.000 | 0 |

### Reliability: 1

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 542 | 0.015 | 0.000 | 0 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 5

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 540 | 0.071 | 0.000 | 0 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 10

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 0 | — | — | 0 |
| [0.1, 0.2) | 490 | 0.138 | 0.000 | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: finish

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 32 | 0.083 | 0.000 | 0 |
| [0.1, 0.2) | 74 | 0.154 | 0.000 | 0 |
| [0.2, 0.3) | 87 | 0.256 | 0.000 | 0 |
| [0.3, 0.4) | 93 | 0.352 | 0.000 | 0 |
| [0.4, 0.5) | 117 | 0.451 | 0.000 | 0 |
| [0.5, 0.6) | 139 | 0.550 | 0.000 | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

## france_2022

| Horizon | N | Brier score | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 429 | 0.04093 | 0.014 | 0.042 | 18 |
| 5 | 429 | 0.19879 | 0.070 | 0.226 | 97 |
| 10 | 379 | 0.29776 | 0.137 | 0.385 | 146 |
| finish | 429 | 0.49223 | 0.310 | 1.000 | 429 |

### Reliability: 1

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 429 | 0.014 | 0.042 | 18 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 5

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 429 | 0.070 | 0.226 | 97 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 10

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 11 | 0.097 | 0.000 | 0 |
| [0.1, 0.2) | 368 | 0.138 | 0.397 | 146 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: finish

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 30 | 0.085 | 1.000 | 30 |
| [0.1, 0.2) | 79 | 0.156 | 1.000 | 79 |
| [0.2, 0.3) | 90 | 0.256 | 1.000 | 90 |
| [0.3, 0.4) | 101 | 0.351 | 1.000 | 101 |
| [0.4, 0.5) | 109 | 0.455 | 1.000 | 109 |
| [0.5, 0.6) | 20 | 0.506 | 1.000 | 20 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

## pooled_prediction

| Horizon | N | Brier score | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 1400 | 0.01269 | 0.015 | 0.013 | 18 |
| 5 | 1398 | 0.06454 | 0.071 | 0.069 | 97 |
| 10 | 1248 | 0.10365 | 0.137 | 0.117 | 146 |
| finish | 1400 | 0.24758 | 0.333 | 0.306 | 429 |

### Reliability: 1

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 1400 | 0.015 | 0.013 | 18 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 5

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 1398 | 0.071 | 0.069 | 97 |
| [0.1, 0.2) | 0 | — | — | 0 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: 10

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 11 | 0.097 | 0.000 | 0 |
| [0.1, 0.2) | 1237 | 0.138 | 0.118 | 146 |
| [0.2, 0.3) | 0 | — | — | 0 |
| [0.3, 0.4) | 0 | — | — | 0 |
| [0.4, 0.5) | 0 | — | — | 0 |
| [0.5, 0.6) | 0 | — | — | 0 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

### Reliability: finish

| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |
| --- | ---: | ---: | ---: | ---: |
| [0.0, 0.1) | 92 | 0.084 | 0.326 | 30 |
| [0.1, 0.2) | 233 | 0.156 | 0.339 | 79 |
| [0.2, 0.3) | 260 | 0.256 | 0.346 | 90 |
| [0.3, 0.4) | 290 | 0.353 | 0.348 | 101 |
| [0.4, 0.5) | 336 | 0.452 | 0.324 | 109 |
| [0.5, 0.6) | 189 | 0.539 | 0.106 | 20 |
| [0.6, 0.7) | 0 | — | — | 0 |
| [0.7, 0.8) | 0 | — | — | 0 |
| [0.8, 0.9) | 0 | — | — | 0 |
| [0.9, 1.0] | 0 | — | — | 0 |

## Conditional green plots

[bahrain_2021: predicted vs actual](bahrain_2021/predicted_vs_actual.png) · [error vs horizon](bahrain_2021/error_vs_horizon.png)

[spain_2022: predicted vs actual](spain_2022/predicted_vs_actual.png) · [error vs horizon](spain_2022/error_vs_horizon.png)

[france_2022: predicted vs actual](france_2022/predicted_vs_actual.png) · [error vs horizon](france_2022/error_vs_horizon.png)

