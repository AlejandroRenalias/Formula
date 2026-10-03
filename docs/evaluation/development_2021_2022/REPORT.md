# Three-race dry development evaluation

Bahrain 2021, Spain 2022 and France 2022 only. The committed median anchor, driver-local pace uncertainty and unestimated 50/50 pit allocation are identical across races. No fitting, other model changes, held-out/wet runs or UI edits.

## Dataset and exclusions

| Race | Scheduled laps | Attempted / valid snapshots | Scored predictions | Runtime s | Stride |
| --- | ---: | ---: | ---: | ---: | ---: |
| bahrain_2021 | 56 | 470 / 429 | 1666 | 279.84 | 1 |
| spain_2022 | 66 | 570 / 542 | 2114 | 427.64 | 1 |
| france_2022 | 53 | 440 / 429 | 1666 | 243.16 | 1 |

Top ten finishers per race; cutoffs from lap 5 through scheduled distance minus 5. Each race was benchmarked separately; every-lap stride retained where below 30 minutes. Acquisition used FastF1 3.8.3 once per authorized race; evaluation and this report run with network connections blocked. Hash-verified normalized and raw caches are local/ignored.

| Race | Exclusion scope | Reason | Count |
| --- | --- | --- | ---: |
| bahrain_2021 | snapshot | no_recent_clean_pace | 20 |
| bahrain_2021 | snapshot | subject_stop_straddles_cutoff | 20 |
| bahrain_2021 | snapshot | unknown_compound | 1 |
| bahrain_2021 | target | target_beyond_finish_or_missing | 50 |
| spain_2022 | snapshot | subject_stop_straddles_cutoff | 28 |
| spain_2022 | target | target_beyond_finish_or_missing | 54 |
| france_2022 | snapshot | subject_stop_straddles_cutoff | 11 |
| france_2022 | target | target_beyond_finish_or_missing | 50 |

| Race | Cutoff status | Valid snapshots |
| --- | --- | ---: |
| bahrain_2021 | GREEN | 428 |
| bahrain_2021 | YELLOW | 1 |
| spain_2022 | GREEN | 542 |
| france_2022 | GREEN | 413 |
| france_2022 | SAFETY_CAR | 11 |
| france_2022 | YELLOW | 5 |

France acquisition warned about late timing data for SAI around laps 13/14 and a 41 ms recorded session-end discrepancy for VER. The cached original streams/corrected crossing labels are retained; no retrospective repair is inserted into engine inputs.

## Per-race and pooled metrics

Error is predicted median minus actual. Error per lap divides each row's error by its actual horizon length before aggregation. Coverage is inclusive p10-p90, nominally 80%. Pit/no-pit uses actual subject entry in (cutoff,target], solely on the outcome side. All snapshots are correlated; final classification selects the survivor cohort. Pooled metrics concatenate predictions: races with more valid cutoffs receive more weight, not equal race weights.

### bahrain_2021

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 429 | 0.709 | +0.260 | -0.087 | +0.260 | -0.087 | 0.709 | 61.3% | 1.020 | 78 | 88 | 5.207 |
| 1 | without_stop | 409 | 0.402 | -0.068 | -0.106 | -0.068 | -0.106 | 0.402 | 64.3% | 1.004 | 58 | 88 | 2.325 |
| 1 | with_stop | 20 | 6.968 | +6.968 | +7.063 | +6.968 | +7.063 | 6.968 | 0.0% | 1.348 | 20 | 0 | 64.145 |
| 5 | all | 429 | 2.296 | -0.596 | -0.728 | -0.119 | -0.146 | 0.459 | 46.6% | 3.261 | 75 | 154 | 15.098 |
| 5 | without_stop | 326 | 1.841 | -0.483 | -0.506 | -0.097 | -0.101 | 0.368 | 52.8% | 3.239 | 52 | 102 | 11.243 |
| 5 | with_stop | 103 | 3.736 | -0.954 | -1.771 | -0.191 | -0.354 | 0.747 | 27.2% | 3.331 | 23 | 52 | 27.299 |
| 10 | all | 379 | 3.795 | -0.958 | -0.530 | -0.096 | -0.053 | 0.379 | 45.6% | 5.938 | 80 | 126 | 24.971 |
| 10 | without_stop | 204 | 3.617 | -0.577 | -0.528 | -0.058 | -0.053 | 0.362 | 47.5% | 6.040 | 47 | 60 | 22.710 |
| 10 | with_stop | 175 | 4.002 | -1.402 | -0.577 | -0.140 | -0.058 | 0.400 | 43.4% | 5.819 | 33 | 66 | 27.606 |
| finish | all | 429 | 8.519 | -1.458 | -2.185 | -0.186 | -0.084 | 0.386 | 47.6% | 15.763 | 57 | 168 | 51.740 |
| finish | without_stop | 158 | 6.315 | -4.573 | -4.883 | -0.449 | -0.496 | 0.539 | 32.3% | 7.302 | 12 | 95 | 41.695 |
| finish | with_stop | 271 | 9.804 | +0.358 | +0.664 | -0.033 | +0.014 | 0.296 | 56.5% | 20.696 | 45 | 73 | 57.597 |

