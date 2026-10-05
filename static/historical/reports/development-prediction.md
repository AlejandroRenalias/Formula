# Frozen development interval calibration

Selected persistent offset multiplier **3**, per-lap noise multiplier **1** from 169 candidates.
Objective: 0.274505 → 0.020538; mean horizon width: 7.776 → 18.881 s.

**Grid boundary selection: per-lap multiplier 1.0 is on the lower edge.** The grid was not extended.

[Predeclared protocol](PROTOCOL.md). [All candidates](selection.json). [Machine-readable metrics](metrics.json).

4704 matched conditional green predictions from 1365 eligible snapshots; 338.6 s offline runtime. All 1400 original snapshots were inspected; only actual green horizons enter calibration. France has no green finish outcomes: finish race pooling has two races.

Entries are before → after. Counts are ordinary integer counts; equal-race rates are weighted. 80% interval score is width plus ten times each outside-interval distance (lower is better). These are in-sample development results after selection, not held-out calibration. Mean-model coefficients and neutralisation probabilities are unchanged; larger draws can move sample medians and traffic interactions.

Parity: 968671 baseline trace laps, 24684 corner/interior trace laps, and all 4704 selected predictions agreed with ordinary engine simulation within 1e-9 s.

Coverage gains come with wider intervals. Equal-race interval score improves at
finish but worsens slightly at 1, 5 and 10 laps. Stop-containing 1-lap coverage
remains only 10.7%; aggregate calibration does not solve the pit-transition
error. Spain SOFT remains a mean-model limitation. Finish coverage is still
73.8%, and France contributes no green finish outcomes. No held-out or wet
races were evaluated.

## bahrain_2021

| Horizon | Pit group | N | Coverage | Width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 428 | 66.4% → 78.3% | 1.015 → 1.742 | 59 → 40 | 85 → 53 | 2.493 → 2.640 |
| 1 | without_stop | 408 | 69.1% → 80.9% | 1.024 → 1.759 | 59 → 40 | 67 → 38 | 2.198 → 2.416 |
| 1 | with_stop | 20 | 10.0% → 25.0% | 0.831 → 1.394 | 0 → 0 | 18 → 15 | 8.512 → 7.214 |
| 5 | all | 428 | 56.8% → 79.4% | 3.495 → 7.916 | 81 → 30 | 104 → 58 | 11.041 → 12.148 |
| 5 | without_stop | 325 | 58.5% → 82.5% | 3.524 → 8.166 | 66 → 23 | 69 → 34 | 9.553 → 10.930 |
| 5 | with_stop | 103 | 51.5% → 69.9% | 3.405 → 7.127 | 15 → 7 | 35 → 24 | 15.737 → 15.991 |
| 10 | all | 378 | 55.8% → 80.7% | 6.741 → 16.664 | 95 → 35 | 72 → 38 | 20.821 → 22.723 |
| 10 | without_stop | 203 | 55.2% → 82.8% | 7.055 → 17.432 | 58 → 21 | 33 → 14 | 18.976 → 21.397 |
| 10 | with_stop | 175 | 56.6% → 78.3% | 6.376 → 15.773 | 37 → 14 | 39 → 24 | 22.962 → 24.260 |
| finish | all | 428 | 37.9% → 77.3% | 17.158 → 43.541 | 161 → 38 | 105 → 59 | 69.572 → 59.317 |
| finish | without_stop | 157 | 43.3% → 73.2% | 8.686 → 20.225 | 21 → 4 | 68 → 38 | 29.953 → 29.005 |
| finish | with_stop | 271 | 34.7% → 79.7% | 22.066 → 57.048 | 140 → 34 | 37 → 21 | 92.524 → 76.878 |

## spain_2022

