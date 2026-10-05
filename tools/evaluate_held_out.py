"""One authorized held-out run using an immutable calibrated development model."""
import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

from src.calculators.projection import ProjectionConfig, Stop
from src.core.models import RaceState
from src.evaluation.races import DEVELOPMENT_RACES
from src.evaluation.snapshot import Snapshot, ExcludedSnapshot
from tools.evaluation_cache import load_dataset
from src.evaluation.prediction import ActualPlan, predict
from src.evaluation.diagnostics import enrich_rows, metrics, metric_tables
from src.evaluation.breakdown import attach_cutoff_features, no_stop_breakdowns
from src.evaluation.offline import network_blocked
from tools.evaluate_bahrain import evaluate_one, plots
from tools.evaluate_conditional import green_rows
from tools.report_neutralization_views import balanced_metrics
from tools.report_development_evaluation import actual_neutralization

ROOT=Path('docs/evaluation/held_out')
TAG='frozen-development-model-calibrated'
SHA='0878c4d093bf5b2b0e901b17ea8887fa42b7bbe8'
HELD_OUT={'spain_2023':{'year':2023,'race':'Spain','scheduled_laps':66},
          'bahrain_2024':{'year':2024,'race':'Bahrain','scheduled_laps':57}}
MULTIPLIERS={'base_pace_uncertainty_multiplier':3.0,'lap_noise_uncertainty_multiplier':1.0}


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def frozen_files():
    paths=[*Path('src').rglob('*.py'),*Path('data/priors').glob('*.json'),Path('data/evaluation/frozen_model.json')]
    return {str(p):digest(p) for p in paths}


def assert_frozen():
    assert subprocess.check_output(['git','rev-parse',TAG+'^{}'],text=True).strip()==SHA
    subprocess.run(['git','diff','--exit-code',TAG,'--','src','data/priors','data/evaluation/frozen_model.json'],check=True)
    freeze=json.loads(Path('data/evaluation/frozen_model.json').read_text())
    assert freeze['configuration']=='wear' and freeze['pace_uncertainty_multipliers']==MULTIPLIERS
    assert freeze['freeze_tag']==TAG
    return frozen_files()


@contextmanager
def authorized_datasets():
    # User approval expands only the data gate, not frozen predictive behaviour.
    with patch.dict(DEVELOPMENT_RACES,HELD_OUT): yield


def acquire(race,offline=False):
    from tools.acquire_bahrain_evaluation import main
    with authorized_datasets(),patch.object(sys,'argv',['acquire','--race',race]+(['--offline'] if offline else [])):
        main()


def labelled(data,rows,records,race):
    rows=attach_cutoff_features(enrich_rows(data,rows),records,race)
    for r in rows:
        r['green_only_outcome']=r['cutoff_track_status']=='GREEN' and not actual_neutralization(data,r)
    return rows


def validate_record(record):
    assert record['audit']['configuration']=='wear'
    assert all(record['config'][k]==v for k,v in MULTIPLIERS.items())
    assert all(t<=record['audit']['cutoff_session_s'] for t in record['audit']['parameter_source_session_s'].values())


