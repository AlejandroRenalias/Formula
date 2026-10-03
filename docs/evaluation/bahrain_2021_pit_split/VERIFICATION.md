# Pit allocation verification

163 tests pass with no exclusions, including the committed projection fixture.
All 429 states, conditional subject plans and non-allocation parameters match the
previous uncertainty run exactly; only pit_in_lap_fraction=0.5 is new.
Every parameter source timestamp is <= cutoff. Dataset and source hashes verified.
41 snapshot exclusions and 50 unavailable horizon targets match the previous run.
Total stop loss is conserved per sample; out-lap cost keeps entry-time pricing.
No share fitting or other model changes. Every lap retained; evaluation offline.