| Horizon | Pit group | N | Coverage | Width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 542 | 63.1% → 79.3% | 1.182 → 1.997 | 54 → 20 | 146 → 92 | 3.578 → 3.708 |
| 1 | without_stop | 514 | 66.5% → 83.3% | 1.188 → 2.009 | 54 → 20 | 118 → 66 | 2.875 → 3.129 |
| 1 | with_stop | 28 | 0.0% → 7.1% | 1.077 → 1.767 | 0 → 0 | 28 → 26 | 16.493 → 14.333 |
| 5 | all | 540 | 48.3% → 73.0% | 4.120 → 8.905 | 60 → 19 | 219 → 127 | 15.926 → 15.412 |
| 5 | without_stop | 400 | 52.2% → 79.2% | 4.215 → 9.276 | 55 → 19 | 136 → 64 | 13.636 → 13.184 |
| 5 | with_stop | 140 | 37.1% → 55.0% | 3.850 → 7.844 | 5 → 0 | 83 → 63 | 22.466 → 21.776 |
| 10 | all | 490 | 50.0% → 77.1% | 7.559 → 17.768 | 42 → 11 | 203 → 101 | 27.497 → 25.991 |
| 10 | without_stop | 234 | 50.9% → 81.2% | 8.218 → 19.802 | 31 → 10 | 84 → 34 | 26.697 → 24.764 |
| 10 | with_stop | 256 | 49.2% → 73.4% | 6.956 → 15.909 | 11 → 1 | 119 → 67 | 28.227 → 27.112 |
| finish | all | 542 | 38.0% → 70.3% | 21.983 → 54.341 | 42 → 1 | 294 → 160 | 102.978 → 92.253 |
| finish | without_stop | 127 | 40.2% → 67.7% | 10.657 → 24.949 | 6 → 0 | 70 → 41 | 57.734 → 48.535 |
| finish | with_stop | 415 | 37.3% → 71.1% | 25.449 → 63.336 | 36 → 1 | 224 → 119 | 116.824 → 105.632 |

## france_2022

| Horizon | Pit group | N | Coverage | Width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 395 | 66.6% → 83.8% | 0.938 → 1.562 | 64 → 23 | 68 → 41 | 2.057 → 2.195 |
| 1 | without_stop | 393 | 66.9% → 84.2% | 0.934 → 1.561 | 63 → 22 | 67 → 40 | 1.862 → 1.999 |
| 1 | with_stop | 2 | 0.0% → 0.0% | 1.652 → 1.694 | 1 → 1 | 1 → 1 | 40.390 → 40.763 |
| 5 | all | 316 | 58.2% → 83.2% | 3.321 → 7.336 | 64 → 20 | 68 → 33 | 9.464 → 9.582 |
| 5 | without_stop | 309 | 58.9% → 84.5% | 3.327 → 7.375 | 64 → 20 | 63 → 28 | 8.262 → 8.478 |
| 5 | with_stop | 7 | 28.6% → 28.6% | 3.065 → 5.593 | 0 → 0 | 5 → 5 | 62.522 → 58.309 |
| 10 | all | 217 | 51.6% → 82.5% | 6.226 → 15.854 | 50 → 17 | 55 → 21 | 20.526 → 20.411 |
| 10 | without_stop | 208 | 53.8% → 85.6% | 6.277 → 16.075 | 50 → 17 | 46 → 13 | 18.162 → 18.972 |
| 10 | with_stop | 9 | 0.0% → 11.1% | 5.036 → 10.742 | 0 → 0 | 9 → 8 | 75.176 → 53.655 |

## pooled_prediction

| Horizon | Pit group | N | Coverage | Width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 1365 | 65.1% → 80.3% | 1.059 → 1.791 | 177 → 83 | 299 → 186 | 2.798 → 2.935 |
| 1 | without_stop | 1315 | 67.5% → 82.8% | 1.061 → 1.798 | 176 → 82 | 252 → 144 | 2.362 → 2.570 |
| 1 | with_stop | 50 | 4.0% → 14.0% | 1.002 → 1.615 | 1 → 1 | 47 → 42 | 14.257 → 12.543 |
| 5 | all | 1284 | 53.6% → 77.6% | 3.715 → 8.189 | 205 → 69 | 391 → 218 | 12.707 → 12.889 |
| 5 | without_stop | 1034 | 56.2% → 81.8% | 3.732 → 8.359 | 185 → 62 | 268 → 126 | 10.747 → 11.069 |
| 5 | with_stop | 250 | 42.8% → 60.4% | 3.645 → 7.485 | 20 → 7 | 123 → 92 | 20.815 → 20.416 |
| 10 | all | 1085 | 52.4% → 79.4% | 7.007 → 17.001 | 187 → 63 | 330 → 160 | 23.777 → 23.736 |
| 10 | without_stop | 645 | 53.2% → 83.1% | 7.226 → 17.854 | 139 → 48 | 163 → 61 | 21.515 → 21.837 |
| 10 | with_stop | 440 | 51.1% → 74.1% | 6.686 → 15.749 | 48 → 15 | 167 → 99 | 27.093 → 26.521 |
| finish | all | 970 | 37.9% → 73.4% | 19.854 → 49.575 | 203 → 39 | 399 → 219 | 88.238 → 77.720 |
| finish | without_stop | 284 | 41.9% → 70.8% | 9.567 → 22.337 | 27 → 4 | 138 → 79 | 42.376 → 37.739 |
| finish | with_stop | 686 | 36.3% → 74.5% | 24.113 → 60.852 | 176 → 35 | 261 → 140 | 107.224 → 94.273 |

