# Bahrain 2021: dry conditional prediction

Bahrain development race only. No race-wide fitting, agreement/disagreement analysis or UI changes.

Prediction source: fresh offline simulation. Previous comparison: docs\evaluation\bahrain_2021_anchor_median.

## Dataset and runtime

- Top ten: HAM, VER, BOT, NOR, PER, LEC, RIC, SAI, TSU, STR.
- Scheduled distance: 56 laps; cutoffs 5–51 inclusive; stride 1.
- Attempted snapshots: 470; evaluated: 429; excluded: 41.
- Scored predictions: 1666; excluded horizon targets: 50.
- Benchmark: 3 snapshots, mean 0.442s/snapshot; estimated full run 3.46 minutes.
- Actual evaluation loop: 255.15s. Every lap retained because estimated runtime was below 30 minutes.
- Entire evaluation ran with socket connections blocked; acquisition was a separate operation.

### Exclusions

| Scope | Reason | Count |
| --- | --- | ---: |
| snapshot | no_recent_clean_pace | 20 |
| snapshot | subject_stop_straddles_cutoff | 20 |
| snapshot | unknown_compound | 1 |
| target | target_beyond_finish_or_missing | 50 |

## Accuracy

Bias is predicted median minus actual elapsed time: negative means too fast. Coverage uses inclusive absolute p10–p90 endpoints; nominal target is 80%. Width is the mean p90 minus p10. Existing uncertainty is reported without post-result widening.

