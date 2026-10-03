# Real-race engine evaluation

Approved 2026-10-03. Keep the UI untouched. Work in bounded slices and stop
after each requested report. Existing work was preserved before slice 1 in
stash `be57e03e13a6c4eef713722bbf4f73cacafeb305`.

## Three layers and implementation order

1. Cutoff-safe data contract and leakage tests.
2. Dry conditional prediction: given the state at lap N and the subject's
   actual future plan, predict elapsed time at 1, 5, 10 laps and finish.
3. Wet/weather and safety-car support.
4. Agreement: compare engine stop events with team stops, one-to-one within
   +/-1 lap, reporting event precision/recall, timing and compound agreement.
5. Disagreements: estimate benefit/regret of the unchosen alternative under
   shared assumptions. Only the team's action is observed; label all alternative
   outcomes counterfactual, with uncertainty and unresolved cases.

## Information boundary

The exact cutoff is the subject's completed lap crossing session time t_N.
All rival pace, tyres, stints, stop events, weather and track status must use
only records timestamped <= t_N. Keep the whole available field as rivals.
Never use final classification as a model feature. Final results may select
the top-ten evaluation cohort, which creates survivor bias.

Approved exception: a rival's crossing time for the SAME lap N may be used
even if later than t_N as a **live timing proxy** for the gap. Snapshot metadata
must identify its source time and the exception. No other values from that
future row may be used. Prefix tests retain this explicitly isolated proxy
channel while removing all other future data.

Use causal timestamped position and tyre updates, not full-session corrected
tyre assignments or positions inferred from final lap sorting. Weather uses
the most recent earlier station sample without forward interpolation. Current
status uses the latest status event; clean-lap filtering inspects already
observed status events over the lap. Keep tyre age and stint length distinct.
Exclude subject snapshots that straddle a stop when a partially paid stop cannot
be represented by the engine. Record exclusions, never silently invent gaps.
Use scheduled race length known beforehand, not realized finish length.

FastF1 session Time is session-relative. Do not add it to session.date as if
session.date were its UTC origin. Use an explicitly labelled session clock or a
verified t0_date; preserve exact session seconds in the snapshot.

## Parameters and weather

Slice 1 uses frozen defaults: pit losses 21.5/12.5/9.5 seconds, compound offsets,
wear and cliff parameters, fuel effect 0.05 s/lap, traffic and SC assumptions.
Use the existing recent-clean-lap pace statistic at the cutoff for base pace.
No parameter fitting, including degradation fitting, in slice 1. Retain existing
32 seeded dry samples, pit spread +/-1.5 s and wear multiplier +/-15%. Expect
under-coverage and report it without widening intervals after seeing outcomes.
Rivals follow engine causal tyre-life/stop assumptions, never actual future plans.

Later causal estimation may update pit loss from completed pre-cutoff stops,
pace/degradation from clean within-stint samples, and neutralized pace from
already observed SC/VSC periods. Sparse data require frozen priors and sample
counts. Every estimate needs its latest source timestamp <= cutoff.

FastF1 has weather observations, not historical forecasts or precise track
wetness. Slice 1 runs no forecast with current observed weather only. Later
compare a causal persistence/no-forecast mode with a separately labelled oracle
weather sensitivity experiment. Oracle inputs are future-informed evaluation
inputs, never a leakage-free forecast or guaranteed mathematical upper bound.
Do not reuse hand-authored scenario forecasts as historical forecasts. Future
SC onsets must not enter either causal mode; any SC oracle is separate.

## Frozen race split

| Set | Races | Permission |
| --- | --- | --- |
| Development | Bahrain 2021, Spain 2022, France 2022 | Slice 1: Bahrain 2021 only |
| Held out | Spain 2023, Bahrain 2024 | Do not run until user explicitly says assumptions are frozen |
| Wet, later phase | Russia 2021, Netherlands 2023, Canada 2024 | Not part of slice 1 |

Top ten classified finishers; every lap from 5 through scheduled race length
minus 5 inclusive. Benchmark a few snapshots first. If projected full runtime
exceeds approximately 30 minutes, use every second lap and disclose it.
Russia later needs a separately labelled final-four-boundary supplement because
the primary endpoint misses much of its late-rain episode.

## Prediction protocol

Freeze the snapshot and parameters before reading future outcomes. The actual
subject stop schedule/compounds are a conditional evaluation treatment, never
state features or rival behavior. Replay this exact treatment, suppressing
autonomous subject stops. Reject unsupported plans explicitly.

Collect absolute simulated elapsed-time samples, not the existing paired
relative-to-reference policy bands. Actual elapsed time is target crossing Time
minus cutoff Time, including pit running. Record the mapping of real pit entry
to simulated boundary and disclose that the engine charges all stop loss on one
lap, although real pit loss can span in/out laps. Preserve lapped finishes and
unavailable 10-lap horizons without fabricating target rows.

For each horizon report N, median prediction MAE, signed bias (prediction minus
actual), inclusive p10-p90 coverage (target ~80%), mean interval width and lower/
upper miss counts. Include interval score where useful. Adjacent laps are highly
correlated; this development race is not independent validation or a calibration
claim. Aggregate by race/driver in later multi-race reports.

## Tests and offline reruns

- Alter/remove future observations: causal state, parameters and prediction
  must be unchanged, except permitted same-lap gap proxy crossing timestamps.
- Truncate input streams before feature processing; retain only the isolated
  approved proxy. Features must match full-input cutoff construction.
- A future proxy row's tyres, pace, pits and positions must never affect state.
- Test pit entry/exit straddling cutoff, same-compound stops and used tyres.
- Parameter/source timestamps must be <= cutoff; future weather/status and
  later retirement/classification must not affect causal fields.
- Change actual future subject plan: only conditional replay changes.
- Network-blocked evaluation must complete from a local cache; cache misses
  and corrupted normalized datasets fail explicitly.

Separate session acquisition from evaluation. Enable FastF1 cache locally;
export normalized timestamped input streams with version/source hashes. The
evaluation loads only those local files, verifies hashes and blocks sockets.
Pin/record FastF1 version because its internal stream API can change.

## Slice 1 deliverables

Bahrain-only CLI and evaluation modules, leakage/regression tests, local cached
inputs, snapshot and prediction records, reproducibility manifest, and a Markdown
report with dataset/exclusion counts, metrics per horizon, predicted-vs-actual
and error-vs-horizon plots, runtime measurements, and five worst predictions
with evidence-based explanatory notes. No agreement/disagreement analysis,
UI changes, held-out runs or wet-race runs. Report and stop.