def race_run(race):
    frozen=assert_frozen()
    output=ROOT/race;output.mkdir(parents=True,exist_ok=True)
    ledger=output/'RUN_STARTED.json'
    if ledger.exists(): raise ValueError('One-run ledger already exists; refusing another held-out evaluation')
    ledger.write_text(json.dumps({'race':race,'frozen_tag':TAG,'frozen_sha':SHA,'source_sha256':frozen,
                                 'protocol_sha256':digest(ROOT/'PROTOCOL.md')},indent=2)+'\n')
    start=time.perf_counter()
    with authorized_datasets(),network_blocked():
        dataset=Path('data/cache/evaluation')/race/'session.json'
        data,cache_digest=load_dataset(dataset)
        cohort=sorted((r for r in data['results'] if r['Position'] is not None and 1<=r['Position']<=10),key=lambda r:r['Position'])
        assert len(cohort)==10
        cache={};bench=[]
        def one(driver,lap):
            key=(driver,lap)
            if key not in cache:
                try: cache[key]=evaluate_one(data,driver,lap)
                except ExcludedSnapshot as exc: cache[key]=str(exc)
            return cache[key]
        for subject,initial in zip((cohort[0],cohort[4],cohort[9]),(8,data['scheduled_laps']//3,data['scheduled_laps']-16)):
            for lap in range(initial,data['scheduled_laps']-4):
                t=time.perf_counter();result=one(subject['DriverNumber'],lap)
                if isinstance(result,str): continue
                bench.append(time.perf_counter()-t);break
        assert len(bench)==3
        estimate=statistics.mean(bench)*10*(data['scheduled_laps']-9)
        stride=2 if estimate>1800 else 1
        print(race,'estimated runtime',round(estimate),'s; stride',stride,flush=True)
        rows=[];excluded=[];records=[]
        for subject in cohort:
            driver=subject['DriverNumber']
            for lap in range(5,data['scheduled_laps']-4,stride):
                result=one(driver,lap)
                if isinstance(result,str):
                    excluded.append({'scope':'snapshot','driver':driver,'lap':lap,'reason':result});continue
                scores,exclusions,record=result
                validate_record(record)
                rows.extend(scores);records.append(record)
                excluded.extend({'scope':'target',**e} for e in exclusions)
            print(race,subject['Abbreviation'],len(records),'snapshots',flush=True)
        if not rows: raise ValueError('No valid held-out predictions')
        rows=labelled(data,rows,records,race)
        assert frozen_files()==frozen,'Frozen model changed during held-out evaluation'
        snapshot_path=dataset.with_name('snapshots_held_out.jsonl')
        snapshot_path.write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in records))
        (output/'predictions.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows))
        (output/'exclusions.json').write_text(json.dumps(excluded,indent=2)+'\n')
        manifest={'race':race,'frozen_tag':TAG,'frozen_sha':SHA,'source_sha256':frozen,
                  'dataset_path':str(dataset),'dataset_sha256':cache_digest,'snapshot_path':str(snapshot_path),
                  'snapshot_sha256':digest(snapshot_path),'prediction_sha256':digest(output/'predictions.jsonl'),
                  'subjects':[r['Abbreviation'] for r in cohort],'scheduled_laps':data['scheduled_laps'],
                  'attempted_snapshots':10*len(range(5,data['scheduled_laps']-4,stride)),
                  'snapshots':len(records),'predictions':len(rows),'green_predictions':len(green_rows(rows)),
                  'exclusions':dict(Counter((e['scope']+':'+e['reason']) for e in excluded)),
                  'benchmark_s':bench,'estimated_full_runtime_s':estimate,'lap_stride':stride,
                  'runtime_s':time.perf_counter()-start,'network_blocked':True,
                  'benchmark_predictions_reused':True,'runner_sha256':digest(__file__),
                  'protocol_sha256':digest(ROOT/'PROTOCOL.md')}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        plots(rows,output,race+' full frozen calibrated')
        green_output=output/'green';green_output.mkdir(exist_ok=True)
        plots(green_rows(rows),green_output,race+' conditional green frozen calibrated')
    print(race,'complete',len(rows),'predictions',flush=True)


def development_reference():
    frozen=assert_frozen()
    with network_blocked():
        for race in tuple(DEVELOPMENT_RACES):
            output=ROOT/'development_reference'/race;output.mkdir(parents=True,exist_ok=True)
            if (output/'predictions.jsonl').exists(): raise ValueError('Development reference already saved')
            source=Path('docs/evaluation/development_parameters_wear')/race/'predictions.jsonl'
            snapshot_path=Path('data/cache/evaluation')/race/'snapshots_parameters_wear.jsonl'
            old=[json.loads(s) for s in source.read_text().splitlines()]
            records=[json.loads(s) for s in snapshot_path.read_text().splitlines()]
            grouped={}
            for r in old:grouped.setdefault((r['driver_number'],r['lap']),[]).append(r)
            rows=[];start=time.perf_counter()
            for i,r in enumerate(records):
                config=ProjectionConfig.model_validate(r['config']).model_copy(update=MULTIPLIERS)
                snapshot=Snapshot(RaceState.model_validate(r['state']),config,r['audit'])
                plan=ActualPlan(tuple(Stop.model_validate(s) for s in r['actual_subject_plan']))
                predicted=predict(snapshot,plan)
                for row in grouped[(r['driver_number'],r['lap'])]:
                    q={**row,**predicted[row['target_lap']]}
                    q.update(error_s=q['median_s']-q['actual_s'],width_s=q['p90_s']-q['p10_s'],
                             covered=q['p10_s']<=q['actual_s']<=q['p90_s'])
                    q['error_per_lap_s']=q['error_s']/q['horizon_laps'];rows.append(q)
                if (i+1)%100==0:print(race,i+1,'development reference snapshots',flush=True)
            assert frozen_files()==frozen
            (output/'predictions.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            (output/'manifest.json').write_text(json.dumps({'network_blocked':True,'frozen_sha':SHA,
                'source_sha256':frozen,'input_sha256':{str(p):digest(p) for p in (source,snapshot_path)},
                'runtime_s':time.perf_counter()-start,'saved_mean_model_inputs_reused':True},indent=2)+'\n')
    expected=json.loads(Path('docs/evaluation/calibration/metrics.json').read_text())['after']
    actual=summarize({race:green_rows(read(ROOT/'development_reference'/race/'predictions.jsonl')) for race in DEVELOPMENT_RACES})
    check_metrics(actual,expected)
    print('Development green reference matches accepted calibration',flush=True)


