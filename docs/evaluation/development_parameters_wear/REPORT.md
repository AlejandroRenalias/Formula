# Causal parameter change: wear

Conditional green predictions evaluated on matched GREEN-cutoff/no-actual-SC-or-VSC outcomes. Same three development races, every lap, pit/no-pit labels unchanged. Entries previous -> current. No interval tuning or SC/VSC prior changes; held-out/wet evaluation races and UI untouched.

Per-prediction and equal-race pools are reported; equal-race pit strata normalize within contributing races. France has no green-only finish outcomes, so pooled green finish has two races.

## bahrain_2021

| Horizon | Pit group | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | all | 428 | -0.114 -> -0.058 | -0.119 -> -0.045 | +0.433 -> +0.423 | -0.114 -> -0.058 | 61.7% -> 66.4% | 0.997 -> 1.015 |
| 1 | without_stop | 408 | -0.068 -> -0.004 | -0.104 -> -0.027 | +0.403 -> +0.387 | -0.068 -> -0.004 | 64.2% -> 69.1% | 1.005 -> 1.024 |
| 1 | with_stop | 20 | -1.048 -> -1.160 | -1.035 -> -1.104 | +1.048 -> +1.160 | -1.048 -> -1.160 | 10.0% -> 10.0% | 0.851 -> 0.831 |
| 5 | all | 428 | -0.481 -> -0.093 | -0.369 -> +0.059 | +1.932 -> +1.855 | -0.096 -> -0.019 | 52.6% -> 56.8% | 3.380 -> 3.495 |
| 5 | without_stop | 325 | -0.420 -> +0.164 | -0.433 -> +0.270 | +1.843 -> +1.691 | -0.084 -> +0.033 | 53.5% -> 58.5% | 3.380 -> 3.524 |
| 5 | with_stop | 103 | -0.676 -> -0.906 | -0.229 -> -0.586 | +2.210 -> +2.370 | -0.135 -> -0.181 | 49.5% -> 51.5% | 3.381 -> 3.405 |
| 10 | all | 378 | -0.016 -> +0.829 | +0.231 -> +1.632 | +3.769 -> +3.727 | -0.002 -> +0.083 | 51.6% -> 55.8% | 6.516 -> 6.741 |
| 10 | without_stop | 203 | -0.419 -> +1.211 | -0.508 -> +1.635 | +3.636 -> +3.510 | -0.042 -> +0.121 | 51.7% -> 55.2% | 6.732 -> 7.055 |
| 10 | with_stop | 175 | +0.452 -> +0.385 | +1.503 -> +1.630 | +3.922 -> +3.979 | +0.045 -> +0.039 | 51.4% -> 56.6% | 6.266 -> 6.376 |
| finish | all | 428 | +1.753 -> +7.270 | -0.094 -> +4.445 | +9.488 -> +13.210 | -0.093 -> +0.093 | 49.5% -> 37.9% | 16.389 -> 17.158 |
| finish | without_stop | 157 | -4.592 -> -2.446 | -4.633 -> -3.197 | +6.196 -> +5.151 | -0.445 -> -0.278 | 36.9% -> 43.3% | 8.035 -> 8.686 |
| finish | with_stop | 271 | +5.430 -> +12.899 | +4.757 -> +13.302 | +11.395 -> +17.878 | +0.111 -> +0.308 | 56.8% -> 34.7% | 21.229 -> 22.066 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 428 | 0.423 | -0.058 | -0.045 | -0.058 | -0.045 | 0.423 | 66.4% | 1.015 | 59 | 85 | 2.493 |
| 1 | without_stop | 408 | 0.387 | -0.004 | -0.027 | -0.004 | -0.027 | 0.387 | 69.1% | 1.024 | 59 | 67 | 2.198 |
| 1 | with_stop | 20 | 1.160 | -1.160 | -1.104 | -1.160 | -1.104 | 1.160 | 10.0% | 0.831 | 0 | 18 | 8.512 |
| 5 | all | 428 | 1.855 | -0.093 | +0.059 | -0.019 | +0.012 | 0.371 | 56.8% | 3.495 | 81 | 104 | 11.041 |
| 5 | without_stop | 325 | 1.691 | +0.164 | +0.270 | +0.033 | +0.054 | 0.338 | 58.5% | 3.524 | 66 | 69 | 9.553 |
| 5 | with_stop | 103 | 2.370 | -0.906 | -0.586 | -0.181 | -0.117 | 0.474 | 51.5% | 3.405 | 15 | 35 | 15.737 |
| 10 | all | 378 | 3.727 | +0.829 | +1.632 | +0.083 | +0.163 | 0.373 | 55.8% | 6.741 | 95 | 72 | 20.821 |
| 10 | without_stop | 203 | 3.510 | +1.211 | +1.635 | +0.121 | +0.164 | 0.351 | 55.2% | 7.055 | 58 | 33 | 18.976 |
| 10 | with_stop | 175 | 3.979 | +0.385 | +1.630 | +0.039 | +0.163 | 0.398 | 56.6% | 6.376 | 37 | 39 | 22.962 |
| finish | all | 428 | 13.210 | +7.270 | +4.445 | +0.093 | +0.166 | 0.476 | 37.9% | 17.158 | 161 | 105 | 69.572 |
| finish | without_stop | 157 | 5.151 | -2.446 | -3.197 | -0.278 | -0.279 | 0.423 | 43.3% | 8.686 | 21 | 68 | 29.953 |
| finish | with_stop | 271 | 17.878 | +12.899 | +13.302 | +0.308 | +0.352 | 0.507 | 34.7% | 22.066 | 140 | 37 | 92.524 |