### spain_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 542 | 0.781 | +0.049 | -0.142 | +0.049 | -0.142 | 0.781 | 62.7% | 1.183 | 73 | 129 | 5.399 |
| 1 | without_stop | 514 | 0.535 | -0.237 | -0.165 | -0.237 | -0.165 | 0.535 | 66.1% | 1.168 | 45 | 129 | 3.112 |
| 1 | with_stop | 28 | 5.303 | +5.303 | +5.401 | +5.303 | +5.401 | 5.303 | 0.0% | 1.472 | 28 | 0 | 47.381 |
| 5 | all | 540 | 2.881 | -1.305 | -1.392 | -0.261 | -0.278 | 0.576 | 41.1% | 3.856 | 87 | 231 | 18.415 |
| 5 | without_stop | 400 | 2.576 | -1.240 | -1.253 | -0.248 | -0.251 | 0.515 | 45.5% | 3.922 | 59 | 159 | 15.484 |
| 5 | with_stop | 140 | 3.753 | -1.492 | -1.776 | -0.298 | -0.355 | 0.751 | 28.6% | 3.666 | 28 | 72 | 26.790 |
| 10 | all | 490 | 5.032 | -2.525 | -2.634 | -0.253 | -0.263 | 0.503 | 40.4% | 6.679 | 66 | 226 | 32.325 |
| 10 | without_stop | 234 | 5.534 | -2.122 | -2.516 | -0.212 | -0.252 | 0.553 | 38.0% | 7.222 | 50 | 95 | 34.066 |
| 10 | with_stop | 256 | 4.574 | -2.893 | -2.691 | -0.289 | -0.269 | 0.457 | 42.6% | 6.181 | 16 | 131 | 30.733 |
| finish | all | 542 | 16.702 | -10.356 | -7.479 | -0.384 | -0.289 | 0.564 | 39.7% | 20.821 | 58 | 269 | 108.721 |
| finish | without_stop | 127 | 9.909 | -7.985 | -6.339 | -0.738 | -0.662 | 0.873 | 35.4% | 9.586 | 7 | 75 | 66.677 |
| finish | with_stop | 415 | 18.781 | -11.081 | -7.704 | -0.276 | -0.217 | 0.470 | 41.0% | 24.259 | 51 | 194 | 121.587 |

### france_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 429 | 1.583 | -0.614 | -0.063 | -0.614 | -0.063 | 1.583 | 62.9% | 0.917 | 71 | 88 | 14.124 |
| 1 | without_stop | 418 | 1.081 | -0.086 | -0.055 | -0.086 | -0.055 | 1.081 | 64.6% | 0.913 | 71 | 77 | 9.170 |
| 1 | with_stop | 11 | 20.664 | -20.664 | -18.451 | -20.664 | -18.451 | 20.664 | 0.0% | 1.083 | 0 | 11 | 202.391 |
| 5 | all | 429 | 22.237 | -4.691 | -0.745 | -0.938 | -0.149 | 4.447 | 41.7% | 3.000 | 79 | 171 | 215.142 |
| 5 | without_stop | 374 | 14.875 | +5.251 | -0.298 | +1.050 | -0.060 | 2.975 | 47.9% | 3.071 | 79 | 116 | 141.817 |
| 5 | with_stop | 55 | 72.301 | -72.301 | -95.092 | -14.460 | -19.018 | 14.460 | 0.0% | 2.519 | 0 | 55 | 713.756 |
| 10 | all | 379 | 51.547 | -8.082 | -3.165 | -0.808 | -0.316 | 5.155 | 31.4% | 5.101 | 59 | 201 | 502.284 |
| 10 | without_stop | 269 | 36.937 | +24.302 | -0.927 | +2.430 | -0.093 | 3.694 | 44.2% | 5.302 | 59 | 91 | 357.055 |
| 10 | with_stop | 110 | 87.274 | -87.274 | -100.351 | -8.727 | -10.035 | 8.727 | 0.0% | 4.609 | 0 | 110 | 857.432 |
| finish | all | 429 | 130.620 | +2.818 | -36.519 | -0.619 | -2.571 | 4.538 | 0.0% | 13.467 | 11 | 418 | 1252.363 |
| finish | without_stop | 278 | 125.876 | +59.746 | -33.789 | +0.398 | -1.904 | 5.053 | 0.0% | 9.809 | 10 | 268 | 1217.000 |
| finish | with_stop | 151 | 139.354 | -101.989 | -133.307 | -2.490 | -3.098 | 3.589 | 0.0% | 20.201 | 1 | 150 | 1317.467 |

### pooled

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1400 | 1.005 | -0.089 | -0.095 | -0.089 | -0.095 | 1.005 | 62.4% | 1.052 | 222 | 305 | 8.014 |
| 1 | without_stop | 1341 | 0.665 | -0.138 | -0.114 | -0.138 | -0.114 | 0.665 | 65.1% | 1.038 | 174 | 294 | 4.761 |
| 1 | with_stop | 59 | 8.731 | +1.026 | +5.629 | +1.026 | +5.629 | 8.731 | 0.0% | 1.357 | 48 | 11 | 81.964 |
| 5 | all | 1398 | 8.641 | -2.127 | -0.951 | -0.425 | -0.190 | 1.728 | 43.0% | 3.411 | 241 | 556 | 77.766 |
| 5 | without_stop | 1100 | 6.540 | +1.191 | -0.654 | +0.238 | -0.131 | 1.308 | 48.5% | 3.430 | 190 | 377 | 57.180 |
| 5 | with_stop | 298 | 16.399 | -14.375 | -2.490 | -2.875 | -0.498 | 3.280 | 22.8% | 3.339 | 51 | 179 | 153.755 |
| 10 | all | 1248 | 18.782 | -3.737 | -1.984 | -0.374 | -0.198 | 1.878 | 39.3% | 5.975 | 205 | 553 | 172.811 |
| 10 | without_stop | 707 | 16.929 | +8.377 | -1.119 | +0.838 | -0.112 | 1.693 | 43.1% | 6.151 | 156 | 246 | 153.681 |
| 10 | with_stop | 541 | 21.204 | -19.568 | -3.465 | -1.957 | -0.346 | 2.120 | 34.2% | 5.745 | 49 | 307 | 197.812 |
| finish | all | 1400 | 49.102 | -3.592 | -11.874 | -0.395 | -0.573 | 1.727 | 29.9% | 17.018 | 126 | 855 | 441.705 |
| finish | without_stop | 563 | 66.163 | +26.417 | -19.905 | -0.096 | -1.066 | 2.843 | 17.1% | 9.055 | 29 | 438 | 627.676 |
| finish | with_stop | 837 | 37.627 | -23.778 | -7.530 | -0.597 | -0.241 | 0.976 | 38.6% | 22.373 | 97 | 417 | 316.613 |

## Reference to the previous Bahrain-only run

Each cell is previous Bahrain pit-split / current. Spain and France have no previous same-race run. These comparisons are unmatched population references, not model improvements. The pooled comparison changes race composition while preserving the model.

### spain_2022 versus Bahrain

