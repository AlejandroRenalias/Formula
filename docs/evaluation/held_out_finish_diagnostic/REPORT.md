# Saved held-out green finish diagnostic: horizons containing a stop

Report only. 645 saved conditional green finish predictions; no prediction/decision replay, snapshot rebuilding, parameter changes or new races. Hash-verified saved predictions and snapshot audits. Signed error is conditional green median minus actual. Adjacent driver/cutoff rows are correlated.

## Hypothesis assessment

**Early-race pessimism is confirmed; the proposed dominant cliff mechanism is
refuted by the direct-cost accounting. Strict fallback wear contributes a
small subset, not most of the errors.** These are descriptive associations,
not a fitted causal attribution or a counterfactual replay.

| Cutoff bucket | N | Mean error s | Median error s | Future cliff cost s | Total cliff cost s |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 187 | +44.027 | +46.077 | 0.894 | 1.927 |
| 15-29 | 288 | +24.521 | +23.373 | 0.540 | 1.272 |
| 30+ | 170 | +2.580 | -2.721 | 0.517 | 1.108 |

Both races show this pattern: early/medium/late mean errors are
+45.376/+31.901/+3.287 s in Spain and +42.573/+17.243/+0.556 s in Bahrain.
The bucket gradient persists when expressed per lap: +0.845/+0.578/+0.020 s/lap
pooled, so it is not solely the longer elapsed-time horizon of early snapshots.

Only 38/645 predictions (5.9%) use any strictly fallback future wear parameter:
31 all-fallback (+50.542 s mean error) and seven mixed (+47.796 s). The 607
all-fitted predictions still average +22.788 s. Within laps 5-14, all-fitted
predictions average +42.494 s (N=149), versus +50.037 s for any fallback (N=38).
Fallback exposures account for only 10.9% of summed positive error. The later
buckets contain no strictly fallback future compounds, yet laps 15-29 remain
strongly pessimistic.

Fitted does not mean data-dominated: coefficients shrink with 60 pseudo clean
laps. As an explicitly exploratory secondary breakdown, call a future estimate
prior-dominated when its stored prior weight is at least 0.5 (sample count <=60).
248 predictions have at least one such future estimate and average +44.364 s;
the other 397 average +11.918 s. In laps 15-29, the comparison is +45.477 s
(N=63) versus +18.654 s (N=225). Almost all early cases are prior-dominated
(185/187), preventing a useful early within-phase comparison. This supports
investigating sparse/strongly shrunk wear estimates, but does not prove they
cause the error; anchor, fuel/track evolution and compound offsets also differ
with race phase and are not isolated here.

425/645 predictions (65.9%) have **zero future-stint cliff exposure** and still
average +29.492 s error. For one to five penalized future laps the mean is
+8.807 s (N=137); for six to ten it is +24.015 s (N=83). There is no monotone
pooled error gradient. All 861 future-stint exposures are retained separately:
622 have zero penalized laps, 156 have 1-5, and 83 have 6-9; none exceeds nine.

Mean nominal future cliff cost is 0.636 s; including remaining current tyres,
it is 1.419 s, compared with +24.393 s overall mean error. Even at the maximum
sample multiplier 1.15, mean direct total cliff cost is only 1.631 s. Maximum
nominal costs are 6.750 s for future stints and 9.900 s including current tyres.
507 of 515 positive errors exceed their own 1.15-times-total-cliff budget.
369 predictions have zero direct subject cliff cost anywhere in the horizon
and still average +26.959 s. These comparisons rule out the direct subject cliff
term as the main explanation; indirect rival/traffic effects are not isolated.

**Agreement-layer directional prediction, registered before that layer runs:**
pessimistic costs for a fresh future compound should favour postponing the
switch, giving later initial box alerts (positive engine-minus-team timing error)
and lower early-phase stop recall. Test this particularly where the immediate
candidate's wear is prior-dominated and current tyres are not near their cliff.
This is a hypothesis about relative action costs, not a consequence guaranteed
by absolute finish bias: a common pace-anchor error may cancel between actions,
and excessive current-tyre wear can favour earlier stops. The agreement plan
predeclares how to distinguish those cases; no direction will be revised after
seeing agreement results.