## spain_2022

| Horizon | Pit group | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | all | 542 | -0.314 -> -0.326 | -0.197 -> -0.201 | +0.600 -> +0.586 | -0.314 -> -0.326 | 63.1% -> 63.1% | 1.162 -> 1.182 |
| 1 | without_stop | 514 | -0.235 -> -0.230 | -0.162 -> -0.157 | +0.536 -> +0.504 | -0.235 -> -0.230 | 66.1% -> 66.5% | 1.167 -> 1.188 |
| 1 | with_stop | 28 | -1.767 -> -2.085 | -1.667 -> -2.084 | +1.767 -> +2.085 | -1.767 -> -2.085 | 7.1% -> 0.0% | 1.078 -> 1.077 |
| 5 | all | 540 | -1.363 -> -1.458 | -1.220 -> -1.177 | +2.630 -> +2.491 | -0.273 -> -0.292 | 46.7% -> 48.3% | 4.020 -> 4.120 |
| 5 | without_stop | 400 | -1.173 -> -1.083 | -1.120 -> -0.817 | +2.551 -> +2.264 | -0.235 -> -0.217 | 46.5% -> 52.2% | 4.106 -> 4.215 |
| 5 | with_stop | 140 | -1.905 -> -2.528 | -1.393 -> -2.241 | +2.856 -> +3.138 | -0.381 -> -0.506 | 47.1% -> 37.1% | 3.775 -> 3.850 |
| 10 | all | 490 | -2.089 -> -2.423 | -2.178 -> -2.175 | +4.756 -> +4.413 | -0.209 -> -0.242 | 45.5% -> 50.0% | 7.347 -> 7.559 |
| 10 | without_stop | 234 | -1.954 -> -1.704 | -2.254 -> -1.498 | +5.477 -> +4.626 | -0.195 -> -0.170 | 40.2% -> 50.9% | 7.947 -> 8.218 |
| 10 | with_stop | 256 | -2.213 -> -3.080 | -2.101 -> -2.721 | +4.096 -> +4.219 | -0.221 -> -0.308 | 50.4% -> 49.2% | 6.799 -> 6.956 |
| finish | all | 542 | -7.339 -> -9.935 | -5.063 -> -8.984 | +16.150 -> +15.983 | -0.309 -> -0.410 | 40.6% -> 38.0% | 21.174 -> 21.983 |
| finish | without_stop | 127 | -7.834 -> -7.801 | -6.511 -> -6.907 | +9.836 -> +8.648 | -0.723 -> -0.762 | 37.0% -> 40.2% | 10.436 -> 10.657 |
| finish | with_stop | 415 | -7.188 -> -10.588 | -3.762 -> -10.332 | +18.082 -> +18.228 | -0.182 -> -0.303 | 41.7% -> 37.3% | 24.460 -> 25.449 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 542 | 0.586 | -0.326 | -0.201 | -0.326 | -0.201 | 0.586 | 63.1% | 1.182 | 54 | 146 | 3.578 |
| 1 | without_stop | 514 | 0.504 | -0.230 | -0.157 | -0.230 | -0.157 | 0.504 | 66.5% | 1.188 | 54 | 118 | 2.875 |
| 1 | with_stop | 28 | 2.085 | -2.085 | -2.084 | -2.085 | -2.084 | 2.085 | 0.0% | 1.077 | 0 | 28 | 16.493 |
| 5 | all | 540 | 2.491 | -1.458 | -1.177 | -0.292 | -0.235 | 0.498 | 48.3% | 4.120 | 60 | 219 | 15.926 |
| 5 | without_stop | 400 | 2.264 | -1.083 | -0.817 | -0.217 | -0.163 | 0.453 | 52.2% | 4.215 | 55 | 136 | 13.636 |
| 5 | with_stop | 140 | 3.138 | -2.528 | -2.241 | -0.506 | -0.448 | 0.628 | 37.1% | 3.850 | 5 | 83 | 22.466 |
| 10 | all | 490 | 4.413 | -2.423 | -2.175 | -0.242 | -0.218 | 0.441 | 50.0% | 7.559 | 42 | 203 | 27.497 |
| 10 | without_stop | 234 | 4.626 | -1.704 | -1.498 | -0.170 | -0.150 | 0.463 | 50.9% | 8.218 | 31 | 84 | 26.697 |
| 10 | with_stop | 256 | 4.219 | -3.080 | -2.721 | -0.308 | -0.272 | 0.422 | 49.2% | 6.956 | 11 | 119 | 28.227 |
| finish | all | 542 | 15.983 | -9.935 | -8.984 | -0.410 | -0.368 | 0.548 | 38.0% | 21.983 | 42 | 294 | 102.978 |
| finish | without_stop | 127 | 8.648 | -7.801 | -6.907 | -0.762 | -0.519 | 0.821 | 40.2% | 10.657 | 6 | 70 | 57.734 |
| finish | with_stop | 415 | 18.228 | -10.588 | -10.332 | -0.303 | -0.340 | 0.464 | 37.3% | 25.449 | 36 | 224 | 116.824 |

