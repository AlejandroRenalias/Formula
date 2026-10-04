"""Offline same-sample green predictions and new-event calibration; no model fitting."""

import argparse

import hashlib

import json

import time

from pathlib import Path

from src.calculators.projection import ProjectionConfig,Stop

from src.core.models import RaceState

from src.evaluation.snapshot import Snapshot,load_dataset,crossings

from src.evaluation.prediction import ActualPlan,predict

from src.evaluation.diagnostics import metrics,metric_tables

from src.evaluation.offline import network_blocked

from tools.evaluate_bahrain import read_predictions,plots

from tools.report_neutralization_evaluation import RACES

from tools.report_neutralization_views import balanced_metrics

from tools.report_development_evaluation import actual_neutralization



ROOT=Path('docs/evaluation/development_conditional')





def kind(status):

    return 'SC' if str(status)=='4' else 'VSC' if str(status) in {'6','7'} else None





def observed_start(track,cutoff,target):

    previous=None

    for row in sorted(track,key=lambda r:r['Time']):

        current=kind(row['Status'])

        if cutoff<row['Time']<=target and current and current!=previous:

            return True

        previous=current

    return False





def calibration(rows):

    result={}

    for horizon in ('1','5','10','finish'):

        group=[r for r in rows if r['horizon']==horizon]

        if not group:continue

        probability=lambda r:r['neutralization_start_probability']

        outcome=lambda r:r['actual_neutralization_start']

        bins=[]

        for i in range(10):

            selected=[r for r in group if min(9,int(probability(r)*10))==i]

            bins.append({'bin':f'[{i/10:.1f}, {(i+1)/10:.1f}'+(']' if i==9 else ')'),

                'n':len(selected), 'mean_probability':sum(probability(r) for r in selected)/len(selected) if selected else None,

                'observed_frequency':sum(outcome(r) for r in selected)/len(selected) if selected else None,

                'observed_starts':sum(outcome(r) for r in selected)})

        result[horizon]={'n':len(group),'brier_score':sum((probability(r)-outcome(r))**2 for r in group)/len(group),

            'mean_probability':sum(probability(r) for r in group)/len(group),

            'observed_frequency':sum(outcome(r) for r in group)/len(group),

            'observed_starts':sum(outcome(r) for r in group),'reliability':bins}

    return result





def green_rows(rows):

    selected=[]

    for r in rows:

        if not r['green_only_outcome'] or r['green_median_s'] is None:continue

        q=dict(r)

        q.update(p10_s=r['green_p10_s'],median_s=r['green_median_s'],p90_s=r['green_p90_s'])

        q.update(error_s=q['median_s']-q['actual_s'],width_s=q['p90_s']-q['p10_s'],

                 covered=q['p10_s']<=q['actual_s']<=q['p90_s'])

        q['error_per_lap_s']=q['error_s']/q['horizon_laps']

        selected.append(q)

    return selected





def replay(race):

    with network_blocked():

        baseline=Path('docs/evaluation')/f'{race}_future'

        manifest=json.loads((baseline/'manifest.json').read_text())

        dataset=Path(manifest['dataset_path']);data,digest=load_dataset(dataset)

        if digest!=manifest['dataset_sha256']:raise ValueError('Dataset changed')

        for name,expected in manifest['source_sha256'].items():

            if name.startswith('src/calculators/') or name.startswith('src/core/') or name.startswith('data/priors/'):

                if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=expected:raise ValueError('Underlying model changed')

        old=read_predictions(baseline/'predictions.csv')

        grouped={}

        for row in old:grouped.setdefault((row['driver_number'],row['lap']),[]).append(row)

        snapshot_path=Path(manifest['snapshot_path'])

        records=[json.loads(s) for s in snapshot_path.read_text().splitlines()]

        output=ROOT/race;output.mkdir(parents=True,exist_ok=True)

        rows=[];started=time.perf_counter()

        for i,record in enumerate(records):

            snapshot=Snapshot(RaceState.model_validate(record['state']),ProjectionConfig.model_validate(record['config']),record['audit'])

            plan=ActualPlan(tuple(Stop.model_validate(s) for s in record['actual_subject_plan']))

            predictions=predict(snapshot,plan)

            driver,lap=record['driver_number'],record['lap']

            labels=crossings(data,driver);cutoff=record['audit']['cutoff_session_s']

            for row in grouped[(driver,lap)]:

                prediction=predictions[row['target_lap']]

                for k in ('p10_s','median_s','p90_s'):

                    if prediction[k]!=row[k]:raise ValueError(f'Combined prediction changed: {race} {driver} {lap} {k}')

                item={**row,**prediction,

                    'green_only_outcome':row['cutoff_track_status']=='GREEN' and not actual_neutralization(data,row),

                    'actual_neutralization_start':observed_start(data['track_status'],cutoff,labels[row['target_lap']])}

                rows.append(item)

            if (i+1)%50==0:print(race,i+1,'snapshots; combined unchanged',flush=True)

        if len(rows)!=len(old):raise ValueError('Cohort changed')

        (output/'predictions.jsonl').write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows))

        inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (baseline/'predictions.csv',baseline/'manifest.json',snapshot_path,dataset)}

        (output/'manifest.json').write_text(json.dumps({'race':race,'network_blocked':True,'combined_predictions_exactly_equal':True,

            'snapshots':len(records),'predictions':len(rows),'runtime_s':time.perf_counter()-started,'inputs_sha256':inputs,

            'output_sha256':hashlib.sha256((output/'predictions.jsonl').read_bytes()).hexdigest(),

            'sources_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in

                (Path(__file__),Path('src/evaluation/prediction.py'))}},indent=2)+'\n')

        print(race,'complete',flush=True)





