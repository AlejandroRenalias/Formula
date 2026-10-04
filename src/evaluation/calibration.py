"""Exact green-prefix replay across pace-uncertainty multipliers.

Engine-recorded rival paths are invariant to subject noise before the first
neutralisation. Subject traffic thresholds are recomputed for every candidate.
"""
from math import ceil
import numpy as np


GRID = tuple((a / 4, b / 4) for a in range(4, 17) for b in range(4, 17))
HORIZONS = ('1', '5', '10', 'finish')


def replay_grid(segments, scenario, config, grid=GRID):
    multipliers = np.asarray(grid, dtype=float)
    total = np.zeros(len(grid))
    times = [total.copy()]
    for i, (nominal, loss, rivals) in enumerate(segments):
        noise = scenario.lap_noise_s[i] if scenario.lap_noise_s else 0.0
        pace = nominal + scenario.base_pace_offset_s * multipliers[:, 0]
        pace = pace + noise * multipliers[:, 1]
        traffic = np.zeros(len(grid), dtype=bool)
        for rival_time, rival_pace, rival_loss in rivals:
            gap = total + loss - (rival_time + rival_loss)
            traffic |= (gap > 0) & (gap <= config.traffic_gap_s) & (rival_pace <= pace)
        total += pace + traffic * config.traffic_penalty_s + loss
        times.append(total.copy())
    return np.asarray(times).T


def green_quantiles(paths, target):
    values = np.stack([p[:, target] for p in paths if p.shape[1] > target], axis=1)
    # Dry scenarios have identical weights; reproduce the engine's step quantile.
    indices = [max(0, ceil(q * values.shape[1] - 1e-12) - 1) for q in (.1, .5, .9)]
    return np.sort(values, axis=1)[:, indices]


def objective(quantiles, rows):
    coverage, widths = [], []
    for h in HORIZONS:
        race_coverage, race_width = [], []
        for race in sorted({r['race_key'] for r in rows}):
            idx = [i for i, r in enumerate(rows) if r['race_key'] == race and r['horizon'] == h]
            if not idx:
                continue
            actual = np.asarray([rows[i]['actual_s'] for i in idx])
            low, high = quantiles[:, idx, 0], quantiles[:, idx, 2]
            race_coverage.append(((low <= actual) & (actual <= high)).mean(axis=1))
            race_width.append((high - low).mean(axis=1))
        if not race_coverage:
            raise ValueError(f'Missing calibration horizon: {h}')
        coverage.append(np.mean(race_coverage, axis=0))
        widths.append(np.mean(race_width, axis=0))
    coverage, widths = np.asarray(coverage).T, np.asarray(widths).T
    return np.abs(coverage - .8).mean(axis=1), widths.mean(axis=1), coverage, widths


def select_candidate(quantiles, rows, grid=GRID):
    scores, widths, coverage, per_horizon_width = objective(quantiles, rows)
    selected = min(range(len(grid)), key=lambda i: (scores[i], widths[i], *grid[i]))
    candidates = [{'persistent_multiplier': a, 'lap_noise_multiplier': b,
                   'objective': float(scores[i]), 'mean_width_s': float(widths[i]),
                   'coverage': dict(zip(HORIZONS, coverage[i].tolist())),
                   'width_s': dict(zip(HORIZONS, per_horizon_width[i].tolist()))}
                  for i, (a, b) in enumerate(grid)]
    return selected, candidates