## france_2022

| Horizon | Pit group | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | all | 395 | -0.067 -> -0.050 | -0.055 -> -0.024 | +0.363 -> +0.370 | -0.067 -> -0.050 | 67.3% -> 66.6% | 0.932 -> 0.938 |
| 1 | without_stop | 393 | -0.050 -> -0.033 | -0.055 -> -0.024 | +0.341 -> +0.348 | -0.050 -> -0.033 | 67.7% -> 66.9% | 0.928 -> 0.934 |
| 1 | with_stop | 2 | -3.415 -> -3.486 | -3.415 -> -3.486 | +4.722 -> +4.637 | -3.415 -> -3.486 | 0.0% -> 0.0% | 1.652 -> 1.652 |
| 5 | all | 316 | -0.157 -> -0.021 | -0.065 -> +0.126 | +1.506 -> +1.604 | -0.031 -> -0.004 | 58.9% -> 58.2% | 3.261 -> 3.321 |
| 5 | without_stop | 309 | -0.011 -> +0.128 | -0.048 -> +0.126 | +1.382 -> +1.482 | -0.002 -> +0.026 | 59.5% -> 58.9% | 3.266 -> 3.327 |
| 5 | with_stop | 7 | -6.573 -> -6.594 | -8.855 -> -8.903 | +6.956 -> +6.966 | -1.315 -> -1.319 | 28.6% -> 28.6% | 3.054 -> 3.065 |
| 10 | all | 217 | -0.282 -> +0.006 | -0.521 -> +0.217 | +2.900 -> +3.346 | -0.028 -> +0.001 | 57.1% -> 51.6% | 6.157 -> 6.226 |
| 10 | without_stop | 208 | +0.101 -> +0.396 | -0.347 -> +0.286 | +2.631 -> +3.100 | +0.010 -> +0.040 | 59.6% -> 53.8% | 6.208 -> 6.277 |
| 10 | with_stop | 9 | -9.117 -> -9.020 | -9.047 -> -9.235 | +9.117 -> +9.020 | -0.912 -> -0.902 | 0.0% -> 0.0% | 4.988 -> 5.036 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 395 | 0.370 | -0.050 | -0.024 | -0.050 | -0.024 | 0.370 | 66.6% | 0.938 | 64 | 68 | 2.057 |
| 1 | without_stop | 393 | 0.348 | -0.033 | -0.024 | -0.033 | -0.024 | 0.348 | 66.9% | 0.934 | 63 | 67 | 1.862 |
| 1 | with_stop | 2 | 4.637 | -3.486 | -3.486 | -3.486 | -3.486 | 4.637 | 0.0% | 1.652 | 1 | 1 | 40.390 |
| 5 | all | 316 | 1.604 | -0.021 | +0.126 | -0.004 | +0.025 | 0.321 | 58.2% | 3.321 | 64 | 68 | 9.464 |
| 5 | without_stop | 309 | 1.482 | +0.128 | +0.126 | +0.026 | +0.025 | 0.296 | 58.9% | 3.327 | 64 | 63 | 8.262 |
| 5 | with_stop | 7 | 6.966 | -6.594 | -8.903 | -1.319 | -1.781 | 1.393 | 28.6% | 3.065 | 0 | 5 | 62.522 |
| 10 | all | 217 | 3.346 | +0.006 | +0.217 | +0.001 | +0.022 | 0.335 | 51.6% | 6.226 | 50 | 55 | 20.526 |
| 10 | without_stop | 208 | 3.100 | +0.396 | +0.286 | +0.040 | +0.029 | 0.310 | 53.8% | 6.277 | 50 | 46 | 18.162 |
| 10 | with_stop | 9 | 9.020 | -9.020 | -9.235 | -0.902 | -0.924 | 0.902 | 0.0% | 5.036 | 0 | 9 | 75.176 |

## pooled_prediction

