# Full and green-only development evaluation

[Matched stage comparisons](COMPARISONS.md). Stages: previous pit split, ongoing event duration, future neutralization risk. All three approved development races; no new simulations. Signed error is predicted median minus actual. Green-only means GREEN at the cutoff and no actual SC/VSC (status 4/6/7) in (cutoff,target]. Outcome status filters are computed only after predictions and never enter engine state or parameters. Pit and no-pit horizons both remain eligible.

Prediction pooling weights each row equally. Race pooling gives each available race equal total weight, then each prediction within that race equal weight. Pit strata are independently normalized within available races. Medians are weighted medians of individual errors, not averages of race medians. Below/above counts are ordinary integer counts in both tables; the extra rate table contains balanced miss rates. Missing race/horizon cells receive no weight. France has no green-only finish horizons, so green-only finish pooling has two races.

# pit_split: full

## bahrain_2021

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

## spain_2022

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

## france_2022

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

## pooled_prediction

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

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1400 | 1.024 | -0.102 | -0.092 | -0.102 | -0.092 | 1.024 | 62.3% | 1.040 | 222 | 305 | 8.244 |
| 1 | without_stop | 1341 | 0.673 | -0.130 | -0.113 | -0.130 | -0.113 | 0.673 | 65.0% | 1.028 | 174 | 294 | 4.869 |
| 1 | with_stop | 59 | 10.978 | -2.798 | +5.401 | -2.798 | +5.401 | 10.978 | 0.0% | 1.301 | 48 | 11 | 104.639 |
| 5 | all | 1398 | 9.138 | -2.198 | -0.925 | -0.440 | -0.185 | 1.828 | 43.2% | 3.372 | 241 | 556 | 82.885 |
| 5 | without_stop | 1100 | 6.430 | +1.176 | -0.635 | +0.235 | -0.127 | 1.286 | 48.7% | 3.411 | 190 | 377 | 56.181 |
| 5 | with_stop | 298 | 26.597 | -24.916 | -3.350 | -4.983 | -0.670 | 5.319 | 18.6% | 3.172 | 51 | 179 | 255.948 |
| 10 | all | 1248 | 20.125 | -3.855 | -1.921 | -0.386 | -0.192 | 2.012 | 39.2% | 5.906 | 205 | 553 | 186.526 |
| 10 | without_stop | 707 | 15.363 | +7.201 | -1.116 | +0.720 | -0.112 | 1.536 | 43.3% | 6.188 | 156 | 246 | 137.944 |
| 10 | with_stop | 541 | 31.950 | -30.523 | -5.191 | -3.052 | -0.519 | 3.195 | 28.7% | 5.537 | 49 | 307 | 305.257 |
| finish | all | 1400 | 51.947 | -2.998 | -12.511 | -0.396 | -0.608 | 1.829 | 29.1% | 16.684 | 126 | 855 | 470.941 |
| finish | without_stop | 563 | 47.367 | +15.729 | -9.902 | -0.263 | -0.858 | 2.155 | 22.6% | 8.899 | 29 | 438 | 441.791 |
| finish | with_stop | 837 | 55.980 | -37.571 | -14.112 | -0.933 | -0.461 | 1.452 | 32.5% | 21.719 | 97 | 417 | 498.884 |

| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | ---: | ---: | ---: |
| 1 | all | 3 | 16.1% | 21.6% |
| 1 | without_stop | 3 | 13.3% | 21.7% |
| 1 | with_stop | 3 | 66.7% | 33.3% |
| 5 | all | 3 | 17.3% | 39.5% |
| 5 | without_stop | 3 | 17.3% | 34.0% |
| 5 | with_stop | 3 | 14.1% | 67.3% |
| 10 | all | 3 | 16.7% | 44.1% |
| 10 | without_stop | 3 | 22.1% | 34.6% |
| 10 | with_stop | 3 | 8.4% | 63.0% |
| finish | all | 3 | 8.9% | 62.1% |
| finish | without_stop | 3 | 5.6% | 71.9% |
| finish | with_stop | 3 | 9.9% | 57.7% |

# pit_split: green_only