| Horizon | Stop group | N reference/current | Mean bias s | Median error s | MAE s | Mean error/lap s | Coverage |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429/542 | +0.260 / +0.049 | -0.087 / -0.142 | +0.709 / +0.781 | +0.260 / +0.049 | 61.3% / 62.7% |
| 1 | without_stop | 409/514 | -0.068 / -0.237 | -0.106 / -0.165 | +0.402 / +0.535 | -0.068 / -0.237 | 64.3% / 66.1% |
| 1 | with_stop | 20/28 | +6.968 / +5.303 | +7.063 / +5.401 | +6.968 / +5.303 | +6.968 / +5.303 | 0.0% / 0.0% |
| 5 | all | 429/540 | -0.596 / -1.305 | -0.728 / -1.392 | +2.296 / +2.881 | -0.119 / -0.261 | 46.6% / 41.1% |
| 5 | without_stop | 326/400 | -0.483 / -1.240 | -0.506 / -1.253 | +1.841 / +2.576 | -0.097 / -0.248 | 52.8% / 45.5% |
| 5 | with_stop | 103/140 | -0.954 / -1.492 | -1.771 / -1.776 | +3.736 / +3.753 | -0.191 / -0.298 | 27.2% / 28.6% |
| 10 | all | 379/490 | -0.958 / -2.525 | -0.530 / -2.634 | +3.795 / +5.032 | -0.096 / -0.253 | 45.6% / 40.4% |
| 10 | without_stop | 204/234 | -0.577 / -2.122 | -0.528 / -2.516 | +3.617 / +5.534 | -0.058 / -0.212 | 47.5% / 38.0% |
| 10 | with_stop | 175/256 | -1.402 / -2.893 | -0.577 / -2.691 | +4.002 / +4.574 | -0.140 / -0.289 | 43.4% / 42.6% |
| finish | all | 429/542 | -1.458 / -10.356 | -2.185 / -7.479 | +8.519 / +16.702 | -0.186 / -0.384 | 47.6% / 39.7% |
| finish | without_stop | 158/127 | -4.573 / -7.985 | -4.883 / -6.339 | +6.315 / +9.909 | -0.449 / -0.738 | 32.3% / 35.4% |
| finish | with_stop | 271/415 | +0.358 / -11.081 | +0.664 / -7.704 | +9.804 / +18.781 | -0.033 / -0.276 | 56.5% / 41.0% |

### france_2022 versus Bahrain

| Horizon | Stop group | N reference/current | Mean bias s | Median error s | MAE s | Mean error/lap s | Coverage |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429/429 | +0.260 / -0.614 | -0.087 / -0.063 | +0.709 / +1.583 | +0.260 / -0.614 | 61.3% / 62.9% |
| 1 | without_stop | 409/418 | -0.068 / -0.086 | -0.106 / -0.055 | +0.402 / +1.081 | -0.068 / -0.086 | 64.3% / 64.6% |
| 1 | with_stop | 20/11 | +6.968 / -20.664 | +7.063 / -18.451 | +6.968 / +20.664 | +6.968 / -20.664 | 0.0% / 0.0% |
| 5 | all | 429/429 | -0.596 / -4.691 | -0.728 / -0.745 | +2.296 / +22.237 | -0.119 / -0.938 | 46.6% / 41.7% |
| 5 | without_stop | 326/374 | -0.483 / +5.251 | -0.506 / -0.298 | +1.841 / +14.875 | -0.097 / +1.050 | 52.8% / 47.9% |
| 5 | with_stop | 103/55 | -0.954 / -72.301 | -1.771 / -95.092 | +3.736 / +72.301 | -0.191 / -14.460 | 27.2% / 0.0% |
| 10 | all | 379/379 | -0.958 / -8.082 | -0.530 / -3.165 | +3.795 / +51.547 | -0.096 / -0.808 | 45.6% / 31.4% |
| 10 | without_stop | 204/269 | -0.577 / +24.302 | -0.528 / -0.927 | +3.617 / +36.937 | -0.058 / +2.430 | 47.5% / 44.2% |
| 10 | with_stop | 175/110 | -1.402 / -87.274 | -0.577 / -100.351 | +4.002 / +87.274 | -0.140 / -8.727 | 43.4% / 0.0% |
| finish | all | 429/429 | -1.458 / +2.818 | -2.185 / -36.519 | +8.519 / +130.620 | -0.186 / -0.619 | 47.6% / 0.0% |
| finish | without_stop | 158/278 | -4.573 / +59.746 | -4.883 / -33.789 | +6.315 / +125.876 | -0.449 / +0.398 | 32.3% / 0.0% |
| finish | with_stop | 271/151 | +0.358 / -101.989 | +0.664 / -133.307 | +9.804 / +139.354 | -0.033 / -2.490 | 56.5% / 0.0% |

### pooled versus Bahrain

| Horizon | Stop group | N reference/current | Mean bias s | Median error s | MAE s | Mean error/lap s | Coverage |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429/1400 | +0.260 / -0.089 | -0.087 / -0.095 | +0.709 / +1.005 | +0.260 / -0.089 | 61.3% / 62.4% |
| 1 | without_stop | 409/1341 | -0.068 / -0.138 | -0.106 / -0.114 | +0.402 / +0.665 | -0.068 / -0.138 | 64.3% / 65.1% |
| 1 | with_stop | 20/59 | +6.968 / +1.026 | +7.063 / +5.629 | +6.968 / +8.731 | +6.968 / +1.026 | 0.0% / 0.0% |
| 5 | all | 429/1398 | -0.596 / -2.127 | -0.728 / -0.951 | +2.296 / +8.641 | -0.119 / -0.425 | 46.6% / 43.0% |
| 5 | without_stop | 326/1100 | -0.483 / +1.191 | -0.506 / -0.654 | +1.841 / +6.540 | -0.097 / +0.238 | 52.8% / 48.5% |
| 5 | with_stop | 103/298 | -0.954 / -14.375 | -1.771 / -2.490 | +3.736 / +16.399 | -0.191 / -2.875 | 27.2% / 22.8% |
| 10 | all | 379/1248 | -0.958 / -3.737 | -0.530 / -1.984 | +3.795 / +18.782 | -0.096 / -0.374 | 45.6% / 39.3% |
| 10 | without_stop | 204/707 | -0.577 / +8.377 | -0.528 / -1.119 | +3.617 / +16.929 | -0.058 / +0.838 | 47.5% / 43.1% |
| 10 | with_stop | 175/541 | -1.402 / -19.568 | -0.577 / -3.465 | +4.002 / +21.204 | -0.140 / -1.957 | 43.4% / 34.2% |
| finish | all | 429/1400 | -1.458 / -3.592 | -2.185 / -11.874 | +8.519 / +49.102 | -0.186 / -0.395 | 47.6% / 29.9% |
| finish | without_stop | 158/563 | -4.573 / +26.417 | -4.883 / -19.905 | +6.315 / +66.163 | -0.449 / -0.096 | 32.3% / 17.1% |
| finish | with_stop | 271/837 | +0.358 / -23.778 | +0.664 / -7.530 | +9.804 / +37.627 | -0.033 / -0.597 | 56.5% / 38.6% |