| Horizon | Pit group | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | all | 1365 | -0.180 -> -0.162 | -0.128 -> -0.092 | +0.479 -> +0.472 | -0.180 -> -0.162 | 63.9% -> 65.1% | 1.044 -> 1.059 |
| 1 | without_stop | 1315 | -0.128 -> -0.101 | -0.113 -> -0.072 | +0.437 -> +0.421 | -0.128 -> -0.101 | 66.0% -> 67.5% | 1.045 -> 1.061 |
| 1 | with_stop | 50 | -1.545 -> -1.771 | -1.374 -> -1.589 | +1.598 -> +1.817 | -1.545 -> -1.771 | 8.0% -> 4.0% | 1.011 -> 1.002 |
| 5 | all | 1284 | -0.772 -> -0.649 | -0.608 -> -0.418 | +2.120 -> +2.060 | -0.154 -> -0.130 | 51.6% -> 53.6% | 3.620 -> 3.715 |
| 5 | without_stop | 1034 | -0.589 -> -0.329 | -0.508 -> -0.239 | +1.979 -> +1.850 | -0.118 -> -0.066 | 52.6% -> 56.2% | 3.627 -> 3.732 |
| 5 | with_stop | 250 | -1.530 -> -1.973 | -1.020 -> -1.484 | +2.705 -> +2.929 | -0.306 -> -0.395 | 47.6% -> 42.8% | 3.592 -> 3.645 |
| 10 | all | 1085 | -1.005 -> -0.804 | -0.802 -> -0.500 | +4.041 -> +3.961 | -0.101 -> -0.080 | 50.0% -> 52.4% | 6.819 -> 7.007 |
| 10 | without_stop | 645 | -0.808 -> -0.110 | -0.766 -> +0.168 | +3.980 -> +3.783 | -0.081 -> -0.011 | 50.1% -> 53.2% | 7.004 -> 7.226 |
| 10 | with_stop | 440 | -1.294 -> -1.823 | -0.961 -> -1.316 | +4.129 -> +4.222 | -0.129 -> -0.182 | 49.8% -> 51.1% | 6.550 -> 6.686 |
| finish | all | 970 | -3.327 -> -2.343 | -2.234 -> -3.320 | +13.210 -> +14.760 | -0.213 -> -0.188 | 44.5% -> 37.9% | 19.063 -> 19.854 |
| finish | without_stop | 284 | -6.042 -> -4.840 | -5.322 -> -3.836 | +7.823 -> +6.715 | -0.569 -> -0.494 | 37.0% -> 41.9% | 9.109 -> 9.567 |
| finish | with_stop | 686 | -2.203 -> -1.310 | +0.626 -> -1.937 | +15.440 -> +18.090 | -0.066 -> -0.062 | 47.7% -> 36.3% | 23.183 -> 24.113 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.472 | -0.162 | -0.092 | -0.162 | -0.092 | 0.472 | 65.1% | 1.059 | 177 | 299 | 2.798 |
| 1 | without_stop | 1315 | 0.421 | -0.101 | -0.072 | -0.101 | -0.072 | 0.421 | 67.5% | 1.061 | 176 | 252 | 2.362 |
| 1 | with_stop | 50 | 1.817 | -1.771 | -1.589 | -1.771 | -1.589 | 1.817 | 4.0% | 1.002 | 1 | 47 | 14.257 |
| 5 | all | 1284 | 2.060 | -0.649 | -0.418 | -0.130 | -0.084 | 0.412 | 53.6% | 3.715 | 205 | 391 | 12.707 |
| 5 | without_stop | 1034 | 1.850 | -0.329 | -0.239 | -0.066 | -0.048 | 0.370 | 56.2% | 3.732 | 185 | 268 | 10.747 |
| 5 | with_stop | 250 | 2.929 | -1.973 | -1.484 | -0.395 | -0.297 | 0.586 | 42.8% | 3.645 | 20 | 123 | 20.815 |
| 10 | all | 1085 | 3.961 | -0.804 | -0.500 | -0.080 | -0.050 | 0.396 | 52.4% | 7.007 | 187 | 330 | 23.777 |
| 10 | without_stop | 645 | 3.783 | -0.110 | +0.168 | -0.011 | +0.017 | 0.378 | 53.2% | 7.226 | 139 | 163 | 21.515 |
| 10 | with_stop | 440 | 4.222 | -1.823 | -1.316 | -0.182 | -0.132 | 0.422 | 51.1% | 6.686 | 48 | 167 | 27.093 |
| finish | all | 970 | 14.760 | -2.343 | -3.320 | -0.188 | -0.162 | 0.516 | 37.9% | 19.854 | 203 | 399 | 88.238 |
| finish | without_stop | 284 | 6.715 | -4.840 | -3.836 | -0.494 | -0.387 | 0.601 | 41.9% | 9.567 | 27 | 138 | 42.376 |
| finish | with_stop | 686 | 18.090 | -1.310 | -1.937 | -0.062 | -0.075 | 0.481 | 36.3% | 24.113 | 176 | 261 | 107.224 |

## pooled_equal_race