## bahrain_2021

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 428 | 0.710 | +0.261 | -0.087 | +0.261 | -0.087 | 0.710 | 61.2% | 1.021 | 78 | 88 | 5.218 |
| 1 | without_stop | 408 | 0.403 | -0.068 | -0.104 | -0.068 | -0.104 | 0.403 | 64.2% | 1.005 | 58 | 88 | 2.329 |
| 1 | with_stop | 20 | 6.968 | +6.968 | +7.063 | +6.968 | +7.063 | 6.968 | 0.0% | 1.348 | 20 | 0 | 64.145 |
| 5 | all | 428 | 2.300 | -0.599 | -0.736 | -0.120 | -0.147 | 0.460 | 46.5% | 3.261 | 75 | 154 | 15.126 |
| 5 | without_stop | 325 | 1.845 | -0.486 | -0.507 | -0.097 | -0.101 | 0.369 | 52.6% | 3.239 | 52 | 102 | 11.268 |
| 5 | with_stop | 103 | 3.736 | -0.954 | -1.771 | -0.191 | -0.354 | 0.747 | 27.2% | 3.331 | 23 | 52 | 27.299 |
| 10 | all | 378 | 3.797 | -0.953 | -0.528 | -0.095 | -0.053 | 0.380 | 45.8% | 5.939 | 80 | 125 | 25.015 |
| 10 | without_stop | 203 | 3.620 | -0.566 | -0.526 | -0.057 | -0.053 | 0.362 | 47.8% | 6.042 | 47 | 59 | 22.782 |
| 10 | with_stop | 175 | 4.002 | -1.402 | -0.577 | -0.140 | -0.058 | 0.400 | 43.4% | 5.819 | 33 | 66 | 27.606 |
| finish | all | 428 | 8.529 | -1.451 | -2.143 | -0.186 | -0.083 | 0.386 | 47.7% | 15.783 | 57 | 167 | 51.834 |
| finish | without_stop | 157 | 6.328 | -4.576 | -5.048 | -0.449 | -0.497 | 0.541 | 32.5% | 7.303 | 12 | 94 | 41.885 |
| finish | with_stop | 271 | 9.804 | +0.358 | +0.664 | -0.033 | +0.014 | 0.296 | 56.5% | 20.696 | 45 | 73 | 57.597 |

## spain_2022

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

## france_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 395 | 0.406 | -0.116 | -0.056 | -0.116 | -0.056 | 0.406 | 67.3% | 0.929 | 60 | 69 | 2.460 |
| 1 | without_stop | 393 | 0.341 | -0.050 | -0.055 | -0.050 | -0.055 | 0.341 | 67.7% | 0.928 | 60 | 67 | 1.830 |
| 1 | with_stop | 2 | 13.052 | -13.052 | -13.052 | -13.052 | -13.052 | 13.052 | 0.0% | 1.060 | 0 | 2 | 126.316 |
| 5 | all | 316 | 1.627 | -0.332 | -0.149 | -0.066 | -0.030 | 0.325 | 55.7% | 3.090 | 65 | 75 | 10.222 |
| 5 | without_stop | 309 | 1.375 | -0.051 | -0.074 | -0.010 | -0.015 | 0.275 | 57.0% | 3.093 | 65 | 68 | 7.766 |
| 5 | with_stop | 7 | 12.730 | -12.730 | -13.770 | -2.546 | -2.754 | 2.546 | 0.0% | 2.955 | 0 | 7 | 118.627 |
| 10 | all | 217 | 3.121 | -0.667 | -0.528 | -0.067 | -0.053 | 0.312 | 54.8% | 5.597 | 43 | 55 | 20.229 |
| 10 | without_stop | 208 | 2.608 | -0.048 | -0.372 | -0.005 | -0.037 | 0.261 | 57.2% | 5.637 | 43 | 46 | 15.332 |
| 10 | with_stop | 9 | 14.980 | -14.980 | -15.186 | -1.498 | -1.519 | 1.498 | 0.0% | 4.661 | 0 | 9 | 133.396 |

Finish: N=0, unavailable; every scored finish horizon contains an actual future neutralization.

