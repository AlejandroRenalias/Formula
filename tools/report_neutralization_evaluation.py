"""Matched, offline three-race reports for structural neutralization stages."""
import argparse
import json
from pathlib import Path
from src.evaluation.diagnostics import metrics, metric_tables, comparison_tables
from tools.evaluate_bahrain import read_predictions

RACES = ('bahrain_2021', 'spain_2022', 'france_2022')

def run(stage, previous):
    output = Path('docs/evaluation') / ('development_' + stage)
    output.mkdir(exist_ok=True)
    summaries, old, pooled, old_pooled = {}, {}, [], []
    lines = [f'# Development neutralization correction: {stage}', '',
             f'Previous run: {previous}. Signed error = predicted median minus actual. '
             'Same driver/cutoff/target cohort, 32 draws, every lap. No held-out or wet evaluation.']
    for race in RACES:
        root = Path('docs/evaluation') / f'{race}_{stage}'
        before = Path('docs/evaluation') / f'{race}_{previous}'
        rows, prior = read_predictions(root/'predictions.csv'), read_predictions(before/'predictions.csv')
        key = lambda r: (r['driver_number'], r['lap'], r['target_lap'], r['horizon'])
        if sorted(map(key,rows)) != sorted(map(key,prior)):
            raise ValueError('Comparison cohort changed')
        summaries[race], old[race] = metrics(rows), metrics(prior)
        pooled.extend(rows); old_pooled.extend(prior)
        lines += ['', f'## {race}', '', *comparison_tables(summaries[race],old[race]),
                  '', *metric_tables(summaries[race]), '',
                  f'[Dataset, exclusions, plots and worst cases](../{race}_{stage}/REPORT.md)']
    summaries['pooled'], old['pooled'] = metrics(pooled), metrics(old_pooled)
    lines += ['', '## Prediction-weighted pool', '', *comparison_tables(summaries['pooled'],old['pooled']),
              '', *metric_tables(summaries['pooled'])]
    (output/'metrics.json').write_text(json.dumps({'current':summaries,'previous':old},indent=2)+'\n')
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({r:{h:{k:v for k,v in m.items() if k!='by_subject_pit_stop'} for h,m in s.items()}
                      for r,s in summaries.items()},indent=2))

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',required=True);p.add_argument('--previous',required=True)
    a=p.parse_args();run(a.stage,a.previous)
