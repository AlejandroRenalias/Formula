# Agreement layer: inspection and proposed protocol

Originally inspection/plan only; execution now authorized. The amendment below
was written before any agreement decision or benchmark call. This follows [EVALUATION_PLAN.md](../EVALUATION_PLAN.md).
The prediction score and frozen profile remain unchanged.

## Frozen decision input and output

Use tag `frozen-development-model-calibrated` (`0878c4d`), including pit+wear,
the 3.0 persistent-offset and 1.0 per-lap-noise multipliers and the unchanged
2019 SC/VSC priors. Reuse the accepted snapshot cohorts: development 1,400
snapshots (Bahrain 2021 429, Spain 2022 542, France 2022 429), held out 1,009
(Spain 2023 550, Bahrain 2024 459). All 2,409 snapshots retained every lap.
Use the saved state and cutoff config, applying the already frozen multipliers
to the historical development configs, exactly as the accepted calibrated
development reference did. Verify all source/data/snapshot hashes before use.

Maintain the exact session cutoff and labelled same-lap gap proxy; all other
position, pace, tyre, stop, status, weather and parameter sources remain <=cutoff.
Use dry no-forecast persistence, observed weather only, the unchanged prior's
remaining duration for any ongoing neutralisation, and sampled future SC/VSC
risk. Do not condition decision samples on the actual future staying green:
the deployed call ranks full probability-weighted race time. A green-status
cutoff stratum can be reported, using information known at the cutoff.

Run the frozen projection decision search with its own `default_policies` and
normal autonomous SC opportunities. Do not pass the actual subject plan,
`fixed_schedule=True`, actual future rival strategies, future weather/status or
team compound choices into this path. Actual stops are a separate label channel
joined only after the calls are frozen. Use the canonical `project` result's
`call` (BOX_NOW or STAY_OUT) and its recommended policy, best box/stay policies,
expected-time margin and confidence. The heuristic scorer's call in
`run_projection_cycle` is commentary, not the strategy decision being scored.

Recommended execution is `project(state, config=..., include_flips=False)`.
This still runs every frozen default policy and all 32 dry Monte Carlo draws.
The flag suppresses only sensitivity sweeps computed after the primary call;
it does not change the primary search, decision objective, prior or uncertainty.
The production wrapper additionally computes those sweeps and specialist
reasoning. If literal wrapper parity is required, verify identical base calls
on a small benchmark subset before the scored run. No source/model change is
needed to use this existing flag. Store raw outputs once and derive all metrics
from them without re-running or tuning confidence thresholds.

## Inspection findings to retain in the score

The decision objective is minimum probability-weighted remaining race time
among finish-legal policies; the call follows the winning policy's initial
action. It is not decided by the median prediction, specialist vote or a newly
chosen confidence cutoff. `call_tolerance_s` affects confidence diagnostics,
not a new abstention rule.

The amended default search has up to ten policies, delayed boundaries on a four-lap
grid, and up to two future stops per policy. Its immediate dry target is HARD
unless the current compound is HARD, in which case it is MEDIUM. It does not
search all compounds, same-compound replacements or arbitrary real schedules.
The matched two-stop variants apply to both immediate-action groups.

**Pre-run candidate-set amendment (2026-10-05):** inspection found no zero-stop
to-finish option. Before any agreement results or benchmark calls exist, add
`stay_to_finish` if the cutoff already proves finish legality: at least two
dry compounds used (including the current compound), or any wet compound used.
This policy has no scheduled or reactive stops and a zero-stop budget. Preserve
every existing candidate and its ordering; allow one additional default-search
slot beyond the existing configured cap. Custom explicit policy sets retain
their existing cap. No prediction sampler, simulator, fitted parameter, prior,
uncertainty, action objective or actual-plan replay changes. Verify actual-plan
outputs against the frozen implementation and saved scores before tagging
`decision-engine-v1`, before the benchmark/scored agreement run. The calibrated
prediction tag/profile remains unchanged. This is a structural inspection fix,
not a response to agreement results. Report its availability and win fraction
by phase. Immediate target HARD (MEDIUM when on HARD) remains a limitation;
primary scoring tests box timing, not compound choice.

When one action has no legal candidate or no policy is legal, report it and
its coverage separately rather than silently dropping or inventing a call.