## pooled_prediction

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.650 | +0.068 | -0.091 | +0.068 | -0.091 | 0.650 | 63.6% | 1.059 | 211 | 286 | 4.492 |
| 1 | without_stop | 1315 | 0.436 | -0.129 | -0.114 | -0.129 | -0.114 | 0.436 | 66.0% | 1.046 | 163 | 284 | 2.486 |
| 1 | with_stop | 50 | 6.279 | +5.234 | +5.921 | +5.234 | +5.921 | 6.279 | 0.0% | 1.406 | 48 | 2 | 57.244 |
| 5 | all | 1284 | 2.379 | -0.830 | -0.755 | -0.166 | -0.151 | 0.476 | 46.5% | 3.469 | 227 | 460 | 15.302 |
| 5 | without_stop | 1034 | 1.987 | -0.648 | -0.577 | -0.130 | -0.115 | 0.397 | 51.2% | 3.460 | 176 | 329 | 11.852 |
| 5 | with_stop | 250 | 3.997 | -1.585 | -1.899 | -0.317 | -0.380 | 0.799 | 27.2% | 3.508 | 51 | 131 | 29.571 |
| 10 | all | 1085 | 4.220 | -1.606 | -1.257 | -0.161 | -0.126 | 0.422 | 45.2% | 6.205 | 189 | 406 | 27.359 |
| 10 | without_stop | 645 | 3.988 | -0.963 | -0.850 | -0.096 | -0.085 | 0.399 | 47.3% | 6.340 | 140 | 200 | 24.473 |
| 10 | with_stop | 440 | 4.559 | -2.547 | -1.861 | -0.255 | -0.186 | 0.456 | 42.0% | 6.006 | 49 | 206 | 31.589 |
| finish | all | 970 | 13.096 | -6.427 | -4.163 | -0.297 | -0.186 | 0.486 | 43.2% | 18.598 | 115 | 436 | 83.620 |
| finish | without_stop | 284 | 7.930 | -6.100 | -5.512 | -0.578 | -0.556 | 0.689 | 33.8% | 8.324 | 19 | 169 | 52.972 |
| finish | with_stop | 686 | 15.235 | -6.562 | -3.203 | -0.180 | -0.098 | 0.401 | 47.1% | 22.851 | 96 | 267 | 96.308 |

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.632 | +0.065 | -0.087 | +0.065 | -0.087 | 0.632 | 63.8% | 1.044 | 211 | 286 | 4.359 |
| 1 | without_stop | 1315 | 0.426 | -0.118 | -0.112 | -0.118 | -0.112 | 0.426 | 66.0% | 1.034 | 163 | 284 | 2.424 |
| 1 | with_stop | 50 | 8.441 | -0.260 | +5.401 | -0.260 | +5.401 | 8.441 | 0.0% | 1.293 | 48 | 2 | 79.281 |
| 5 | all | 1284 | 2.269 | -0.745 | -0.650 | -0.149 | -0.130 | 0.454 | 47.8% | 3.402 | 227 | 460 | 14.588 |
| 5 | without_stop | 1034 | 1.932 | -0.592 | -0.514 | -0.118 | -0.103 | 0.386 | 51.7% | 3.418 | 176 | 329 | 11.506 |
| 5 | with_stop | 250 | 6.740 | -5.059 | -3.350 | -1.012 | -0.670 | 1.348 | 18.6% | 3.318 | 51 | 131 | 57.572 |
| 10 | all | 1085 | 3.983 | -1.382 | -0.986 | -0.138 | -0.099 | 0.398 | 47.0% | 6.072 | 189 | 406 | 25.856 |
| 10 | without_stop | 645 | 3.921 | -0.912 | -0.811 | -0.091 | -0.081 | 0.392 | 47.7% | 6.301 | 140 | 200 | 24.060 |
| 10 | with_stop | 440 | 7.852 | -6.425 | -5.191 | -0.643 | -0.519 | 0.785 | 28.7% | 5.554 | 49 | 206 | 63.912 |
| finish | all | 970 | 12.616 | -5.904 | -4.024 | -0.285 | -0.168 | 0.475 | 43.7% | 18.302 | 115 | 436 | 80.277 |
| finish | without_stop | 284 | 8.119 | -6.280 | -5.552 | -0.594 | -0.570 | 0.707 | 34.0% | 8.444 | 19 | 169 | 54.281 |
| finish | with_stop | 686 | 14.292 | -5.362 | -2.544 | -0.154 | -0.078 | 0.383 | 48.7% | 22.477 | 96 | 267 | 89.592 |

| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | ---: | ---: | ---: |
| 1 | all | 3 | 15.6% | 20.6% |
| 1 | without_stop | 3 | 12.7% | 21.2% |
| 1 | with_stop | 3 | 66.7% | 33.3% |
| 5 | all | 3 | 18.1% | 34.2% |
| 5 | without_stop | 3 | 17.3% | 31.0% |
| 5 | with_stop | 3 | 14.1% | 67.3% |
| 10 | all | 3 | 18.1% | 34.8% |
| 10 | without_stop | 3 | 21.7% | 30.6% |
| 10 | with_stop | 3 | 8.4% | 63.0% |
| finish | all | 2 | 12.0% | 44.3% |
| finish | without_stop | 2 | 6.6% | 59.5% |
| finish | with_stop | 2 | 14.4% | 36.8% |

# ongoing: full

## bahrain_2021

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

## spain_2022

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

## france_2022

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