## No-stop tyre diagnostics

Groups use causal compound and tyre age at cutoff, not future tyre labels. Age bins are fixed at 0-9, 10-19, 20-29 and 30+ laps; joint compound/age groups help distinguish changing compound mix. Track-status groups show the unchanged safety-car persistence assumption separately. Every group reports sample count and row-normalized error. [GREEN-only supplementary tables](TYRE_DIAGNOSTICS_GREEN.md) reduce cutoff-status confounding without changing the model or headline metrics. Sparse bins and different finish-horizon lengths require caution. These are associations, not fitted degradation estimates or proof that wear alone causes the residuals.

### bahrain_2021

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | age | 0-9 | 167 | +0.060 | -0.010 | 0.444 | 65.3% |
| 1 | age | 10-19 | 215 | -0.146 | -0.144 | 0.366 | 61.9% |
| 1 | age | 20-29 | 22 | -0.207 | -0.235 | 0.456 | 77.3% |
| 1 | age | 30+ | 5 | -0.372 | -0.339 | 0.372 | 80.0% |
| 1 | compound | HARD | 224 | -0.026 | -0.089 | 0.432 | 60.3% |
| 1 | compound | MEDIUM | 161 | -0.128 | -0.135 | 0.351 | 69.6% |
| 1 | compound | SOFT | 24 | -0.056 | +0.012 | 0.465 | 66.7% |
| 1 | compound_and_age | HARD/0-9 | 107 | +0.181 | +0.037 | 0.460 | 60.7% |
| 1 | compound_and_age | HARD/10-19 | 92 | -0.214 | -0.222 | 0.396 | 54.3% |
| 1 | compound_and_age | HARD/20-29 | 20 | -0.191 | -0.195 | 0.464 | 80.0% |
| 1 | compound_and_age | HARD/30+ | 5 | -0.372 | -0.339 | 0.372 | 80.0% |
| 1 | compound_and_age | MEDIUM/0-9 | 60 | -0.156 | -0.114 | 0.414 | 73.3% |
| 1 | compound_and_age | MEDIUM/10-19 | 99 | -0.106 | -0.135 | 0.313 | 67.7% |
| 1 | compound_and_age | MEDIUM/20-29 | 2 | -0.373 | -0.373 | 0.373 | 50.0% |
| 1 | compound_and_age | SOFT/10-19 | 24 | -0.056 | +0.012 | 0.465 | 66.7% |
| 1 | track_status | GREEN | 408 | -0.068 | -0.104 | 0.403 | 64.2% |
| 1 | track_status | YELLOW | 1 | -0.184 | -0.184 | 0.184 | 100.0% |
| 10 | age | 0-9 | 147 | +0.026 | +0.005 | 0.328 | 53.7% |
| 10 | age | 10-19 | 51 | -0.323 | -0.372 | 0.456 | 25.5% |
| 10 | age | 20-29 | 6 | +0.138 | -0.019 | 0.396 | 83.3% |
| 10 | compound | HARD | 140 | -0.037 | -0.011 | 0.419 | 37.9% |
| 10 | compound | MEDIUM | 64 | -0.102 | -0.063 | 0.236 | 68.8% |
| 10 | compound_and_age | HARD/0-9 | 92 | +0.107 | +0.145 | 0.370 | 45.7% |
| 10 | compound_and_age | HARD/10-19 | 42 | -0.378 | -0.541 | 0.529 | 14.3% |
| 10 | compound_and_age | HARD/20-29 | 6 | +0.138 | -0.019 | 0.396 | 83.3% |
| 10 | compound_and_age | MEDIUM/0-9 | 55 | -0.109 | -0.067 | 0.257 | 67.3% |
| 10 | compound_and_age | MEDIUM/10-19 | 9 | -0.062 | -0.051 | 0.112 | 77.8% |
| 10 | track_status | GREEN | 203 | -0.057 | -0.053 | 0.362 | 47.8% |
| 10 | track_status | YELLOW | 1 | -0.295 | -0.295 | 0.295 | 0.0% |
| 5 | age | 0-9 | 166 | +0.026 | -0.000 | 0.344 | 61.4% |
| 5 | age | 10-19 | 141 | -0.206 | -0.203 | 0.372 | 44.7% |
| 5 | age | 20-29 | 18 | -0.354 | -0.500 | 0.563 | 33.3% |
| 5 | age | 30+ | 1 | -0.407 | -0.407 | 0.407 | 100.0% |
| 5 | compound | HARD | 205 | -0.103 | -0.136 | 0.431 | 42.4% |
| 5 | compound | MEDIUM | 117 | -0.075 | -0.037 | 0.257 | 70.9% |
| 5 | compound | SOFT | 4 | -0.395 | -0.430 | 0.395 | 50.0% |
| 5 | compound_and_age | HARD/0-9 | 106 | +0.118 | +0.074 | 0.369 | 54.7% |
| 5 | compound_and_age | HARD/10-19 | 80 | -0.336 | -0.343 | 0.485 | 27.5% |
| 5 | compound_and_age | HARD/20-29 | 18 | -0.354 | -0.500 | 0.563 | 33.3% |
| 5 | compound_and_age | HARD/30+ | 1 | -0.407 | -0.407 | 0.407 | 100.0% |
| 5 | compound_and_age | MEDIUM/0-9 | 60 | -0.136 | -0.130 | 0.299 | 73.3% |
| 5 | compound_and_age | MEDIUM/10-19 | 57 | -0.010 | -0.009 | 0.212 | 68.4% |
| 5 | compound_and_age | SOFT/10-19 | 4 | -0.395 | -0.430 | 0.395 | 50.0% |
| 5 | track_status | GREEN | 325 | -0.097 | -0.101 | 0.369 | 52.6% |
| 5 | track_status | YELLOW | 1 | +0.104 | +0.104 | 0.104 | 100.0% |
| finish | age | 0-9 | 75 | -0.186 | -0.082 | 0.376 | 46.7% |
| finish | age | 10-19 | 75 | -0.667 | -0.651 | 0.667 | 21.3% |
| finish | age | 20-29 | 8 | -0.875 | -0.877 | 0.875 | 0.0% |
| finish | compound | HARD | 145 | -0.481 | -0.546 | 0.580 | 26.9% |
| finish | compound | MEDIUM | 13 | -0.089 | -0.061 | 0.089 | 92.3% |
| finish | compound_and_age | HARD/0-9 | 71 | -0.193 | -0.091 | 0.394 | 45.1% |
| finish | compound_and_age | HARD/10-19 | 66 | -0.744 | -0.685 | 0.744 | 10.6% |
| finish | compound_and_age | HARD/20-29 | 8 | -0.875 | -0.877 | 0.875 | 0.0% |
| finish | compound_and_age | MEDIUM/0-9 | 4 | -0.064 | -0.039 | 0.064 | 75.0% |
| finish | compound_and_age | MEDIUM/10-19 | 9 | -0.100 | -0.082 | 0.100 | 100.0% |
| finish | track_status | GREEN | 157 | -0.449 | -0.497 | 0.541 | 32.5% |
| finish | track_status | YELLOW | 1 | -0.349 | -0.349 | 0.349 | 0.0% |