`project` internally checks/re-snapshots history at the cutoff. Its fitted wear
and pit parameters still come from the supplied frozen cutoff config/state.
Verify that the internal history filtering preserves the information boundary;
do not substitute full-session corrected histories.

## Stop labels, repeated alerts and matching

Map actual pit entry to the existing boundary convention:
`team_boundary = corrected PitIn row NumberOfLaps - 1`. BOX at snapshot N is
a commitment after completed lap N, charged on projected lap N+1. Keep entry
session time and corrected lap coordinates in outcome labels only. Retain
same-compound physical stops and do not require target-compound agreement for
binary timing matches. Retain all existing snapshot exclusions, including pit
straddles and unknown causal compounds; an unavailable snapshot is not STAY_OUT.

Primary event metrics follow the original plan's one-to-one rule. Within each
driver/race, collapse consecutive valid, adjacent BOX_NOW cutoffs into one
alert episode, timestamped at its **first** BOX call. This prevents repeated
alerts from claiming the same team stop repeatedly, and does not slide an
early persistent episode forward to make it match. A missing cutoff breaks
the observed segment; mark the next BOX episode left-censored. Do not bridge
gaps using team outcomes. Retain first-observed alerts in precision, and report
censored timing separately rather than pretending an unobserved onset is known.

Match alerts to actual stop boundaries within +/-1 lap, maximizing the number
of one-to-one matches, then minimizing summed absolute timing distance; final
ties prefer earlier alerts. Preserve chronological matching within a driver.
TP = matched alert/stop pair, FP = unmatched alert, FN = unmatched eligible
team stop. Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 as a supplement.
Zero denominators are unavailable, not perfect scores. This is agreement with
the team's action, not evidence that the team's or engine's action was better.

A team stop is observable for recall when its +/-1 window intersects at least
one valid scored cutoff. Report total stops, observable stops, stops with no
valid window, and partially observed boundary windows. Include all scored
alerts in precision. Report exact-lap matching as a secondary view. Also report
raw per-cutoff BOX precision against the +/-1 team-stop label (repeated alerts
allowed there), explicitly labelled as a different metric from event precision.
If a +1 match is after the team's stop was already observed, flag it; do not
describe it as a successful pre-stop forecast.

## Timing and phase metrics

Signed timing error = engine alert boundary minus team boundary: negative is
earlier, positive later. For primary +/-1 matches, report mean, median, MAE and
counts at -1/0/+1. This distribution is tolerance-truncated and cannot diagnose
large early or late errors alone.

Predeclare a secondary diagnostic match with the same one-to-one rules and a
fixed +/-10-lap window. Report signed timing, -10..-2 / -1..1 / +2..+10 counts,
matched fraction and remaining unmatched alerts/stops. Never replace the
primary +/-1 score with this broader score. Report uncensored/censored episodes
separately and do not let broad matching hide extra alerts or missed stops.
No unrestricted far-away pairing that assigns an unrelated late alert to an
early stop merely to obtain a signed error.

Use the diagnostic's fixed cutoff buckets 5-14, 15-29, 30+ as the primary race
phase definition; add scheduled-distance thirds as a secondary cross-race view.
Precision by phase uses the alert's phase; recall uses the team's stop phase.
This avoids moving missed team stops into the engine's preferred phase.
Report BOX rate, alert count, stop count, valid cutoffs and abstention/exclusion
coverage by phase so a high STAY_OUT rate cannot hide missed stops.

Report each development race and each held-out race separately, then separate
development and held-out pools. Provide event-count pooling and equal-race
macro precision/recall (available races only). Timing pools should have both
per-match and equal-race summaries. No mixing the two race sets to select a
different rule or threshold. Include sparse phase counts and no uncertainty
claim based on treating neighboring cutoffs as independent trials.

## Directional prediction, fixed before agreement results

[Report-only diagnosis](held_out_finish_diagnostic/REPORT.md) confirms early
absolute pessimism: stop-containing green finish bias +44.027 s at laps 5-14,
+24.521 s at 15-29 and +2.580 s at 30+. It does **not** support the proposed
dominant cliff cause: mean future cliff budget is only 0.636 s, and zero-future-
cliff cases still have +29.492 s bias. Strict fallback future wear applies to
only 38/645 rows; sparse fitted estimates also remain prior-dominated.

