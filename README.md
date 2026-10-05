# Formula Pit Wall

A hybrid deterministic + multi-agent Formula 1 pit-wall strategy system built with Python, FastF1, Pydantic, Plotly, and Streamlit.

> Experimental/educational project. Not affiliated with Formula 1, the FIA, any Formula 1 team, or FastF1.

[Project roadmap](docs/ROADMAP.md) · [Historical mode plan](docs/HISTORICAL_MODE_PLAN.md)

## What it does

Formula Pit Wall combines a deterministic strategy engine with selective LLM reasoning infrastructure. Deterministic Python owns measurable strategy facts and scoring; the LLM layer is constrained to reason over already-computed evidence when the engine flags a close decision.

Core capabilities currently include:

- deterministic candidate generation and scoring;
- explicit factor ownership across Pace & Tyre, Weather, and Race Control specialists;
- semantic candidate IDs and auditable score breakdowns;
- season-aware rules infrastructure;
- structural knowledge cutoffs to prevent future-data leakage;
- FastF1 historical-session ingestion;
- synthetic and scenario-based race inputs;
- end-to-end data provenance (`REAL_FASTF1`, `DERIVED_MODEL`, `SCENARIO_FORECAST`, `USER_DEFINED`);
- Streamlit pit-wall dashboard;
- selective LLM evidence, opinion, and one-round debate contracts using fake providers for tests.

## Architecture

```text
FastF1 / Scenario / Sandbox inputs
                ↓
            Adapters
                ↓
            RaceState
                ↓
  Deterministic specialist models
                ↓
        Chief Strategist
                ↓
        StrategyDecision
                ↓
      conflict_detected?
         ↙           ↘
       no             yes
       ↓               ↓
 deterministic     structured LLM
    result           reasoning
       ↓               ↓
          Streamlit UI
```

### Engineering invariants

- Python calculates deterministic facts and scores.
- LLMs may reason over supplied evidence but must not silently recalculate or invent strategy facts.
- Factor ownership is explicit and non-overlapping.
- The UI is presentation-only.
- Future session data is structurally excluded before calculators run.
- Every important metric retains provenance.

## Quick start

Requires Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the dashboard:

```powershell
streamlit run app.py
```

Run the tests:

```powershell
python -m pytest tests/
```

## Repository layout

```text
app.py                  Streamlit entrypoint
src/adapters/            FastF1, scenarios, and synthetic inputs
src/agents/rules/        Deterministic specialist and Chief logic
src/calculators/         Strategy calculation models
src/core/                Domain models, provenance, triggers, LLM contracts
src/orchestrator/        Deterministic strategy pipeline and conflict detection
src/ui/                  Streamlit dashboard and components
tests/                   Unit, cutoff, and tactical scenario tests
```

## Security and dependency hygiene

- Never commit API keys, tokens, `.env` files, or Streamlit secrets.
- Live LLM credentials are not required by the current fake-provider test architecture.
- CI runs the test suite and `pip-audit` on every push/PR.
- Dependabot checks Python and GitHub Actions dependencies.

See [`SECURITY.md`](SECURITY.md) for the security policy.

## Development status

Active development. The deterministic engine, FastF1/dashboard layer, and selective LLM reasoning/debate infrastructure are implemented; live-model integration and later strategy-resolution/evaluation work remain experimental.