### spain_2022

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | age | 0-9 | 251 | -0.181 | -0.145 | 0.598 | 63.7% |
| 1 | age | 10-19 | 241 | -0.300 | -0.186 | 0.475 | 67.6% |
| 1 | age | 20-29 | 22 | -0.196 | -0.161 | 0.465 | 77.3% |
| 1 | compound | MEDIUM | 274 | -0.250 | -0.200 | 0.425 | 65.7% |
| 1 | compound | SOFT | 240 | -0.222 | -0.113 | 0.660 | 66.7% |
| 1 | compound_and_age | MEDIUM/0-9 | 136 | -0.256 | -0.229 | 0.472 | 60.3% |
| 1 | compound_and_age | MEDIUM/10-19 | 122 | -0.238 | -0.170 | 0.360 | 70.5% |
| 1 | compound_and_age | MEDIUM/20-29 | 16 | -0.290 | -0.259 | 0.526 | 75.0% |
| 1 | compound_and_age | SOFT/0-9 | 115 | -0.091 | +0.045 | 0.748 | 67.8% |
| 1 | compound_and_age | SOFT/10-19 | 119 | -0.363 | -0.201 | 0.592 | 64.7% |
| 1 | compound_and_age | SOFT/20-29 | 6 | +0.055 | +0.011 | 0.301 | 83.3% |
| 1 | track_status | GREEN | 514 | -0.237 | -0.165 | 0.535 | 66.1% |
| 10 | age | 0-9 | 186 | -0.211 | -0.253 | 0.582 | 33.3% |
| 10 | age | 10-19 | 45 | -0.220 | -0.231 | 0.459 | 53.3% |
| 10 | age | 20-29 | 3 | -0.179 | -0.135 | 0.202 | 100.0% |
| 10 | compound | MEDIUM | 146 | -0.386 | -0.415 | 0.484 | 40.4% |
| 10 | compound | SOFT | 88 | +0.075 | +0.299 | 0.668 | 34.1% |
| 10 | compound_and_age | MEDIUM/0-9 | 115 | -0.413 | -0.445 | 0.525 | 35.7% |
| 10 | compound_and_age | MEDIUM/10-19 | 28 | -0.297 | -0.255 | 0.347 | 53.6% |
| 10 | compound_and_age | MEDIUM/20-29 | 3 | -0.179 | -0.135 | 0.202 | 100.0% |
| 10 | compound_and_age | SOFT/0-9 | 71 | +0.116 | +0.354 | 0.674 | 29.6% |
| 10 | compound_and_age | SOFT/10-19 | 17 | -0.093 | -0.200 | 0.644 | 52.9% |
| 10 | track_status | GREEN | 234 | -0.212 | -0.252 | 0.553 | 38.0% |
| 5 | age | 0-9 | 235 | -0.220 | -0.274 | 0.550 | 42.1% |
| 5 | age | 10-19 | 156 | -0.281 | -0.211 | 0.469 | 48.7% |
| 5 | age | 20-29 | 9 | -0.408 | -0.432 | 0.408 | 77.8% |
| 5 | compound | MEDIUM | 222 | -0.295 | -0.318 | 0.411 | 45.5% |
| 5 | compound | SOFT | 178 | -0.189 | -0.112 | 0.645 | 45.5% |
| 5 | compound_and_age | MEDIUM/0-9 | 135 | -0.342 | -0.368 | 0.480 | 38.5% |
| 5 | compound_and_age | MEDIUM/10-19 | 78 | -0.200 | -0.205 | 0.292 | 53.8% |
| 5 | compound_and_age | MEDIUM/20-29 | 9 | -0.408 | -0.432 | 0.408 | 77.8% |
| 5 | compound_and_age | SOFT/0-9 | 100 | -0.054 | +0.085 | 0.645 | 47.0% |
| 5 | compound_and_age | SOFT/10-19 | 78 | -0.363 | -0.244 | 0.646 | 43.6% |
| 5 | track_status | GREEN | 400 | -0.248 | -0.251 | 0.515 | 45.5% |
| finish | age | 0-9 | 68 | -0.702 | -0.824 | 0.950 | 19.1% |
| finish | age | 10-19 | 51 | -0.829 | -0.300 | 0.835 | 47.1% |
| finish | age | 20-29 | 8 | -0.462 | -0.532 | 0.462 | 100.0% |
| finish | compound | MEDIUM | 44 | -0.587 | -0.534 | 0.587 | 43.2% |
| finish | compound | SOFT | 83 | -0.818 | -0.796 | 1.025 | 31.3% |
| finish | compound_and_age | MEDIUM/0-9 | 18 | -0.959 | -0.866 | 0.959 | 0.0% |
| finish | compound_and_age | MEDIUM/10-19 | 18 | -0.269 | -0.188 | 0.269 | 61.1% |
| finish | compound_and_age | MEDIUM/20-29 | 8 | -0.462 | -0.532 | 0.462 | 100.0% |
| finish | compound_and_age | SOFT/0-9 | 50 | -0.610 | -0.770 | 0.947 | 26.0% |
| finish | compound_and_age | SOFT/10-19 | 33 | -1.134 | -0.917 | 1.144 | 39.4% |
| finish | track_status | GREEN | 127 | -0.738 | -0.662 | 0.873 | 35.4% |

