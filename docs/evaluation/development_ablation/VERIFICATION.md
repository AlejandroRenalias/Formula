# Verification

Each candidate: 1,400 matched snapshots / 5,446 matched predictions. All source times <= cutoff; hashes verified. Pit estimates, ongoing neutralisation assumptions, noise sizing, onset probabilities, sampled onset frequencies and conditional sample counts/masses are identical to the current offsets run.

A has exactly the same state, fitted wear, offsets and cutoff base pace as offsets. Its green quantiles differ only by the analytically expected fixed-fuel time shift. B records a fixed -0.05 trend with source time zero. Actual future data is used only for subject plans and scoring. No new races or UI changes.


After selecting pit+wear, 220 full-suite tests pass with the frozen default.
All 1,400 frozen-default snapshots exactly match the saved pit+wear state and
configuration fields. All 31 available horizon predictions across nine
representative snapshots (early/middle/late in each race) match the saved
pit+wear outputs exactly, including conditional quantiles and onset probabilities.
These checks ran with networking blocked; see frozen_verification.json.

Reproduction: python -m tools.evaluate_ablation --race <development race>
runs A and B, and --report-only generates matched metrics/selection. Use
python -m tools.verify_frozen_model to verify the active frozen default against
its saved evaluated profile. The tag is local; no push or new race evaluation.
