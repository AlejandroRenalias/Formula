# Phase 6: historical mode plan

Approved foundation slice: reservation gate, offline export and track assets only. UI implementation remains pending review. Keep the pit-wall design, typography and layout. Historical mode presents **decision-engine-v1 exactly as scored**, using saved artifacts for Bahrain 2021, Spain 2022, France 2022, Spain 2023 and Bahrain 2024. There are 2,409 saved calls (429 / 542 / 429 / 550 / 459). No engine execution, new race evaluation, changed candidate set, tuning or simulated user strategy is involved.

Source version: [decision-engine-v1](https://github.com/AlejandroRenalias/Formula/tree/decision-engine-v1), commit `18e1bb0b093b4f7e175af8e962702737b8676a8e`. Prediction profile: [frozen-development-model-calibrated](https://github.com/AlejandroRenalias/Formula/tree/frozen-development-model-calibrated), `0878c4d093bf5b2b0e901b17ea8887fa42b7bbe8`. Source contracts: [agreement plan](evaluation/AGREEMENT_PLAN.md), [agreement score](evaluation/agreement/REPORT.md), [disagreement protocol](evaluation/disagreement/PROTOCOL.md).

The current [Streamlit wrapper](../src/ui/projection_dashboard.py) embeds the [pit-wall document](../design/pitwall-concept.html), CSS, JavaScript and a synthetic fixture into an iframe. Extend this same presentation path, not the legacy live-data/engine path. Delivery is **per-record static files**, with no endpoint and no whole-race download. The page fetches only the selected causal JSON and fetches its separate outcome JSON only after Lock and an explicit Reveal. Use Streamlit's static-file serving for the archive and geometry, with a wrapper-supplied asset base URL; on a static host use the same files and a relative base URL. This wiring is for the next UI slice. Files and predictable URLs prevent accidental screen spoilers, not a determined user using developer tools or directly fetching outcomes.

## Data contract and source joins

Asset layout under `static/historical/`, suitable for Streamlit static serving and later static hosting:

| File | Contents | Load rule |
| --- | --- | --- |
| `catalog.json` | Schema version; five race identities, circuit IDs, scheduled lap counts, archived top-ten cohort in alphabetical order and engine version. No results, finish ranks, actual strategies or available-future-lap summaries. | Choosing state. |
| `causal/<race>/<driver>/<lap>.json` | One whitelisted saved decision/state record per key. | Fetch only the selected file. |
| `outcomes/<race>/<driver>/<lap>.json` | One separate reveal label with fitted compound, accepted matching IDs, flags and relevant tags. No predictive inputs. | Explicit Reveal action only, after a call is locked. Never prefetch. |
| `manifest.json` | Source/asset hashes, schema, row counts, exporter version and frozen tags. No scenario outcomes. | Build validation; show version/hash only. |

All joins use `(race_key, driver_number, lap)`; no rounded clock join. Exact session cutoff seconds remain numeric. Snapshot epoch timestamps are an encoding of session-relative time, not wall UTC. Keep full numeric precision in assets; display rounded values without changing the saved call or ranking.

Each causal record contains:

| Field | Source and meaning |
| --- | --- |
| `id`, `race_key`, `driver_number`, `lap`, `cutoff_session_s`, `phase` | Saved `calls.jsonl`; phase buckets remain 5–14, 15–29, 30+. |
| `call` | Exact saved `BOX_NOW` or `STAY_OUT`; UI labels BOX / STAY. |
| `margin_s`, `box_minus_stay_s` | Saved absolute `call_margin_s`; signed difference of saved best BOX and STAY mean times. Positive signed margin favours STAY. Validate absolute parity. |
| `confidence` | Saved STAY-clearly-better, BOX-clearly-better and too-close shares plus 1-second tolerance. These are model sample shares, not probability of correctness. |
| `recommended_policy_id`, `best_box`, `best_stay` | Join saved best-policy IDs to `raw_calls.jsonl.gz`; retain policy ID, label, nominal scheduled boundary/compound pairs, reactive flag, stop cap, saved mean-to-finish and invalid share. Any representative stops are explicitly **modelled**, never team outcomes. No trajectories or actual-plan replay included. |
| `stay_to_finish_available`, `stay_to_finish_selected` | Saved availability and `recommended == stay_to_finish`; legal no-stop option means zero scheduled/reactive stops. |
| `subject` | Saved causal snapshot: abbreviation, team, position, compound, tyre age, stop count so far, used compounds, last observed lap time. Tyre age is not assumed to equal fresh-stint length. |
| `field` | Subject plus saved competitors: driver identity, saved position, compound/age, signed gap to subject, last observed lap, in-pit flag, stops so far. Preserve saved order/positions; do not replace them with corrected future classifications. |
| `track_status`, `observed_weather`, `forecast_mode` | Saved cutoff observations; dry no-forecast persistence. SC/VSC onset/remaining-duration annotations only if present in the cutoff audit. |
| `provenance` | Snapshot hash; parameter source timestamps; latest weather/status sources; each gap's approved `live_timing_proxy_same_lap_crossing` basis and exception flag; omitted-rival markers. Detailed wear/pit counts and fallbacks may live in a separate causal audit asset if needed. |
| `reliability_note_id` | Deterministic rule below, using only current lap/status and saved confidence; never the selected snapshot's actual future. |

Source snapshots are the accepted `snapshots_parameters_wear.jsonl` (development) and `snapshots_held_out.jsonl` (held-out), hash-checked against saved manifests. Slim calls alone lack plan schedules and subject/field details: read saved raw calls and snapshots, not FastF1 or the engine. Explicitly exclude `actual_subject_plan`, `actual_tyres`, results, prediction actuals/errors, actual future neutralisation, directional outcome strata, matching results and disagreement tags from causal records.

### Outcome record

Store physical `stop_id`, accepted boundary lap, physical pit-entry/out-lap numbers when known, exact entry/exit seconds, fitted compound and data quality. The display must distinguish “after boundary lap N” from “pit entry on physical lap N+1”; do not relabel the accepted coordinate silently. Exclude after-finish garage visits using the accepted finish boundary.

For each playable snapshot, derive the reveal label without engine execution. Outcome schema v2 stores `team_action_this_lap`: BOX exactly when a physical team's stop boundary equals the selected cutoff lap; STAY otherwise. `team_stop_this_lap` supplies that stop's details. `next_team_stop` is the first entry strictly after the cutoff with signed `laps_from_cutoff`, or null. The headline and session tally use this exact pointwise action. HAM, Bahrain 2021, cutoff 11 is STAY, agreeing with Formula; his next stop is boundary 12 (+1), physical entry lap 13, HARD.

`near_miss` follows the requested flag: Formula differs from this lap's action and a team stop boundary is within one lap (including the boundary itself). `near_miss_stop` identifies a nonzero one-lap neighbour, including an earlier stop. Only that neighbour produces the wording “Close: the team boxed one lap later” or “earlier”; an exact missed BOX has no earlier/later note. Missing labels fail closed rather than guessing.

The accepted episode-start one-to-one matching within +/-1 lap stays unchanged, in `accepted_episode` and `accepted_episode_match`. It remains a separate linked evaluation reference; pointwise agreement is not precision/recall. No rematching, new engine run or altered score.

Attach saved tags to their actual unmatched event ID. A missed stop can carry overlapping tags and unknowns; a matched stop has “no unmatched-stop classification”, not “no possible tactical explanation”. FP context can be a different stop ±10 laps away: show its distance and provenance separately, never present those tags as the revealed stop's own tags. No claim about who was right.

## Screen states and session tally

| State | Screen and permitted action | Data boundary |
| --- | --- | --- |
| Choosing | Keep synthetic mode available. Selector label: **Archive: top-ten finishers from five races, decision-engine v1**. Use fixed scheduled lap range 5 through scheduled laps minus 5; no future event markers or finish-order driver sorting. | Static catalog only. |
| Call shown | Render the saved Formula call, confidence shares, margin, best BOX/STAY plans, causal field/map, tyre/stop-so-far state and reliability note. User chooses BOX or STAY; Reveal disabled. Unavailable cutoff shows “No archived decision at this cutoff”, without revealing a future stop/exclusion reason. | Requested causal record only. |
| Call locked | Freeze the selected snapshot and user's call. Display the choice and enable Reveal; do not load outcomes yet. Changing race/driver/lap starts a new attempt and clears the lock/reveal; no silent change to a locked attempt. | Same causal record, session-local choice. |
| Revealed | Explicitly load that snapshot's outcome label. Show this-lap team action, next stop boundary and compound, pointwise agreement, near-miss note and relevant tags/unknowns. Link the unchanged episode matching as a separate reference. Evaluation report links become available here because the reports themselves contain outcomes. Offer another lap. | Outcomes allowed only for this revealed attempt. |

Use `sessionStorage` for a simple per-tab tally: attempts revealed, user agreements / scorable attempts, Formula pointwise agreements / scorable attempts. Label it “agreement with the team”, never “correct decisions” or wins. Each snapshot increments once per session; repeated reveal does not score twice. Preserve the locked first answer for that attempt, provide an explicit reset, and never submit a user call to an engine or server for simulation.

No historical widget may retain the synthetic fixture's future rain, crossover, actual strategy, radio text or scenario positions. Preserve the styling while populating only supported saved causal fields; omit unsupported radio/weather-forecast content with a neutral “not archived” label. The synthetic mode retains its existing content and behavior.

## Reliability note: fixed presentation rule

Use cautious wording rather than “good” or “reliable” as a universal claim. The [held-out comparison](evaluation/held_out/COMPARISON.md) reports equal-race conditional-green 10-lap MAE 4.509 s and coverage 75.2% (development 3.897 s / 80.1%); finish MAE 20.926 s / coverage 67.6%. Stop-containing green finish MAE is 29.234 s, and one-lap stop coverage only 20%. The [finish diagnostic](evaluation/held_out_finish_diagnostic/REPORT.md) shows early/middle/late stop-containing finish mean errors +44.027 / +24.521 / +2.580 s. These are retrospective cohort results, not per-snapshot guarantees or proofs about box timing.

Apply this fixed rule, with no optimization or new thresholds:

1. Always show “Experimental model. Timing agreement is limited; confidence is model agreement, not accuracy.” Prediction skill and BOX timing are different evaluations.
2. Green cutoff, lap 5–14: “Early-race finish projections have large errors. Shorter-horizon green predictions performed better in evaluation.” Lap 15–29: “Finish projections remain uncertain, especially across stops.” Lap 30+: “Shorter remaining distance; pit-transition and compound limitations still apply.” These use the existing phase buckets, not an actual future stop label.
3. Non-green cutoff: replace the phase performance reassurance with “Neutralisation duration is uncertain; green-only scores do not validate this state.” Never select this message based on a future SC/VSC.
4. Append the exact confidence shares. Reuse the disagreement report's **descriptive** labels: saved chosen-side clearly-better share ≥0.8 means “strong model preference”; otherwise close share ≥0.5 means “close in the model”; otherwise “mixed model samples”. Do not convert these shares to a correctness score. No new confidence tuning.
5. Optional small factual caption: “Green 10-lap coverage: development 80%, held-out 75%; target 80%.” This is a static global reference, not a label that the selected horizon actually remained green. Detailed outcome-bearing reports open only after reveal.

## Map and track assets

Assets `data/tracks/bahrain.json`, `barcelona.json`, `barcelona_2023.json` and `paul_ricard.json` use the existing [Silverstone schema](../data/tracks/silverstone.json) and [map interpolation](../design/assets/circuit-map.js): normalized polyline, cumulative distance, sectors, finish line, approximate pit entry/exit and provenance. Barcelona has separate 2022/2023 layouts; the catalog selects the correct variant. Geometry is an immutable reference asset, not race outcome data. Sources are qualifying from Bahrain 2021, Spain 2022, Spain 2023 and France 2022, checked before race start through the gate. No reserved races, race sessions or engine runs. Pit markers are configured approximations, not measured pit-lane paths. Assets replay from local cache offline.

At the selected subject boundary, anchor the subject at the finish line. Put competitors on a **schematic** distance map from the saved signed gaps using a reference time profile scaled by causal pace, not a future race lap. Saved gap convention: positive means competitor ahead; leader-relative gap = largest saved gap minus car gap when a gap-consistent leader exists. Preserve saved positions if order/gap disagree; flag the schematic approximation rather than correcting it using future data. Lapped offsets and unknown geometry/pit position remain labelled approximate; no invented exact telemetry. Static shape is permissible, but the dynamic profile scale cannot depend on the selected race's future pace.

Display only cars actually in the saved snapshot; show the observed field count and omissions. Do not fabricate the full field, resurrect a retired car from final results, use actual rejoin positions or animate future outcomes. If no leader-consistent field is available, keep subject-relative positioning. Optional rejoin ghost may use only saved causal pit-loss/traffic estimates, with “modelled” label; defer it if these values cannot be exported exactly.

## Leakage and parity tests planned for implementation

- Hash-verify all accepted source artifacts; conversion imports no engine/sampler/snapshot builder and runs with network blocked. Patch those operations to raise if invoked. Reserved identities remain unavailable.
- Whitelist causal schema fields. Assert parameter/observation timestamps ≤ cutoff; retain the **only** approved same-lap live-gap proxy exception explicitly. Mutating future outcome labels, tyres, positions, times and SC/VSC must leave the causal record, reliability note, DOM and map identical. Modelled future plans remain permitted predictions.
- Treat all outcomes as a separate module/file: before reveal, no request, cache read, payload join, hidden DOM, tooltip, accessibility text, URL parameter, telemetry log or tally may contain outcomes. Test choosing, shown and locked states with outcome requests blocked. Load outcomes only after lock plus explicit Reveal.
- Inspect network payloads to ensure only the selected causal file is requested, with no outcome request before lock plus Reveal. This static-file boundary prevents accidental spoilers, not determined inspection; later records and outcome URLs remain directly fetchable. No server endpoint is planned.
- Randomize/corrupt future causal rows: selected-lap screen must not change. No future driver-ordering, lap-availability heatmap, pit markers, radio or synthetic rain overlays. Switching selection resets locked/revealed state and clears outcome-derived UI.
- Verify all 2,409 exported calls, confidence shares, margins, best-policy IDs and plan schedules against saved calls/raw plans; no numerical reconstruction beyond signed subtraction and display rounding. Render unavailable cutoffs without fallback to another lap or a fresh engine call.
- Test lock immutability, missing labels, straddling/partially observable windows, repeated alert episodes, prior observed stops and FP context provenance. Tally updates exactly once per scorable revealed snapshot; no correctness claims.
- Verify field placement against saved gaps and approximate lap offsets on all three circuits. Desktop/mobile screenshots must preserve typography/layout and synthetic-mode behavior. Geometry, fonts and replay must work offline.

## Size estimates and archive limitations

The original read-only in-memory serialization probe joined saved calls, raw best plans and causal snapshots; it wrote no website exports and ran no engine. Numbers below describe that original whole-race sizing probe, not delivered per-record files. The implemented per-record export sizes and compression overhead are reported in [foundation report](PHASE6_FOUNDATION_REPORT.md). Whole-race archives are not served.

| Race | Records | Causal JSON KiB | Causal gzip KiB | Existing ±1 audit-only outcome JSON / gzip KiB |
| --- | ---: | ---: | ---: | ---: |
| Bahrain 2021 | 429 | 3,597.2 | 302.9 | 5.2 / 0.6 |
| Spain 2022 | 542 | 4,544.6 | 385.9 | 7.9 / 0.9 |
| France 2022 | 429 | 3,590.7 | 287.2 | 2.9 / 0.4 |
| Spain 2023 | 550 | 4,911.3 | 413.8 | 7.3 / 0.8 |
| Bahrain 2024 | 459 | 4,042.4 | 334.8 | 8.4 / 0.8 |

Audit-only outcomes are a measured lower bound, not the final reveal contract: compounds, per-snapshot labels and slim tag evidence will add bytes. Budget approximately 100 KiB uncompressed / 15 KiB gzipped per race for that separate file, then measure the actual export. Catalog, circuit geometry and optional detailed causal audits are extra; geometry sizes cannot be known until assets exist. Fetch one race/record at a time; do not bundle raw multi-megabyte scenario trajectories or all case-card evidence into the page.

Fields unavailable or incomplete in saved **calls alone**, and their handling:

- Subject/team/tyre details, weather, field order and gaps: join accepted causal snapshots. Their saved fields contain 17–20 cars depending on race/cutoff (Bahrain 2021 only 17–19), not a guaranteed complete field. Do not fill gaps from post-cutoff classification.
- Best BOX/STAY schedules and legality details: join saved raw plans. The immediate candidate limitation remains HARD or MEDIUM while on HARD; show it, do not expand choices for Formula. The browser-visible causal fingerprint hashes only whitelisted causal state, not the original scored snapshot hash (which also contains the actual future plan); original hashes stay in the offline audit manifest.
- Exact car distance, GPS, pit-lane progress and authoritative leader-relative lapped gaps: absent; use labelled schematic geometry/gap placement.
- Explicit stint ID/start time/fresh-versus-used tyre-set identity: not consistently supplied as a compact snapshot field. Show compound, saved tyre age, used compounds and stops so far; do not claim age equals laps since a fresh set was fitted.
- Live forecast, team intent/radio, real-time undercut assessment, full-wrapper specialist prose and sensitivity flips: not archived by the call-only run. No fabricated historical commentary.
- Complete driver/lap coverage: only the original top-ten-finisher cohort was scored; show that explicitly in the selector without final ranks. Excluded cutoffs have no calls and show **No archived decision at this cutoff**. An unavailable lap can hint at a nearby stop; generic text cannot remove that inference. Both limitations are accepted for phase 6, with no new runs. Do not claim absolute spoiler isolation.
- Per-stop fitted compounds and tags: not in causal calls; obtain only from saved outcome channels/cache and disagreement events, behind reveal. A matched stop has no unmatched-stop tag record.

## Implementation order after review

Implement the reservation gate and tests first; then the pure offline exporter and parity/leakage tests; then geometry from pre-race sessions of the already evaluated weekends through that gate. Stop after those three foundations. The next slice adds the four-state interaction, static fetching and tally within the existing design, then verifies desktop/mobile rendering, outcome isolation and synthetic parity. Predictive calculators/profile remain unchanged; the adapter's access guard is a documented operational source change, not a new engine score.


## Implementation review

The pointwise schema fix and historical UI are implemented; see [UI report and all four desktop/mobile states](historical_ui/REPORT.md). Streamlit enables static serving in `.streamlit/config.toml` and embeds the same playback script with `/app/static/` as its asset base (including a configured server path prefix). The ordinary static page resolves `../static/`. Methodology and exact report copies are linked only after Reveal. Synthetic JS/CSS and fixture content are unchanged. No model reruns, acquisition or publication.


## Accepted foundation and UX order

The initial historical mode and exact pointwise reveal were accepted. The subsequent [UX review](historical_ux/REPORT.md) supersedes the display order above: default is situation and user choice, Lock shows Formula, Reveal shows the team. An explicit Formula-first toggle retains the earlier order and has a separate session tally. This is presentation only; per-record causal/outcome JSON, scored artifacts and the frozen engine are unchanged.