### france_2022

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | age | 0-9 | 142 | +0.594 | +0.162 | 1.981 | 54.2% |
| 1 | age | 10-19 | 170 | -0.164 | -0.137 | 0.275 | 72.9% |
| 1 | age | 20-29 | 93 | -0.010 | +0.046 | 0.341 | 69.9% |
| 1 | age | 30+ | 13 | -7.042 | -0.954 | 7.098 | 30.8% |
| 1 | compound | HARD | 284 | -0.112 | -0.038 | 1.359 | 61.3% |
| 1 | compound | MEDIUM | 134 | -0.031 | -0.078 | 0.493 | 71.6% |
| 1 | compound_and_age | HARD/0-9 | 84 | +0.940 | +0.270 | 2.775 | 50.0% |
| 1 | compound_and_age | HARD/10-19 | 97 | -0.203 | -0.217 | 0.311 | 68.0% |
| 1 | compound_and_age | HARD/20-29 | 90 | +0.005 | +0.070 | 0.337 | 68.9% |
| 1 | compound_and_age | HARD/30+ | 13 | -7.042 | -0.954 | 7.098 | 30.8% |
| 1 | compound_and_age | MEDIUM/0-9 | 58 | +0.093 | +0.003 | 0.831 | 60.3% |
| 1 | compound_and_age | MEDIUM/10-19 | 73 | -0.112 | -0.111 | 0.226 | 79.5% |
| 1 | compound_and_age | MEDIUM/20-29 | 3 | -0.455 | -0.567 | 0.455 | 100.0% |
| 1 | track_status | GREEN | 402 | -0.335 | -0.061 | 0.620 | 66.4% |
| 1 | track_status | SAFETY_CAR | 11 | +8.898 | +14.821 | 18.253 | 0.0% |
| 1 | track_status | YELLOW | 5 | +0.194 | +0.072 | 0.387 | 60.0% |
| 10 | age | 0-9 | 117 | +6.842 | +0.211 | 7.175 | 50.4% |
| 10 | age | 10-19 | 94 | -0.215 | -0.239 | 0.261 | 51.1% |
| 10 | age | 20-29 | 58 | -2.184 | -2.994 | 2.236 | 20.7% |
| 10 | compound | HARD | 230 | +2.477 | -0.119 | 3.911 | 40.9% |
| 10 | compound | MEDIUM | 39 | +2.151 | +0.115 | 2.411 | 64.1% |
| 10 | compound_and_age | HARD/0-9 | 82 | +8.736 | +0.264 | 9.094 | 46.3% |
| 10 | compound_and_age | HARD/10-19 | 90 | -0.221 | -0.251 | 0.269 | 48.9% |
| 10 | compound_and_age | HARD/20-29 | 58 | -2.184 | -2.994 | 2.236 | 20.7% |
| 10 | compound_and_age | MEDIUM/0-9 | 35 | +2.407 | +0.183 | 2.677 | 60.0% |
| 10 | compound_and_age | MEDIUM/10-19 | 4 | -0.084 | -0.092 | 0.084 | 100.0% |
| 10 | track_status | GREEN | 253 | -0.567 | -0.112 | 0.777 | 47.0% |
| 10 | track_status | SAFETY_CAR | 11 | +72.241 | +77.997 | 72.241 | 0.0% |
| 10 | track_status | YELLOW | 5 | +0.477 | +0.419 | 0.477 | 0.0% |
| 5 | age | 0-9 | 142 | +4.775 | +0.176 | 5.658 | 48.6% |
| 5 | age | 10-19 | 129 | -0.188 | -0.192 | 0.248 | 56.6% |
| 5 | age | 20-29 | 90 | -1.901 | -0.140 | 2.080 | 41.1% |
| 5 | age | 30+ | 13 | -6.922 | -6.836 | 6.922 | 0.0% |
| 5 | compound | HARD | 280 | +1.238 | -0.094 | 3.536 | 40.4% |
| 5 | compound | MEDIUM | 94 | +0.492 | -0.009 | 1.303 | 70.2% |
| 5 | compound_and_age | HARD/0-9 | 84 | +7.481 | +0.316 | 8.172 | 40.5% |
| 5 | compound_and_age | HARD/10-19 | 93 | -0.223 | -0.265 | 0.286 | 45.2% |
| 5 | compound_and_age | HARD/20-29 | 90 | -1.901 | -0.140 | 2.080 | 41.1% |
| 5 | compound_and_age | HARD/30+ | 13 | -6.922 | -6.836 | 6.922 | 0.0% |
| 5 | compound_and_age | MEDIUM/0-9 | 58 | +0.856 | +0.047 | 2.017 | 60.3% |
| 5 | compound_and_age | MEDIUM/10-19 | 36 | -0.096 | -0.094 | 0.151 | 86.1% |
| 5 | track_status | GREEN | 358 | -0.891 | -0.090 | 1.120 | 49.4% |
| 5 | track_status | SAFETY_CAR | 11 | +64.502 | +70.807 | 64.502 | 0.0% |
| 5 | track_status | YELLOW | 5 | +0.431 | +0.268 | 0.431 | 40.0% |
| finish | age | 0-9 | 85 | +7.739 | -1.001 | 10.088 | 0.0% |
| finish | age | 10-19 | 90 | -1.818 | -1.794 | 1.818 | 0.0% |
| finish | age | 20-29 | 90 | -3.319 | -3.080 | 3.319 | 0.0% |
| finish | age | 30+ | 13 | -6.527 | -6.759 | 6.527 | 0.0% |
| finish | compound | HARD | 272 | +0.507 | -1.872 | 5.064 | 0.0% |
| finish | compound | MEDIUM | 6 | -4.543 | -4.141 | 4.543 | 0.0% |
| finish | compound_and_age | HARD/0-9 | 79 | +8.672 | -0.997 | 10.510 | 0.0% |
| finish | compound_and_age | HARD/10-19 | 90 | -1.818 | -1.794 | 1.818 | 0.0% |
| finish | compound_and_age | HARD/20-29 | 90 | -3.319 | -3.080 | 3.319 | 0.0% |
| finish | compound_and_age | HARD/30+ | 13 | -6.527 | -6.759 | 6.527 | 0.0% |
| finish | compound_and_age | MEDIUM/0-9 | 6 | -4.543 | -4.141 | 4.543 | 0.0% |
| finish | track_status | GREEN | 264 | -2.438 | -1.948 | 2.438 | 0.0% |
| finish | track_status | SAFETY_CAR | 10 | +75.767 | +81.831 | 75.767 | 0.0% |
| finish | track_status | YELLOW | 4 | -0.869 | -0.907 | 0.869 | 0.0% |

