"""Offline final ablations, matched reporting, and the predeclared freeze decision."""
import argparse
import hashlib
import json
from pathlib import Path
from math import isclose
from src.evaluation.offline import network_blocked
from src.evaluation.diagnostics import metrics
from src.evaluation.breakdown import no_stop_breakdowns
from src.evaluation.selection import select_configuration
from tools.evaluate_conditional import RACES,green_rows
from tools.report_neutralization_views import balanced_metrics
from tools.evaluate_causal_parameters import run,report as stage_report,root,comparison,breakdown_compare

OUTPUT=Path('docs/evaluation/development_ablation')
CONFIGURATIONS=('wear','offsets','ablation_a','ablation_b')


def read_rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines()]


def run_race(race):
    for stage in ('ablation_a','ablation_b'):
        print('Running',stage,race,flush=True)
        run(stage,race)


def verify():
    counts={};hashes={}
    with network_blocked():
        for race in RACES:
            old_manifest=json.loads((root('offsets')/race/'manifest.json').read_text())
            old=read_rows(old_manifest['snapshot_path']);old_predictions=read_rows(root('offsets')/race/'predictions.jsonl')
            for stage in ('ablation_a','ablation_b'):
                manifest_path=root(stage)/race/'manifest.json';manifest=json.loads(manifest_path.read_text())
                for p,d in manifest['source_sha256'].items():
                    if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=d:raise ValueError('Candidate model source changed')
                for kind in ('dataset','snapshot'):
                    p=Path(manifest[kind+'_path'])
                    if hashlib.sha256(p.read_bytes()).hexdigest()!=manifest[kind+'_sha256']:raise ValueError('Input hash changed')
                new=read_rows(manifest['snapshot_path']);predictions=read_rows(root(stage)/race/'predictions.jsonl')
                if len(new)!=len(old) or len(predictions)!=len(old_predictions):raise ValueError('Cohort changed')
                for a,b in zip(old,new):
                    assert (a['driver_number'],a['lap'])==(b['driver_number'],b['lap'])
                    for k in ('pit_loss_estimate','pace_uncertainty','ongoing_neutralization'):assert a['audit'][k]==b['audit'][k],k
                    allowed={'base_pace_s','degradation_rates_s_per_lap','race_trend_s_per_lap','compound_offsets_s'}
                    assert {k:v for k,v in a['config'].items() if k not in allowed}=={k:v for k,v in b['config'].items() if k not in allowed}
                    assert all(t<=b['audit']['cutoff_session_s'] for t in b['audit']['parameter_source_session_s'].values())
                    for group in ('wear_estimates','compound_offset_estimates'):
                        for estimate in b['audit'][group].values():assert estimate['latest_source_session_s']<=b['audit']['cutoff_session_s']
                    assert b['config']['race_trend_s_per_lap']==-.05
                    if stage=='ablation_a':
                        assert a['state']==b['state']
                        assert {k:v for k,v in a['config'].items() if k!='race_trend_s_per_lap'}=={k:v for k,v in b['config'].items() if k!='race_trend_s_per_lap'}
                    else:
                        assert b['audit']['race_trend_estimate']['value_s_per_lap']==-.05
                        assert b['audit']['race_trend_estimate']['fallback_reason']=='fixed_fuel_ablation'
                snapshot_by_key={(r['driver_number'],r['lap']):r for r in old}
                for a,b in zip(old_predictions,predictions):
                    for k in ('driver_number','lap','target_lap','horizon','actual_s','green_sample_count','green_probability_mass','neutralization_start_probability','sampled_neutralization_start_probability'):assert a[k]==b[k],(race,stage,k)
                    if stage=='ablation_a' and a['green_only_outcome'] and a['cutoff_track_status']=='GREEN':
                        fitted=snapshot_by_key[(a['driver_number'],a['lap'])]['config']['race_trend_s_per_lap']
                        n=a['horizon_laps'];shift=(-.05-fitted)*n*(n+1)/2
                        for k in ('green_p10_s','green_median_s','green_p90_s'):assert isclose(b[k]-a[k],shift,abs_tol=1e-8),(race,k,b[k]-a[k],shift)
                counts.setdefault(stage,{'snapshots':0,'predictions':0});counts[stage]['snapshots']+=len(new);counts[stage]['predictions']+=len(predictions)
                for p in (manifest_path,Path(manifest['snapshot_path']),root(stage)/race/'predictions.jsonl'):
                    hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    return counts,hashes