## pooled_prediction

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

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1400 | 1.024 | -0.102 | -0.092 | -0.102 | -0.092 | 1.024 | 62.3% | 1.040 | 222 | 305 | 8.244 |
| 1 | without_stop | 1341 | 0.673 | -0.130 | -0.113 | -0.130 | -0.113 | 0.673 | 65.0% | 1.028 | 174 | 294 | 4.869 |
| 1 | with_stop | 59 | 10.978 | -2.798 | +5.401 | -2.798 | +5.401 | 10.978 | 0.0% | 1.301 | 48 | 11 | 104.639 |
| 5 | all | 1398 | 7.814 | -3.522 | -0.925 | -0.704 | -0.185 | 1.563 | 43.2% | 3.378 | 241 | 556 | 69.618 |
| 5 | without_stop | 1100 | 4.911 | -0.343 | -0.635 | -0.069 | -0.127 | 0.982 | 48.7% | 3.417 | 190 | 377 | 40.963 |
| 5 | with_stop | 298 | 26.597 | -24.916 | -3.350 | -4.983 | -0.670 | 5.319 | 18.6% | 3.172 | 51 | 179 | 255.948 |
| 10 | all | 1248 | 14.776 | -9.204 | -1.921 | -0.920 | -0.192 | 1.478 | 39.2% | 5.926 | 205 | 553 | 132.948 |
| 10 | without_stop | 707 | 7.826 | -0.336 | -1.116 | -0.034 | -0.112 | 0.783 | 43.3% | 6.216 | 156 | 246 | 62.457 |
| 10 | with_stop | 541 | 31.950 | -30.523 | -5.191 | -3.052 | -0.519 | 3.195 | 28.7% | 5.537 | 49 | 307 | 305.257 |
| finish | all | 1400 | 30.887 | -24.058 | -12.511 | -1.015 | -0.608 | 1.211 | 29.1% | 16.745 | 126 | 855 | 260.102 |
| finish | without_stop | 563 | 18.042 | -13.596 | -9.902 | -1.124 | -0.858 | 1.294 | 22.6% | 8.988 | 29 | 438 | 148.200 |
| finish | with_stop | 837 | 50.137 | -43.413 | -14.112 | -1.105 | -0.461 | 1.280 | 32.5% | 21.729 | 97 | 417 | 440.396 |

| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | ---: | ---: | ---: |
| 1 | all | 3 | 16.1% | 21.6% |
| 1 | without_stop | 3 | 13.3% | 21.7% |
| 1 | with_stop | 3 | 66.7% | 33.3% |
| 5 | all | 3 | 17.3% | 39.5% |
| 5 | without_stop | 3 | 17.3% | 34.0% |
| 5 | with_stop | 3 | 14.1% | 67.3% |
| 10 | all | 3 | 16.7% | 44.1% |
| 10 | without_stop | 3 | 22.1% | 34.6% |
| 10 | with_stop | 3 | 8.4% | 63.0% |
| finish | all | 3 | 8.9% | 62.1% |
| finish | without_stop | 3 | 5.6% | 71.9% |
| finish | with_stop | 3 | 9.9% | 57.7% |

# ongoing: green_only

## bahrain_2021

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 428 | 0.710 | +0.261 | -0.087 | +0.261 | -0.087 | 0.710 | 61.2% | 1.021 | 78 | 88 | 5.218 |
| 1 | without_stop | 408 | 0.403 | -0.068 | -0.104 | -0.068 | -0.104 | 0.403 | 64.2% | 1.005 | 58 | 88 | 2.329 |
| 1 | with_stop | 20 | 6.968 | +6.968 | +7.063 | +6.968 | +7.063 | 6.968 | 0.0% | 1.348 | 20 | 0 | 64.145 |
| 5 | all | 428 | 2.300 | -0.599 | -0.736 | -0.120 | -0.147 | 0.460 | 46.5% | 3.261 | 75 | 154 | 15.126 |
| 5 | without_stop | 325 | 1.845 | -0.486 | -0.507 | -0.097 | -0.101 | 0.369 | 52.6% | 3.239 | 52 | 102 | 11.268 |
| 5 | with_stop | 103 | 3.736 | -0.954 | -1.771 | -0.191 | -0.354 | 0.747 | 27.2% | 3.331 | 23 | 52 | 27.299 |
| 10 | all | 378 | 3.797 | -0.953 | -0.528 | -0.095 | -0.053 | 0.380 | 45.8% | 5.939 | 80 | 125 | 25.015 |
| 10 | without_stop | 203 | 3.620 | -0.566 | -0.526 | -0.057 | -0.053 | 0.362 | 47.8% | 6.042 | 47 | 59 | 22.782 |
| 10 | with_stop | 175 | 4.002 | -1.402 | -0.577 | -0.140 | -0.058 | 0.400 | 43.4% | 5.819 | 33 | 66 | 27.606 |
| finish | all | 428 | 8.529 | -1.451 | -2.143 | -0.186 | -0.083 | 0.386 | 47.7% | 15.783 | 57 | 167 | 51.834 |
| finish | without_stop | 157 | 6.328 | -4.576 | -5.048 | -0.449 | -0.497 | 0.541 | 32.5% | 7.303 | 12 | 94 | 41.885 |
| finish | with_stop | 271 | 9.804 | +0.358 | +0.664 | -0.033 | +0.014 | 0.296 | 56.5% | 20.696 | 45 | 73 | 57.597 |

