# Development neutralization correction: future

Previous run: ongoing. Signed error = predicted median minus actual. Same driver/cutoff/target cohort, 32 draws, every lap. No held-out or wet evaluation.

## bahrain_2021

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429 | +0.260 → +0.260 | -0.087 → -0.087 | 0.709 → 0.709 | 61.3% → 61.3% | 1.020 → 1.020 |
| 1 | without_stop | 409 | -0.068 → -0.068 | -0.106 → -0.106 | 0.402 → 0.402 | 64.3% → 64.3% | 1.004 → 1.004 |
| 1 | with_stop | 20 | +6.968 → +6.968 | +7.063 → +7.063 | 6.968 → 6.968 | 0.0% → 0.0% | 1.348 → 1.348 |
| 5 | all | 429 | -0.596 → -0.402 | -0.728 → -0.582 | 2.296 → 2.265 | 46.6% → 49.9% | 3.261 → 3.715 |
| 5 | without_stop | 326 | -0.483 → -0.291 | -0.506 → -0.205 | 1.841 → 1.826 | 52.8% → 55.5% | 3.239 → 3.692 |
| 5 | with_stop | 103 | -0.954 → -0.755 | -1.771 → -1.627 | 3.736 → 3.655 | 27.2% → 32.0% | 3.331 → 3.786 |
| 10 | all | 379 | -0.958 → -0.245 | -0.530 → +0.106 | 3.795 → 3.818 | 45.6% → 78.4% | 5.938 → 35.290 |
| 10 | without_stop | 204 | -0.577 → +0.126 | -0.528 → +0.136 | 3.617 → 3.639 | 47.5% → 77.0% | 6.040 → 35.417 |
| 10 | with_stop | 175 | -1.402 → -0.677 | -0.577 → +0.106 | 4.002 → 4.027 | 43.4% → 80.0% | 5.819 → 35.143 |
| finish | all | 429 | -1.458 → +7.125 | -2.185 → +2.861 | 8.519 → 12.697 | 47.6% → 71.6% | 15.763 → 139.221 |
| finish | without_stop | 158 | -4.573 → -3.340 | -4.883 → -4.134 | 6.315 → 5.965 | 32.3% → 69.0% | 7.302 → 68.725 |
| finish | with_stop | 271 | +0.358 → +13.226 | +0.664 → +11.175 | 9.804 → 16.622 | 56.5% → 73.1% | 20.696 → 180.321 |

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

[Dataset, exclusions, plots and worst cases](../bahrain_2021_future/REPORT.md)

## spain_2022

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 542 | +0.049 → +0.049 | -0.142 → -0.142 | 0.781 → 0.781 | 62.7% → 62.7% | 1.183 → 1.183 |
| 1 | without_stop | 514 | -0.237 → -0.237 | -0.165 → -0.165 | 0.535 → 0.535 | 66.1% → 66.1% | 1.168 → 1.168 |
| 1 | with_stop | 28 | +5.303 → +5.303 | +5.401 → +5.401 | 5.303 → 5.303 | 0.0% → 0.0% | 1.472 → 1.472 |
| 5 | all | 540 | -1.305 → -1.063 | -1.392 → -1.146 | 2.881 → 2.811 | 41.1% → 46.9% | 3.856 → 4.377 |
| 5 | without_stop | 400 | -1.240 → -1.002 | -1.253 → -0.962 | 2.576 → 2.503 | 45.5% → 50.2% | 3.922 → 4.462 |
| 5 | with_stop | 140 | -1.492 → -1.237 | -1.776 → -1.568 | 3.753 → 3.689 | 28.6% → 37.1% | 3.666 → 4.134 |
| 10 | all | 490 | -2.525 → -1.683 | -2.634 → -1.760 | 5.032 → 4.888 | 40.4% → 85.3% | 6.679 → 32.865 |
| 10 | without_stop | 234 | -2.122 → -1.270 | -2.516 → -1.530 | 5.534 → 5.365 | 38.0% → 78.2% | 7.222 → 33.036 |
| 10 | with_stop | 256 | -2.893 → -2.061 | -2.691 → -1.930 | 4.574 → 4.452 | 42.6% → 91.8% | 6.181 → 32.709 |
| finish | all | 542 | -10.356 → +1.313 | -7.479 → -1.174 | 16.702 → 16.007 | 39.7% → 77.7% | 20.821 → 174.074 |
| finish | without_stop | 127 | -7.985 → -6.198 | -6.339 → -4.811 | 9.909 → 8.608 | 35.4% → 71.7% | 9.586 → 53.100 |
| finish | with_stop | 415 | -11.081 → +3.612 | -7.704 → +3.748 | 18.781 → 18.271 | 41.0% → 79.5% | 24.259 → 211.095 |

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

[Dataset, exclusions, plots and worst cases](../spain_2022_future/REPORT.md)

