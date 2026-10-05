"""Outcome-only development/held-out compound-age and event diagnostics."""
import json
from pathlib import Path
from tools.evaluate_held_out import ROOT, HELD_OUT, authorized_datasets, assert_frozen, read, digest
from tools.evaluate_conditional import green_rows, calibration, observed_start
from src.evaluation.snapshot import crossings
from tools.evaluation_cache import load_dataset
from src.evaluation.offline import network_blocked
from src.evaluation.breakdown import no_stop_breakdowns, breakdown_table


def run():
    assert_frozen()
    with authorized_datasets(),network_blocked():
        held={race:read(ROOT/race/'predictions.jsonl') for race in HELD_OUT}
        dev={race:read(ROOT/'development_reference'/race/'predictions.jsonl')
             for race in ('bahrain_2021','spain_2022','france_2022')}
        lines=['# Read-only held-out diagnostics','',
            'Conditional green no-stop compound/age groups use cutoff tyre ages, as in development. '
            'These descriptive, correlated groups do not enter the model. No fitting or tuning.']
        breakdowns={}
        for label,per_race in (('development',dev),('held_out',held)):
            all_groups={**per_race,'pooled_prediction':[r for rows in per_race.values() for r in rows]}
            breakdowns[label]={race:no_stop_breakdowns(green_rows(rows)) for race,rows in all_groups.items()}
        for race,rows in breakdowns['held_out'].items():
            selected=[r for r in rows if r['horizon'] in ('10','finish') and r['dimension']!='track_status']
            lines+=['',f'## {race}: no-stop long-horizon compound/age','',*breakdown_table(selected)]
        a={(r['horizon'],r['dimension'],r['group']):r for r in breakdowns['development']['pooled_prediction']}
        lines+=['','## Development → held-out pooled no-stop comparison','',
            '| Horizon | Dimension | Group | N dev / held-out | Mean error/lap s | Median error/lap s | MAE/lap s | Coverage |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |']
        for b in breakdowns['held_out']['pooled_prediction']:
            if b['horizon'] not in ('10','finish') or b['dimension']=='track_status':continue
            previous=a.get((b['horizon'],b['dimension'],b['group']))
            if previous:
                cells=[f"{previous[k]:+.3f} → {b[k]:+.3f}" for k in ('mean_error_per_lap_s','median_error_per_lap_s','mae_per_lap_s')]
                cells += [f"{100*previous['coverage']:.1f}% → {100*b['coverage']:.1f}%"]
                lines.append(f"| {b['horizon']} | {b['dimension']} | {b['group']} | {previous['n']} / {b['n']} | "+' | '.join(cells)+' |')
        event_results={}
        for race,rows in held.items():
            data,_=load_dataset(Path('data/cache/evaluation')/race/'session.json')
            times={driver:crossings(data,driver) for driver in {r['driver_number'] for r in rows}}
            for row in rows:
                labels=times[row['driver_number']]
                row['actual_neutralization_start']=observed_start(data['track_status'],labels[row['lap']],labels[row['target_lap']])
            event_results[race]=calibration(rows)
        event_results['pooled_prediction']=calibration([r for rows in held.values() for r in rows])
        lines+=['','## Neutralisation probability: descriptive check only','',
            'Same Brier/reliability definitions as development. Two races are too few to judge '
            'risk calibration; overlapping horizons are highly correlated. Priors remain unchanged.']
        for race,summary in event_results.items():
            lines+=['',f'### {race}','',
                    '| Horizon | N | Brier score | Mean predicted probability | Observed frequency | Observed starts |',
                    '| --- | ---: | ---: | ---: | ---: | ---: |']
            for h,m in summary.items():
                lines.append(f"| {h} | {m['n']} | {m['brier_score']:.5f} | {100*m['mean_probability']:.1f}% | {100*m['observed_frequency']:.1f}% | {m['observed_starts']} |")
            lines+=['','| Horizon | Probability bin | N | Mean probability | Observed frequency |','| --- | --- | ---: | ---: | ---: |']
            for h,m in summary.items():
                for b in m['reliability']:
                    if b['n']:lines.append(f"| {h} | {b['bin']} | {b['n']} | {100*b['mean_probability']:.1f}% | {100*b['observed_frequency']:.1f}% |")
        (ROOT/'DIAGNOSTICS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        (ROOT/'compound_age_comparison.json').write_text(json.dumps(breakdowns,indent=2)+'\n')
        (ROOT/'neutralization_probability.json').write_text(json.dumps(event_results,indent=2)+'\n')
        manifest=json.loads((ROOT/'manifest.json').read_text())
        manifest['diagnostic_reporter_sha256']=digest(__file__)
        (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        report=ROOT/'REPORT.md'
        text=report.read_text(encoding='utf-8')
        if '[Compound/age and event diagnostics]' not in text:
            report.write_text(text+'\n[Compound/age and event diagnostics](DIAGNOSTICS.md).\n',encoding='utf-8')


if __name__=='__main__':run()