Future stints follow the saved conditional actual plan up to the scored driver finish. Each replacement starts at engine age zero on its charged entry lap, exactly as the frozen model. Fitted means `fallback_used=false` in the cutoff audit; fitted values still shrink toward defaults. All-fallback/mixed/all-fitted describe all future compounds collectively, including repeated compounds.

Cliff ages: SOFT 15, MEDIUM 24, HARD 35. A future stint of L laps is charged at ages 0..L-1; strictly penalized laps k=max(0,L-1-cliff_age). The common length-minus-threshold count differs by one and is also retained in the detail file. Future cliff buckets sum penalized laps across all future stints; max-stint buckets and the per-stint table are reported separately.

Nominal direct cliff cost is 0.15 times the sum of excess ages, equivalently 0.15*k*(k+1)/2 per fresh stint. Total cliff cost also includes remaining running on current tyres. Each existing wear sample scales that term by 0.85..1.15. These budgets are an accounting check, not a no-cliff counterfactual: they do not rerun traffic or remove any real tyre loss. Future linear wear costs are shown separately. No causal attribution from group correlations.

[Metrics](metrics.json). [Per-prediction/per-stint audit](prediction_stint_details.jsonl).

## pooled_prediction

| Group | N | Mean error s | Median error s | MAE s | Error/lap s | Coverage | Future cliff s | Total cliff s | Future linear wear s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 645 | +24.393 | +23.168 | 29.640 | +0.508 | 62.5% | 0.636 | 1.419 | 24.194 |
| cutoff_bucket:15-29 | 288 | +24.521 | +23.373 | 27.886 | +0.578 | 65.6% | 0.540 | 1.272 | 26.197 |
| cutoff_bucket:30+ | 170 | +2.580 | -2.721 | 16.705 | +0.020 | 52.9% | 0.517 | 1.108 | 12.829 |
| cutoff_bucket:5-14 | 187 | +44.027 | +46.077 | 44.101 | +0.845 | 66.3% | 0.894 | 1.927 | 31.441 |
| future_wear_status:all_fallback | 31 | +50.542 | +53.137 | 50.542 | +0.912 | 74.2% | 0.634 | 1.297 | 27.326 |
| future_wear_status:all_fitted | 607 | +22.788 | +22.272 | 28.358 | +0.484 | 61.6% | 0.624 | 1.414 | 23.906 |
| future_wear_status:mixed | 7 | +47.796 | +60.156 | 48.192 | +0.823 | 85.7% | 1.671 | 2.357 | 35.337 |
| future_cliff_bucket:0 | 425 | +29.492 | +28.371 | 31.420 | +0.677 | 63.3% | 0.000 | 0.592 | 24.869 |
| future_cliff_bucket:1-5 | 137 | +8.807 | +6.254 | 22.864 | +0.049 | 59.9% | 0.719 | 1.717 | 21.657 |
| future_cliff_bucket:6-10 | 83 | +24.015 | +29.960 | 31.710 | +0.404 | 62.7% | 3.757 | 5.158 | 24.926 |
| max_stint_cliff_bucket:0 | 425 | +29.492 | +28.371 | 31.420 | +0.677 | 63.3% | 0.000 | 0.592 | 24.869 |
| max_stint_cliff_bucket:1-5 | 137 | +8.807 | +6.254 | 22.864 | +0.049 | 59.9% | 0.719 | 1.717 | 21.657 |
| max_stint_cliff_bucket:6-10 | 83 | +24.015 | +29.960 | 31.710 | +0.404 | 62.7% | 3.757 | 5.158 | 24.926 |
| any_future_prior_dominated:False | 397 | +11.918 | +8.405 | 20.407 | +0.276 | 62.2% | 0.513 | 1.152 | 19.787 |
| any_future_prior_dominated:True | 248 | +44.364 | +45.514 | 44.420 | +0.880 | 62.9% | 0.833 | 1.845 | 31.249 |
| phase×wear:5-14/all_fallback | 31 | +50.542 | +53.137 | 50.542 | +0.912 | 74.2% | 0.634 | 1.297 | 27.326 |
| phase×wear:5-14/mixed | 7 | +47.796 | +60.156 | 48.192 | +0.823 | 85.7% | 1.671 | 2.357 | 35.337 |
| phase×wear:5-14/all_fitted | 149 | +42.494 | +45.493 | 42.569 | +0.833 | 63.8% | 0.911 | 2.038 | 32.115 |
| phase×cliff:5-14/0 | 110 | +46.539 | +47.821 | 46.539 | +0.920 | 61.8% | 0.000 | 0.215 | 27.050 |
| phase×cliff:5-14/1-5 | 48 | +29.091 | +20.329 | 29.380 | +0.525 | 83.3% | 0.828 | 2.769 | 37.084 |
| phase×cliff:5-14/6-10 | 29 | +59.221 | +53.915 | 59.221 | +1.093 | 55.2% | 4.391 | 7.024 | 38.760 |
| phase×wear:15-29/all_fitted | 288 | +24.521 | +23.373 | 27.886 | +0.578 | 65.6% | 0.540 | 1.272 | 26.197 |
| phase×cliff:15-29/0 | 213 | +29.336 | +27.090 | 29.676 | +0.710 | 64.8% | 0.000 | 0.599 | 27.788 |
| phase×cliff:15-29/1-5 | 42 | +7.667 | +13.903 | 24.074 | +0.123 | 57.1% | 0.882 | 1.918 | 21.539 |
| phase×cliff:15-29/6-10 | 33 | +14.896 | +10.319 | 21.177 | +0.300 | 81.8% | 3.586 | 4.795 | 21.855 |
| phase×wear:30+/all_fitted | 170 | +2.580 | -2.721 | 16.705 | +0.020 | 52.9% | 0.517 | 1.108 | 12.829 |
| phase×cliff:30+/0 | 102 | +11.433 | +9.382 | 18.756 | +0.345 | 61.8% | 0.000 | 0.985 | 16.422 |
| phase×cliff:30+/1-5 | 47 | -10.889 | -14.172 | 15.127 | -0.504 | 38.3% | 0.463 | 0.463 | 6.007 |
| phase×cliff:30+/6-10 | 21 | -10.272 | -11.209 | 10.272 | -0.386 | 42.9% | 3.150 | 3.150 | 10.648 |

