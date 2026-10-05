# Decision-engine-v1 agreement evaluation

Timing agreement only: no disagreement/counterfactual quality analysis. Development and held-out sets remain separate. No model or threshold fitting to these results. Signed timing = engine alert minus team stop boundary (negative earlier, positive later).

## Candidate amendment and frozen prediction parity

The finish-legal zero-stop candidate was documented and committed/tagged before the first agreement benchmark. Existing candidates retain their ordering and budget, with one reserved extra slot. No-stop uses no reactive or SC stops. Immediate target HARD (MEDIUM when on HARD), four-lap deferral grid and two-stop cap remain limitations. The calibrated prediction profile is unchanged. Actual-plan summaries were checked against all saved accepted prediction fields; see [prediction_parity.json](prediction_parity.json).

## Runtime and cohort

| Race | Valid calls | Excluded cutoffs | Stride | Projected every-lap s | Scored run s | Reused benchmark calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bahrain_2021 | 429 | 41 | 1 | 265.1 | 265.6 | 4 |
| spain_2022 | 542 | 28 | 1 | 404.0 | 458.6 | 4 |
| france_2022 | 429 | 11 | 1 | 332.7 | 285.8 | 5 |
| spain_2023 | 550 | 20 | 1 | 417.1 | 461.2 | 4 |
| bahrain_2024 | 459 | 21 | 1 | 321.3 | 327.0 | 4 |

Benchmark selection was recorded before calls: phase maximum candidates, per-race minimum candidates, and France ongoing SC. The three full-wrapper parity states matched call, recommendation, ranking, candidate means, margins and confidence exactly. All runs blocked network access and hash-verified cached inputs. Benchmark calls are reused, not scored twice. Run timings exclude full-wrapper parity overhead.

All physical subject stops are labels, including same-compound stops. A stop is recall-observable only if its +/-1 window intersects a valid cutoff. Physical stop labels before lap 5 remain in overall counts and are listed separately, outside the 5-14 phase. Missing cutoffs break alert episodes; the first BOX in an observed segment is left-censored. Repeated adjacent BOX calls collapse to their first call. Primary matches maximize chronological one-to-one cardinality within +/-1, then minimize absolute distance, then prefer earlier alerts. No sliding persistent alerts to the actual stop.

## Primary +/-1-lap event agreement

| Race/set | Alerts | Observable stops | TP | FP | FN | Precision | Recall | Equal-race precision | Equal-race recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bahrain_2021 | 4 | 20 | 2 | 2 | 18 | 50.0% | 10.0% | NA | NA |
| spain_2022 | 18 | 28 | 3 | 15 | 25 | 16.7% | 10.7% | NA | NA |
| france_2022 | 1 | 11 | 0 | 1 | 11 | 0.0% | 0.0% | NA | NA |
| spain_2023 | 12 | 20 | 7 | 5 | 13 | 58.3% | 35.0% | NA | NA |
| bahrain_2024 | 20 | 20 | 8 | 12 | 12 | 40.0% | 40.0% | NA | NA |
| development | 23 | 59 | 5 | 18 | 54 | 21.7% | 8.5% | 22.2% | 6.9% |
| held_out | 32 | 40 | 15 | 17 | 25 | 46.9% | 37.5% | 49.2% | 37.5% |

## bahrain_2021: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 75 | 1.3% | 1 | 7 | 1/1 | 100.0% | 14.3% | 8 | 0 | 0.0% | 0.0% |
| 15-29 | 142 | 0.7% | 1 | 6 | 0/0 | 0.0% | 0.0% | 123 | 1 | 0.7% | 0.8% |
| 30+ | 212 | 6.1% | 2 | 7 | 1/1 | 50.0% | 14.3% | 203 | 178 | 84.0% | 87.7% |

| Phase | Excluded cutoffs | No legal BOX | No legal STAY | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| 5-14 | 25 | 0 | 0 | 0 |
| 15-29 | 8 | 0 | 0 | 0 |
| 30+ | 8 | 0 | 0 | 0 |

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 2 | -0.50 | -0.50 | +0.50 | 1/1/0 | 0 | 0 |
| +/-1 uncensored | 2 | -0.50 | -0.50 | +0.50 | 1/1/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 4 | -2.75 | -1.50 | +2.75 | 1/1/0 | 2 | 0 |
| +/-10 uncensored | 4 | -2.75 | -1.50 | +2.75 | 1/1/0 | 2 | 0 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 1 | +0.00 | +0.00 | 0 | 0 |
| 15-29 uncensored | 0 | NA | NA | 0 | 0 |
| 30+ uncensored | 3 | -3.67 | -2.00 | 2 | 0 |

