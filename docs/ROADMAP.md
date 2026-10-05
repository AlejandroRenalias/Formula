# Project roadmap

Updated 2026-10-05. Phases 1–5 are complete. Phase 6 is **in progress: reservation gate, saved-call export and geometry complete; historical UI implemented, awaiting review**. This supersedes the earlier phase-5 “in progress” status following acceptance of the saved-call disagreement report. The existing prediction profile and decision-engine-v1 scores remain frozen.

| Phase | Status | Done when | Evidence and version |
| --- | --- | --- | --- |
| 1. Prototype and design | Done | The pit-wall prototype establishes the current design, typography, layout and synthetic interaction. | [Prototype](../design/pitwall-concept.html), [map/design commit](https://github.com/AlejandroRenalias/Formula/commit/3011618); no separate prototype tag. |
| 2. Projection engine | Done | Causal race state produces auditable BOX/STAY projections with documented uncertainty and legal policy candidates. | [Model](../MODEL.md), [engine](../src/calculators/projection.py), [frozen-development-model](https://github.com/AlejandroRenalias/Formula/tree/frozen-development-model). |
| 3. Prediction evaluation | Done | The model and calibration are frozen, the development protocol is recorded, and the held-out races are scored once without retuning. | [Evaluation plan](EVALUATION_PLAN.md), [ablation/freeze](evaluation/development_ablation/REPORT.md), [calibration](evaluation/calibration/REPORT.md), [held-out score](evaluation/held_out/REPORT.md), [comparison](evaluation/held_out/COMPARISON.md), [frozen-development-model-calibrated](https://github.com/AlejandroRenalias/Formula/tree/frozen-development-model-calibrated). |
| 4. Agreement evaluation | Done | Frozen decision calls are saved and scored against team stops under the predeclared matching protocol, separately for development and held-out. | [Agreement protocol](evaluation/AGREEMENT_PLAN.md), [score](evaluation/agreement/REPORT.md), [prediction parity](evaluation/agreement/prediction_parity.json), [decision-engine-v1](https://github.com/AlejandroRenalias/Formula/tree/decision-engine-v1). |
| 5. Disagreement analysis | Done | Every unmatched observable stop and alert has observable tags and audits, all missed-stop windows and selected case cards are reported, and the registered hypothesis is assessed without claiming who was right. | [Protocol](evaluation/disagreement/PROTOCOL.md), [report](evaluation/disagreement/REPORT.md), [event register](evaluation/disagreement/EVENT_TAGS.md), [missed-stop windows](evaluation/disagreement/MISSED_STOP_WINDOWS.md), [case cards](evaluation/disagreement/case_cards.json); scored version [decision-engine-v1](https://github.com/AlejandroRenalias/Formula/tree/decision-engine-v1), [report commit](https://github.com/AlejandroRenalias/Formula/commit/1a262f4). |
| 6. Historical mode on the website | In progress — UI implemented; awaiting review | The existing page replays saved v1 calls, locks a user call before explicit outcome reveal, passes leakage/parity checks, and retains the synthetic scenario and current design. | [Historical mode plan](HISTORICAL_MODE_PLAN.md), [foundation report](PHASE6_FOUNDATION_REPORT.md), [UI report and screenshots](historical_ui/REPORT.md); source [decision-engine-v1](https://github.com/AlejandroRenalias/Formula/tree/decision-engine-v1), [agreement score](evaluation/agreement/REPORT.md). No historical UI release tag yet. |
| 7. Decision engine v2 | After phase 6 | The ranked structural changes are tested on development data, assumptions and calibration are frozen before reserved races are acquired, and a separately registered untouched test is scored once. | Ranked shortlist below; [v1 limitations](../MODEL.md), [disagreement evidence](evaluation/disagreement/REPORT.md), [reserved-race denylist](evaluation/DENYLIST.md). No v2 tag/report yet; v1 remains the historical-mode version. |
| 8. Wet races | Later | A separate causal observed-weather/no-forecast protocol and labelled forecast bounds are evaluated on the predeclared wet cohort without importing future observations. | [Evaluation plan](EVALUATION_PLAN.md), [denylist/release gates](evaluation/DENYLIST.md). Russia 2021, Netherlands 2023 and Canada 2024 remain deferred; no wet evaluation tag/report. |
| 9. Publish and methodology write-up | Last | The methodology, causal exceptions, model limitations, reproducible artifacts and distinct prediction/agreement scores accompany a reviewed public release. | [Model](../MODEL.md), [evaluation plan](EVALUATION_PLAN.md), [held-out score](evaluation/held_out/REPORT.md), [agreement score](evaluation/agreement/REPORT.md), [disagreement report](evaluation/disagreement/REPORT.md). Publication tag/write-up pending. |

Tag links name local repository tags; a GitHub link becomes available only if that tag has been pushed. This document does not publish anything.

## Phase 7: ranked shortlist

1. Consider all legal dry compounds for the immediate BOX option.
2. Save the full field in every state and add a position-aware objective (undercut and cover).
3. Event-driven decision points at SC/VSC onset, not only at lap boundaries.
4. Season-specific tyre priors from the previous season at the same venue.

These are v2 proposals, not changes to the frozen model or to historical v1 playback. Prior-race acquisitions must also respect the reserved-race gate: a reserved race cannot become a prior while v2 is being developed.

## Reserved test races

Proposed dry test cohort, **untouchable until decision-engine v2 is frozen**:

| Race key | Race | Purpose |
| --- | --- | --- |
| `italy_2023` | Italy 2023 (Monza) | A different venue with dry compound and stop decisions. |
| `hungary_2024` | Hungary 2024 (Hungaroring) | A different venue with position-sensitive pit timing. |
| `bahrain_2025` | Bahrain 2025 (Sakhir) | A later season at an already evaluated venue. |

These three races have no recorded acquisition or evaluation in the project's local season caches, evaluation caches or saved report cohorts as inspected on 2026-10-05. This is a repository/cache audit, not a claim about data outside the project. Public event summaries were consulted only to confirm the dry-race proposal; no FastF1 sessions, telemetry, tyre series or labels were acquired. Dry does not mean no SC/VSC.

Event references: [Italy 2023](https://www.formula1.com/en/racing/2023/italy), [Hungary 2024](https://www.formula1.com/en/latest/article/piastri-wins-hungarian-grand-prix-as-norris-belatedly-hands-back-lead-in.70F4mNzYrbmvNYaj8KXm18), [Bahrain 2025](https://www.formula1.com/en/latest/article/piastri-storms-to-controlled-victory-in-bahrain-grand-prix-ahead-of-russell.47YQh0Ex2gkZcx58fRaRqJ).

The [evaluation denylist](evaluation/DENYLIST.md) records their reservation and the existing enforcement boundary. Do not acquire them for development, prior fitting, calibration, map assets or UI demonstrations. A frozen v2 tag is necessary but not sufficient to unlock them: first record the test protocol and obtain explicit authorization for the one held-out acquisition/run. Do not reuse the already scored Spain 2023/Bahrain 2024 cohort as untouched v2 tests.