## spain_2022

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

## france_2022

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 395 | 0.406 | -0.116 | -0.056 | -0.116 | -0.056 | 0.406 | 67.3% | 0.929 | 60 | 69 | 2.460 |
| 1 | without_stop | 393 | 0.341 | -0.050 | -0.055 | -0.050 | -0.055 | 0.341 | 67.7% | 0.928 | 60 | 67 | 1.830 |
| 1 | with_stop | 2 | 13.052 | -13.052 | -13.052 | -13.052 | -13.052 | 13.052 | 0.0% | 1.060 | 0 | 2 | 126.316 |
| 5 | all | 316 | 1.627 | -0.332 | -0.149 | -0.066 | -0.030 | 0.325 | 55.7% | 3.090 | 65 | 75 | 10.222 |
| 5 | without_stop | 309 | 1.375 | -0.051 | -0.074 | -0.010 | -0.015 | 0.275 | 57.0% | 3.093 | 65 | 68 | 7.766 |
| 5 | with_stop | 7 | 12.730 | -12.730 | -13.770 | -2.546 | -2.754 | 2.546 | 0.0% | 2.955 | 0 | 7 | 118.627 |
| 10 | all | 217 | 3.121 | -0.667 | -0.528 | -0.067 | -0.053 | 0.312 | 54.8% | 5.597 | 43 | 55 | 20.229 |
| 10 | without_stop | 208 | 2.608 | -0.048 | -0.372 | -0.005 | -0.037 | 0.261 | 57.2% | 5.637 | 43 | 46 | 15.332 |
| 10 | with_stop | 9 | 14.980 | -14.980 | -15.186 | -1.498 | -1.519 | 1.498 | 0.0% | 4.661 | 0 | 9 | 133.396 |

Finish: N=0, unavailable; every scored finish horizon contains an actual future neutralization.

## pooled_prediction

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.650 | +0.068 | -0.091 | +0.068 | -0.091 | 0.650 | 63.6% | 1.059 | 211 | 286 | 4.492 |
| 1 | without_stop | 1315 | 0.436 | -0.129 | -0.114 | -0.129 | -0.114 | 0.436 | 66.0% | 1.046 | 163 | 284 | 2.486 |
| 1 | with_stop | 50 | 6.279 | +5.234 | +5.921 | +5.234 | +5.921 | 6.279 | 0.0% | 1.406 | 48 | 2 | 57.244 |
| 5 | all | 1284 | 2.379 | -0.830 | -0.755 | -0.166 | -0.151 | 0.476 | 46.5% | 3.469 | 227 | 460 | 15.302 |
| 5 | without_stop | 1034 | 1.987 | -0.648 | -0.577 | -0.130 | -0.115 | 0.397 | 51.2% | 3.460 | 176 | 329 | 11.852 |
| 5 | with_stop | 250 | 3.997 | -1.585 | -1.899 | -0.317 | -0.380 | 0.799 | 27.2% | 3.508 | 51 | 131 | 29.571 |
| 10 | all | 1085 | 4.220 | -1.606 | -1.257 | -0.161 | -0.126 | 0.422 | 45.2% | 6.205 | 189 | 406 | 27.359 |
| 10 | without_stop | 645 | 3.988 | -0.963 | -0.850 | -0.096 | -0.085 | 0.399 | 47.3% | 6.340 | 140 | 200 | 24.473 |
| 10 | with_stop | 440 | 4.559 | -2.547 | -1.861 | -0.255 | -0.186 | 0.456 | 42.0% | 6.006 | 49 | 206 | 31.589 |
| finish | all | 970 | 13.096 | -6.427 | -4.163 | -0.297 | -0.186 | 0.486 | 43.2% | 18.598 | 115 | 436 | 83.620 |
| finish | without_stop | 284 | 7.930 | -6.100 | -5.512 | -0.578 | -0.556 | 0.689 | 33.8% | 8.324 | 19 | 169 | 52.972 |
| finish | with_stop | 686 | 15.235 | -6.562 | -3.203 | -0.180 | -0.098 | 0.401 | 47.1% | 22.851 | 96 | 267 | 96.308 |

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.632 | +0.065 | -0.087 | +0.065 | -0.087 | 0.632 | 63.8% | 1.044 | 211 | 286 | 4.359 |
| 1 | without_stop | 1315 | 0.426 | -0.118 | -0.112 | -0.118 | -0.112 | 0.426 | 66.0% | 1.034 | 163 | 284 | 2.424 |
| 1 | with_stop | 50 | 8.441 | -0.260 | +5.401 | -0.260 | +5.401 | 8.441 | 0.0% | 1.293 | 48 | 2 | 79.281 |
| 5 | all | 1284 | 2.269 | -0.745 | -0.650 | -0.149 | -0.130 | 0.454 | 47.8% | 3.402 | 227 | 460 | 14.588 |
| 5 | without_stop | 1034 | 1.932 | -0.592 | -0.514 | -0.118 | -0.103 | 0.386 | 51.7% | 3.418 | 176 | 329 | 11.506 |
| 5 | with_stop | 250 | 6.740 | -5.059 | -3.350 | -1.012 | -0.670 | 1.348 | 18.6% | 3.318 | 51 | 131 | 57.572 |
| 10 | all | 1085 | 3.983 | -1.382 | -0.986 | -0.138 | -0.099 | 0.398 | 47.0% | 6.072 | 189 | 406 | 25.856 |
| 10 | without_stop | 645 | 3.921 | -0.912 | -0.811 | -0.091 | -0.081 | 0.392 | 47.7% | 6.301 | 140 | 200 | 24.060 |
| 10 | with_stop | 440 | 7.852 | -6.425 | -5.191 | -0.643 | -0.519 | 0.785 | 28.7% | 5.554 | 49 | 206 | 63.912 |
| finish | all | 970 | 12.616 | -5.904 | -4.024 | -0.285 | -0.168 | 0.475 | 43.7% | 18.302 | 115 | 436 | 80.277 |
| finish | without_stop | 284 | 8.119 | -6.280 | -5.552 | -0.594 | -0.570 | 0.707 | 34.0% | 8.444 | 19 | 169 | 54.281 |
| finish | with_stop | 686 | 14.292 | -5.362 | -2.544 | -0.154 | -0.078 | 0.383 | 48.7% | 22.477 | 96 | 267 | 89.592 |

| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | ---: | ---: | ---: |
| 1 | all | 3 | 15.6% | 20.6% |
| 1 | without_stop | 3 | 12.7% | 21.2% |
| 1 | with_stop | 3 | 66.7% | 33.3% |
| 5 | all | 3 | 18.1% | 34.2% |
| 5 | without_stop | 3 | 17.3% | 31.0% |
| 5 | with_stop | 3 | 14.1% | 67.3% |
| 10 | all | 3 | 18.1% | 34.8% |
| 10 | without_stop | 3 | 21.7% | 30.6% |
| 10 | with_stop | 3 | 8.4% | 63.0% |
| finish | all | 2 | 12.0% | 44.3% |
| finish | without_stop | 2 | 6.6% | 59.5% |
| finish | with_stop | 2 | 14.4% | 36.8% |

# future: full

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

| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | ---: | ---: | ---: |
| 1 | all | 3 | 15.4% | 22.3% |
| 1 | without_stop | 3 | 12.6% | 22.4% |
| 1 | with_stop | 3 | 66.7% | 33.3% |
| 5 | all | 3 | 18.2% | 34.4% |
| 5 | without_stop | 3 | 18.1% | 29.2% |
| 5 | with_stop | 3 | 14.8% | 62.2% |
| 10 | all | 3 | 17.5% | 9.4% |
| 10 | without_stop | 3 | 22.5% | 2.0% |
| 10 | with_stop | 3 | 9.4% | 27.6% |
| finish | all | 3 | 12.8% | 9.1% |
| finish | without_stop | 3 | 5.9% | 21.4% |
| finish | with_stop | 3 | 15.4% | 0.6% |

# future: green_only