Exact-lap precision/recall: 25.0% / 5.0%. Raw per-cutoff BOX precision: 46.7% (repeated alerts allowed). Unobservable stops: 2; partial stop windows: 20; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 0/16.

## spain_2022: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 92 | 0.0% | 0 | 8 | 0/0 | NA | 0.0% | 16 | 0 | 0.0% | 0.0% |
| 15-29 | 147 | 12.9% | 9 | 3 | 1/1 | 11.1% | 33.3% | 138 | 0 | 0.0% | 0.0% |
| 30+ | 303 | 22.4% | 9 | 17 | 2/2 | 22.2% | 11.8% | 303 | 126 | 41.6% | 41.6% |

| Phase | Excluded cutoffs | No legal BOX | No legal STAY | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| 5-14 | 8 | 0 | 0 | 0 |
| 15-29 | 3 | 0 | 0 | 0 |
| 30+ | 17 | 0 | 0 | 0 |

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 3 | -0.33 | +0.00 | +0.33 | 1/2/0 | 0 | 0 |
| +/-1 uncensored | 3 | -0.33 | +0.00 | +0.33 | 1/2/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 16 | -3.12 | -3.00 | +3.12 | 1/2/0 | 13 | 0 |
| +/-10 uncensored | 16 | -3.12 | -3.00 | +3.12 | 1/2/0 | 13 | 0 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 0 | NA | NA | 0 | 0 |
| 15-29 uncensored | 2 | -2.00 | -2.00 | 1 | 0 |
| 30+ uncensored | 14 | -3.29 | -3.00 | 12 | 0 |

Exact-lap precision/recall: 11.1% / 7.1%. Raw per-cutoff BOX precision: 36.8% (repeated alerts allowed). Unobservable stops: 1; partial stop windows: 28; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 2/12.

## france_2022: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 100 | 0.0% | 0 | 0 | 0/0 | NA | NA | 0 | 0 | 0.0% | NA |
| 15-29 | 140 | 0.0% | 0 | 10 | 0/0 | NA | 0.0% | 112 | 49 | 35.0% | 43.8% |
| 30+ | 189 | 1.6% | 1 | 1 | 0/0 | 0.0% | 0.0% | 189 | 183 | 96.8% | 96.8% |

| Phase | Excluded cutoffs | No legal BOX | No legal STAY | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| 5-14 | 0 | 0 | 0 | 0 |
| 15-29 | 10 | 0 | 0 | 0 |
| 30+ | 1 | 0 | 0 | 0 |

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-1 uncensored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 1 | -8.00 | -8.00 | +8.00 | 0/0/0 | 1 | 0 |
| +/-10 uncensored | 1 | -8.00 | -8.00 | +8.00 | 0/0/0 | 1 | 0 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 0 | NA | NA | 0 | 0 |
| 15-29 uncensored | 0 | NA | NA | 0 | 0 |
| 30+ uncensored | 1 | -8.00 | -8.00 | 1 | 0 |

Exact-lap precision/recall: 0.0% / 0.0%. Raw per-cutoff BOX precision: 0.0% (repeated alerts allowed). Unobservable stops: 0; partial stop windows: 11; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 0/10.

## spain_2023: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 97 | 0.0% | 0 | 4 | 0/0 | NA | 0.0% | 6 | 0 | 0.0% | 0.0% |
| 15-29 | 143 | 4.2% | 4 | 6 | 4/4 | 100.0% | 66.7% | 83 | 1 | 0.7% | 1.2% |
| 30+ | 310 | 13.2% | 8 | 10 | 3/3 | 37.5% | 30.0% | 296 | 149 | 48.1% | 50.3% |

