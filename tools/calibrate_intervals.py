"""Offline predeclared grid, exact engine parity, and matched interval reports."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from src.calculators.projection import ProjectionConfig, Stop, sample_scenarios, simulate_policy, _quantile
from src.core.models import RaceState, TrackStatus
from src.evaluation.calibration import GRID, HORIZONS, replay_grid, green_quantiles, select_candidate
from src.evaluation.prediction import ActualPlan
from src.evaluation.offline import network_blocked
from src.evaluation.snapshot import load_dataset
from src.evaluation.diagnostics import metrics
from tools.report_neutralization_views import balanced_metrics

ROOT = Path('docs/evaluation/calibration')
RACES = ('bahrain_2021', 'spain_2022', 'france_2022')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_with_quantiles(row, values):
    row = dict(row)
    low, median, high = map(float, values)
    row.update(p10_s=low, median_s=median, p90_s=high,
               green_p10_s=low, green_median_s=median, green_p90_s=high,
               error_s=median-row['actual_s'], error_per_lap_s=(median-row['actual_s'])/row['horizon_laps'],
               covered=low <= row['actual_s'] <= high, width_s=high-low)
    return row


def summaries(rows):
    races = {race: [r for r in rows if r['race_key'] == race] for race in RACES}
    return {**{race: metrics(r) for race, r in races.items()},
            'pooled_prediction': metrics(rows), 'pooled_equal_race': balanced_metrics(races)}


def run():
    if not (ROOT/'PROTOCOL.md').exists():
        raise ValueError('Protocol must exist before running')
    start = time.perf_counter()
    inputs = {str(ROOT/'PROTOCOL.md'): sha(ROOT/'PROTOCOL.md')}
    snapshots, rows, results = [], [], []
    baseline_checks = corner_checks = 0
    with network_blocked():
        for race in RACES:
            snapshot_path = Path('data/cache/evaluation')/race/'snapshots_parameters_wear.jsonl'
            prediction_path = Path('docs/evaluation/development_parameters_wear')/race/'predictions.jsonl'
            dataset_path = snapshot_path.parent/'session.json'
            load_dataset(dataset_path)  # verifies offline cache integrity
            for p in (snapshot_path, prediction_path, dataset_path): inputs[str(p)] = sha(p)
            records = [json.loads(x) for x in snapshot_path.read_text().splitlines()]
            old_rows = [json.loads(x) for x in prediction_path.read_text().splitlines()]
            grouped = {}
            for r in old_rows:
                if r['green_only_outcome']:
                    grouped.setdefault((r['driver_number'], r['lap']), []).append(r)
            for index, record in enumerate(records):
                scored = grouped.get((record['driver_number'], record['lap']), [])
                if not scored: continue
                state = RaceState.model_validate(record['state'])
                config = ProjectionConfig.model_validate(record['config'])
                assert state.track_status == TrackStatus.GREEN
                assert config.base_pace_uncertainty_multiplier == config.lap_noise_uncertainty_multiplier == 1
                assert not state.observed_weather.rainfall.value and state.weather_forecast.rain_probability.value == 0
                assert all(t <= record['audit']['cutoff_session_s'] for t in record['audit']['parameter_source_session_s'].values())
                plan = ActualPlan(tuple(Stop.model_validate(s) for s in record['actual_subject_plan']))
                scenarios = sample_scenarios(state, config)
                assert len({s.weight for s in scenarios}) == 1
                paths = []
                for s in scenarios:
                    segments = []
                    trace = simulate_policy(state, plan, s, config, fixed_schedule=True, green_segments=segments)
                    paths.append(replay_grid(segments, s, config))
                    np.testing.assert_allclose(paths[-1][0], trace.times[:len(segments)+1], rtol=0, atol=1e-9)
                    baseline_checks += len(segments)
                if index in (0, len(records)//2, len(records)-1):
                    for a, b in ((1,4), (4,1), (4,4), (2.25,3.5)):
                        cell = GRID.index((a,b))
                        changed = config.model_copy(update={'base_pace_uncertainty_multiplier': a,
                                                           'lap_noise_uncertainty_multiplier': b})
                        for s, path in zip(sample_scenarios(state, changed), paths):
                            trace = simulate_policy(state, plan, s, changed, fixed_schedule=True)
                            np.testing.assert_allclose(path[cell], trace.times[:path.shape[1]], rtol=0, atol=1e-9)
                            corner_checks += path.shape[1]-1
                for row in scored:
                    q = green_quantiles(paths, row['horizon_laps'])
                    np.testing.assert_allclose(q[0], [row['green_p10_s'],row['green_median_s'],row['green_p90_s']], rtol=0, atol=1e-9)
                    rows.append(row); results.append(q)
                snapshots.append((state, config, plan, scored))
                if (index+1)%50 == 0: print(race, index+1, 'grid snapshots', flush=True)
            print(race, 'complete', flush=True)
        quantiles = np.stack(results, axis=1)
        selected, candidates = select_candidate(quantiles, rows)
        a, b = GRID[selected]
        # Save selection before verification: a verification failure aborts delivery.
        print('Selected', a, b, candidates[selected], flush=True)
        selected_checks = 0
        offset = 0
        for index, (state, config, plan, scored) in enumerate(snapshots):
            changed = config.model_copy(update={'base_pace_uncertainty_multiplier': a,
                                               'lap_noise_uncertainty_multiplier': b})
            scenarios = sample_scenarios(state, changed)
            traces = []
            prefix_lengths = []
            for s in scenarios:
                segments = []
                traces.append(simulate_policy(state, plan, s, changed, fixed_schedule=True, green_segments=segments))
                prefix_lengths.append(len(segments))
            for row in scored:
                target = row['horizon_laps']
                eligible = [i for i, length in enumerate(prefix_lengths) if length >= target]
                values = [traces[i].times[target] for i in eligible]
                weights = [scenarios[i].weight for i in eligible]
                exact = [_quantile(values,weights,q) for q in (.1,.5,.9)]
                np.testing.assert_allclose(quantiles[selected,offset], exact, rtol=0, atol=1e-9)
                # Report actual engine output rather than rounded/accelerated output.
                quantiles[selected,offset] = exact
                offset += 1; selected_checks += 1
            if (index+1)%100 == 0: print(index+1, 'selected snapshots verified', flush=True)
    before = [row_with_quantiles(r, [r['green_p10_s'],r['green_median_s'],r['green_p90_s']]) for r in rows]
    after = [row_with_quantiles(r, q) for r,q in zip(rows,quantiles[selected])]
    report = {'before': summaries(before), 'after': summaries(after)}
    selection = {'selected': candidates[selected], 'edge_of_grid': a in (1,4) or b in (1,4),
                 'candidate_count': len(GRID), 'prediction_count': len(rows),
                 'snapshot_count': len(snapshots), 'candidates': candidates}
    ROOT.mkdir(exist_ok=True)
    (ROOT/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    (ROOT/'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    (ROOT/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in after))
    cache = Path('data/cache/evaluation/calibration'); cache.mkdir(exist_ok=True)
    np.savez_compressed(cache/'grid_quantiles.npz', quantiles=quantiles)
    manifest = {'network_blocked': True, 'protocol_sha256': sha(ROOT/'PROTOCOL.md'),
                'source_and_inputs_sha256': inputs, 'runtime_s': time.perf_counter()-start,
                'baseline_trace_laps_verified': baseline_checks, 'corner_trace_laps_verified': corner_checks,
                'selected_predictions_verified': selected_checks, 'parity_tolerance_s': 1e-9,
                'grid_quantiles_sha256': sha(cache/'grid_quantiles.npz')}
    for p in (Path(__file__),Path('src/evaluation/calibration.py'),Path('src/calculators/projection.py')):
        manifest['source_and_inputs_sha256'][str(p)] = sha(p)
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    lines = ['# Frozen development interval calibration', '',
        f'Selected persistent offset multiplier **{a:g}**, per-lap noise multiplier **{b:g}** from 169 candidates.',
        f'Objective: {candidates[0]["objective"]:.6f} → {candidates[selected]["objective"]:.6f}; mean horizon width: '
        f'{candidates[0]["mean_width_s"]:.3f} → {candidates[selected]["mean_width_s"]:.3f} s.', '',
        '**Grid boundary selection: '+str(selection['edge_of_grid'])+'**. The grid was not extended.', '',
        '[Predeclared protocol](PROTOCOL.md). [All candidates](selection.json). [Machine-readable metrics](metrics.json).', '',
        f'{len(rows)} matched conditional green predictions from {len(snapshots)} eligible snapshots; '
        f'{manifest["runtime_s"]:.1f} s offline runtime. All 1400 original snapshots were inspected; '
        'only actual green horizons enter calibration. France has no green finish outcomes: finish race pooling has two races.', '',
        'Entries are before → after. Counts are ordinary integer counts; equal-race rates are weighted. '
        '80% interval score is width plus ten times each outside-interval distance (lower is better). '
        'These are in-sample development results after selection, not held-out calibration. '
        'Mean-model coefficients and neutralisation probabilities are unchanged; larger draws can move sample medians and traffic interactions.', '',
        f'Parity: {baseline_checks} baseline trace laps, {corner_checks} corner/interior trace laps, '
        f'and all {selected_checks} selected predictions agreed with ordinary engine simulation within 1e-9 s.']
    for group, summary in report['after'].items():
        lines += ['',f'## {group}', '',
            '| Horizon | Pit group | N | Coverage | Width s | Below p10 | Above p90 | Interval score s |',
            '| --- | --- | ---: | --- | --- | --- | --- | --- |']
        for h, value in summary.items():
            old = report['before'][group][h]
            for label, current, previous in [('all',value,old), *[(k,v,old['by_subject_pit_stop'][k]) for k,v in value['by_subject_pit_stop'].items()]]:
                if not current['n']: continue
                cells = [f'{100*previous["coverage"]:.1f}% → {100*current["coverage"]:.1f}%',
                         f'{previous["mean_width_s"]:.3f} → {current["mean_width_s"]:.3f}']
                cells += [f'{previous[k]} → {current[k]}' for k in ('lower_misses','upper_misses')]
                cells += [f'{previous["interval_score_s"]:.3f} → {current["interval_score_s"]:.3f}']
                lines.append(f'| {h} | {label} | {current["n"]} | '+' | '.join(cells)+' |')
        if group == 'pooled_equal_race':
            lines += ['', '| Horizon | Pit group | Equal-race below p10 rate | Equal-race above p90 rate |',
                      '| --- | --- | --- | --- |']
            for h,value in summary.items():
                old = report['before'][group][h]
                for label,current,previous in [('all',value,old), *[(k,v,old['by_subject_pit_stop'][k]) for k,v in value['by_subject_pit_stop'].items()]]:
                    if current['n']:
                        lines.append(f'| {h} | {label} | {100*previous["lower_miss_rate"]:.1f}% → {100*current["lower_miss_rate"]:.1f}% | '
                                     f'{100*previous["upper_miss_rate"]:.1f}% → {100*current["upper_miss_rate"]:.1f}% |')
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in selection.items() if k!='candidates'},indent=2), flush=True)


if __name__ == '__main__': run()