### pooled

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | age | 0-9 | 560 | +0.088 | -0.049 | 0.903 | 61.8% |
| 1 | age | 10-19 | 626 | -0.210 | -0.155 | 0.383 | 67.1% |
| 1 | age | 20-29 | 137 | -0.072 | -0.004 | 0.379 | 72.3% |
| 1 | age | 30+ | 18 | -5.189 | -0.752 | 5.230 | 44.4% |
| 1 | compound | HARD | 508 | -0.074 | -0.059 | 0.950 | 60.8% |
| 1 | compound | MEDIUM | 569 | -0.164 | -0.142 | 0.420 | 68.2% |
| 1 | compound | SOFT | 264 | -0.207 | -0.094 | 0.642 | 66.7% |
| 1 | compound_and_age | HARD/0-9 | 191 | +0.515 | +0.178 | 1.478 | 56.0% |
| 1 | compound_and_age | HARD/10-19 | 189 | -0.208 | -0.220 | 0.353 | 61.4% |
| 1 | compound_and_age | HARD/20-29 | 110 | -0.031 | +0.039 | 0.360 | 70.9% |
| 1 | compound_and_age | HARD/30+ | 18 | -5.189 | -0.752 | 5.230 | 44.4% |
| 1 | compound_and_age | MEDIUM/0-9 | 254 | -0.153 | -0.143 | 0.540 | 63.4% |
| 1 | compound_and_age | MEDIUM/10-19 | 294 | -0.162 | -0.136 | 0.311 | 71.8% |
| 1 | compound_and_age | MEDIUM/20-29 | 21 | -0.321 | -0.311 | 0.501 | 76.2% |
| 1 | compound_and_age | SOFT/0-9 | 115 | -0.091 | +0.045 | 0.748 | 67.8% |
| 1 | compound_and_age | SOFT/10-19 | 143 | -0.311 | -0.164 | 0.571 | 65.0% |
| 1 | compound_and_age | SOFT/20-29 | 6 | +0.055 | +0.011 | 0.301 | 83.3% |
| 1 | track_status | GREEN | 1324 | -0.215 | -0.114 | 0.520 | 65.6% |
| 1 | track_status | SAFETY_CAR | 11 | +8.898 | +14.821 | 18.253 | 0.0% |
| 1 | track_status | YELLOW | 6 | +0.131 | -0.036 | 0.353 | 66.7% |
| 10 | age | 0-9 | 450 | +1.700 | +0.020 | 2.213 | 44.4% |
| 10 | age | 10-19 | 190 | -0.245 | -0.266 | 0.360 | 44.7% |
| 10 | age | 20-29 | 67 | -1.886 | -2.795 | 1.980 | 29.9% |
| 10 | compound | HARD | 370 | +1.526 | -0.101 | 2.590 | 39.7% |
| 10 | compound | MEDIUM | 249 | +0.085 | -0.147 | 0.722 | 51.4% |
| 10 | compound | SOFT | 88 | +0.075 | +0.299 | 0.668 | 34.1% |
| 10 | compound_and_age | HARD/0-9 | 174 | +4.173 | +0.182 | 4.482 | 46.0% |
| 10 | compound_and_age | HARD/10-19 | 132 | -0.271 | -0.304 | 0.352 | 37.9% |
| 10 | compound_and_age | HARD/20-29 | 64 | -1.966 | -2.940 | 2.063 | 26.6% |
| 10 | compound_and_age | MEDIUM/0-9 | 205 | +0.150 | -0.158 | 0.821 | 48.3% |
| 10 | compound_and_age | MEDIUM/10-19 | 41 | -0.225 | -0.139 | 0.269 | 63.4% |
| 10 | compound_and_age | MEDIUM/20-29 | 3 | -0.179 | -0.135 | 0.202 | 100.0% |
| 10 | compound_and_age | SOFT/0-9 | 71 | +0.116 | +0.354 | 0.674 | 29.6% |
| 10 | compound_and_age | SOFT/10-19 | 17 | -0.093 | -0.200 | 0.644 | 52.9% |
| 10 | track_status | GREEN | 690 | -0.296 | -0.119 | 0.579 | 44.2% |
| 10 | track_status | SAFETY_CAR | 11 | +72.241 | +77.997 | 72.241 | 0.0% |
| 10 | track_status | YELLOW | 6 | +0.348 | +0.358 | 0.447 | 0.0% |
| 5 | age | 0-9 | 543 | +1.162 | +0.004 | 1.823 | 49.7% |
| 5 | age | 10-19 | 426 | -0.228 | -0.205 | 0.370 | 49.8% |
| 5 | age | 20-29 | 117 | -1.548 | -0.227 | 1.718 | 42.7% |
| 5 | age | 30+ | 14 | -6.457 | -6.799 | 6.457 | 7.1% |
| 5 | compound | HARD | 485 | +0.671 | -0.108 | 2.224 | 41.2% |
| 5 | compound | MEDIUM | 433 | -0.065 | -0.149 | 0.563 | 57.7% |
| 5 | compound | SOFT | 182 | -0.194 | -0.116 | 0.640 | 45.6% |
| 5 | compound_and_age | HARD/0-9 | 190 | +3.373 | +0.183 | 3.819 | 48.4% |
| 5 | compound_and_age | HARD/10-19 | 173 | -0.275 | -0.307 | 0.378 | 37.0% |
| 5 | compound_and_age | HARD/20-29 | 108 | -1.643 | -0.173 | 1.827 | 39.8% |
| 5 | compound_and_age | HARD/30+ | 14 | -6.457 | -6.799 | 6.457 | 7.1% |
| 5 | compound_and_age | MEDIUM/0-9 | 253 | -0.019 | -0.188 | 0.789 | 51.8% |
| 5 | compound_and_age | MEDIUM/10-19 | 171 | -0.115 | -0.090 | 0.235 | 65.5% |
| 5 | compound_and_age | MEDIUM/20-29 | 9 | -0.408 | -0.432 | 0.408 | 77.8% |
| 5 | compound_and_age | SOFT/0-9 | 100 | -0.054 | +0.085 | 0.645 | 47.0% |
| 5 | compound_and_age | SOFT/10-19 | 82 | -0.364 | -0.252 | 0.634 | 43.9% |
| 5 | track_status | GREEN | 1083 | -0.415 | -0.139 | 0.671 | 48.9% |
| 5 | track_status | SAFETY_CAR | 11 | +64.502 | +70.807 | 64.502 | 0.0% |
| 5 | track_status | YELLOW | 6 | +0.377 | +0.218 | 0.377 | 50.0% |
| finish | age | 0-9 | 228 | +2.615 | -0.739 | 4.168 | 21.1% |
| finish | age | 10-19 | 216 | -1.185 | -1.237 | 1.186 | 18.5% |
| finish | age | 20-29 | 106 | -2.919 | -2.786 | 2.919 | 7.5% |
| finish | age | 30+ | 13 | -6.527 | -6.759 | 6.527 | 0.0% |
| finish | compound | HARD | 417 | +0.163 | -1.240 | 3.505 | 9.4% |
| finish | compound | MEDIUM | 63 | -0.861 | -0.436 | 0.861 | 49.2% |
| finish | compound | SOFT | 83 | -0.818 | -0.796 | 1.025 | 31.3% |
| finish | compound_and_age | HARD/0-9 | 150 | +4.476 | -0.669 | 5.722 | 21.3% |
| finish | compound_and_age | HARD/10-19 | 156 | -1.364 | -1.540 | 1.364 | 4.5% |
| finish | compound_and_age | HARD/20-29 | 98 | -3.119 | -2.887 | 3.119 | 0.0% |
| finish | compound_and_age | HARD/30+ | 13 | -6.527 | -6.759 | 6.527 | 0.0% |
| finish | compound_and_age | MEDIUM/0-9 | 28 | -1.599 | -0.903 | 1.599 | 10.7% |
| finish | compound_and_age | MEDIUM/10-19 | 27 | -0.213 | -0.152 | 0.213 | 74.1% |
| finish | compound_and_age | MEDIUM/20-29 | 8 | -0.462 | -0.532 | 0.462 | 100.0% |
| finish | compound_and_age | SOFT/0-9 | 50 | -0.610 | -0.770 | 0.947 | 26.0% |
| finish | compound_and_age | SOFT/10-19 | 33 | -1.134 | -0.917 | 1.144 | 39.4% |
| finish | track_status | GREEN | 548 | -1.474 | -1.109 | 1.532 | 17.5% |
| finish | track_status | SAFETY_CAR | 10 | +75.767 | +81.831 | 75.767 | 0.0% |
| finish | track_status | YELLOW | 5 | -0.765 | -0.863 | 0.765 | 0.0% |