| Phase | Excluded cutoffs | No legal BOX | No legal STAY | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| 5-14 | 3 | 0 | 0 | 0 |
| 15-29 | 7 | 0 | 0 | 0 |
| 30+ | 10 | 0 | 0 | 0 |

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 7 | -0.57 | -1.00 | +0.57 | 4/3/0 | 0 | 0 |
| +/-1 uncensored | 7 | -0.57 | -1.00 | +0.57 | 4/3/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 10 | -1.20 | -1.00 | +3.20 | 4/3/0 | 2 | 1 |
| +/-10 uncensored | 10 | -1.20 | -1.00 | +3.20 | 4/3/0 | 2 | 1 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 0 | NA | NA | 0 | 0 |
| 15-29 uncensored | 4 | -0.50 | -0.50 | 0 | 0 |
| 30+ uncensored | 6 | -1.67 | -1.00 | 2 | 1 |

Exact-lap precision/recall: 25.0% / 15.0%. Raw per-cutoff BOX precision: 31.9% (repeated alerts allowed). Unobservable stops: 0; partial stop windows: 20; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 2/10.

## bahrain_2024: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 91 | 20.9% | 10 | 9 | 6/6 | 60.0% | 66.7% | 17 | 0 | 0.0% | 0.0% |
| 15-29 | 147 | 1.4% | 0 | 2 | 0/0 | NA | 0.0% | 145 | 2 | 1.4% | 1.4% |
| 30+ | 221 | 19.9% | 10 | 9 | 2/2 | 20.0% | 22.2% | 221 | 167 | 75.6% | 75.6% |

| Phase | Excluded cutoffs | No legal BOX | No legal STAY | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| 5-14 | 9 | 0 | 0 | 0 |
| 15-29 | 3 | 0 | 0 | 0 |
| 30+ | 9 | 0 | 0 | 0 |

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 8 | -0.75 | -1.00 | +0.75 | 6/2/0 | 0 | 0 |
| +/-1 uncensored | 8 | -0.75 | -1.00 | +0.75 | 6/2/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 18 | -2.44 | -2.00 | +2.44 | 6/2/0 | 10 | 0 |
| +/-10 uncensored | 18 | -2.44 | -2.00 | +2.44 | 6/2/0 | 10 | 0 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 8 | -1.50 | -1.00 | 2 | 0 |
| 15-29 uncensored | 1 | -2.00 | -2.00 | 1 | 0 |
| 30+ uncensored | 9 | -3.33 | -3.00 | 7 | 0 |

Exact-lap precision/recall: 10.0% / 10.0%. Raw per-cutoff BOX precision: 46.2% (repeated alerts allowed). Unobservable stops: 0; partial stop windows: 20; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 2/2.

## development: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 267 | 0.4% | 1 | 15 | 1/1 | 100.0% | 6.7% | 24 | 0 | 0.0% | 0.0% |
| 15-29 | 429 | 4.7% | 10 | 19 | 1/1 | 10.0% | 5.3% | 373 | 50 | 11.7% | 13.4% |
| 30+ | 704 | 11.9% | 12 | 25 | 3/3 | 25.0% | 12.0% | 695 | 487 | 69.2% | 70.1% |

Equal-race phase precision/recall: 5-14: 100.0% / 7.1%; 15-29: 5.6% / 11.1%; 30+: 24.1% / 8.7%.

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 5 | -0.40 | +0.00 | +0.40 | 2/3/0 | 0 | 0 |
| +/-1 uncensored | 5 | -0.40 | +0.00 | +0.40 | 2/3/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 21 | -3.29 | -3.00 | +3.29 | 2/3/0 | 16 | 0 |
| +/-10 uncensored | 21 | -3.29 | -3.00 | +3.29 | 2/3/0 | 16 | 0 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 1 | +0.00 | +0.00 | 0 | 0 |
| 15-29 uncensored | 2 | -2.00 | -2.00 | 1 | 0 |
| 30+ uncensored | 18 | -3.61 | -3.00 | 15 | 0 |

Exact-lap precision/recall: 13.0% / 5.1%. Raw per-cutoff BOX precision: 37.1% (repeated alerts allowed). Unobservable stops: 3; partial stop windows: 59; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 2/38.

## held_out: phase and no-stop wins

| Phase | Calls | BOX rate | Alerts | Observable stops | Matched alerts/stops | Precision | Recall | Stay-finish available | Wins | Wins / all | Wins / available |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 5-14 | 188 | 10.1% | 10 | 13 | 6/6 | 60.0% | 46.2% | 23 | 0 | 0.0% | 0.0% |
| 15-29 | 290 | 2.8% | 4 | 8 | 4/4 | 100.0% | 50.0% | 228 | 3 | 1.0% | 1.3% |
| 30+ | 531 | 16.0% | 18 | 19 | 5/5 | 27.8% | 26.3% | 517 | 316 | 59.5% | 61.1% |

