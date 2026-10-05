# Evaluation denylist and release gates

Recorded 2026-10-05. Reservations are enforced by [the shared gate](../../tools/reservation_gate.py) and [fail-closed policy](../../data/access/reservations.json). Predictive calculators/profile remain frozen; access wiring is operational.

| Key | FastF1 identity | Gate | Forbidden uses before release |
| --- | --- | --- | --- |
| `italy_2023` | 2023 / Italy / R | Decision-engine v2 frozen, untouched-test protocol committed, explicit run authorization | Acquisition, evaluation, fitting, calibration, prior extraction, UI examples and geometry acquisition from this event. |
| `hungary_2024` | 2024 / Hungary / R | Same v2 gate | Same restrictions, including using this race as a previous-season prior. |
| `bahrain_2025` | 2025 / Bahrain / R | Same v2 gate | Same restrictions. |
| `russia_2021` | 2021 / Russia / R | Wet-phase protocol and explicit authorization | Wet acquisition/evaluation remains deferred. |
| `netherlands_2023` | 2023 / Netherlands / R | Same wet-phase gate | Same wet restriction. |
| `canada_2024` | 2024 / Canada / R | Same wet-phase gate | Same wet restriction. |

## What is enforced today

There was no separately consumed denylist configuration before this document. The current [race guard](../../src/evaluation/races.py) is fail-closed: it authorizes only Bahrain 2021, Spain 2022 and France 2022. The acquisition CLI restricts its race argument to those entries. The separate held-out tool authorizes only Spain 2023 and Bahrain 2024, with a one-run ledger; agreement/report tools name those same five races explicitly. Read-only guard checks confirm the three new reserved identities raise `ValueError`. None was added to an executable allowlist.

The implemented shared gate now also protects the generic FastF1 adapter, acquisition/prior entrypoints and the operational wrapper around cached evaluation loads. It resolves keys, aliases and known round numbers; unknown identities/purposes/sessions and missing/malformed policy fail closed. Geometry permits only pre-race practice/qualifying sessions from evaluated weekends. All identities in a prior batch are checked before cache activation. The unmodified frozen snapshot loader is used behind that wrapper. Direct ad-hoc FastF1 calls outside project entrypoints are not sandboxed by this gate; future tools must use it.

## Required before extending the tools

Every future acquisition/evaluation/prior/geometry entrypoint must use the shared fail-closed gate **before** opening FastF1, the network or a race cache. The current tests cover reserved identities/aliases/rounds, missing/malformed policy, offline reuse, prior batch checking, and helper/adapter bypass attempts. Preserve the frozen source/tag; the gate is outside predictive model code. Reading the reservation policy itself is necessary for authorization and is not race-cache access. No bypass/release flag is supplied.

Already scored held-out races remain closed to model retuning/re-evaluation. Historical mode may read the saved five-race artifacts; that is not a new evaluation. See [roadmap](../ROADMAP.md) and [historical mode plan](../HISTORICAL_MODE_PLAN.md).
