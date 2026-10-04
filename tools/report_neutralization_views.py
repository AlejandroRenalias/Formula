"""Outcome-only green horizon views and equal-race weighted diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
from src.evaluation.diagnostics import metrics, metric_tables
from src.evaluation.breakdown import attach_cutoff_features
from src.evaluation.offline import network_blocked
from src.evaluation.snapshot import load_dataset
from tools.evaluate_bahrain import read_predictions
from tools.report_development_evaluation import actual_neutralization
from tools.report_neutralization_evaluation import RACES


def weighted_median(values):
    ordered=sorted(values)
    total=sum(w for _,w in ordered)
    cumulative=0.
    for i,(value,weight) in enumerate(ordered):
        cumulative+=weight
        if abs(cumulative-total/2)<1e-12 and i+1<len(ordered):
            return (value+ordered[i+1][0])/2
        if cumulative>total/2:
            return value
    return ordered[-1][0]


def balanced_summary(per_race):
    available={race:rows for race,rows in per_race.items() if rows}
    if not available:return {'n':0,'contributing_races':0}
    weighted=[(r,1/(len(available)*len(rows))) for rows in available.values() for r in rows]
    mean=lambda fn:sum(fn(r)*w for r,w in weighted)
    return {'n':len(weighted),'contributing_races':len(available),
        'race_weights':{r:1/len(available) for r in available},
        'mae_s':mean(lambda r:abs(r['error_s'])), 'bias_s':mean(lambda r:r['error_s']),
        'median_error_s':weighted_median([(r['error_s'],w) for r,w in weighted]),
        'mean_error_per_lap_s':mean(lambda r:r['error_s']/r['horizon_laps']),
        'median_error_per_lap_s':weighted_median([(r['error_s']/r['horizon_laps'],w) for r,w in weighted]),
        'mae_per_lap_s':mean(lambda r:abs(r['error_s'])/r['horizon_laps']),
        'coverage':mean(lambda r:r['covered']), 'mean_width_s':mean(lambda r:r['width_s']),
        'lower_misses':sum(r['actual_s']<r['p10_s'] for r,w in weighted),
        'upper_misses':sum(r['actual_s']>r['p90_s'] for r,w in weighted),
        'lower_miss_rate':mean(lambda r:r['actual_s']<r['p10_s']),
        'upper_miss_rate':mean(lambda r:r['actual_s']>r['p90_s']),
        'interval_score_s':mean(lambda r:r['width_s']+10*max(0,r['p10_s']-r['actual_s'])+10*max(0,r['actual_s']-r['p90_s']))}


def balanced_metrics(per_race):
    result={}
    for horizon in ('1','5','10','finish'):
        groups={race:[r for r in rows if r['horizon']==horizon] for race,rows in per_race.items()}
        value=balanced_summary(groups)
        if value['n']:
            value['by_subject_pit_stop']={label:balanced_summary({race:[r for r in rows if r['contains_subject_pit_stop']==stop]
                for race,rows in groups.items()}) for label,stop in (('without_stop',False),('with_stop',True))}
            result[horizon]=value
    return result


def table(title,summary):
    lines=['',f'## {title}','',*metric_tables(summary)]
    if any('race_weights' in v for v in summary.values()):
        lines+=['','| Horizon | Pit group | Contributing races | Equal-race below p10 rate | Equal-race above p90 rate |',
                '| --- | --- | ---: | ---: | ---: |']
        for h,v in summary.items():
            for label,m in [('all',v),*v['by_subject_pit_stop'].items()]:
                if not m['n']:continue
                lines.append(f"| {h} | {label} | {m['contributing_races']} | {100*m['lower_miss_rate']:.1f}% | {100*m['upper_miss_rate']:.1f}% |")
    return lines


def run():
    output=Path('docs/evaluation/development_neutralization_views');output.mkdir(exist_ok=True)
    results,hashes={},{}
    lines=['# Full and green-only development evaluation','',
        '[Matched stage comparisons](COMPARISONS.md). Stages: previous pit split, ongoing event duration, future neutralization risk. All three approved development races; no new simulations. '
        'Signed error is predicted median minus actual. Green-only means GREEN at the cutoff and no actual SC/VSC (status 4/6/7) in (cutoff,target]. '
        'Outcome status filters are computed only after predictions and never enter engine state or parameters. Pit and no-pit horizons both remain eligible.','',
        'Prediction pooling weights each row equally. Race pooling gives each available race equal total weight, then each prediction within that race equal weight. '
        'Pit strata are independently normalized within available races. Medians are weighted medians of individual errors, not averages of race medians. '
        'Below/above counts are ordinary integer counts in both tables; the extra rate table contains balanced miss rates. '
        'Missing race/horizon cells receive no weight. France has no green-only finish horizons, so green-only finish pooling has two races.']
    with network_blocked():
        for stage in ('pit_split','ongoing','future'):
            full,green={},{}
            for race in RACES:
                root=Path('docs/evaluation')/f'{race}_{stage}'
                manifest=json.loads((root/'manifest.json').read_text())
                data,digest=load_dataset(Path('data/cache/evaluation')/race/'session.json')
                if digest!=manifest['dataset_sha256']:raise ValueError('Dataset changed')
                snapshot_path=Path(manifest['snapshot_path'])
                records=[json.loads(s) for s in snapshot_path.read_text().splitlines()]
                rows=attach_cutoff_features(read_predictions(root/'predictions.csv'),records,race)
                full[race]=rows
                green[race]=[r for r in rows if r['cutoff_track_status']=='GREEN' and not actual_neutralization(data,r)]
                for p in (root/'predictions.csv',root/'manifest.json',snapshot_path):hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
            views={}
            for name,per_race in (('full',full),('green_only',green)):
                summaries={r:metrics(rows) for r,rows in per_race.items()}
                summaries['pooled_prediction']=metrics([r for rows in per_race.values() for r in rows])
                summaries['pooled_equal_race']=balanced_metrics(per_race)
                views[name]=summaries
                lines+=['',f'# {stage}: {name}']
                for race,m in summaries.items():
                    lines+=table(race,m)
                    if name=='green_only' and race=='france_2022':
                        lines+=['','Finish: N=0, unavailable; every scored finish horizon contains an actual future neutralization.']
            results[stage]=views
    comparisons=['# Matched full and green-only stage comparisons','',
        'Each entry is previous -> current. Reporting changes do not alter predictions. '
        'Per-race groups and both pooling schemes retain their exact outcome-filtered cohorts.']
    for stage,previous in (('ongoing','pit_split'),('future','ongoing')):
        comparisons += ['',f'## {previous} -> {stage}','',
            '| View | Race / pool | Horizon | N | Bias s | Median error s | MAE s | Error/lap s | Coverage | Width s | Below / above p10-p90 |',
            '| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- |']
        for view,current in results[stage].items():
            for race,summary in current.items():
                for h,b in summary.items():
                    a=results[previous][view][race][h]
                    if a['n']!=b['n']:raise ValueError('View cohort changed')
                    cells=[f"{a[k]:+.3f} -> {b[k]:+.3f}" for k in ('bias_s','median_error_s','mae_s','mean_error_per_lap_s')]
                    cells += [f"{100*a['coverage']:.1f}% -> {100*b['coverage']:.1f}%",
                              f"{a['mean_width_s']:.2f} -> {b['mean_width_s']:.2f}",
                              f"{a['lower_misses']}/{a['upper_misses']} -> {b['lower_misses']}/{b['upper_misses']}"]
                    comparisons.append(f"| {view} | {race} | {h} | {b['n']} | "+' | '.join(cells)+' |')
    (output/'COMPARISONS.md').write_text('\n'.join(comparisons)+'\n',encoding='utf-8')
    (output/'metrics.json').write_text(json.dumps(results,indent=2)+'\n')
    (output/'manifest.json').write_text(json.dumps({'network_blocked':True,'report_only':True,'input_sha256':hashes},indent=2)+'\n')
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':run()