Equal-race phase precision/recall: 5-14: 60.0% / 33.3%; 15-29: 100.0% / 33.3%; 30+: 28.7% / 26.1%.

Precision phase belongs to the alert; recall phase belongs to the team stop. Matched counts can differ across a phase boundary.

| Timing view | Matched N | Mean laps | Median laps | MAE laps | -1 / 0 / +1 | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| +/-1 all | 15 | -0.67 | -1.00 | +0.67 | 10/5/0 | 0 | 0 |
| +/-1 uncensored | 15 | -0.67 | -1.00 | +0.67 | 10/5/0 | 0 | 0 |
| +/-1 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |
| +/-10 all | 28 | -2.00 | -1.00 | +2.71 | 10/5/0 | 12 | 1 |
| +/-10 uncensored | 28 | -2.00 | -1.00 | +2.71 | 10/5/0 | 12 | 1 |
| +/-10 censored | 0 | NA | NA | NA | 0/0/0 | 0 | 0 |

| Wide diagnostic by team-stop phase | Matches | Mean laps | Median laps | Earlier 2-10 | Later 2-10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-14 uncensored | 8 | -1.50 | -1.00 | 2 | 0 |
| 15-29 uncensored | 5 | -0.80 | -1.00 | 1 | 0 |
| 30+ uncensored | 15 | -2.67 | -3.00 | 9 | 1 |

Exact-lap precision/recall: 15.6% / 12.5%. Raw per-cutoff BOX precision: 40.2% (repeated alerts allowed). Unobservable stops: 0; partial stop windows: 40; left-censored alerts: 0. Primary matches after the stop was observed: 0. Wide diagnostic unmatched alerts/stops: 4/12.

## Registered later-early-call hypothesis

The expected direction was not changed after the cliff diagnosis: pessimistic fresh-compound costs predict later first BOX alerts, lower early stop recall and fewer early BOX calls. The registered causal stratum is cutoff laps 5-14, immediate target wear prior weight >=0.5, and current tyre age +4 <= cliff. It uses no actual future compounds. Absolute finish bias alone need not change relative action costs.

| Race/set | Stratum cutoffs | BOX rate | Alerts | Observable stops | Precision | Recall | Wide early uncensored N / mean | Wide stratum uncensored N / mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| bahrain_2021 | 55 | 0.0% | 0 | 3 | NA | 0.0% | 1 / +0.00 | 0 / NA |
| spain_2022 | 66 | 0.0% | 0 | 5 | NA | 0.0% | 0 / NA | 0 / NA |
| france_2022 | 92 | 0.0% | 0 | 1 | NA | 0.0% | 0 / NA | 0 / NA |
| spain_2023 | 61 | 0.0% | 0 | 1 | NA | 0.0% | 0 / NA | 0 / NA |
| bahrain_2024 | 57 | 0.0% | 0 | 1 | NA | 0.0% | 9 / -1.56 | 0 / NA |
| development | 213 | 0.0% | 0 | 9 | NA | 0.0% | 1 / +0.00 | 0 / NA |
| held_out | 118 | 0.0% | 0 | 2 | NA | 0.0% | 9 / -1.56 | 0 / NA |

Primary timing is tolerance-truncated. The fixed +/-10 diagnostic remains subject to unmatched events and censoring; it does not assign arbitrary far-away alerts to teams. Adjacent cutoffs and driver/race events are correlated; no independent-trial significance claim. Empty denominators are NA.

## Saved evidence

Full unmodified projection outputs are compressed in each race `raw_calls.jsonl.gz`; `calls.jsonl` preserves causal audit fields, candidate means and call summaries. `matching_audit.json` contains episodes, outcome-only stop labels and every 0/1/10-lap match/unmatched index. `metrics.json` includes scheduled-distance thirds, per-phase timing, censoring and equal-race timing summaries. Per-race manifests seal input/output hashes and snapshot exclusions. See [benchmark.json](benchmark.json), [metrics.json](metrics.json), [manifest.json](manifest.json) and the [protocol](../AGREEMENT_PLAN.md).
