# Development neutralization correction: ongoing

Previous run: pit_split. Signed error = predicted median minus actual. Same driver/cutoff/target cohort, 32 draws, every lap. No held-out or wet evaluation.

## bahrain_2021

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429 | +0.260 → +0.260 | -0.087 → -0.087 | 0.709 → 0.709 | 61.3% → 61.3% | 1.020 → 1.020 |
| 1 | without_stop | 409 | -0.068 → -0.068 | -0.106 → -0.106 | 0.402 → 0.402 | 64.3% → 64.3% | 1.004 → 1.004 |
| 1 | with_stop | 20 | +6.968 → +6.968 | +7.063 → +7.063 | 6.968 → 6.968 | 0.0% → 0.0% | 1.348 → 1.348 |
| 5 | all | 429 | -0.596 → -0.596 | -0.728 → -0.728 | 2.296 → 2.296 | 46.6% → 46.6% | 3.261 → 3.261 |
| 5 | without_stop | 326 | -0.483 → -0.483 | -0.506 → -0.506 | 1.841 → 1.841 | 52.8% → 52.8% | 3.239 → 3.239 |
| 5 | with_stop | 103 | -0.954 → -0.954 | -1.771 → -1.771 | 3.736 → 3.736 | 27.2% → 27.2% | 3.331 → 3.331 |
| 10 | all | 379 | -0.958 → -0.958 | -0.530 → -0.530 | 3.795 → 3.795 | 45.6% → 45.6% | 5.938 → 5.938 |
| 10 | without_stop | 204 | -0.577 → -0.577 | -0.528 → -0.528 | 3.617 → 3.617 | 47.5% → 47.5% | 6.040 → 6.040 |
| 10 | with_stop | 175 | -1.402 → -1.402 | -0.577 → -0.577 | 4.002 → 4.002 | 43.4% → 43.4% | 5.819 → 5.819 |
| finish | all | 429 | -1.458 → -1.458 | -2.185 → -2.185 | 8.519 → 8.519 | 47.6% → 47.6% | 15.763 → 15.763 |
| finish | without_stop | 158 | -4.573 → -4.573 | -4.883 → -4.883 | 6.315 → 6.315 | 32.3% → 32.3% | 7.302 → 7.302 |
| finish | with_stop | 271 | +0.358 → +0.358 | +0.664 → +0.664 | 9.804 → 9.804 | 56.5% → 56.5% | 20.696 → 20.696 |

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

[Dataset, exclusions, plots and worst cases](../bahrain_2021_ongoing/REPORT.md)

## spain_2022

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 542 | +0.049 → +0.049 | -0.142 → -0.142 | 0.781 → 0.781 | 62.7% → 62.7% | 1.183 → 1.183 |
| 1 | without_stop | 514 | -0.237 → -0.237 | -0.165 → -0.165 | 0.535 → 0.535 | 66.1% → 66.1% | 1.168 → 1.168 |
| 1 | with_stop | 28 | +5.303 → +5.303 | +5.401 → +5.401 | 5.303 → 5.303 | 0.0% → 0.0% | 1.472 → 1.472 |
| 5 | all | 540 | -1.305 → -1.305 | -1.392 → -1.392 | 2.881 → 2.881 | 41.1% → 41.1% | 3.856 → 3.856 |
| 5 | without_stop | 400 | -1.240 → -1.240 | -1.253 → -1.253 | 2.576 → 2.576 | 45.5% → 45.5% | 3.922 → 3.922 |
| 5 | with_stop | 140 | -1.492 → -1.492 | -1.776 → -1.776 | 3.753 → 3.753 | 28.6% → 28.6% | 3.666 → 3.666 |
| 10 | all | 490 | -2.525 → -2.525 | -2.634 → -2.634 | 5.032 → 5.032 | 40.4% → 40.4% | 6.679 → 6.679 |
| 10 | without_stop | 234 | -2.122 → -2.122 | -2.516 → -2.516 | 5.534 → 5.534 | 38.0% → 38.0% | 7.222 → 7.222 |
| 10 | with_stop | 256 | -2.893 → -2.893 | -2.691 → -2.691 | 4.574 → 4.574 | 42.6% → 42.6% | 6.181 → 6.181 |
| finish | all | 542 | -10.356 → -10.356 | -7.479 → -7.479 | 16.702 → 16.702 | 39.7% → 39.7% | 20.821 → 20.821 |
| finish | without_stop | 127 | -7.985 → -7.985 | -6.339 → -6.339 | 9.909 → 9.909 | 35.4% → 35.4% | 9.586 → 9.586 |
| finish | with_stop | 415 | -11.081 → -11.081 | -7.704 → -7.704 | 18.781 → 18.781 | 41.0% → 41.0% | 24.259 → 24.259 |

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