| Horizon | Pit group | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | all | 1365 | -0.165 -> -0.145 | -0.119 -> -0.085 | +0.465 -> +0.460 | -0.165 -> -0.145 | 64.0% -> 65.3% | 1.031 -> 1.045 |
| 1 | without_stop | 1315 | -0.118 -> -0.089 | -0.111 -> -0.064 | +0.427 -> +0.413 | -0.118 -> -0.089 | 66.0% -> 67.5% | 1.033 -> 1.049 |
| 1 | with_stop | 50 | -2.077 -> -2.244 | -1.336 -> -1.412 | +2.512 -> +2.627 | -2.077 -> -2.244 | 5.7% -> 3.3% | 1.194 -> 1.187 |
| 5 | all | 1284 | -0.667 -> -0.524 | -0.501 -> -0.304 | +2.022 -> +1.983 | -0.133 -> -0.105 | 52.7% -> 54.4% | 3.554 -> 3.645 |
| 5 | without_stop | 1034 | -0.535 -> -0.264 | -0.472 -> -0.142 | +1.925 -> +1.813 | -0.107 -> -0.053 | 53.2% -> 56.5% | 3.584 -> 3.688 |
| 5 | with_stop | 250 | -3.051 -> -3.342 | -1.485 -> -1.897 | +4.007 -> +4.158 | -0.610 -> -0.668 | 41.7% -> 39.1% | 3.403 -> 3.440 |
| 10 | all | 1085 | -0.796 -> -0.530 | -0.628 -> -0.169 | +3.808 -> +3.829 | -0.080 -> -0.053 | 51.4% -> 52.5% | 6.673 -> 6.842 |
| 10 | without_stop | 645 | -0.758 -> -0.032 | -0.722 -> +0.212 | +3.915 -> +3.745 | -0.076 -> -0.003 | 50.5% -> 53.3% | 6.962 -> 7.183 |
| 10 | with_stop | 440 | -3.626 -> -3.905 | -3.855 -> -4.504 | +5.712 -> +5.739 | -0.363 -> -0.390 | 33.9% -> 35.3% | 6.017 -> 6.123 |
| finish | all | 970 | -2.793 -> -1.332 | -1.901 -> -2.564 | +12.819 -> +14.597 | -0.201 -> -0.159 | 45.1% -> 37.9% | 18.781 -> 19.571 |
| finish | without_stop | 284 | -6.213 -> -5.123 | -5.478 -> -3.876 | +8.016 -> +6.899 | -0.584 -> -0.520 | 37.0% -> 41.7% | 9.236 -> 9.672 |
| finish | with_stop | 686 | -0.879 -> +1.156 | +1.404 -> +1.586 | +14.739 -> +18.053 | -0.035 -> +0.002 | 49.3% -> 36.0% | 22.844 -> 23.758 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.460 | -0.145 | -0.085 | -0.145 | -0.085 | 0.460 | 65.3% | 1.045 | 177 | 299 | 2.709 |
| 1 | without_stop | 1315 | 0.413 | -0.089 | -0.064 | -0.089 | -0.064 | 0.413 | 67.5% | 1.049 | 176 | 252 | 2.311 |
| 1 | with_stop | 50 | 2.627 | -2.244 | -1.412 | -2.244 | -1.412 | 2.627 | 3.3% | 1.187 | 1 | 47 | 21.798 |
| 5 | all | 1284 | 1.983 | -0.524 | -0.304 | -0.105 | -0.061 | 0.397 | 54.4% | 3.645 | 205 | 391 | 12.143 |
| 5 | without_stop | 1034 | 1.813 | -0.264 | -0.142 | -0.053 | -0.028 | 0.363 | 56.5% | 3.688 | 185 | 268 | 10.484 |
| 5 | with_stop | 250 | 4.158 | -3.342 | -1.897 | -0.668 | -0.379 | 0.832 | 39.1% | 3.440 | 20 | 123 | 33.575 |
| 10 | all | 1085 | 3.829 | -0.530 | -0.169 | -0.053 | -0.017 | 0.383 | 52.5% | 6.842 | 187 | 330 | 22.948 |
| 10 | without_stop | 645 | 3.745 | -0.032 | +0.212 | -0.003 | +0.021 | 0.375 | 53.3% | 7.183 | 139 | 163 | 21.278 |
| 10 | with_stop | 440 | 5.739 | -3.905 | -4.504 | -0.390 | -0.450 | 0.574 | 35.3% | 6.123 | 48 | 167 | 42.122 |
| finish | all | 970 | 14.597 | -1.332 | -2.564 | -0.159 | -0.123 | 0.512 | 37.9% | 19.571 | 203 | 399 | 86.275 |
| finish | without_stop | 284 | 6.899 | -5.123 | -3.876 | -0.520 | -0.392 | 0.622 | 41.7% | 9.672 | 27 | 138 | 43.844 |
| finish | with_stop | 686 | 18.053 | +1.156 | +1.586 | +0.002 | +0.054 | 0.486 | 36.0% | 23.758 | 176 | 261 | 104.674 |

## No-stop long-horizon compound/age: bahrain_2021

