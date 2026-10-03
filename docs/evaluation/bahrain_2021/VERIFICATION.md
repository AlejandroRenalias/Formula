# Slice 1 verification

Completed 2026-10-03. The report and plots use the final socket-blocked run,
not the earlier aborted run with provisional UNKNOWN actual-plan tyre labels.

## Tests

- Evaluation-specific tests: **18 passed**. Includes altered future packets,
  isolated same-lap proxy, raw stream prefix equivalence, real-cache prefix
  replay, pit straddling, pre-race visits, used tyre ages, frozen parameter/source
  timestamps, weather/status boundaries, separate outcome labels, three-stop and
  same-compound plans, absolute intervals, horizon exclusions, cache integrity,
  held-out guard, and blocked networking.
- Full repository suite: **149 passed, 1 pre-existing failure**.
- The failing test is
  `tests/unit/test_projection.py::test_committed_fixture_reproduces_from_its_source_inputs`.
  It fails during RaceState validation because the committed fixture's weather
  provenance uses SYNTHETIC, absent from the committed DataSource enum. Both
  facts were verified directly with `git show HEAD:...`; evaluation does not
  modify these files. The prior uncommitted provenance work is preserved in the
  stash rather than silently mixed into this slice.
- `git diff --check` passed. No UI files are changed by the evaluation slice.

Commands, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_evaluation.py -q -p no:cacheprovider --basetemp=data/cache/pytest-input-audit
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp=data/cache/pytest-final-verification
.\.venv\Scripts\python.exe -m tools.evaluate_bahrain
```

## Final artifact checks

- 470 attempted snapshots, 429 evaluated, 41 explicit exclusions.
- 1,666 scored predictions, 50 unavailable ten-lap targets.
- The complete evaluation loop took **257.60 seconds** (4.29 minutes); every lap
  was retained. Three-snapshot benchmark estimated 211.27 seconds.
- All 429 snapshots' recorded parameter/input source timestamps are <= cutoff.
  The separately labelled same-lap gap-proxy timestamps are the sole approved
  state exception. Actual future subject plans remain a separate treatment.
- Dataset SHA256:
  `7b415e3a8e090ca9b5e969890f552f02238f2b4cd0e87e3fac7f73444597b15b`.
- Independently recomputed counts and MAE from predictions.csv match metrics.json.
- Every recorded source hash matches the final source files.
- Network-blocked fresh replays of HAM lap 16, PER lap 8 and STR lap 40 exactly
  match the saved actual/median/p10/p90 values for all available horizons.
- Both plot files were visually inspected. No assumptions or uncertainty widths
  were tuned to outcomes. Held-out and wet races were not run.

## Preserved prior work

Existing tracked and untracked changes remain in `stash@{0}`:
`be57e03e13a6c4eef713722bbf4f73cacafeb305`, message
`Before Bahrain evaluation slice 1: preserve existing work`.
The working tree was verified clean immediately after stashing. This slice's
new plan, code, tests and report are left uncommitted for review. The stash was
not reapplied or dropped.