## pooled_equal_race

| Horizon | Pit group | N | Coverage | Width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 1365 | 65.3% → 80.5% | 1.045 → 1.767 | 177 → 83 | 299 → 186 | 2.709 → 2.848 |
| 1 | without_stop | 1315 | 67.5% → 82.8% | 1.049 → 1.777 | 176 → 82 | 252 → 144 | 2.311 → 2.515 |
| 1 | with_stop | 50 | 3.3% → 10.7% | 1.187 → 1.618 | 1 → 1 | 47 → 42 | 21.798 → 20.770 |
| 5 | all | 1284 | 54.4% → 78.5% | 3.645 → 8.052 | 205 → 69 | 391 → 218 | 12.143 → 12.380 |
| 5 | without_stop | 1034 | 56.5% → 82.1% | 3.688 → 8.273 | 185 → 62 | 268 → 126 | 10.484 → 10.864 |
| 5 | with_stop | 250 | 39.1% → 51.2% | 3.440 → 6.855 | 20 → 7 | 123 → 92 | 33.575 → 32.025 |
| 10 | all | 1085 | 52.5% → 80.1% | 6.842 → 16.762 | 187 → 63 | 330 → 160 | 22.948 → 23.041 |
| 10 | without_stop | 645 | 53.3% → 83.2% | 7.183 → 17.770 | 139 → 48 | 163 → 61 | 21.278 → 21.711 |
| 10 | with_stop | 440 | 35.3% → 54.3% | 6.123 → 14.141 | 48 → 15 | 167 → 99 | 42.122 → 35.009 |
| finish | all | 970 | 37.9% → 73.8% | 19.571 → 48.941 | 203 → 39 | 399 → 219 | 86.275 → 75.785 |
| finish | without_stop | 284 | 41.7% → 70.5% | 9.672 → 22.587 | 27 → 4 | 138 → 79 | 43.844 → 38.770 |
| finish | with_stop | 686 | 36.0% → 75.4% | 23.758 → 60.192 | 176 → 35 | 261 → 140 | 104.674 → 91.255 |

| Horizon | Pit group | Equal-race below p10 rate | Equal-race above p90 rate |
| --- | --- | --- | --- |
| 1 | all | 13.3% → 6.3% | 21.3% → 13.2% |
| 1 | without_stop | 13.7% → 6.4% | 18.8% → 10.8% |
| 1 | with_stop | 16.7% → 16.7% | 80.0% → 72.6% |
| 5 | all | 16.8% → 5.6% | 28.8% → 15.8% |
| 5 | without_stop | 18.3% → 6.1% | 25.2% → 11.8% |
| 5 | with_stop | 6.0% → 2.3% | 54.9% → 46.6% |
| 10 | all | 18.9% → 6.4% | 28.6% → 13.4% |
| 10 | without_stop | 22.0% → 7.6% | 24.8% → 9.2% |
| 10 | with_stop | 8.5% → 2.8% | 56.3% → 42.9% |
| finish | all | 22.7% → 4.5% | 39.4% → 21.7% |
| finish | without_stop | 9.1% → 1.3% | 49.2% → 28.2% |
| finish | with_stop | 30.2% → 6.4% | 33.8% → 18.2% |