## bahrain_2021

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 428 | 0.710 | +0.261 | -0.087 | +0.261 | -0.087 | 0.710 | 61.2% | 1.021 | 78 | 88 | 5.218 |
| 1 | without_stop | 408 | 0.403 | -0.068 | -0.104 | -0.068 | -0.104 | 0.403 | 64.2% | 1.005 | 58 | 88 | 2.329 |
| 1 | with_stop | 20 | 6.968 | +6.968 | +7.063 | +6.968 | +7.063 | 6.968 | 0.0% | 1.348 | 20 | 0 | 64.145 |
| 5 | all | 428 | 2.269 | -0.405 | -0.590 | -0.081 | -0.118 | 0.454 | 49.8% | 3.714 | 81 | 134 | 14.374 |
| 5 | without_stop | 325 | 1.830 | -0.294 | -0.210 | -0.059 | -0.042 | 0.366 | 55.4% | 3.691 | 56 | 89 | 10.824 |
| 5 | with_stop | 103 | 3.655 | -0.755 | -1.627 | -0.151 | -0.325 | 0.731 | 32.0% | 3.786 | 25 | 45 | 25.577 |
| 10 | all | 378 | 3.821 | -0.238 | +0.140 | -0.024 | +0.014 | 0.382 | 78.3% | 35.288 | 82 | 0 | 41.539 |
| 10 | without_stop | 203 | 3.644 | +0.140 | +0.208 | +0.014 | +0.021 | 0.364 | 76.8% | 35.413 | 47 | 0 | 42.570 |
| 10 | with_stop | 175 | 4.027 | -0.677 | +0.106 | -0.068 | +0.011 | 0.403 | 80.0% | 35.143 | 35 | 0 | 40.343 |
| finish | all | 428 | 12.719 | +7.149 | +2.980 | +0.054 | +0.108 | 0.476 | 71.5% | 139.382 | 81 | 41 | 156.982 |
| finish | without_stop | 157 | 5.981 | -3.339 | -4.140 | -0.370 | -0.412 | 0.505 | 68.8% | 68.716 | 13 | 36 | 79.595 |
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
| 1 | all | 395 | 0.406 | -0.116 | -0.056 | -0.116 | -0.056 | 0.406 | 67.3% | 0.929 | 60 | 69 | 2.460 |
| 1 | without_stop | 393 | 0.341 | -0.050 | -0.055 | -0.050 | -0.055 | 0.341 | 67.7% | 0.928 | 60 | 67 | 1.830 |
| 1 | with_stop | 2 | 13.052 | -13.052 | -13.052 | -13.052 | -13.052 | 13.052 | 0.0% | 1.060 | 0 | 2 | 126.316 |
| 5 | all | 316 | 1.639 | -0.167 | -0.022 | -0.033 | -0.004 | 0.328 | 60.4% | 3.528 | 68 | 57 | 9.982 |
| 5 | without_stop | 309 | 1.392 | +0.113 | +0.058 | +0.023 | +0.012 | 0.278 | 61.8% | 3.533 | 68 | 50 | 7.622 |
| 5 | with_stop | 7 | 12.522 | -12.522 | -13.493 | -2.504 | -2.699 | 2.504 | 0.0% | 3.265 | 0 | 7 | 114.161 |
| 10 | all | 217 | 3.105 | -0.034 | +0.137 | -0.003 | +0.014 | 0.310 | 79.3% | 36.642 | 45 | 0 | 42.044 |
| 10 | without_stop | 208 | 2.622 | +0.581 | +0.416 | +0.058 | +0.042 | 0.262 | 78.4% | 36.695 | 45 | 0 | 42.330 |
| 10 | with_stop | 9 | 14.251 | -14.251 | -14.076 | -1.425 | -1.408 | 1.425 | 100.0% | 35.425 | 0 | 0 | 35.425 |

Finish: N=0, unavailable; every scored finish horizon contains an actual future neutralization.

## pooled_prediction

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.650 | +0.068 | -0.091 | +0.068 | -0.091 | 0.650 | 63.6% | 1.059 | 211 | 286 | 4.492 |
| 1 | without_stop | 1315 | 0.436 | -0.129 | -0.114 | -0.129 | -0.114 | 0.436 | 66.0% | 1.046 | 163 | 284 | 2.486 |
| 1 | with_stop | 50 | 6.279 | +5.234 | +5.921 | +5.234 | +5.921 | 6.279 | 0.0% | 1.406 | 48 | 2 | 57.244 |
| 5 | all | 1284 | 2.342 | -0.623 | -0.569 | -0.125 | -0.114 | 0.468 | 51.2% | 3.947 | 238 | 389 | 14.485 |
| 5 | without_stop | 1034 | 1.960 | -0.446 | -0.377 | -0.089 | -0.075 | 0.392 | 55.3% | 3.942 | 185 | 277 | 11.244 |
| 5 | with_stop | 250 | 3.922 | -1.354 | -1.639 | -0.271 | -0.328 | 0.784 | 34.0% | 3.966 | 53 | 112 | 27.890 |
| 10 | all | 1085 | 4.160 | -0.850 | -0.557 | -0.085 | -0.056 | 0.416 | 81.7% | 34.465 | 199 | 0 | 39.820 |
| 10 | without_stop | 645 | 3.939 | -0.229 | -0.148 | -0.023 | -0.015 | 0.394 | 77.8% | 34.964 | 143 | 0 | 41.624 |
| 10 | with_stop | 440 | 4.483 | -1.760 | -1.260 | -0.176 | -0.126 | 0.448 | 87.3% | 33.732 | 56 | 0 | 37.177 |
| finish | all | 970 | 14.556 | +3.888 | +0.651 | -0.027 | +0.024 | 0.514 | 74.9% | 158.767 | 174 | 69 | 175.152 |
| finish | without_stop | 284 | 7.156 | -4.618 | -4.227 | -0.478 | -0.434 | 0.633 | 70.1% | 61.733 | 21 | 64 | 76.088 |
| finish | with_stop | 686 | 17.620 | +7.410 | +7.301 | +0.159 | +0.231 | 0.464 | 77.0% | 198.938 | 153 | 5 | 216.163 |

