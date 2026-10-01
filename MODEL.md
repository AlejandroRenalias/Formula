# Formula strategy models

## Legacy specialist scorer

The scorer produces dimensionless heuristic points, not predicted race time.
`score_margin` is the winner's score minus the runner-up's score. It replaces
the misleading name `expected_advantage_s`; the JSON contract uses the new name.
Weights remain unchanged. Scorer output is retained for specialist explanations.

Known limitations:

- Green-flag pit loss is available in seconds but contributes zero scoring points.
  STAY receives +1 raw point for preserving track position. SC/VSC rewards are
  fixed points, not a time calculation.
- Rejoin gaps below 1.5s receive -2 traffic points; above 4s receive +1.2
  clean-air points. Between these thresholds, including a P1-to-P3 rejoin at
  3.5s, there is no traffic score. Position loss is not directly scored.
- Rain at probability >=60% and ETA <=2 laps enters an imminent-rain branch.
  ETA >=3 receives the dry baseline despite forecast rain. Dry baseline weather
  is the same offset for all slick/STAY candidates. Pre-emptive intermediates
  receive a fixed reward without simulating their dry-running time cost.
- Compound progress receives +2 raw points only for a new dry compound or a
  wet compound establishing the existing exemption semantics. This remains an
  immediate-compliance heuristic, not a calculation of a later stop's cost.

The separate projection must enforce compound compliance through the finish,
charge stop losses in seconds, and evaluate weather-reactive policies.