def make_report(bias_rule='absolute'):
    for stage in ('ablation_a','ablation_b'):stage_report(stage)
    counts,hashes=verify();summaries={};rows_by_configuration={}
    for configuration in CONFIGURATIONS:
        rows={r:green_rows(read_rows(root(configuration)/r/'predictions.jsonl')) for r in RACES}
        rows_by_configuration[configuration]=rows
        summaries[configuration]={r:metrics(v) for r,v in rows.items()}
        summaries[configuration]['pooled_prediction']=metrics([x for v in rows.values() for x in v])
        summaries[configuration]['pooled_equal_race']=balanced_metrics(rows)
        for r in RACES:
            p=root(configuration)/r/'predictions.jsonl';hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    key=lambda r:(r['driver_number'],r['lap'],r['target_lap'],r['horizon'],r['actual_s'])
    for r in RACES:
        cohort=sorted(map(key,rows_by_configuration['wear'][r]))
        assert all(sorted(map(key,rows_by_configuration[c][r]))==cohort for c in CONFIGURATIONS)
    decision=select_configuration(summaries,bias_rule=bias_rule)
    signed_audit=select_configuration(summaries,bias_rule='signed')
    lines=['# Final development ablation','',
        '[Predeclared protocol](PROTOCOL.md). Same cached Bahrain 2021, Spain 2022 and France 2022 snapshots and actual subject plans. '
        'No new races, interval tuning, SC/VSC prior changes or UI edits. Signed error is predicted median minus actual. '
        'Green means GREEN at cutoff and no actual SC/VSC in the horizon; future outcome filters are scoring only.','',
        'A retains fitted trend for historical regression and the cutoff pace anchor, then projects fixed fuel only. '
        'B fits and projects fixed fuel. Prior strengths and eligibility are identical to the preceding regression slices. '
        'Each candidate has 1,400 snapshots / 5,446 scored predictions; the matched green cohort has 4,704 predictions. '
        'France has no green finish cohort, so finish equal-race pooling uses Bahrain and Spain.','',
        '## Selection','',
        f"Primary bias rule: {bias_rule}; unrounded pit+wear finish bias {decision['baseline_bias_s']:.16g} s.",
        'Both-horizon equal-race minima are required; no weighted sum is used. Pit+wear is also an eligible fallback.','',
        '| Configuration | Equal-race 10-lap MAE s | Equal-race finish MAE s | Per-prediction finish bias s | Bias gate |',
        '| --- | ---: | ---: | ---: | --- |']
    for c in CONFIGURATIONS:
        s=summaries[c];eligible=c in decision['eligible_configurations']
        lines.append(f"| {c} | {s['pooled_equal_race']['10']['mae_s']:.6f} | {s['pooled_equal_race']['finish']['mae_s']:.6f} | {s['pooled_prediction']['finish']['bias_s']:+.6f} | {'pass' if eligible else 'fail / reference only'} |")
    lines+=['',f"Selected configuration: **{decision['selected_configuration']}**. Reason: {decision['reason']}.",'',
            f"Signed-bias interpretation audit selects **{signed_audit['selected_configuration']}**; primary selection does not switch gates after outcomes."]
    breakdowns={}
    for candidate in ('ablation_a','ablation_b'):
        breakdowns[candidate]={}
        for baseline in ('wear','offsets'):
            lines+=['',f'## {candidate} versus {baseline}','', 'Entries baseline -> candidate. Exact matched cohorts.']
            for race,current in summaries[candidate].items():lines+=['',f'### {race}','',*comparison(current,summaries[baseline][race])]
            breakdowns[candidate][baseline]={}
            current_rows=rows_by_configuration[candidate];previous_rows=rows_by_configuration[baseline]
            for race,rows in {**current_rows,'pooled_prediction':[x for v in current_rows.values() for x in v]}.items():
                previous=previous_rows[race] if race in previous_rows else [x for v in previous_rows.values() for x in v]
                a,b=no_stop_breakdowns(previous),no_stop_breakdowns(rows)
                breakdowns[candidate][baseline][race]={'baseline':a,'candidate':b}
                lines+=['',f'### No-stop compound/age: {race}','',*breakdown_compare(a,b)]
    OUTPUT.mkdir(parents=True,exist_ok=True)
    (OUTPUT/'metrics.json').write_text(json.dumps(summaries,indent=2)+'\n')
    (OUTPUT/'selection.json').write_text(json.dumps({'primary':decision,'signed_audit':signed_audit},indent=2)+'\n')
    (OUTPUT/'no_stop_breakdowns.json').write_text(json.dumps(breakdowns,indent=2)+'\n')
    (OUTPUT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for p in (Path(__file__),Path('src/evaluation/selection.py'),OUTPUT/'PROTOCOL.md'):hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    (OUTPUT/'manifest.json').write_text(json.dumps({'network_blocked_replay':True,'counts':counts,'source_and_inputs_sha256':hashes},indent=2)+'\n')
    (OUTPUT/'VERIFICATION.md').write_text('# Verification\n\nEach candidate: 1,400 matched snapshots / 5,446 matched predictions. All source times <= cutoff; hashes verified. Pit estimates, ongoing neutralisation assumptions, noise sizing, onset probabilities, sampled onset frequencies and conditional sample counts/masses are identical to the current offsets run.\n\nA has exactly the same state, fitted wear, offsets and cutoff base pace as offsets. Its green quantiles differ only by the analytically expected fixed-fuel time shift. B records a fixed -0.05 trend with source time zero. Actual future data is used only for subject plans and scoring. No new races or UI changes.\n')
    print(json.dumps({'selection':decision,'signed_audit':signed_audit,'counts':counts},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--race',choices=RACES);p.add_argument('--report-only',action='store_true');p.add_argument('--bias-rule',choices=('absolute','signed'),default='absolute');a=p.parse_args()
    if a.race:run_race(a.race)
    elif a.report_only:make_report(a.bias_rule)
    else:p.error('Choose --race or --report-only')
