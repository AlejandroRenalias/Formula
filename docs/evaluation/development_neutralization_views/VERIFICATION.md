# Verification

- Full suite: 187 passed, no skips, using workspace-local temporary files.
- Offline evaluation: all three development races, every lap, 1,400 snapshots
  and 5,446 scored predictions in each stage; matching cohorts verified.
- Cutoff protection: altered future data and truncated streams, real France SC
  cutoff, pit boundaries, parameter timestamps, and network blocking tested.
- External frozen prior: only 2019 dry races; hashed evidence committed, raw
  FastF1 responses cached locally. Rates are global, not track-specific.
- Neutralization tests: elapsed survival conditioning, finite lifecycle,
  reproducible/non-overlapping event draws, unchanged old random streams,
  sampled SC/VSC pit price, conserved split loss, and SC subject-clock safety.
- Report tests: unequal row counts, missing races/pit strata and weighted median.
- Report input hashes rechecked; report-only processing did not change predictions.
- No degradation fitting or interval tuning. UI untouched. Held-out and wet
  evaluation races remain unrun. No push performed.