[Dataset, exclusions, plots and worst cases](../spain_2022_ongoing/REPORT.md)

## france_2022

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429 | -0.614 → -0.614 | -0.063 → -0.063 | 1.583 → 1.583 | 62.9% → 62.9% | 0.917 → 0.917 |
| 1 | without_stop | 418 | -0.086 → -0.086 | -0.055 → -0.055 | 1.081 → 1.081 | 64.6% → 64.6% | 0.913 → 0.913 |
| 1 | with_stop | 11 | -20.664 → -20.664 | -18.451 → -18.451 | 20.664 → 20.664 | 0.0% → 0.0% | 1.083 → 1.083 |
| 5 | all | 429 | -4.691 → -8.665 | -0.745 → -0.745 | 22.237 → 18.264 | 41.7% → 41.7% | 3.000 → 3.017 |
| 5 | without_stop | 374 | +5.251 → +0.693 | -0.298 → -0.298 | 14.875 → 10.317 | 47.9% → 47.9% | 3.071 → 3.091 |
| 5 | with_stop | 55 | -72.301 → -72.301 | -95.092 → -95.092 | 72.301 → 72.301 | 0.0% → 0.0% | 2.519 → 2.519 |
| 10 | all | 379 | -8.082 → -24.129 | -3.165 → -3.165 | 51.547 → 35.500 | 31.4% → 31.4% | 5.101 → 5.161 |
| 10 | without_stop | 269 | +24.302 → +1.693 | -0.927 → -0.927 | 36.937 → 14.328 | 44.2% → 44.2% | 5.302 → 5.387 |
| 10 | with_stop | 110 | -87.274 → -87.274 | -100.351 → -100.351 | 87.274 → 87.274 | 0.0% → 0.0% | 4.609 → 4.609 |
| finish | all | 429 | +2.818 → -60.361 | -36.519 → -36.519 | 130.620 → 67.441 | 0.0% → 0.0% | 13.467 → 13.650 |
| finish | without_stop | 278 | +59.746 → -28.230 | -33.789 → -33.789 | 125.876 → 37.900 | 0.0% → 0.0% | 9.809 → 10.075 |
| finish | with_stop | 151 | -101.989 → -119.517 | -133.307 → -133.307 | 139.354 → 121.827 | 0.0% → 0.0% | 20.201 → 20.233 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 429 | 1.583 | -0.614 | -0.063 | -0.614 | -0.063 | 1.583 | 62.9% | 0.917 | 71 | 88 | 14.124 |
| 1 | without_stop | 418 | 1.081 | -0.086 | -0.055 | -0.086 | -0.055 | 1.081 | 64.6% | 0.913 | 71 | 77 | 9.170 |
| 1 | with_stop | 11 | 20.664 | -20.664 | -18.451 | -20.664 | -18.451 | 20.664 | 0.0% | 1.083 | 0 | 11 | 202.391 |
| 5 | all | 429 | 18.264 | -8.665 | -0.745 | -1.733 | -0.149 | 3.653 | 41.7% | 3.017 | 79 | 171 | 175.342 |
| 5 | without_stop | 374 | 10.317 | +0.693 | -0.298 | +0.139 | -0.060 | 2.063 | 47.9% | 3.091 | 79 | 116 | 96.163 |
| 5 | with_stop | 55 | 72.301 | -72.301 | -95.092 | -14.460 | -19.018 | 14.460 | 0.0% | 2.519 | 0 | 55 | 713.756 |
| 10 | all | 379 | 35.500 | -24.129 | -3.165 | -2.413 | -0.316 | 3.550 | 31.4% | 5.161 | 59 | 201 | 341.549 |
| 10 | without_stop | 269 | 14.328 | +1.693 | -0.927 | +0.169 | -0.093 | 1.433 | 44.2% | 5.387 | 59 | 91 | 130.593 |
| 10 | with_stop | 110 | 87.274 | -87.274 | -100.351 | -8.727 | -10.035 | 8.727 | 0.0% | 4.609 | 0 | 110 | 857.432 |
| finish | all | 429 | 67.441 | -60.361 | -36.519 | -2.474 | -2.571 | 2.682 | 0.0% | 13.650 | 11 | 418 | 619.846 |
| finish | without_stop | 278 | 37.900 | -28.230 | -33.789 | -2.185 | -1.904 | 2.470 | 0.0% | 10.075 | 10 | 268 | 336.228 |
| finish | with_stop | 151 | 121.827 | -119.517 | -133.307 | -3.006 | -3.098 | 3.073 | 0.0% | 20.233 | 1 | 150 | 1142.003 |