Tyre age is at the cutoff; these are descriptive correlated groups, not regression inputs.

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s |
| --- | --- | --- | ---: | --- | --- | --- |
| 10 | age | 0-9 | 147 | +0.043 -> +0.162 | +0.014 -> +0.212 | +0.332 -> +0.318 |
| 10 | age | 10-19 | 50 | -0.314 -> -0.066 | -0.420 -> -0.214 | +0.454 -> +0.410 |
| 10 | age | 20-29 | 6 | +0.156 -> +0.673 | -0.017 -> +0.371 | +0.390 -> +0.673 |
| 10 | compound | HARD | 139 | -0.016 -> +0.128 | -0.007 -> +0.178 | +0.420 -> +0.383 |
| 10 | compound | MEDIUM | 64 | -0.099 -> +0.105 | -0.062 -> +0.161 | +0.241 -> +0.281 |
| 10 | compound_and_age | HARD/0-9 | 92 | +0.131 -> +0.194 | +0.190 -> +0.254 | +0.374 -> +0.332 |
| 10 | compound_and_age | HARD/10-19 | 41 | -0.370 -> -0.099 | -0.543 -> -0.294 | +0.529 -> +0.456 |
| 10 | compound_and_age | HARD/20-29 | 6 | +0.156 -> +0.673 | -0.017 -> +0.371 | +0.390 -> +0.673 |
| 10 | compound_and_age | MEDIUM/0-9 | 55 | -0.105 -> +0.109 | -0.067 -> +0.184 | +0.262 -> +0.294 |
| 10 | compound_and_age | MEDIUM/10-19 | 9 | -0.061 -> +0.081 | -0.051 -> +0.053 | +0.112 -> +0.200 |
| finish | age | 0-9 | 75 | -0.188 -> -0.080 | -0.080 -> -0.021 | +0.366 -> +0.324 |
| finish | age | 10-19 | 74 | -0.660 -> -0.438 | -0.648 -> -0.423 | +0.660 -> +0.497 |
| finish | age | 20-29 | 8 | -0.856 -> -0.656 | -0.856 -> -0.696 | +0.856 -> +0.656 |
| finish | compound | HARD | 144 | -0.477 -> -0.278 | -0.551 -> -0.291 | +0.570 -> +0.430 |
| finish | compound | MEDIUM | 13 | -0.084 -> -0.283 | -0.061 -> -0.078 | +0.084 -> +0.337 |
| finish | compound_and_age | HARD/0-9 | 71 | -0.194 -> -0.035 | -0.092 -> +0.050 | +0.383 -> +0.293 |
| finish | compound_and_age | HARD/10-19 | 65 | -0.740 -> -0.497 | -0.692 -> -0.492 | +0.740 -> +0.552 |
| finish | compound_and_age | HARD/20-29 | 8 | -0.856 -> -0.656 | -0.856 -> -0.696 | +0.856 -> +0.656 |
| finish | compound_and_age | MEDIUM/0-9 | 4 | -0.077 -> -0.877 | -0.063 -> -0.873 | +0.077 -> +0.877 |
| finish | compound_and_age | MEDIUM/10-19 | 9 | -0.087 -> -0.018 | -0.061 -> +0.028 | +0.087 -> +0.097 |

## No-stop long-horizon compound/age: spain_2022

Tyre age is at the cutoff; these are descriptive correlated groups, not regression inputs.

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s |
| --- | --- | --- | ---: | --- | --- | --- |
| 10 | age | 0-9 | 186 | -0.189 -> -0.209 | -0.225 -> -0.255 | +0.575 -> +0.476 |
| 10 | age | 10-19 | 45 | -0.224 -> -0.037 | -0.231 -> +0.051 | +0.458 -> +0.420 |
| 10 | age | 20-29 | 3 | -0.173 -> +0.223 | -0.135 -> +0.284 | +0.219 -> +0.260 |
| 10 | compound | MEDIUM | 146 | -0.365 -> -0.097 | -0.387 -> -0.130 | +0.473 -> +0.407 |
| 10 | compound | SOFT | 88 | +0.087 -> -0.292 | +0.301 -> -0.281 | +0.672 -> +0.555 |
| 10 | compound_and_age | MEDIUM/0-9 | 115 | -0.386 -> -0.146 | -0.417 -> -0.210 | +0.511 -> +0.451 |
| 10 | compound_and_age | MEDIUM/10-19 | 28 | -0.300 -> +0.068 | -0.245 -> +0.054 | +0.342 -> +0.241 |
| 10 | compound_and_age | MEDIUM/20-29 | 3 | -0.173 -> +0.223 | -0.135 -> +0.284 | +0.219 -> +0.260 |
| 10 | compound_and_age | SOFT/0-9 | 71 | +0.131 -> -0.311 | +0.339 -> -0.309 | +0.678 -> +0.517 |
| 10 | compound_and_age | SOFT/10-19 | 17 | -0.099 -> -0.211 | -0.200 -> -0.059 | +0.649 -> +0.715 |
| finish | age | 0-9 | 68 | -0.679 -> -0.785 | -0.813 -> -0.600 | +0.943 -> +0.793 |
| finish | age | 10-19 | 51 | -0.820 -> -0.825 | -0.300 -> -0.482 | +0.832 -> +0.940 |
| finish | age | 20-29 | 8 | -0.475 -> -0.157 | -0.533 -> -0.243 | +0.475 -> +0.298 |
| finish | compound | MEDIUM | 44 | -0.582 -> -0.186 | -0.540 -> -0.311 | +0.584 -> +0.345 |
| finish | compound | SOFT | 83 | -0.798 -> -1.067 | -0.769 -> -0.953 | +1.020 -> +1.073 |
| finish | compound_and_age | MEDIUM/0-9 | 18 | -0.939 -> -0.489 | -0.849 -> -0.486 | +0.939 -> +0.489 |
| finish | compound_and_age | MEDIUM/10-19 | 18 | -0.272 -> +0.105 | -0.174 -> +0.183 | +0.276 -> +0.221 |
| finish | compound_and_age | MEDIUM/20-29 | 8 | -0.475 -> -0.157 | -0.533 -> -0.243 | +0.475 -> +0.298 |
| finish | compound_and_age | SOFT/0-9 | 50 | -0.586 -> -0.892 | -0.751 -> -0.917 | +0.944 -> +0.902 |
| finish | compound_and_age | SOFT/10-19 | 33 | -1.119 -> -1.332 | -0.890 -> -1.047 | +1.135 -> +1.332 |

