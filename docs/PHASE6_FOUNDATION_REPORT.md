# Phase 6 foundation: gate, per-record export and track geometry

Completed the approved (a)Ã¢â‚¬â€œ(c) slice on 2026-10-05. The historical UI is **not built** and the current page/synthetic fixture is unchanged. Predictive calculators, evaluation state builder, profile, priors and accepted scores remain frozen. No new engine race runs or new test races.

## Verification

- Final full suite: **335 passed in 54.78 seconds**. Commands used the workspace-local test/temp directories under `data/cache`.
- Reservation gate: **75 cases** covering keys, aliases, round numbers, missing/malformed policy, offline cache reuse, unknown identities, pre-race geometry restrictions, direct adapter and mutated-CLI bypass, and prior-batch preflight.
- Export: **7 tests**, including independent parity assertions for **all 2,409 calls**, saved confidence/margins/policies/means, subject/field/weather state, separate outcome joins, future-label poisoning/truncation and schema isolation. Engine/sampler/snapshot functions were patched to fail; networking was blocked. Export itself imports no predictive engine.
- Geometry: **7 tests**, plus the unchanged map suite. All four assets were regenerated from cache under `network_blocked()` with `offline=True`; the shapes were visually inspected in [the review figure](historical/track_geometry_review.png).
- Existing source hashes match the accepted agreement manifest except for the approved two-line adapter authorization guard. The exporter checks that removing only those guard lines restores the accepted adapter bytes (allowing Windows newline normalization). Accepted manifests are not rewritten to hide that change.
- `git diff --check` passed. All output file hashes are sealed in [the export manifest](../static/historical/manifest.json). Policy: [reservations.json](../data/access/reservations.json); gate: [reservation_gate.py](../tools/reservation_gate.py).

The first full-suite run reported two legacy fake-identity failures: `Test GP` is intentionally unauthorized. Those tests now use authorized Bahrain with the same mocked FastF1 behavior. The final full suite passes. Earlier sandbox temporary-directory cleanup noise was avoided by putting Python temporary files inside the workspace.
After normalizing sealed JSON to LF: **89 new foundation tests passed in 10.17 seconds**; all 4,818 per-record JSON files retained identical bytes.


## Static delivery and coverage

The exporter writes one `static/historical/causal/<race>/<driver>/<lap>.json` and one `static/historical/outcomes/<race>/<driver>/<lap>.json` for each saved call, plus a catalog and offline audit manifest. No whole-race download or endpoint is needed. The next UI step configures Streamlit static-file serving and supplies its asset base URL to the iframe; a static host serves the identical directory with a relative base URL. No outcome file is embedded in a causal record. Outcomes are fetched only after Lock plus explicit Reveal when that UI is implemented.

Selector text is **Archive: top-ten finishers from five races, decision-engine v1**. Missing laps use **No archived decision at this cutoff**. The final-result-selected cohort and missing laps (which can hint at a nearby stop) are accepted limitations. Static URLs prevent accidental spoilers, not determined developer-tool inspection. Fetch/lock/reveal browser tests belong to the next UI slice; this report does not claim that unbuilt behavior is tested.

All 2,409 original calls remain exact decision-engine-v1 outputs. Best plan schedules are predictions, never actual future plans. The browser-visible fingerprint covers only whitelisted causal state; original scored snapshot fingerprints, which include actual-plan labels, stay in the offline audit. Gaps retain the approved same-lap live timing proxy exception. Field coverage is unchanged: omitted cars remain omitted, not reconstructed from results.

## Export sizes

Raw files are shipped; gzip figures are deterministic estimates for **each individual file** (`gzip.compress(..., mtime=0)`) summed per race, not shared whole-race compression. Hosts may enable HTTP compression later. MiB = 1,048,576 bytes; KiB = 1,024 bytes. The page fetches just one causal record, then at most its single outcome record.

| Race | Records | Causal JSON MiB | Causal individual-gzip MiB | Outcome JSON KiB | Outcome individual-gzip KiB |
| --- | --- | --- | --- | --- | --- |
| bahrain_2021 | 429 | 3.90 | 0.98 | 355.4 | 200.2 |
| spain_2022 | 542 | 4.94 | 1.24 | 510.0 | 273.2 |
| france_2022 | 429 | 3.93 | 0.98 | 307.2 | 181.1 |
| spain_2023 | 550 | 5.19 | 1.28 | 443.9 | 252.0 |
| bahrain_2024 | 459 | 4.33 | 1.06 | 384.7 | 212.4 |


Total: 4,818 per-record files. Catalog: 3,704 bytes. Offline audit manifest: 487,953 bytes; do not fetch it as the page's outcome-bearing catalog.

## Geometry sources

Only qualifying sessions from already-evaluated weekends were acquired. The gate checked each identity before FastF1/cache access; dates were checked before loading telemetry. No race session was loaded. Barcelona needs a 2023 variant because its final sector differs from 2022. Bahrain 2024 reuses the earlier Bahrain reference. Pit entry/exit markers are configured approximations, not measured pit-lane paths.

| Asset | Year | Session | Reference driver | Lap | Measured distance m | JSON KiB |
| --- | --- | --- | --- | --- | --- | --- |
| [bahrain](../data/tracks/bahrain.json) | 2021 | Q | VER | 14 | 5399.8 | 98.6 |
| [barcelona](../data/tracks/barcelona.json) | 2022 | Q | LEC | 10 | 4636.7 | 95.7 |
| [barcelona_2023](../data/tracks/barcelona_2023.json) | 2023 | Q | VER | 17 | 4638.2 | 97.9 |
| [paul_ricard](../data/tracks/paul_ricard.json) | 2022 | Q | LEC | 16 | 5775.3 | 98.3 |

## One record for review

[Full causal JSON: Bahrain 2021 / HAM / cutoff 11](../static/historical/causal/bahrain_2021/44/11.json) and [its separate outcome JSON](../static/historical/outcomes/bahrain_2021/44/11.json).

| Causal field | Saved value |
| --- | --- |
| Cutoff session seconds | 3435.867 |
| Subject | HAM, P2, MEDIUM, tyre age 14, 0 stops so far |
| Formula call | STAY_OUT |
| Signed BOX minus STAY margin | 5.075066 s |
| STAY / BOX / close model shares | 0.93750 / 0.06250 / 0.00000 |
| Best BOX | box_two_stop_31 |
| Best STAY | wait_to_23 |
| Causal file bytes | 9702 |


Reveal only: the team entered on physical lap **13**, accepted stop boundary **12**, fitted **HARD**. That is within Ã‚Â±1 boundary lap of this selected cutoff, so the pointwise team action is BOX and Formula's STAY disagrees. The missed-stop record tags strategy count; undercut/cover evidence is unknown. This interaction label is separate from the accepted one-to-one episode-start matching. Outcome file: 1,188 bytes. No claim about the better decision.

## Reproduction and next boundary

Run `python -m tools.export_historical --output <empty-directory>` offline with the accepted local caches present; it refuses a nonempty output directory. Geometry replays with `python -m tools.acquire_historical_geometry --track <id> --offline` under network blocking. The exporter verifies source hashes before/after conversion, and unknown/reserved identities cannot be selected. No UI deployment, publication, v2 changes or disagreement outcome-quality analysis is included.