## pooled_equal_race

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 1365 | 0.632 | +0.065 | -0.087 | +0.065 | -0.087 | 0.632 | 63.8% | 1.044 | 211 | 286 | 4.359 |
| 1 | without_stop | 1315 | 0.426 | -0.118 | -0.112 | -0.118 | -0.112 | 0.426 | 66.0% | 1.034 | 163 | 284 | 2.424 |
| 1 | with_stop | 50 | 8.441 | -0.260 | +5.401 | -0.260 | +5.401 | 8.441 | 0.0% | 1.293 | 48 | 2 | 79.281 |
| 5 | all | 1284 | 2.239 | -0.545 | -0.455 | -0.109 | -0.091 | 0.448 | 52.4% | 3.873 | 238 | 389 | 13.855 |
| 5 | without_stop | 1034 | 1.908 | -0.394 | -0.335 | -0.079 | -0.067 | 0.382 | 55.8% | 3.895 | 185 | 277 | 10.943 |
| 5 | with_stop | 250 | 6.622 | -4.838 | -3.106 | -0.968 | -0.621 | 1.324 | 23.1% | 3.728 | 53 | 112 | 55.005 |
| 10 | all | 1085 | 3.938 | -0.652 | -0.232 | -0.065 | -0.023 | 0.394 | 81.0% | 34.932 | 199 | 0 | 40.364 |
| 10 | without_stop | 645 | 3.877 | -0.183 | -0.122 | -0.018 | -0.012 | 0.388 | 77.8% | 35.048 | 143 | 0 | 41.692 |
| 10 | with_stop | 440 | 7.576 | -5.663 | -4.523 | -0.566 | -0.452 | 0.758 | 90.6% | 34.425 | 56 | 0 | 36.947 |
| finish | all | 970 | 14.363 | +4.231 | +0.881 | -0.019 | +0.037 | 0.510 | 74.6% | 156.728 | 174 | 69 | 173.241 |
| finish | without_stop | 284 | 7.295 | -4.769 | -4.238 | -0.491 | -0.444 | 0.648 | 70.2% | 60.908 | 21 | 64 | 75.674 |
| finish | with_stop | 686 | 17.447 | +8.419 | +8.096 | +0.184 | +0.246 | 0.463 | 76.3% | 195.708 | 153 | 5 | 213.674 |

| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | ---: | ---: | ---: |
| 1 | all | 3 | 15.6% | 20.6% |
| 1 | without_stop | 3 | 12.7% | 21.2% |
| 1 | with_stop | 3 | 66.7% | 33.3% |
| 5 | all | 3 | 19.0% | 28.7% |
| 5 | without_stop | 3 | 18.2% | 26.0% |
| 5 | with_stop | 3 | 14.8% | 62.2% |
| 10 | all | 3 | 19.0% | 0.0% |
| 10 | without_stop | 3 | 22.2% | 0.0% |
| 10 | with_stop | 3 | 9.4% | 0.0% |
| finish | all | 2 | 18.0% | 7.4% |
| finish | without_stop | 2 | 7.3% | 22.5% |
| finish | with_stop | 2 | 22.8% | 0.9% |

## Reading these results

The final full-view equal-race MAE is 0.982 / 6.788 / 13.554 / 28.688 s at
1 / 5 / 10 laps / finish; coverage is 62.3% / 47.4% / 73.1% / 78.1%.
Green-only equal-race MAE is 0.632 / 2.239 / 3.938 / 14.363 s, with coverage
63.8% / 52.4% / 81.0% / 74.6%. The finish green-only result uses two races.
Full mean error/lap is -0.291 / -0.861 / -0.960 / -0.793 s; green-only is
+0.065 / -0.109 / -0.065 / -0.019 s. The remaining full-horizon bias is
therefore substantially associated with neutralized horizons. This is an
outcome-conditioned diagnostic, not causal proof that the wear model is right.
The green view still contains pit loss, traffic, driver pace and selection
variation. No degradation fitting, interval tuning or further model changes
were made for this reporting step.