## No-stop long-horizon compound/age: france_2022

Tyre age is at the cutoff; these are descriptive correlated groups, not regression inputs.

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s |
| --- | --- | --- | ---: | --- | --- | --- |
| 10 | age | 0-9 | 99 | +0.209 -> +0.289 | +0.170 -> +0.292 | +0.284 -> +0.340 |
| 10 | age | 10-19 | 94 | -0.205 -> -0.234 | -0.222 -> -0.259 | +0.254 -> +0.297 |
| 10 | age | 20-29 | 15 | +0.044 -> +0.109 | -0.016 -> +0.090 | +0.180 -> +0.195 |
| 10 | compound | HARD | 172 | -0.029 -> +0.003 | -0.054 -> -0.018 | +0.252 -> +0.312 |
| 10 | compound | MEDIUM | 36 | +0.198 -> +0.212 | +0.115 -> +0.255 | +0.315 -> +0.300 |
| 10 | compound_and_age | HARD/0-9 | 67 | +0.199 -> +0.312 | +0.170 -> +0.275 | +0.256 -> +0.344 |
| 10 | compound_and_age | HARD/10-19 | 90 | -0.211 -> -0.244 | -0.231 -> -0.269 | +0.262 -> +0.308 |
| 10 | compound_and_age | HARD/20-29 | 15 | +0.044 -> +0.109 | -0.016 -> +0.090 | +0.180 -> +0.195 |
| 10 | compound_and_age | MEDIUM/0-9 | 32 | +0.231 -> +0.239 | +0.186 -> +0.306 | +0.344 -> +0.329 |
| 10 | compound_and_age | MEDIUM/10-19 | 4 | -0.069 -> -0.005 | -0.091 -> -0.008 | +0.087 -> +0.067 |

## No-stop long-horizon compound/age: pooled_prediction

Tyre age is at the cutoff; these are descriptive correlated groups, not regression inputs.

| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s |
| --- | --- | --- | ---: | --- | --- | --- |
| 10 | age | 0-9 | 432 | -0.019 -> +0.031 | +0.018 -> +0.108 | +0.425 -> +0.391 |
| 10 | age | 10-19 | 189 | -0.238 -> -0.143 | -0.236 -> -0.185 | +0.356 -> +0.356 |
| 10 | age | 20-29 | 24 | +0.045 -> +0.265 | -0.021 -> +0.112 | +0.237 -> +0.323 |
| 10 | compound | HARD | 311 | -0.023 -> +0.059 | -0.051 -> +0.027 | +0.327 -> +0.344 |
| 10 | compound | MEDIUM | 246 | -0.214 -> +0.001 | -0.151 -> +0.042 | +0.389 -> +0.358 |
| 10 | compound | SOFT | 88 | +0.087 -> -0.292 | +0.301 -> -0.281 | +0.672 -> +0.555 |
| 10 | compound_and_age | HARD/0-9 | 159 | +0.160 -> +0.244 | +0.174 -> +0.257 | +0.324 -> +0.337 |
| 10 | compound_and_age | HARD/10-19 | 131 | -0.261 -> -0.198 | -0.289 -> -0.274 | +0.345 -> +0.354 |
| 10 | compound_and_age | HARD/20-29 | 21 | +0.076 -> +0.270 | -0.016 -> +0.090 | +0.240 -> +0.332 |
| 10 | compound_and_age | MEDIUM/0-9 | 202 | -0.212 -> -0.015 | -0.154 -> +0.034 | +0.417 -> +0.389 |
| 10 | compound_and_age | MEDIUM/10-19 | 41 | -0.225 -> +0.064 | -0.139 -> +0.051 | +0.267 -> +0.215 |
| 10 | compound_and_age | MEDIUM/20-29 | 3 | -0.173 -> +0.223 | -0.135 -> +0.284 | +0.219 -> +0.260 |
| 10 | compound_and_age | SOFT/0-9 | 71 | +0.131 -> -0.311 | +0.339 -> -0.309 | +0.678 -> +0.517 |
| 10 | compound_and_age | SOFT/10-19 | 17 | -0.099 -> -0.211 | -0.200 -> -0.059 | +0.649 -> +0.715 |
| finish | age | 0-9 | 143 | -0.422 -> -0.415 | -0.460 -> -0.299 | +0.641 -> +0.547 |
| finish | age | 10-19 | 125 | -0.726 -> -0.596 | -0.615 -> -0.430 | +0.730 -> +0.678 |
| finish | age | 20-29 | 16 | -0.666 -> -0.407 | -0.680 -> -0.420 | +0.666 -> +0.477 |
| finish | compound | HARD | 144 | -0.477 -> -0.278 | -0.551 -> -0.291 | +0.570 -> +0.430 |
| finish | compound | MEDIUM | 57 | -0.468 -> -0.208 | -0.336 -> -0.190 | +0.470 -> +0.343 |
| finish | compound | SOFT | 83 | -0.798 -> -1.067 | -0.769 -> -0.953 | +1.020 -> +1.073 |
| finish | compound_and_age | HARD/0-9 | 71 | -0.194 -> -0.035 | -0.092 -> +0.050 | +0.383 -> +0.293 |
| finish | compound_and_age | HARD/10-19 | 65 | -0.740 -> -0.497 | -0.692 -> -0.492 | +0.740 -> +0.552 |
| finish | compound_and_age | HARD/20-29 | 8 | -0.856 -> -0.656 | -0.856 -> -0.696 | +0.856 -> +0.656 |
| finish | compound_and_age | MEDIUM/0-9 | 22 | -0.783 -> -0.560 | -0.813 -> -0.568 | +0.783 -> +0.560 |
| finish | compound_and_age | MEDIUM/10-19 | 27 | -0.210 -> +0.064 | -0.147 -> +0.101 | +0.213 -> +0.179 |
| finish | compound_and_age | MEDIUM/20-29 | 8 | -0.475 -> -0.157 | -0.533 -> -0.243 | +0.475 -> +0.298 |
| finish | compound_and_age | SOFT/0-9 | 50 | -0.586 -> -0.892 | -0.751 -> -0.917 | +0.944 -> +0.902 |
| finish | compound_and_age | SOFT/10-19 | 33 | -1.119 -> -1.332 | -0.890 -> -1.047 | +1.135 -> +1.332 |