def read(p): return [json.loads(s) for s in Path(p).read_text().splitlines()]


def summarize(per_race):
    return {**{race:metrics(rows) for race,rows in per_race.items()},
            'pooled_prediction':metrics([r for rows in per_race.values() for r in rows]),
            'pooled_equal_race':balanced_metrics(per_race)}


def check_metrics(actual,expected):
    if isinstance(expected,dict):
        for k,v in expected.items(): check_metrics(actual[k],v)
    elif isinstance(expected,(float,int)):
        assert abs(actual-expected)<1e-8,(actual,expected)
    else: assert actual==expected


def report():
    frozen=assert_frozen()
    with authorized_datasets(),network_blocked():
        held={race:read(ROOT/race/'predictions.jsonl') for race in HELD_OUT}
        dev={race:read(ROOT/'development_reference'/race/'predictions.jsonl') for race in ('bahrain_2021','spain_2022','france_2022')}
        manifests={race:json.loads((ROOT/race/'manifest.json').read_text()) for race in HELD_OUT}
        for race,m in manifests.items():
            assert m['source_sha256']==frozen
            assert digest(m['dataset_path'])==m['dataset_sha256']
            assert digest(m['snapshot_path'])==m['snapshot_sha256']
            assert digest(ROOT/race/'predictions.jsonl')==m['prediction_sha256']
        results={name:{'held_out':summarize({race:fn(rows) for race,rows in held.items()}),
                       'development':summarize({race:fn(rows) for race,rows in dev.items()})}
                 for name,fn in (('full',lambda r:r),('conditional_green',green_rows))}
        check_metrics(results['conditional_green']['development'],json.loads(Path('docs/evaluation/calibration/metrics.json').read_text())['after'])
        lines=['# Held-out evaluation: frozen calibrated development model','',
            f'One evaluation of Spain 2023 and Bahrain 2024. Frozen tag `{TAG}`, commit `{SHA}`. '
            'No predictive code, priors, fitting rules or calibration changes. Acquisition was separate; '
            'all evaluation, development-reference replay and reporting ran with networking blocked.','',
            '[Protocol](PROTOCOL.md). [Metrics](metrics.json). [Development comparison](COMPARISON.md).', '',
            'Signed error is median prediction minus actual. Full metrics mix green and sampled SC/VSC outcomes; '
            'conditional green metrics restrict both samples and actual outcomes as in development. '
            'Pools weight either each prediction or each available race equally. Pit strata normalize independently. '
            'Integer miss counts remain unweighted; equal-race rates are separate. Correlated snapshots are not independent observations.', '',
            '| Race | Scheduled laps | Stride | Attempted / valid snapshots | Full / green predictions | Runtime s |',
            '| --- | ---: | ---: | --- | --- | ---: |']
        for race,m in manifests.items():
            lines.append(f"| {race} | {m['scheduled_laps']} | {m['lap_stride']} | {m['attempted_snapshots']} / {m['snapshots']} | {m['predictions']} / {m['green_predictions']} | {m['runtime_s']:.1f} |")
        for race,m in manifests.items():
            lines+=['',f'## Exclusions: {race}','','| Scope / reason | Count |','| --- | ---: |']
            lines += [f'| {key} | {n} |' for key,n in sorted(m['exclusions'].items())]
            if not m['exclusions']: lines += ['| None | 0 |']
        comparison=['# Development versus held-out: same frozen calibrated profile','',
            'Columns are development → held-out. These are different race cohorts, not matched predictions. '
            'Both pooling schemes and pit strata use the existing definitions. France has no green finish outcomes.']
        for view,pools in results.items():
            for race,summary in pools['held_out'].items():
                lines+=['',f'## {view}: {race}','',*metric_tables(summary)]
                if race=='pooled_equal_race':
                    lines+=['','| Horizon | Pit group | Races | Below p10 rate | Above p90 rate |','| --- | --- | ---: | ---: | ---: |']
                    for h,m in summary.items():
                        for label,v in [('all',m),*m['by_subject_pit_stop'].items()]:
                            if v['n']: lines.append(f"| {h} | {label} | {v['contributing_races']} | {100*v['lower_miss_rate']:.1f}% | {100*v['upper_miss_rate']:.1f}% |")
            for pool in ('pooled_prediction','pooled_equal_race'):
                comparison+=['',f'## {view}: {pool}','',
                    '| Horizon | Pit group | N dev / held-out | MAE s | Bias s | Median error s | Error/lap s | Coverage | Width s | Below p10 | Above p90 | Interval score s |',
                    '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
                for h,b in pools['held_out'][pool].items():
                    a=pools['development'][pool][h]
                    for label,c,p in [('all',b,a),*[(k,v,a['by_subject_pit_stop'][k]) for k,v in b['by_subject_pit_stop'].items()]]:
                        if not c['n'] or not p['n']:continue
                        cells=[f"{p[k]:+.3f} → {c[k]:+.3f}" for k in ('mae_s','bias_s','median_error_s','mean_error_per_lap_s')]
                        cells += [f"{100*p['coverage']:.1f}% → {100*c['coverage']:.1f}%",f"{p['mean_width_s']:.3f} → {c['mean_width_s']:.3f}"]
                        cells += [f"{p[k]} → {c[k]}" for k in ('lower_misses','upper_misses')]
                        cells += [f"{p['interval_score_s']:.3f} → {c['interval_score_s']:.3f}"]
                        comparison.append(f"| {h} | {label} | {p['n']} / {c['n']} | "+' | '.join(cells)+' |')
        for race,rows in held.items():
            lines+=['',f'## Five worst full predictions: {race}','',
                    '| Driver | Cutoff | Horizon | Median error s | Actual SC/VSC in horizon | Stop in horizon |',
                    '| --- | ---: | --- | ---: | --- | --- |']
            data,_=load_dataset(Path('data/cache/evaluation')/race/'session.json')
            for r in sorted(rows,key=lambda r:abs(r['error_s']),reverse=True)[:5]:
                lines.append(f"| {r['driver']} | {r['lap']} | {r['horizon']} | {r['error_s']:+.3f} | {actual_neutralization(data,r)} | {r['contains_subject_pit_stop']} |")
            lines+=['','These labels are descriptive, not proof of cause. Pace anchor, wear/cliff and '
                    'pit-transition assumptions can dominate green errors; actual neutralisations can dominate full-view errors.',
                    '',f'![Predicted versus actual]({race}/predicted_vs_actual.png)',
                    '',f'![Error versus horizon]({race}/error_vs_horizon.png)']
        assert frozen_files()==frozen
        (ROOT/'metrics.json').write_text(json.dumps(results,indent=2)+'\n')
        (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        (ROOT/'COMPARISON.md').write_text('\n'.join(comparison)+'\n',encoding='utf-8')
        (ROOT/'manifest.json').write_text(json.dumps({'network_blocked':True,'frozen_tag':TAG,'frozen_sha':SHA,
            'model_files_unchanged':True,'source_sha256':frozen,'runner_sha256':digest(__file__),
            'development_green_matches_accepted_calibration':True,'held_out_manifests':manifests},indent=2)+'\n')
        (ROOT/'no_stop_breakdowns.json').write_text(json.dumps({race:no_stop_breakdowns(green_rows(rows)) for race,rows in held.items()},indent=2)+'\n')
    print(json.dumps({view:p['held_out']['pooled_equal_race'] for view,p in results.items()},indent=2))


def main():
    p=argparse.ArgumentParser();p.add_argument('operation',choices=('acquire','race','development-reference','report'))
    p.add_argument('--race',choices=tuple(HELD_OUT));p.add_argument('--offline',action='store_true');a=p.parse_args()
    try:
        if a.operation=='acquire':
            if not a.race:p.error('--race required')
            assert_frozen();acquire(a.race,a.offline)
        elif a.operation=='race':
            if not a.race:p.error('--race required')
            race_run(a.race)
        elif a.operation=='development-reference':development_reference()
        else:report()
    except Exception as exc:
        ROOT.mkdir(parents=True,exist_ok=True)
        (ROOT/'FAILURE.md').write_text(f'# Held-out operation stopped\n\nOperation: {a.operation}; race: {a.race}.\n\n{type(exc).__name__}: {exc}\n\nNo model fix or held-out rerun performed.\n')
        raise


if __name__=='__main__':main()