## spain_2023

| Group | N | Mean error s | Median error s | MAE s | Error/lap s | Coverage | Future cliff s | Total cliff s | Future linear wear s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 366 | +25.622 | +25.917 | 32.241 | +0.498 | 62.6% | 0.679 | 2.031 | 25.748 |
| cutoff_bucket:15-29 | 143 | +31.901 | +32.488 | 34.639 | +0.715 | 63.6% | 0.536 | 2.008 | 30.951 |
| cutoff_bucket:30+ | 126 | +3.287 | -7.492 | 19.298 | +0.018 | 48.4% | 0.423 | 1.220 | 11.093 |
| cutoff_bucket:5-14 | 97 | +45.376 | +46.171 | 45.519 | +0.800 | 79.4% | 1.222 | 3.118 | 37.115 |
| future_wear_status:all_fallback | 12 | +60.144 | +73.199 | 60.144 | +0.988 | 83.3% | 1.000 | 2.538 | 34.436 |
| future_wear_status:all_fitted | 348 | +24.089 | +25.014 | 31.043 | +0.476 | 61.5% | 0.655 | 2.010 | 25.306 |
| future_wear_status:mixed | 6 | +45.469 | +44.729 | 45.931 | +0.758 | 83.3% | 1.425 | 2.225 | 34.020 |
| future_cliff_bucket:0 | 206 | +32.489 | +31.092 | 36.351 | +0.713 | 58.3% | 0.000 | 1.215 | 28.939 |
| future_cliff_bucket:1-5 | 107 | +11.260 | +6.349 | 23.778 | +0.098 | 64.5% | 0.290 | 1.489 | 20.657 |
| future_cliff_bucket:6-10 | 53 | +27.925 | +33.689 | 33.352 | +0.465 | 75.5% | 4.101 | 6.294 | 23.626 |
| max_stint_cliff_bucket:0 | 206 | +32.489 | +31.092 | 36.351 | +0.713 | 58.3% | 0.000 | 1.215 | 28.939 |
| max_stint_cliff_bucket:1-5 | 107 | +11.260 | +6.349 | 23.778 | +0.098 | 64.5% | 0.290 | 1.489 | 20.657 |
| max_stint_cliff_bucket:6-10 | 53 | +27.925 | +33.689 | 33.352 | +0.465 | 75.5% | 4.101 | 6.294 | 23.626 |
| any_future_prior_dominated:False | 230 | +13.748 | +14.276 | 24.221 | +0.295 | 57.0% | 0.385 | 1.488 | 19.034 |
| any_future_prior_dominated:True | 136 | +45.702 | +45.907 | 45.804 | +0.840 | 72.1% | 1.176 | 2.949 | 37.104 |
| phase×wear:5-14/all_fallback | 12 | +60.144 | +73.199 | 60.144 | +0.988 | 83.3% | 1.000 | 2.538 | 34.436 |
| phase×wear:5-14/mixed | 6 | +45.469 | +44.729 | 45.931 | +0.758 | 83.3% | 1.425 | 2.225 | 34.020 |
| phase×wear:5-14/all_fitted | 79 | +43.126 | +46.133 | 43.266 | +0.774 | 78.5% | 1.240 | 3.273 | 37.757 |
| phase×cliff:5-14/0 | 38 | +51.444 | +55.291 | 51.444 | +0.912 | 81.6% | 0.000 | 0.588 | 35.916 |
| phase×cliff:5-14/1-5 | 39 | +30.975 | +17.297 | 31.331 | +0.544 | 84.6% | 0.500 | 2.685 | 37.597 |
| phase×cliff:5-14/6-10 | 20 | +61.928 | +57.458 | 61.928 | +1.085 | 65.0% | 4.950 | 8.768 | 38.454 |
| phase×wear:15-29/all_fitted | 143 | +31.901 | +32.488 | 34.639 | +0.715 | 63.6% | 0.536 | 2.008 | 30.951 |
| phase×cliff:15-29/0 | 97 | +39.052 | +36.564 | 39.554 | +0.889 | 56.7% | 0.000 | 1.314 | 35.395 |
| phase×cliff:15-29/1-5 | 28 | +14.129 | +18.290 | 25.868 | +0.296 | 64.3% | 0.198 | 1.736 | 21.481 |
| phase×cliff:15-29/6-10 | 18 | +21.011 | +25.009 | 21.796 | +0.434 | 100.0% | 3.950 | 6.167 | 21.735 |
| phase×wear:30+/all_fitted | 126 | +3.287 | -7.492 | 19.298 | +0.018 | 48.4% | 0.423 | 1.220 | 11.093 |
| phase×cliff:30+/0 | 71 | +13.377 | +15.704 | 23.898 | +0.368 | 47.9% | 0.000 | 1.415 | 16.384 |
| phase×cliff:30+/1-5 | 40 | -9.971 | -13.027 | 14.950 | -0.474 | 45.0% | 0.150 | 0.150 | 3.564 |
| phase×cliff:30+/6-10 | 15 | -9.118 | -7.495 | 9.118 | -0.323 | 60.0% | 3.150 | 3.150 | 6.123 |