## Interpretation

This is a mixed result, not a validated improvement. Pooled per-prediction green
10-lap MAE changes 4.041 -> 3.961 s, bias -1.005 -> -0.804 s, coverage
50.0% -> 52.3%. Equal-race 10-lap MAE instead changes 3.808 -> 3.829 s.
Pooled green finish MAE worsens 13.210 -> 14.759 s and coverage falls
44.5% -> 37.9%; equal-race finish MAE worsens 12.819 -> 14.597 s.
France has no qualifying green finish outcomes.

No-stop finish MAE improves in Bahrain 6.196 -> 5.151 s and Spain
9.835 -> 8.648 s. Bahrain's signed error/lap improves -0.445 -> -0.278,
but Spain's worsens -0.723 -> -0.762. These are averages of per-prediction
error/lap, so shorter remaining horizons can move that metric differently
from absolute MAE. At 10 laps France's average bias is nearly zero, but
MAE worsens 2.900 -> 3.346 s. Bahrain's overall finish bias overshoots to
+7.270 s; the pit-containing finish stratum worsens despite identical stop
parameters because forecasts span multiple fitted-compound stints.

Pooled no-stop finish error/lap improves on HARD -0.477 -> -0.278 and
MEDIUM -0.468 -> -0.208, while SOFT worsens -0.798 -> -1.067.
The compound/age tables above show every matched group, including joint
compound/age strata. These results do not support a claim that the remaining
bias has been solved by wear fitting. Within-stint slopes can conflate fuel
correction error, track evolution, traffic and pace management with tyre wear.
No further fitting, selection by evaluation error or interval tuning was done.

## Causal parameter availability

Rates below summarize estimates across snapshots, not a fitted race-wide final
parameter. Each snapshot retains its own counts, fallback flag and source time.
France's unused SOFT retains its default throughout; Spain HARD often falls back.

| Race | Compound | Fallback snapshots / total | Rate min / median / max s/lap | Maximum qualifying lap count |
| --- | --- | ---: | --- | ---: |
| bahrain_2021 | SOFT | 24 / 429 | 0.081 / 0.083 / 0.165 | 61 |
| bahrain_2021 | MEDIUM | 21 / 429 | 0.061 / 0.087 / 0.117 | 376 |
| bahrain_2021 | HARD | 30 / 429 | 0.040 / 0.069 / 0.108 | 313 |
| spain_2022 | SOFT | 10 / 542 | 0.077 / 0.107 / 0.191 | 483 |
| spain_2022 | MEDIUM | 30 / 542 | 0.070 / 0.110 / 0.155 | 442 |
| spain_2022 | HARD | 287 / 542 | 0.037 / 0.040 / 0.080 | 30 |
| france_2022 | SOFT | 429 / 429 | 0.120 / 0.120 / 0.120 | 0 |
| france_2022 | MEDIUM | 10 / 429 | 0.060 / 0.076 / 0.111 | 276 |
| france_2022 | HARD | 20 / 429 | 0.024 / 0.047 / 0.068 | 444 |
