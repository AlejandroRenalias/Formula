# Verification

- Full suite: 193 passed, no skips; workspace-local temporary directory.
- Final conditioning/calibration focused checks: 6 passed.
- Offline replay of the same 1,400 stored states/configurations/actual plans;
  5,446 scored predictions, same cohorts, no new exclusions or stride changes.
- Every combined median, p10 and p90 exactly equals the previous saved result.
  Every combined per-race metric exactly equals its previous JSON reference.
- Model calculator/core/prior source hashes checked against previous manifests;
  no change to scenario draws, simulation, parameters or prior rates.
- Conditional quantile tests cover weighted renormalization, horizon prefixes,
  empty subsets, ongoing events and preservation of combined outputs.
- Probability tests cover exclusion of known ongoing laps, exact first-onset
  marginal, separation from sampled fraction, and observed VSC 6/7 transitions.
- Calibration tests cover Brier score, decile boundaries including 0/1 and empty
  bins. Outcome filtering tests reject actual neutralization and empty subsets.
- Report regenerated offline and plots inspected, including France's unavailable
  green-only finish panel. Output fields retain subset count/probability mass.
- Three races are insufficient for calibration claims; overlapping driver/lap
  outcomes are correlated. No tuning, new races or UI edits. No push performed.