## france_2022

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429 | -0.614 → -1.181 | -0.063 → -0.083 | 1.583 → 1.455 | 62.9% → 62.9% | 0.917 → 0.937 |
| 1 | without_stop | 418 | -0.086 → -0.669 | -0.055 → -0.075 | 1.081 → 0.950 | 64.6% → 64.6% | 0.913 → 0.933 |
| 1 | with_stop | 11 | -20.664 → -20.664 | -18.451 → -18.451 | 20.664 → 20.664 | 0.0% → 0.0% | 1.083 → 1.083 |
| 5 | all | 429 | -8.665 → -11.448 | -0.745 → -0.573 | 18.264 → 15.288 | 41.7% → 45.5% | 3.017 → 3.477 |
| 5 | without_stop | 374 | +0.693 → -2.523 | -0.298 → -0.173 | 10.317 → 6.928 | 47.9% → 52.1% | 3.091 → 3.581 |
| 5 | with_stop | 55 | -72.301 → -72.138 | -95.092 → -94.720 | 72.301 → 72.138 | 0.0% → 0.0% | 2.519 → 2.766 |
| 10 | all | 379 | -24.129 → -26.862 | -3.165 → -2.576 | 35.500 → 31.957 | 31.4% → 55.7% | 5.161 → 35.392 |
| 10 | without_stop | 269 | +1.693 → -2.401 | -0.927 → -0.128 | 14.328 → 9.579 | 44.2% → 71.4% | 5.387 → 35.319 |
| 10 | with_stop | 110 | -87.274 → -86.682 | -100.351 → -99.939 | 87.274 → 86.682 | 0.0% → 17.3% | 4.609 → 35.572 |
| finish | all | 429 | -60.361 → -55.723 | -36.519 → -34.581 | 67.441 → 57.359 | 0.0% → 85.1% | 13.650 → 140.470 |
| finish | without_stop | 278 | -28.230 → -28.687 | -33.789 → -30.924 | 37.900 → 30.810 | 0.0% → 77.3% | 10.075 → 110.088 |
| finish | with_stop | 151 | -119.517 → -105.499 | -133.307 → -113.780 | 121.827 → 106.238 | 0.0% → 99.3% | 20.233 → 196.405 |

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

[Dataset, exclusions, plots and worst cases](../france_2022_future/REPORT.md)

## Prediction-weighted pool

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 1400 | -0.089 → -0.263 | -0.095 → -0.110 | 1.005 → 0.965 | 62.4% → 62.4% | 1.052 → 1.058 |
| 1 | without_stop | 1341 | -0.138 → -0.320 | -0.114 → -0.117 | 0.665 → 0.624 | 65.1% → 65.1% | 1.038 → 1.045 |
| 1 | with_stop | 59 | +1.026 → +1.026 | +5.629 → +5.629 | 8.731 → 8.731 | 0.0% → 0.0% | 1.357 → 1.357 |
| 5 | all | 1398 | -3.346 → -4.047 | -0.951 → -0.743 | 7.422 → 6.472 | 43.0% → 47.4% | 3.416 → 3.897 |
| 5 | without_stop | 1100 | -0.358 → -1.308 | -0.654 → -0.446 | 4.990 → 3.807 | 48.5% → 52.5% | 3.437 → 3.934 |
| 5 | with_stop | 298 | -14.375 → -14.156 | -2.490 → -2.241 | 16.399 → 16.310 | 22.8% → 28.5% | 3.339 → 3.761 |
| 10 | all | 1248 | -8.610 → -8.893 | -1.984 → -1.303 | 13.909 → 12.783 | 39.3% → 74.2% | 5.993 → 34.369 |
| 10 | without_stop | 707 | -0.225 → -1.297 | -1.119 → -0.406 | 8.327 → 6.470 | 43.1% → 75.2% | 6.183 → 34.592 |
| 10 | with_stop | 541 | -19.568 → -18.819 | -3.465 → -2.739 | 21.204 → 21.034 | 34.2% → 72.8% | 5.745 → 34.078 |
| finish | all | 1400 | -22.952 → -14.384 | -11.874 → -5.677 | 29.742 → 27.664 | 29.9% → 78.1% | 17.074 → 153.097 |
| finish | without_stop | 563 | -17.024 → -16.501 | -19.905 → -15.116 | 22.722 → 18.829 | 17.1% → 73.7% | 9.186 → 85.625 |
| finish | with_stop | 837 | -26.940 → -12.960 | -7.530 → +1.977 | 34.464 → 33.607 | 38.6% → 81.0% | 22.379 → 198.481 |

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

## Interpretation

Future risk improves finish coverage to 71.6% Bahrain, 77.7% Spain and 85.1%
France; prediction pooling is 78.1%. This is mainly slow-side uncertainty,
not accurate prediction of actual event timing. France retains a -34.581 s
median finish error. Its five worst medians are early VER finish forecasts;
their actual horizons include later SC/VSC while the median draw does not
reconstruct that realized sequence. Pace/wear and low clean-lap counts can
also contribute. Bahrain finish MAE worsens from 8.519 to 12.697 s. No tuning
was applied to remove this trade-off. See the subsequent outcome-only green
view to isolate horizons without actual neutralization.
