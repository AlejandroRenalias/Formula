"""Saved-output-only stop-containing green finish diagnostics. No model replay."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from src.calculators.tyre_model import TyreModel
from src.core.models import TireCompound
from src.evaluation.diagnostics import _summary
from src.evaluation.offline import network_blocked
from tools.report_neutralization_views import balanced_summary

SOURCE=Path('docs/evaluation/held_out')
OUTPUT=Path('docs/evaluation/held_out_finish_diagnostic')
RACES=('spain_2023','bahrain_2024')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def phase(lap):return '5-14' if lap<15 else '15-29' if lap<30 else '30+'


def cliff_group(laps):return '0' if laps==0 else '1-5' if laps<=5 else '6-10' if laps<=10 else '11+'


def stint(compound,length,initial_age,config):
    threshold=TyreModel.get_compound_specs(TireCompound(compound)).cliff_lap_threshold
    ages=range(initial_age,initial_age+length)
    overshoot=sum(max(0,age-threshold) for age in ages)
    return {'compound':compound,'length_laps':length,'first_charged_age':initial_age,
        'last_charged_age':initial_age+length-1 if length else None,'cliff_age':threshold,
        'penalized_laps':sum(age>threshold for age in ages),'excess_age_lap_units':overshoot,
        'nominal_cliff_cost_s':config['cliff_rate_s']*overshoot,
        'nominal_linear_wear_cost_s':config['degradation_rates_s_per_lap'][compound]*config['degradation_scale']*sum(ages)}


def annotate(row,record):
    r=dict(row)
    r.update(p10_s=r['green_p10_s'],median_s=r['green_median_s'],p90_s=r['green_p90_s'])
    r.update(error_s=r['median_s']-r['actual_s'],covered=r['p10_s']<=r['actual_s']<=r['p90_s'],width_s=r['p90_s']-r['p10_s'])
    r['error_per_lap_s']=r['error_s']/r['horizon_laps']
    stops=sorted((s for s in record['actual_subject_plan'] if s['lap']<r['target_lap']),key=lambda s:s['lap'])
    assert stops and stops[0]['lap']>=r['lap']
    config=record['config'];wear=record['audit']['wear_estimates']
    future=[]
    for i,s in enumerate(stops):
        end=stops[i+1]['lap'] if i+1<len(stops) else r['target_lap']
        value=stint(s['compound'],end-s['lap'],0,config)
        value.update(stop_boundary=s['lap'],last_running_lap=end,
                     fallback_used=wear[s['compound']]['fallback_used'],
                     sample_count=wear[s['compound']]['sample_count'],
                     prior_weight=wear[s['compound']]['prior_weight'],
                     wear_rate_s_per_lap=wear[s['compound']]['rate_s_per_lap'],
                     latest_source_session_s=wear[s['compound']]['latest_source_session_s'],
                     completed_laps_beyond_cliff=max(0,value['length_laps']-value['cliff_age']))
        assert value['latest_source_session_s']<=record['audit']['cutoff_session_s']
        future.append(value)
    current=stint(record['state']['subject_driver']['current_compound'],stops[0]['lap']-r['lap'],
                  record['state']['subject_driver']['stint_length_laps'],config)
    fallback=[s['fallback_used'] for s in future]
    r.update(cutoff_bucket=phase(r['lap']),future_wear_status='all_fallback' if all(fallback) else 'mixed' if any(fallback) else 'all_fitted',
        any_future_fallback=any(fallback),future_stints=future,current_remainder=current,
        any_future_prior_dominated=any(s['prior_weight']>=.5 for s in future),
        future_penalized_laps=sum(s['penalized_laps'] for s in future),
        max_future_stint_penalized_laps=max(s['penalized_laps'] for s in future),
        future_cliff_cost_s=sum(s['nominal_cliff_cost_s'] for s in future),
        current_cliff_cost_s=current['nominal_cliff_cost_s'],
        future_linear_wear_cost_s=sum(s['nominal_linear_wear_cost_s'] for s in future))
    r['total_cliff_cost_s']=r['future_cliff_cost_s']+r['current_cliff_cost_s']
    r['future_cliff_bucket']=cliff_group(r['future_penalized_laps'])
    r['max_stint_cliff_bucket']=cliff_group(r['max_future_stint_penalized_laps'])
    return r


def extra_summary(rows):
    if not rows:return {'n':0}
    value=_summary(rows)
    value.update(future_cliff_mean_s=sum(r['future_cliff_cost_s'] for r in rows)/len(rows),
        total_cliff_mean_s=sum(r['total_cliff_cost_s'] for r in rows)/len(rows),
        future_linear_wear_mean_s=sum(r['future_linear_wear_cost_s'] for r in rows)/len(rows),
        future_penalized_laps_mean=sum(r['future_penalized_laps'] for r in rows)/len(rows),
        positive_errors=sum(r['error_s']>0 for r in rows),
        error_above_1_15_total_cliff_budget=sum(r['error_s']>1.15*r['total_cliff_cost_s'] for r in rows))
    return value


def tables(title,groups):
    lines=['',f'## {title}','','| Group | N | Mean error s | Median error s | MAE s | Error/lap s | Coverage | Future cliff s | Total cliff s | Future linear wear s |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for key,v in groups.items():
        if v['n']:
            lines.append(f"| {key} | {v['n']} | {v['bias_s']:+.3f} | {v['median_error_s']:+.3f} | {v['mae_s']:.3f} | {v['mean_error_per_lap_s']:+.3f} | {100*v['coverage']:.1f}% | {v['future_cliff_mean_s']:.3f} | {v['total_cliff_mean_s']:.3f} | {v['future_linear_wear_mean_s']:.3f} |")
    return lines


def run():
    hashes={};all_rows=[]
    with network_blocked():
        for race in RACES:
            root=SOURCE/race
            manifest=json.loads((root/'manifest.json').read_text())
            snapshot_path=Path(manifest['snapshot_path'])
            assert sha(snapshot_path)==manifest['snapshot_sha256']
            assert sha(root/'predictions.jsonl')==manifest['prediction_sha256']
            snapshots={(r['driver_number'],r['lap']):r for r in map(json.loads,snapshot_path.read_text().splitlines())}
            rows=[r for r in map(json.loads,(root/'predictions.jsonl').read_text().splitlines())
                  if r['horizon']=='finish' and r['green_only_outcome'] and r['contains_subject_pit_stop'] and r['green_median_s'] is not None]
            all_rows.extend(annotate(r,snapshots[(r['driver_number'],r['lap'])]) for r in rows)
            for p in (snapshot_path,root/'predictions.jsonl',root/'manifest.json'):hashes[str(p)]=sha(p)
        expected=json.loads((SOURCE/'metrics.json').read_text())['conditional_green']['held_out']['pooled_prediction']['finish']['by_subject_pit_stop']['with_stop']
        baseline=_summary(all_rows)
        assert baseline['n']==expected['n']==645
        for k in ('bias_s','median_error_s','mae_s','coverage'):assert abs(baseline[k]-expected[k])<1e-9
        results={}
        for name,rows in [('pooled_prediction',all_rows),*[(race,[r for r in all_rows if r['race_key']==race]) for race in RACES]]:
            groups={'all':extra_summary(rows)}
            for dimension in ('cutoff_bucket','future_wear_status','future_cliff_bucket','max_stint_cliff_bucket','any_future_prior_dominated'):
                for value in sorted({r[dimension] for r in rows}):groups[f'{dimension}:{value}']=extra_summary([r for r in rows if r[dimension]==value])
            for p in ('5-14','15-29','30+'):
                for wear in ('all_fallback','mixed','all_fitted'):
                    selected=[r for r in rows if r['cutoff_bucket']==p and r['future_wear_status']==wear]
                    if selected:groups[f'phase×wear:{p}/{wear}']=extra_summary(selected)
                for cliffs in ('0','1-5','6-10','11+'):
                    selected=[r for r in rows if r['cutoff_bucket']==p and r['future_cliff_bucket']==cliffs]
                    if selected:groups[f'phase×cliff:{p}/{cliffs}']=extra_summary(selected)
            results[name]=groups
        by_stint=defaultdict(list)
        for row in all_rows:
            for i,s in enumerate(row['future_stints']):
                by_stint[(row['race_key'],s['compound'], 'fallback' if s['fallback_used'] else 'fitted',cliff_group(s['penalized_laps']))].append((row,s))
        stint_groups=[{'race':race,'compound':c,'wear':w,'cliff_laps':k,'stint_exposures':len(values),
            'unique_predictions':len({(r['driver_number'],r['lap']) for r,s in values}),
            'mean_parent_finish_error_s':sum(r['error_s'] for r,s in values)/len(values),
            'mean_stint_length':sum(s['length_laps'] for r,s in values)/len(values),
            'mean_stint_cliff_cost_s':sum(s['nominal_cliff_cost_s'] for r,s in values)/len(values)}
            for (race,c,w,k),values in sorted(by_stint.items())]
        results['equal_race_all']=balanced_summary({race:[r for r in all_rows if r['race_key']==race] for race in RACES})
        OUTPUT.mkdir(parents=True,exist_ok=True)
        (OUTPUT/'metrics.json').write_text(json.dumps(results,indent=2)+'\n')
        (OUTPUT/'prediction_stint_details.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in all_rows))
        (OUTPUT/'stint_groups.json').write_text(json.dumps(stint_groups,indent=2)+'\n')
        lines=['# Saved held-out green finish diagnostic: horizons containing a stop','',
            'Report only. 645 saved conditional green finish predictions; no prediction/decision replay, '
            'snapshot rebuilding, parameter changes or new races. Hash-verified saved predictions and snapshot audits. '
            'Signed error is conditional green median minus actual. Adjacent driver/cutoff rows are correlated.', '',
            'Future stints follow the saved conditional actual plan up to the scored driver finish. Each replacement '
            'starts at engine age zero on its charged entry lap, exactly as the frozen model. Fitted means '
            '`fallback_used=false` in the cutoff audit; fitted values still shrink toward defaults. '
            'All-fallback/mixed/all-fitted describe all future compounds collectively, including repeated compounds.', '',
            'Cliff ages: SOFT 15, MEDIUM 24, HARD 35. A future stint of L laps is charged at ages 0..L-1; '
            'strictly penalized laps k=max(0,L-1-cliff_age). The common length-minus-threshold count differs '
            'by one and is also retained in the detail file. Future cliff buckets sum penalized laps across '
            'all future stints; max-stint buckets and the per-stint table are reported separately.', '',
            'Nominal direct cliff cost is 0.15 times the sum of excess ages, equivalently '
            '0.15*k*(k+1)/2 per fresh stint. Total cliff cost also includes remaining running on current tyres. '
            'Each existing wear sample scales that term by 0.85..1.15. These budgets are an accounting check, '
            'not a no-cliff counterfactual: they do not rerun traffic or remove any real tyre loss. '
            'Future linear wear costs are shown separately. No causal attribution from group correlations.', '',
            '[Metrics](metrics.json). [Per-prediction/per-stint audit](prediction_stint_details.jsonl).']
        for name,groups in results.items():
            if name!='equal_race_all':lines+=tables(name,groups)
        lines+=['','## Individual future-stint exposures','',
            'A prediction with multiple future stints appears in multiple rows. Parent finish errors '
            'are exposure-weighted descriptive values, not additive errors assigned to a stint. '
            'Use the prediction-level tables for unbiased row counts.', '',
            '| Race | Compound | Cutoff wear | Penalized laps in stint | Stint exposures | Predictions | Mean length | Parent finish error s | Cliff cost s |',
            '| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
        for r in stint_groups:
            lines.append(f"| {r['race']} | {r['compound']} | {r['wear']} | {r['cliff_laps']} | {r['stint_exposures']} | {r['unique_predictions']} | {r['mean_stint_length']:.2f} | {r['mean_parent_finish_error_s']:+.3f} | {r['mean_stint_cliff_cost_s']:.3f} |")
        for p,h in hashes.items():assert sha(p)==h
        (OUTPUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        (OUTPUT/'manifest.json').write_text(json.dumps({'report_only':True,'network_blocked':True,
            'no_model_calls':True,'input_sha256':hashes,'reporter_sha256':sha(__file__),'predictions':len(all_rows)},indent=2)+'\n')
    print(json.dumps(results['pooled_prediction'],indent=2))


if __name__=='__main__':run()
