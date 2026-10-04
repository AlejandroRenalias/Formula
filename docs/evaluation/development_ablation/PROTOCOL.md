# Final ablation protocol

Predeclared before candidate replays. A retains joint fitted trend in the
regression/causal historical anchor, but uses fixed fuel (-0.05 s/lap) after the
cutoff. B fits wear and offsets with the fixed fuel correction and projects it.
All prior strengths, samples, noise sizing, pit and neutralisation assumptions
are unchanged. Same three cached development races; no held-out/wet races.

Candidates are compared to pit+wear (02341a7) and offsets (e6270ef). Report all
horizons, per race, per prediction/equal race, pit/no-pit and compound/age groups.

Bias gate: per-prediction pooled green finish absolute mean bias must be at most
2.3433399051303514 s, the magnitude of pit+wear's stored bias. Among passing A/B and pit+wear,
a candidate must have minimum equal-race green MAE at BOTH 10 laps and finish.
If horizon winners differ, keep pit+wear. No weighting introduced after results.
The signed interpretation (bias >= baseline bias) is also reported as an audit,
not an alternative metric chosen after outcomes. Exact ties retain pit+wear when
it is a joint minimum, otherwise A precedes B.

Tag name: frozen-development-model. Freeze records the selected profile, exact
selection inputs and hashes. Model selection uses development outcomes only;
each replay snapshot and parameter estimate remains cutoff-safe.
