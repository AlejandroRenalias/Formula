# Bahrain 2021 controlled iterations

All stages use the same 429 valid snapshots and 1,666 scored predictions, on locally cached Bahrain 2021 only. Every lap remains sampled (cutoffs 5-51); 41 snapshot exclusions and 50 unavailable 10-lap targets are identical. UI files are untouched. Spain 2022, France 2022, held-out and wet races remain unrun. No model parameters are fitted to future outcomes.

## Commits and reports

- Baseline: `1597011`, [original report](bahrain_2021/REPORT.md).
- Diagnostics: `928418f`, [report](bahrain_2021_diagnostics/REPORT.md); all original predictions preserved exactly.
- Median anchor: `251841c`, [report](bahrain_2021_anchor_median/REPORT.md); only the recent-clean-lap anchor changes.
- Causal pace uncertainty: the commit containing this summary, [report](bahrain_2021_uncertainty/REPORT.md); same median anchor and existing parameters/draws.

To reproduce an earlier model, use its corresponding commit and the explicit output command from its report. Current code enables the new uncertainty in evaluation snapshots; running it into an older output directory would replace that artifact with the current model. The local cache and baseline snapshot audit remain preserved.

## Diagnostics

Signed error is predicted median minus actual. Baseline 1-lap mean +0.397 s masks median -0.428 s: 409 no-stop horizons average -0.432 s, while 20 pit-entry horizons average +17.354 s. All 324 actuals above p90 are no-stop cases. The single-lap pit-charge approximation therefore explains the large positive group.

No-stop baseline mean error per lap is -0.432/-0.493/-0.475 at 1/5/10 laps, supporting approximately -0.4 to -0.5 s/lap over short horizons. It is not constant: finish no-stop mean is -0.826 s/lap (overall -0.567). The controlled median-anchor improvement supports anchor optimism as a substantial contributor, while wear/fuel/cliff and cohort effects remain possible.

Every stage report contains every metric split by actual subject pit entry inside (cutoff, target], plus row-normalized mean/median/absolute error per lap. Future stop labels are outcome-side diagnostics only.

## Point accuracy across changes

Each cell is baseline / median anchor / added uncertainty, in seconds.

| Horizon | Mean bias | Median signed error | MAE | Mean error per lap |
| --- | ---: | ---: | ---: | ---: |
| 1 | +0.397 / +0.774 / +0.759 | -0.428 / -0.068 / -0.087 | 1.337 / 1.205 / 1.208 | +0.397 / +0.774 / +0.759 |
| 5 | -1.972 / -0.090 / -0.071 | -2.614 / -0.728 / -0.728 | 3.823 / 2.823 / 2.823 | -0.394 / -0.018 / -0.014 |
| 10 | -4.554 / -0.666 / -0.586 | -4.670 / -0.668 / -0.530 | 6.139 / 4.166 / 4.165 | -0.455 / -0.067 / -0.059 |
| finish | -11.869 / -1.687 / -1.462 | -9.919 / -2.342 / -2.185 | 13.338 / 8.413 / 8.514 | -0.567 / -0.192 / -0.186 |

## Uncertainty change

The same driver's pre-cutoff six-clean-lap window is normalized by nominal tyre/wear and fuel cost. Sample scatter s sizes persistent Normal SD=s/sqrt(n) and independent lap-noise SD=s. One observation gives zero scatter. This is an assumed split, not a fitted variance decomposition. Independent seed streams preserve weather/pit/wear draws; antithetic pairs center the new draws. Persistent offsets remain constant through each sample's entire trace.

| Horizon | Coverage, median only | Coverage, added noise | Width, median only (s) | Width, added noise (s) |
| --- | ---: | ---: | ---: | ---: |
| 1 | 11.9% | 61.3% | 0.219 | 1.063 |
| 5 | 11.7% | 46.6% | 0.965 | 3.279 |
| 10 | 16.6% | 45.1% | 1.655 | 5.940 |
| finish | 15.9% | 47.3% | 3.636 | 15.745 |

Coverage improves substantially but remains below 80%. Point MAE is nearly unchanged. The residual one-lap pit-entry group still has zero coverage; no further widening or model correction is made. Finish no-stop coverage is 32.3%, versus 56.1% with stops: aggregate coverage does not hide those remaining weaknesses.

## Verification

- Final suite: 156 passed, one known pre-existing test deselected (`test_committed_fixture_reproduces_from_its_source_inputs`). The committed fixture uses SYNTHETIC but the current committed provenance enum lacks it; the fix is in the preserved stash. No combined stash/evaluation test was run.
- All 23 evaluation tests pass, including altered future data, truncated streams, pit straddling, parameter timestamps, network blocking, and driver-local uncertainty.
- Persistent offsets versus per-lap noise have separately verified linear and increment accumulation. Added uncertainty preserves the existing weather/pit/wear draws and reproducible shared realizations.
- All 429 uncertainty-run states and actual subject plans equal the median-only run exactly. Config differences are limited to the two new sigmas. All source timestamps are <= cutoff; every cohort key and exclusion matches.
- Three real snapshots (HAM16, PER8, STR40) with both sigmas reset to zero exactly reproduce median-only predictions at every scored horizon.
- Cache digest and current source hashes verified. Report-only protocol text correction after simulation is explicitly recorded in the uncertainty manifest, preserving the original simulation runner hash.
- Both plots inspected in each fresh run. Uncertainty runtime 255.15 s; every lap retained.
- Stash remains intact: [full inventory](STASH_CONTENTS.md).
