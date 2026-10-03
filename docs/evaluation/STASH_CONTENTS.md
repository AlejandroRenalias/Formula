# Preserved work: stash@{0}

Read-only inspection after baseline commit `1597011`; no apply/drop performed.
Stash SHA: `be57e03e13a6c4eef713722bbf4f73cacafeb305`.
25 files; 995 insertions and 85 deletions, plus binary assets.

## Functional work (nine previously tracked files)

- `src/ui/dashboard.py`: Local simulation / Historical FastF1 modes, optional
  local fake-provider specialist/Chief reasoning, visible failure handling, and
  downloadable state + decision JSON.
- `src/adapters/fastf1_adapter.py`: explicit forecast provenance parameter;
  missing/incomplete cutoff weather raises an error rather than inventing values.
- `src/adapters/synthetic_adapter.py` and `src/core/provenance.py`: synthetic
  observations labelled SYNTHETIC; adds that enum value. This addresses the
  committed fixture/enum mismatch currently failing one baseline test.
- `src/core/llm.py`: requested specialist identity and ownership of cited
  evidence enforced at both initial and debate provider boundaries.
- `README.md`: historical loading/cache/forecast instructions, fake-provider
  reasoning and JSON export descriptions, provenance and development status.
  Its old statement that evaluation is not implemented would now need updating.
- `tests/unit/test_adapters.py`, `test_llm.py`,
  `test_provenance_and_presentation.py`: corresponding missing-weather,
  provider-role and synthetic-provenance test updates.

## Previously untracked functional files

- `src/ui/historical.py`: historical session selection, explicit loading,
  session reuse, driver/lap controls and user-defined forecasts.
- `tests/unit/test_dashboard.py`: dashboard historical/simulation interactions,
  export/reasoning and recovery checks.
- `tests/unit/test_specialist_boundary.py`: provider role/evidence ownership
  boundary tests.

## Previously untracked design artifacts (13)

- `design/archivo-rain-zone-preview.png`
- `design/circuit-preview.png`
- `design/decision-type-preview.png`
- `design/field-cars-preview.png`
- `design/final-map-preview.png`
- `design/map-polish-preview.png`
- `design/pitwall-scorer-study.html`
- `design/projection-preview.jpg`
- `design/radio-copy-preview.png`
- `design/rain-atmosphere-preview.png`
- `design/rain-ribbon-preview.png`
- `design/rain-soft-clouds-preview.png`
- `design/synthetic-lap18-output.json`

The stash is substantive prior work, not just generated previews. Applying it
would require reviewing its older README claims against the new evaluation;
dropping it would discard the functional changes and tests as well as previews.
No tests of the combined stash + evaluation tree were run during this inspection.

## Archive completed

The exact requested `git stash branch archive/pre-evaluation-work stash@{0}`
succeeded. All 25 files were committed as-is on that branch at `58ac83f`.
The command dropped the stash after successful restoration; its contents are
now durable in that archive commit. Main retains only the SYNTHETIC enum fix
and a round-trip test, plus a fixture-test compatibility adjustment for the
previous slice's two disabled uncertainty fields. No model predictions or UI
artifacts are changed by this repair.

Worth reviewing for a later slice:

- Missing-weather rejection and explicit forecast provenance in FastF1Adapter.
- Specialist role and evidence ownership checks, with their boundary tests.
- Historical dashboard loading/session reuse, explicit user forecasts, JSON
  export and fake-provider reasoning/error handling, with dashboard tests.
- Accurate SYNTHETIC provenance in SyntheticRaceAdapter and its weather tests.
- Design previews/study for future presentation work; these are not engine fixes.

The archived README predates the evaluation work and needs reconciliation
before adoption. None of those broader features was brought into main here.