## bahrain_2024

| Group | N | Mean error s | Median error s | MAE s | Error/lap s | Coverage | Future cliff s | Total cliff s | Future linear wear s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 279 | +22.782 | +20.534 | 26.228 | +0.522 | 62.4% | 0.581 | 0.616 | 22.155 |
| cutoff_bucket:15-29 | 145 | +17.243 | +13.510 | 21.225 | +0.442 | 67.6% | 0.543 | 0.546 | 21.508 |
| cutoff_bucket:30+ | 44 | +0.556 | +4.644 | 9.279 | +0.025 | 65.9% | 0.787 | 0.787 | 17.801 |
| cutoff_bucket:5-14 | 90 | +42.573 | +44.546 | 42.573 | +0.895 | 52.2% | 0.540 | 0.643 | 25.326 |
| future_wear_status:all_fallback | 19 | +44.478 | +50.052 | 44.478 | +0.863 | 68.4% | 0.403 | 0.513 | 22.836 |
| future_wear_status:all_fitted | 259 | +21.040 | +18.427 | 24.752 | +0.495 | 61.8% | 0.584 | 0.613 | 22.024 |
| future_wear_status:mixed | 1 | +61.758 | +61.758 | 61.758 | +1.211 | 100.0% | 3.150 | 3.150 | 43.244 |
| future_cliff_bucket:0 | 219 | +26.672 | +24.017 | 26.781 | +0.643 | 68.0% | 0.000 | 0.006 | 21.041 |
| future_cliff_bucket:1-5 | 30 | +0.059 | -6.701 | 19.605 | -0.127 | 43.3% | 2.250 | 2.530 | 25.223 |
| future_cliff_bucket:6-10 | 30 | +17.108 | -3.698 | 28.809 | +0.295 | 40.0% | 3.150 | 3.150 | 27.224 |
| max_stint_cliff_bucket:0 | 219 | +26.672 | +24.017 | 26.781 | +0.643 | 68.0% | 0.000 | 0.006 | 21.041 |
| max_stint_cliff_bucket:1-5 | 30 | +0.059 | -6.701 | 19.605 | -0.127 | 43.3% | 2.250 | 2.530 | 25.223 |
| max_stint_cliff_bucket:6-10 | 30 | +17.108 | -3.698 | 28.809 | +0.295 | 40.0% | 3.150 | 3.150 | 27.224 |
| any_future_prior_dominated:False | 167 | +9.398 | +6.993 | 15.154 | +0.250 | 69.5% | 0.690 | 0.690 | 20.824 |
| any_future_prior_dominated:True | 112 | +42.739 | +44.223 | 42.739 | +0.928 | 51.8% | 0.418 | 0.505 | 24.140 |
| phase×wear:5-14/all_fallback | 19 | +44.478 | +50.052 | 44.478 | +0.863 | 68.4% | 0.403 | 0.513 | 22.836 |
| phase×wear:5-14/mixed | 1 | +61.758 | +61.758 | 61.758 | +1.211 | 100.0% | 3.150 | 3.150 | 43.244 |
| phase×wear:5-14/all_fitted | 70 | +41.781 | +40.755 | 41.781 | +0.899 | 47.1% | 0.540 | 0.643 | 25.746 |
| phase×cliff:5-14/0 | 72 | +43.950 | +44.754 | 43.950 | +0.924 | 51.4% | 0.000 | 0.019 | 22.370 |
| phase×cliff:5-14/1-5 | 9 | +20.927 | +21.605 | 20.927 | +0.443 | 77.8% | 2.250 | 3.133 | 34.861 |
| phase×cliff:5-14/6-10 | 9 | +53.203 | +50.689 | 53.203 | +1.112 | 33.3% | 3.150 | 3.150 | 39.440 |
| phase×wear:15-29/all_fitted | 145 | +17.243 | +13.510 | 21.225 | +0.442 | 67.6% | 0.543 | 0.546 | 21.508 |
| phase×cliff:15-29/0 | 116 | +21.211 | +16.451 | 21.417 | +0.561 | 71.6% | 0.000 | 0.000 | 21.427 |
| phase×cliff:15-29/1-5 | 14 | -5.257 | -16.257 | 20.487 | -0.221 | 42.9% | 2.250 | 2.282 | 21.655 |
| phase×cliff:15-29/6-10 | 15 | +7.557 | -8.604 | 20.434 | +0.140 | 60.0% | 3.150 | 3.150 | 21.999 |
| phase×wear:30+/all_fitted | 44 | +0.556 | +4.644 | 9.279 | +0.025 | 65.9% | 0.787 | 0.787 | 17.801 |
| phase×cliff:30+/0 | 31 | +6.980 | +6.890 | 6.980 | +0.292 | 93.5% | 0.000 | 0.000 | 16.507 |
| phase×cliff:30+/1-5 | 7 | -16.139 | -15.754 | 16.139 | -0.672 | 0.0% | 2.250 | 2.250 | 19.965 |
| phase×cliff:30+/6-10 | 6 | -13.156 | -13.513 | 13.156 | -0.544 | 0.0% | 3.150 | 3.150 | 21.962 |