**Primary prospective directional hypothesis:** overly pessimistic fresh
future-compound costs bias the engine toward **waiting/later first box alerts**
(positive timing error), lower early-phase stop recall and fewer early BOX
calls relative to observed team stops. Test it particularly in laps 5-14 where
the immediate target compound's causal wear audit has prior weight >=0.5 and
the current tyre age plus the four-lap deferral does not cross its cliff.
That stratification uses candidate compounds and cutoff audits, not actual
future team compounds. Keep the broad early-phase score as well.

This is a falsifiable mechanism prediction, not something absolute finish bias
alone guarantees: a common pace-anchor/fuel error can cancel between actions;
excessive current-tyre wear can push in the opposite, earlier direction; the
SC discount can encourage waiting; and the inspected missing no-stop option could create
late-race false BOX alerts (addressed by the pre-run amendment above). Report the sign actually observed and reject the
directional hypothesis if early calls are earlier or show no delay. Do not
relabel the expected direction after seeing agreement results.

## Runtime estimate and proposed bounded execution

No decision benchmark was run for this inspection. The saved calibrated
development prediction replay took 33.1/63.4/40.7 s for 429/542/429 snapshots:
137.3 s total, about 0.098 s per one-policy snapshot. This excludes rebuilding
states; held-out prediction runs including state construction took 543.6 and
370.2 s. Using saved states avoids paying that construction cost again.

The primary decision search uses 2-10 policies per scored state (up to 320
Monte Carlo traces versus 32 in prediction), plus display traces, legality
checks and autonomous SC opportunity lookahead. A planning estimate for all
2,409 snapshots is **20-60 minutes serial**, with substantial uncertainty.
It is not a measured decision-engine runtime. The heaviest early/SC states
may exceed that range; measure before committing to the full cohort.

Literal production-wrapper runs also execute sensitivity sweeps: up to 35
rain-arrival/no-rain points, about 13 pit-loss points and 12 SC-start points.
The rain-probability sweep is unavailable with dry/no-forecast ETA=None, but
the arrival sweep still re-evaluates unchanged dry branches. Roughly 30-60
extra full policy evaluations per state imply **many hours, potentially
10-40 hours serial** across the cohort. Those sweeps are not necessary to score
the unchanged immediate call; do not confuse their cost with policy search.

On authorization of implementation, first benchmark a small predeclared set
covering each race, early/middle/late cutoffs, GREEN and France's ongoing SC,
and small/large policy sets. Save and reuse those decisions in the scored run.
Measure call-only versus literal-wrapper overhead on a very small subset and
confirm their base call/policy/margin agree. Re-estimate per race with phase
weights, not just easy late snapshots. Keep draws, prior and policies frozen.

Follow the original approximate 30-minute-per-race rule: if an every-lap race
run is projected above that budget, disclose and use every second lap. This
coarsens +/-1 event coverage and may merge/miss alert onsets; explicitly report
the changed observability/censoring rather than comparing it unqualified with
an every-lap score. Prefer existing call-only execution and per-race bounded
runs to avoid losing every-lap coverage. No runtime shortcut that changes
sampling, candidate policies, confidence or action selection.

Before scoring, test future poisoning/truncated streams, the permitted gap
exception, pit straddles and parameter timestamps, and that adding/removing or
changing actual future subject plans cannot affect decision outputs. Verify
hashes against the tag, block networking, fail on model/data mismatch and never
repair/tune the frozen engine based on agreement. Keep UI untouched. Save calls,
episode/match audit, exclusions, per-race/set metrics and a Markdown report;
stop for review before any disagreement/counterfactual analysis.

## Exact benchmark selection before calls

For each race and each primary phase, select the valid saved snapshot with
maximum candidate count; ties choose the lap nearest phase midpoint (9.5, 22,
and midpoint of 30..scheduled_laps-5), then driver number and lap. Also select
the minimum-candidate snapshot per race (ties latest lap, then driver number),
and France's ongoing-SC snapshot nearest lap 19 (driver number tie). Deduplicate
keys. Select from causal records only, before producing any decision. Weight
phase mean call-only timings by scored phase counts to estimate each race.
For full-wrapper parity, use three benchmark states: Bahrain 2021 early phase,
France ongoing SC, and Bahrain 2024 late phase. Compare canonical call, chosen
policy, ranking, candidate means, best action policies, margin and confidence;
ignore wrapper-only commentary and sensitivity fields. Save benchmark outputs
and reuse call-only results in the scored run.
