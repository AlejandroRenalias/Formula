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
