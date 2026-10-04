"""Matched offline development evaluation for causal pit and wear parameter slices."""
import argparse,hashlib,json,time
from pathlib import Path
from src.calculators.projection import Stop
from src.evaluation.snapshot import build_snapshot,load_dataset
from src.evaluation.prediction import ActualPlan,predict
from src.evaluation.diagnostics import metrics,metric_tables
from src.evaluation.breakdown import no_stop_breakdowns
from src.evaluation.offline import network_blocked
from tools.evaluate_conditional import RACES,green_rows
from tools.report_neutralization_views import balanced_metrics
from tools.evaluate_bahrain import plots


def root(stage):return Path('docs/evaluation')/f'development_parameters_{stage}'
def previous_root(stage):return Path('docs/evaluation/development_conditional') if stage=='pit' else root({'wear':'pit','trend':'wear','offsets':'trend','ablation_a':'offsets','ablation_b':'offsets'}[stage])


def run(stage,race):
    output=root(stage)/race;output.mkdir(parents=True,exist_ok=True)
    previous=previous_root(stage)/race
    old=[json.loads(s) for s in (previous/'predictions.jsonl').read_text().splitlines()]
    if stage=='pit':
        old_manifest=json.loads((previous/'manifest.json').read_text())
        snapshot_path=next(Path(p) for p in old_manifest['inputs_sha256'] if 'snapshots_' in p)
        dataset=next(Path(p) for p in old_manifest['inputs_sha256'] if p.endswith('session.json'))
    else:
        old_manifest=json.loads((previous/'manifest.json').read_text())
        snapshot_path=Path(old_manifest['snapshot_path']);dataset=Path(old_manifest['dataset_path'])
    records=[json.loads(s) for s in snapshot_path.read_text().splitlines()]
    grouped={}
    for r in old:grouped.setdefault((r['driver_number'],r['lap']),[]).append(r)
    rows=[];snapshots=[]
    with network_blocked():
        data,digest=load_dataset(dataset)
        def one(record):
            driver,lap=record['driver_number'],record['lap']
            snapshot=build_snapshot(data,driver,lap,cutoff_s=record['audit']['cutoff_session_s'],configuration=stage)
            plan=ActualPlan(tuple(Stop.model_validate(s) for s in record['actual_subject_plan']))
            predictions=predict(snapshot,plan)
            result=[]
            for old_row in grouped[(driver,lap)]:
                q={**old_row,**predictions[old_row['target_lap']]}
                q.update(error_s=q['median_s']-q['actual_s'],width_s=q['p90_s']-q['p10_s'],
                         covered=q['p10_s']<=q['actual_s']<=q['p90_s'])
                q['error_per_lap_s']=q['error_s']/q['horizon_laps']
                result.append(q)
            record={**record,'state':snapshot.state.model_dump(mode='json'),
                    'config':snapshot.config.model_dump(mode='json'),'audit':snapshot.audit}
            if any(t>snapshot.audit['cutoff_session_s'] for t in snapshot.audit['parameter_source_session_s'].values()):raise ValueError('Future parameter source')
            return result,record
        benchmark=[]
        for i in (0,len(records)//2,len(records)-1):
            start=time.perf_counter();one(records[i]);benchmark.append(time.perf_counter()-start)
        estimate=sum(benchmark)/len(benchmark)*len(records)
        print(race,'estimated runtime',round(estimate),'s; same every-lap cohort',flush=True)
        started=time.perf_counter()
        for i,record in enumerate(records):
            scores,snapshot=one(record);rows.extend(scores);snapshots.append(snapshot)
            if (i+1)%50==0:print(race,i+1,'snapshots',flush=True)
        snapshot_output=dataset.with_name(f'snapshots_parameters_{stage}.jsonl')
        snapshot_output.write_text(''.join(json.dumps(s,allow_nan=False)+'\n' for s in snapshots),encoding='utf-8')
        (output/'predictions.jsonl').write_text(''.join(json.dumps(s,allow_nan=False)+'\n' for s in rows),encoding='utf-8')
        sources=[*Path('src/evaluation').glob('*.py'),*Path('src/calculators').glob('*.py'),
                 *Path('data/priors').glob('*.json'),Path(__file__)]
        manifest={'stage':stage,'race':race,'network_blocked':True,'dataset_path':str(dataset),'dataset_sha256':digest,
            'snapshot_path':str(snapshot_output),'snapshot_sha256':hashlib.sha256(snapshot_output.read_bytes()).hexdigest(),
            'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'benchmark_s':benchmark,'estimated_runtime_s':estimate,'runtime_s':time.perf_counter()-started,
            'snapshots':len(snapshots),'predictions':len(rows),'previous':str(previous),
            'previous_predictions_sha256':hashlib.sha256((previous/'predictions.jsonl').read_bytes()).hexdigest()}
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(race,'complete',flush=True)


def comparison(current,previous):
    lines=['| Horizon | Pit group | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s |',
           '| --- | --- | ---: | --- | --- | --- | --- | --- | --- |']
    for h,v in current.items():
        for group in ('all','without_stop','with_stop'):
            a=previous[h] if group=='all' else previous[h]['by_subject_pit_stop'][group]
            b=v if group=='all' else v['by_subject_pit_stop'][group]
            if a['n']!=b['n']:raise ValueError('Conditional comparison cohort changed')
            if not b['n']:continue
            cells=[f"{a[k]:+.3f} -> {b[k]:+.3f}" for k in ('bias_s','median_error_s','mae_s','mean_error_per_lap_s')]
            cells += [f"{100*a['coverage']:.1f}% -> {100*b['coverage']:.1f}%",f"{a['mean_width_s']:.3f} -> {b['mean_width_s']:.3f}"]
            lines.append(f"| {h} | {group} | {b['n']} | "+' | '.join(cells)+' |')
    return lines


def breakdown_compare(before,after):
    index={(r['horizon'],r['dimension'],r['group']):r for r in before}
    lines=['| Horizon | Dimension | Cutoff group | N | Mean error/lap s | Median error/lap s | MAE/lap s |',
           '| --- | --- | --- | ---: | --- | --- | --- |']
    for b in after:
        if b['horizon'] not in ('10','finish') or b['dimension']=='track_status':continue
        a=index[(b['horizon'],b['dimension'],b['group'])]
        if a['n']!=b['n']:raise ValueError('Breakdown cohort changed')
        cells=[f"{a[k]:+.3f} -> {b[k]:+.3f}" for k in ('mean_error_per_lap_s','median_error_per_lap_s','mae_per_lap_s')]
        lines.append(f"| {b['horizon']} | {b['dimension']} | {b['group']} | {b['n']} | "+' | '.join(cells)+' |')
    return lines


def report(stage):
    output=root(stage);current={};previous={};manifests={};breakdowns={}
    with network_blocked():
        for race in RACES:
            manifest=json.loads((output/race/'manifest.json').read_text())
            if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=d for p,d in manifest['source_sha256'].items()):raise ValueError('Model changed since run')
            records=[json.loads(s) for s in Path(manifest['snapshot_path']).read_text().splitlines()]
            if any(t>r['audit']['cutoff_session_s'] for r in records for t in r['audit']['parameter_source_session_s'].values()):raise ValueError('Future source')
            current[race]=green_rows([json.loads(s) for s in (output/race/'predictions.jsonl').read_text().splitlines()])
            previous[race]=green_rows([json.loads(s) for s in (previous_root(stage)/race/'predictions.jsonl').read_text().splitlines()])
            key=lambda r:(r['driver_number'],r['lap'],r['target_lap'],r['horizon'])
            if sorted(map(key,current[race]))!=sorted(map(key,previous[race])):raise ValueError('Matched green cohort changed')
            manifests[race]=manifest
    summaries={};old={}
    for pool,source in (('current',current),('previous',previous)):
        m={r:metrics(rows) for r,rows in source.items()}
        m['pooled_prediction']=metrics([r for rows in source.values() for r in rows])
        m['pooled_equal_race']=balanced_metrics(source)
        if pool=='current':summaries=m
        else:old=m
    lines=[f'# Causal parameter change: {stage}','',
        'Conditional green predictions evaluated on matched GREEN-cutoff/no-actual-SC-or-VSC outcomes. '
        'Same three development races, every lap, pit/no-pit labels unchanged. Entries previous -> current. '
        'No interval tuning or SC/VSC prior changes; held-out/wet evaluation races and UI untouched.','',
        'Per-prediction and equal-race pools are reported; equal-race pit strata normalize within contributing races. '
        'France has no green-only finish outcomes, so pooled green finish has two races.']
    for race,m in summaries.items():
        lines+=['',f'## {race}','',*comparison(m,old[race]),'',*metric_tables(m)]
    for race,rows in {**current,'pooled_prediction':[r for rows in current.values() for r in rows]}.items():
        before=previous[race] if race in previous else [r for rows in previous.values() for r in rows]
        a,b=no_stop_breakdowns(before),no_stop_breakdowns(rows)
        breakdowns[race]={'previous':a,'current':b}
        lines+=['',f'## No-stop long-horizon compound/age: {race}','',
                'Tyre age is at the cutoff; these are descriptive correlated groups, not regression inputs.',
                '',*breakdown_compare(a,b)]
    (output/'metrics.json').write_text(json.dumps({'current':summaries,'previous':old},indent=2)+'\n',encoding='utf-8')
    (output/'no_stop_breakdowns.json').write_text(json.dumps(breakdowns,indent=2)+'\n',encoding='utf-8')
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for race,rows in current.items():plots(rows,output/race,race+' conditional green '+stage)
    print(json.dumps({r:{h:{k:v for k,v in m.items() if k!='by_subject_pit_stop'} for h,m in s.items()} for r,s in summaries.items()},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=('pit','wear','trend','offsets','ablation_a','ablation_b'),required=True);p.add_argument('--race',choices=RACES);p.add_argument('--report-only',action='store_true');a=p.parse_args()
    if a.race:run(a.stage,a.race)
    elif a.report_only:report(a.stage)
    else:p.error('Choose --race or --report-only')