| Horizon | N | MAE (s) | Mean bias (s) | Median error (s) | Coverage | Mean width (s) | Below p10 | Above p90 | Interval score (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 429 | 1.208 | +0.759 | -0.087 | 61.3% | 1.063 | 78 | 88 | 10.042 |
| 5 | 429 | 2.823 | -0.071 | -0.728 | 46.6% | 3.279 | 75 | 154 | 20.245 |
| 10 | 379 | 4.165 | -0.586 | -0.530 | 45.1% | 5.940 | 82 | 126 | 28.422 |
| finish | 429 | 8.514 | -1.462 | -2.185 | 47.3% | 15.745 | 58 | 168 | 51.686 |

## Median error, pit-stop split and error per lap

Signed error is predicted median minus actual. Pit-stop labels use actual subject pit-entry timestamps in (cutoff, target], solely as outcome diagnostics. All metrics are split by this label. Error/lap is computed for each prediction, then averaged or median-aggregated; finish horizons have different lengths.

| Horizon | Stops in horizon | N | MAE s | Mean bias s | Median error s | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage | Mean width s | Below p10 | Above p90 | Interval score s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | all | 429 | 1.208 | +0.759 | -0.087 | +0.759 | -0.087 | 1.208 | 61.3% | 1.063 | 78 | 88 | 10.042 |
| 1 | without_stop | 409 | 0.402 | -0.068 | -0.106 | -0.068 | -0.106 | 0.402 | 64.3% | 1.004 | 58 | 88 | 2.325 |
| 1 | with_stop | 20 | 17.683 | +17.683 | +17.773 | +17.683 | +17.773 | 17.683 | 0.0% | 2.264 | 20 | 0 | 167.839 |
| 5 | all | 429 | 2.823 | -0.071 | -0.728 | -0.014 | -0.146 | 0.565 | 46.6% | 3.279 | 75 | 154 | 20.245 |
| 5 | without_stop | 326 | 1.840 | -0.484 | -0.506 | -0.097 | -0.101 | 0.368 | 52.8% | 3.238 | 52 | 102 | 11.242 |
| 5 | with_stop | 103 | 5.935 | +1.238 | -1.821 | +0.248 | -0.364 | 1.187 | 27.2% | 3.411 | 23 | 52 | 48.743 |
| 10 | all | 379 | 4.165 | -0.586 | -0.530 | -0.059 | -0.053 | 0.417 | 45.1% | 5.940 | 82 | 126 | 28.422 |
| 10 | without_stop | 204 | 3.615 | -0.576 | -0.528 | -0.058 | -0.053 | 0.361 | 47.5% | 6.037 | 47 | 60 | 22.692 |
| 10 | with_stop | 175 | 4.807 | -0.598 | -0.577 | -0.060 | -0.058 | 0.481 | 42.3% | 5.827 | 35 | 66 | 35.101 |
| finish | all | 429 | 8.514 | -1.462 | -2.185 | -0.186 | -0.088 | 0.385 | 47.3% | 15.745 | 58 | 168 | 51.686 |
| finish | without_stop | 158 | 6.309 | -4.569 | -4.883 | -0.449 | -0.496 | 0.539 | 32.3% | 7.289 | 12 | 95 | 41.656 |
| finish | with_stop | 271 | 9.799 | +0.349 | +0.664 | -0.033 | +0.015 | 0.296 | 56.1% | 20.675 | 46 | 73 | 57.533 |

## Matched comparison with previous run

Same driver/cutoff/target cohort. Entries are previous → current; zero-sample pit-stop strata are unavailable. No outcome-derived tuning is applied.

| Horizon | Stops | N | Mean bias s | Median error s | MAE s | Coverage | Mean width s |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| 1 | all | 429 | +0.774 → +0.759 | -0.068 → -0.087 | 1.205 → 1.208 | 11.9% → 61.3% | 0.219 → 1.063 |
| 1 | without_stop | 409 | -0.051 → -0.068 | -0.087 → -0.106 | 0.401 → 0.402 | 12.5% → 64.3% | 0.124 → 1.004 |
| 1 | with_stop | 20 | +17.652 → +17.683 | +17.721 → +17.773 | 17.652 → 17.683 | 0.0% → 0.0% | 2.162 → 2.264 |
| 5 | all | 429 | -0.090 → -0.071 | -0.728 → -0.728 | 2.823 → 2.823 | 11.7% → 46.6% | 0.965 → 3.279 |
| 5 | without_stop | 326 | -0.479 → -0.484 | -0.450 → -0.506 | 1.829 → 1.840 | 11.0% → 52.8% | 0.599 → 3.238 |
| 5 | with_stop | 103 | +1.140 → +1.238 | -1.871 → -1.821 | 5.968 → 5.935 | 13.6% → 27.2% | 2.123 → 3.411 |
| 10 | all | 379 | -0.666 → -0.586 | -0.668 → -0.530 | 4.166 → 4.165 | 16.6% → 45.1% | 1.655 → 5.940 |
| 10 | without_stop | 204 | -0.610 → -0.576 | -0.645 → -0.528 | 3.616 → 3.615 | 14.2% → 47.5% | 1.143 → 6.037 |
| 10 | with_stop | 175 | -0.732 → -0.598 | -0.727 → -0.577 | 4.808 → 4.807 | 19.4% → 42.3% | 2.252 → 5.827 |
| finish | all | 429 | -1.687 → -1.462 | -2.342 → -2.185 | 8.413 → 8.514 | 15.9% → 47.3% | 3.636 → 15.745 |
| finish | without_stop | 158 | -4.568 → -4.569 | -4.803 → -4.883 | 6.288 → 6.309 | 15.8% → 32.3% | 1.802 → 7.289 |
| finish | with_stop | 271 | -0.008 → +0.349 | +0.569 → +0.664 | 9.651 → 9.799 | 15.9% → 56.1% | 4.705 → 20.675 |

Coverage remains below 80%; the model's uncertainty does not cover all real pace and pit timing variation. These are correlated snapshots from one development race, not an independent calibration result.

![Predicted vs actual](predicted_vs_actual.png)

![Signed error vs horizon](error_vs_horizon.png)

## Five worst predictions

Ranked across all scored horizons by absolute median error; several may come from the same driver or adjacent cutoffs.

| Driver | Cutoff | Target / horizon | Actual (s) | Median (s) | p10–p90 (s) | Error (s) |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| LEC | 7 | 56 / finish | 4756.830 | 4806.681 | 4803.857–4810.207 | +49.851 |
| PER | 8 | 56 / finish | 4640.842 | 4684.638 | 4661.748–4699.661 | +43.796 |
| NOR | 7 | 56 / finish | 4743.546 | 4785.559 | 4782.171–4790.525 | +42.013 |
| STR | 7 | 56 / finish | 4780.939 | 4743.535 | 4740.491–4748.166 | -37.404 |
| LEC | 10 | 56 / finish | 4462.759 | 4499.518 | 4468.028–4524.084 | +36.759 |

1. **LEC, cutoff 7, finish:** Pace anchor: median, clean lap(s) [6]; fresh base 97.164s, cutoff tyre age 10; 2 future stop(s) in this horizon. Prediction is too slow. Fixed compound wear/cliff and the cutoff pace anchor can accumulate excessive cost over the horizon. This is a model-based diagnostic, not proof of a single cause.

2. **PER, cutoff 8, finish:** Pace anchor: median, clean lap(s) [6, 7]; fresh base 96.685s, cutoff tyre age 9; 2 future stop(s) in this horizon. Prediction is too slow. Fixed compound wear/cliff and the cutoff pace anchor can accumulate excessive cost over the horizon. This is a model-based diagnostic, not proof of a single cause.

3. **NOR, cutoff 7, finish:** Pace anchor: median, clean lap(s) [6]; fresh base 96.763s, cutoff tyre age 10; 2 future stop(s) in this horizon. Prediction is too slow. Fixed compound wear/cliff and the cutoff pace anchor can accumulate excessive cost over the horizon. This is a model-based diagnostic, not proof of a single cause.

4. **STR, cutoff 7, finish:** Pace anchor: median, clean lap(s) [6]; fresh base 95.916s, cutoff tyre age 10; 2 future stop(s) in this horizon. Prediction is too fast. Long-horizon fixed wear/fuel and the clean-lap anchor can sustain more pace than the driver actually delivered. This is a model-based diagnostic, not proof of a single cause.

5. **LEC, cutoff 10, finish:** Pace anchor: median, clean lap(s) [8, 6]; fresh base 96.740s, cutoff tyre age 13; 2 future stop(s) in this horizon. Prediction is too slow. Fixed compound wear/cliff and the cutoff pace anchor can accumulate excessive cost over the horizon. This is a model-based diagnostic, not proof of a single cause.

## Protocol and limitations

- Exact cutoff coordinates and actual elapsed labels use FastF1 corrected crossing Time. Pace/position/pit state uses only earlier raw TimingData packets; tyres use earlier TimingAppData updates. A LastLapTime received after the crossing is excluded until its packet arrives, even if this leaves the newest known pace one lap old.
- Gap exception: only rival same-lap crossing Time may follow cutoff, tagged live_timing_proxy_same_lap_crossing. Its other fields are never read. Missing crossings use a disclosed stale earlier common-lap gap. This is a retrospective crossing proxy, not a captured live gap feed.
- Session datetimes are epoch-encoded session-relative clocks, not asserted UTC wall times. Each snapshot saves exact cutoff seconds, source timestamps and parameter configuration.
- Frozen compound degradation scale 1, fuel 0.05s/lap, pit losses 21.5/12.5/9.5s, cliff/traffic/SC defaults. Fresh base pace uses the median of the last six available clean laps, removing the central observation(s)' nominal compound/wear cost and advancing fuel effect to cutoff (minimum baseline uses its single fastest observation). No regression-based degradation or race-wide fitting is used.
- Dry persistence, no forecast; seed 18, 32 shared samples, uniform pit offsets +/-1.5s and wear multipliers +/-15%. Normal subject-only persistent pace offset (SD=s/sqrt(n)) and independent per-lap noise (SD=s), sized from the same driver's last six available clean laps after nominal wear/fuel corrections; antithetic paired draws, separate seed streams. One clean observation gives zero scatter. No error-based tuning. Random traffic, damage, strategic lift-off, warm-up and future neutralizations remain unmodeled.
- Actual subject stop schedule/compounds are supplied only AFTER constructing the snapshot, as conditional treatment. Autonomous subject stops are suppressed. Corrected full-session tyre labels are used only for this actual-plan treatment, never cutoff features. Rivals retain engine tyre-life stop assumptions, not observed future strategies.
- Pit-in lap K maps to boundary K−1; the engine charges the entire modeled stop loss on lap K and assumes fresh tyres there. Real losses span in/out laps; used replacement tyres are not modeled. Subject snapshots inside the pit are excluded.
- Fixed status persistence follows the existing engine. No actual future status is injected. Final classification selects subjects outside the engine (survivor bias). No held-out or wet races were acquired or evaluated by this slice.

## Reproduction

From the repository root, after acquiring the authorized race once:

```powershell
.\.venv\Scripts\python.exe -m tools.evaluate_bahrain --output docs/evaluation/bahrain_2021_uncertainty --compare-to docs\evaluation\bahrain_2021_anchor_median
```

The command loads only the hash-verified local normalized cache, blocks network connections and regenerates this report. A missing/corrupt cache fails rather than downloading. Acquisition: `python -m tools.acquire_bahrain_evaluation` (Bahrain only).

- [Metrics](metrics.json), [predictions](predictions.csv), [exclusions](exclusions.json).
- [Manifest](manifest.json) records source/code hashes, versions, benchmark and defaults.
- Full state/config/plan audit: local ignored `data\cache\evaluation\bahrain_2021\snapshots_bahrain_2021_uncertainty.jsonl`.