[Dataset, exclusions, plots and worst cases](../france_2022_ongoing/REPORT.md)

## Prediction-weighted pool

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 1400 | -0.089 → -0.089 | -0.095 → -0.095 | 1.005 → 1.005 | 62.4% → 62.4% | 1.052 → 1.052 |
| 1 | without_stop | 1341 | -0.138 → -0.138 | -0.114 → -0.114 | 0.665 → 0.665 | 65.1% → 65.1% | 1.038 → 1.038 |
| 1 | with_stop | 59 | +1.026 → +1.026 | +5.629 → +5.629 | 8.731 → 8.731 | 0.0% → 0.0% | 1.357 → 1.357 |
| 5 | all | 1398 | -2.127 → -3.346 | -0.951 → -0.951 | 8.641 → 7.422 | 43.0% → 43.0% | 3.411 → 3.416 |
| 5 | without_stop | 1100 | +1.191 → -0.358 | -0.654 → -0.654 | 6.540 → 4.990 | 48.5% → 48.5% | 3.430 → 3.437 |
| 5 | with_stop | 298 | -14.375 → -14.375 | -2.490 → -2.490 | 16.399 → 16.399 | 22.8% → 22.8% | 3.339 → 3.339 |
| 10 | all | 1248 | -3.737 → -8.610 | -1.984 → -1.984 | 18.782 → 13.909 | 39.3% → 39.3% | 5.975 → 5.993 |
| 10 | without_stop | 707 | +8.377 → -0.225 | -1.119 → -1.119 | 16.929 → 8.327 | 43.1% → 43.1% | 6.151 → 6.183 |
| 10 | with_stop | 541 | -19.568 → -19.568 | -3.465 → -3.465 | 21.204 → 21.204 | 34.2% → 34.2% | 5.745 → 5.745 |
| finish | all | 1400 | -3.592 → -22.952 | -11.874 → -11.874 | 49.102 → 29.742 | 29.9% → 29.9% | 17.018 → 17.074 |
| finish | without_stop | 563 | +26.417 → -17.024 | -19.905 → -19.905 | 66.163 → 22.722 | 17.1% → 17.1% | 9.055 → 9.186 |
| finish | with_stop | 837 | -23.778 → -26.940 | -7.530 → -7.530 | 37.627 → 34.464 | 38.6% → 38.6% | 22.373 → 22.379 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1400 | 1.005 | -0.089 | -0.095 | -0.089 | -0.095 | 1.005 | 62.4% | 1.052 | 222 | 305 | 8.014 |
| 1 | without_stop | 1341 | 0.665 | -0.138 | -0.114 | -0.138 | -0.114 | 0.665 | 65.1% | 1.038 | 174 | 294 | 4.761 |
| 1 | with_stop | 59 | 8.731 | +1.026 | +5.629 | +1.026 | +5.629 | 8.731 | 0.0% | 1.357 | 48 | 11 | 81.964 |
| 5 | all | 1398 | 7.422 | -3.346 | -0.951 | -0.669 | -0.190 | 1.484 | 43.0% | 3.416 | 241 | 556 | 65.553 |
| 5 | without_stop | 1100 | 4.990 | -0.358 | -0.654 | -0.072 | -0.131 | 0.998 | 48.5% | 3.437 | 190 | 377 | 41.658 |
| 5 | with_stop | 298 | 16.399 | -14.375 | -2.490 | -2.875 | -0.498 | 3.280 | 22.8% | 3.339 | 51 | 179 | 153.755 |
| 10 | all | 1248 | 13.909 | -8.610 | -1.984 | -0.861 | -0.198 | 1.391 | 39.3% | 5.993 | 205 | 553 | 123.999 |
| 10 | without_stop | 707 | 8.327 | -0.225 | -1.119 | -0.023 | -0.112 | 0.833 | 43.1% | 6.183 | 156 | 246 | 67.516 |
| 10 | with_stop | 541 | 21.204 | -19.568 | -3.465 | -1.957 | -0.346 | 2.120 | 34.2% | 5.745 | 49 | 307 | 197.812 |
| finish | all | 1400 | 29.742 | -22.952 | -11.874 | -0.964 | -0.573 | 1.159 | 29.9% | 17.074 | 126 | 855 | 247.884 |
| finish | without_stop | 563 | 22.722 | -17.024 | -19.905 | -1.372 | -1.066 | 1.568 | 17.1% | 9.186 | 29 | 438 | 192.766 |
| finish | with_stop | 837 | 34.464 | -26.940 | -7.530 | -0.690 | -0.241 | 0.883 | 38.6% | 22.379 | 97 | 417 | 284.958 |