## Findings and limits

The pit allocation improves Bahrain's 1-lap pit mean bias from +17.683 to +6.968 s and its 5-lap pit MAE from 5.935 to 3.736 s; no-stop metrics are nearly unchanged. The 50/50 share remains unestimated and does not deliver calibrated pit-entry intervals.

Spain finish MAE is 16.702 s and coverage 39.7%, versus Bahrain 8.519 s and 47.6%. France finish MAE is 130.620 s with zero coverage. Its median finish error is -36.519 s despite mean bias +2.818 s: 418 actuals exceed p90 and 11 are below p10. The 11 safety-car cutoff snapshots explain the large positive tail; the five worst are lap-19 SC snapshots with approximately +2,790 to +2,834 s finish error. The unchanged engine holds observed SC status and last-lap-based rival paces through the entire remaining race, so this tail is not a tyre-wear signal.

Every scored France finish horizon includes a real later neutralization, given the last allowed cutoff at lap 48. Therefore there are no France no-stop finish rows in the no-actual-neutralization subset. Widespread negative finish errors cannot be attributed to wear alone when the unchanged model lacks those future neutralizations. No actual future status was injected to correct them.

Within GREEN-cutoff, non-neutralized no-stop finish horizons, Bahrain HARD mean error/lap becomes -0.193/-0.750/-0.875 s at age 0-9/10-19/20-29 (n=71/65/8). Spain SOFT becomes -0.610/-1.134 s at age 0-9/10-19 (n=50/33). These patterns are consistent with a remaining age-related modeling error, but Spain MEDIUM is non-monotonic (-0.959/-0.269/-0.462; n=18/18/8), and France's neutralization-free 5/10-lap age groups are also non-monotonic. Wear is a plausible contributor, not an established sole cause or a justification for fitting a new degradation coefficient in this slice. Horizon length, race/driver selection and fuel remain confounders even in the joint compound/age tables.

Pooled coverage at 1/5/10/finish is 62.4/43.0/39.3/29.9%, below 80% at every horizon. Pooled mean finish bias -3.592 s conceals median -11.874 s and MAE 49.102 s. No further model changes or interval tuning are performed.

## Reproduction and artifacts

Use the explicit offline evaluation commands in each linked per-race report. The current legacy CLI names accept only the three approved development races. Bahrain pit-split predictions are reused unchanged; new cutoff columns are joined from its saved causal snapshots without predicting again.

```powershell
.\.venv\Scripts\python.exe -m tools.report_development_evaluation
```

- [Bahrain](../bahrain_2021_pit_split/REPORT.md), [Spain](../spain_2022_pit_split/REPORT.md), [France](../france_2022_pit_split/REPORT.md): counts, every metric, worst predictions and plots.
- [Metrics](metrics.json), [no-stop breakdowns](no_stop_breakdowns.json), [pooled predictions](predictions.csv), [manifest](manifest.json).