## Individual future-stint exposures

A prediction with multiple future stints appears in multiple rows. Parent finish errors are exposure-weighted descriptive values, not additive errors assigned to a stint. Use the prediction-level tables for unbiased row counts.

| Race | Compound | Cutoff wear | Penalized laps in stint | Stint exposures | Predictions | Mean length | Parent finish error s | Cliff cost s |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| bahrain_2024 | HARD | fallback | 0 | 36 | 20 | 22.83 | +46.055 | 0.000 |
| bahrain_2024 | HARD | fitted | 0 | 258 | 217 | 23.49 | +27.898 | 0.000 |
| bahrain_2024 | SOFT | fallback | 1-5 | 2 | 2 | 21.00 | +18.344 | 2.250 |
| bahrain_2024 | SOFT | fallback | 6-10 | 1 | 1 | 22.00 | +57.249 | 3.150 |
| bahrain_2024 | SOFT | fitted | 1-5 | 28 | 28 | 21.00 | -1.247 | 2.250 |
| bahrain_2024 | SOFT | fitted | 6-10 | 29 | 29 | 22.00 | +15.724 | 3.150 |
| spain_2023 | HARD | fallback | 0 | 18 | 16 | 27.67 | +54.493 | 0.000 |
| spain_2023 | HARD | fitted | 0 | 222 | 220 | 27.71 | +38.214 | 0.000 |
| spain_2023 | MEDIUM | fallback | 0 | 3 | 3 | 20.67 | +84.607 | 0.000 |
| spain_2023 | MEDIUM | fallback | 1-5 | 2 | 2 | 26.00 | +34.186 | 0.150 |
| spain_2023 | MEDIUM | fitted | 0 | 39 | 39 | 20.36 | +45.065 | 0.000 |
| spain_2023 | MEDIUM | fitted | 1-5 | 27 | 27 | 26.00 | +9.847 | 0.150 |
| spain_2023 | SOFT | fallback | 0 | 2 | 2 | 15.00 | +18.670 | 0.000 |
| spain_2023 | SOFT | fallback | 1-5 | 3 | 3 | 18.00 | +57.411 | 0.600 |
| spain_2023 | SOFT | fallback | 6-10 | 2 | 2 | 23.50 | +101.816 | 4.950 |
| spain_2023 | SOFT | fitted | 0 | 44 | 44 | 15.00 | -2.815 | 0.000 |
| spain_2023 | SOFT | fitted | 1-5 | 94 | 94 | 17.26 | +10.368 | 0.265 |
| spain_2023 | SOFT | fitted | 6-10 | 51 | 51 | 22.76 | +25.027 | 4.068 |