def report():

    full={};manifests={}

    with network_blocked():

        for race in RACES:

            root=ROOT/race;m=json.loads((root/'manifest.json').read_text())

            if hashlib.sha256((root/'predictions.jsonl').read_bytes()).hexdigest()!=m['output_sha256']:raise ValueError('Predictions changed')

            if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=d for p,d in m['inputs_sha256'].items()):raise ValueError('Replay inputs changed')

            full[race]=[json.loads(s) for s in (root/'predictions.jsonl').read_text().splitlines()]

            manifests[race]=m

    green={r:green_rows(rows) for r,rows in full.items()}

    pooled=[r for rows in full.values() for r in rows]

    results={'conditional_green':{r:metrics(rows) for r,rows in green.items()},

             'combined':{r:metrics(rows) for r,rows in full.items()},

             'calibration':{r:calibration(rows) for r,rows in full.items()}}

    for view,rows in (('conditional_green',green),('combined',full)):

        results[view]['pooled_prediction']=metrics([r for values in rows.values() for r in values])

        results[view]['pooled_equal_race']=balanced_metrics(rows)

    results['calibration']['pooled_prediction']=calibration(pooled)
    for race in RACES:
        previous=json.loads((Path('docs/evaluation')/f'{race}_future/metrics.json').read_text())
        if results['combined'][race]!=previous:raise ValueError('Combined reference metrics changed')

    lines=['# Same-sample conditional green predictions and neutralization probability','',

        'Bahrain 2021, Spain 2022 and France 2022 only. No model changes, parameter changes, tuning or new races. '

        'All combined median/p10/p90 values reproduce the previous future-risk run exactly. '

        'Predictions come from the same 32 samples per branch and saved snapshots/plans, offline.','',

        '## Definitions','',

        '- **If it stays green:** median/p10/p90 conditional on no SC/VSC active in the projected horizon, using the retained samples and their original weights, renormalized within that subset. '

        'This is not a new all-green simulation or a change to the base pace model. Retained sample count and probability mass are output for every horizon. '

        'If none remain (including known ongoing neutralization inside the horizon), the conditional prediction is unavailable, never replaced by the combined prediction.',

        '- **Green-only outcome:** GREEN at cutoff and no actual SC/VSC through target, matching the existing reporting definition. Yellow cutoffs are excluded. '

        'Actual future status is an outcome-side filter only. Both pit and no-pit horizons remain; signed error is prediction minus actual.',

        '- **New-event probability:** exact marginal probability from the unchanged frozen rates: 1-(1-p_SC-p_VSC)^K, where K is the number of eligible future laps after the known ongoing-event schedule. Until the first new start, event duration cannot affect this probability. The sampled onset fraction is also output separately, without changing any draw. '

        'An already ongoing event does not count as a start. Observed starts use actual status transitions during (exact cutoff time, target crossing time]. '

        'VSC codes 6/7 are one continuous kind; repeated same-kind messages do not count as new starts. '

        'All scored snapshots, including ongoing-event cutoffs, enter calibration. Calibration uses the exact marginal probability; the green quantiles still use the original finite 32-draw subset. Whole-lap simulation and sampling remain unchanged.','',

        '**Three races are far too few to judge calibration.** Driver snapshots and overlapping horizons share the same few race-wide episodes. '

        'The thousands of rows are not independent trials. Brier scores and bin frequencies are descriptive development diagnostics; no calibration fitting is performed. '

        'Empty bins are unavailable. Probability bins are fixed deciles, chosen before viewing results.','',

        '## Dataset and availability','',

        '| Race | Snapshots | Predictions | Green-only outcomes | Conditional available on green outcomes | Unavailable on green outcomes |',

        '| --- | ---: | ---: | ---: | ---: | ---: |']

    for race,rows in full.items():

        eligible=sum(r['green_only_outcome'] for r in rows)

        lines.append(f"| {race} | {manifests[race]['snapshots']} | {len(rows)} | {eligible} | {len(green[race])} | {eligible-len(green[race])} |")

    lines+=['','Exclusions remain those of the previous replay; no new cutoff/target exclusions or stride changes. '

        'France has no eligible green-only finish outcomes. Equal-race pooling normalizes each contributing race, and each pit stratum, separately; missing cells have no weight.']

    for view,title in (('conditional_green','If it stays green, evaluated on green-only outcomes'),('combined','Full combined metrics: unchanged reference')):

        lines+=['',f'# {title}']

        for race,summary in results[view].items():

            lines+=['',f'## {race}','',*metric_tables(summary)]

            if view=='conditional_green' and race=='france_2022':lines+=['','Finish: N=0, unavailable.']

    lines+=['','# Neutralization-start calibration','']

    for race,summaries in results['calibration'].items():

        lines+=['',f'## {race}','',

            '| Horizon | N | Brier score | Mean predicted P | Observed frequency | Observed starts |',

            '| --- | ---: | ---: | ---: | ---: | ---: |']

        for h,m in summaries.items():

            lines.append(f"| {h} | {m['n']} | {m['brier_score']:.5f} | {m['mean_probability']:.3f} | {m['observed_frequency']:.3f} | {m['observed_starts']} |")

        for h,m in summaries.items():

            lines+=['',f'### Reliability: {h}','',

                '| Predicted P bin | N | Mean predicted P | Observed frequency | Observed starts |',

                '| --- | ---: | ---: | ---: | ---: |']

            for b in m['reliability']:

                fmt=lambda v:'—' if v is None else f'{v:.3f}'

                lines.append(f"| {b['bin']} | {b['n']} | {fmt(b['mean_probability'])} | {fmt(b['observed_frequency'])} | {b['observed_starts']} |")

    summary=['## Pooled green-only result','',
        'Prediction-weighted pooling; finish uses Bahrain and Spain because France has no green-only finish outcomes.','',
        '| Horizon | N | MAE s | Bias s | Error/lap s | Coverage | Mean width s | Brier score (all outcomes) |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for h,v in results['conditional_green']['pooled_prediction'].items():
        b=results['calibration']['pooled_prediction'][h]['brier_score']
        summary.append(f"| {h} | {v['n']} | {v['mae_s']:.3f} | {v['bias_s']:+.3f} | {v['mean_error_per_lap_s']:+.3f} | {100*v['coverage']:.1f}% | {v['mean_width_s']:.3f} | {b:.5f} |")
    summary+=['','The conditional pace distribution still under-covers and is too fast on average at longer horizons. '
        'The combined distribution remains unchanged and continues to reflect both worlds. '
        'Three race histories and overlapping snapshots cannot establish calibration.','']
    position=lines.index('## Definitions')
    lines[position:position]=summary
    lines+=['','## Conditional green plots','']
    for race in RACES:
        lines += [f'[{race}: predicted vs actual]({race}/predicted_vs_actual.png) · [error vs horizon]({race}/error_vs_horizon.png)','']
    (ROOT/'metrics.json').write_text(json.dumps(results,indent=2)+'\n')

    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

    for race,rows in green.items():plots(rows,ROOT/race,race+' — if it stays green')



if __name__=='__main__':

    p=argparse.ArgumentParser();p.add_argument('--race',choices=RACES);p.add_argument('--report-only',action='store_true')

    a=p.parse_args()

    if a.race:replay(a.race)

    elif a.report_only:report()

    else:p.error('Choose --race or --report-only')

