"""Append matched cumulative regression comparison; run as python -m tools.report_regression_baseline."""
from pathlib import Path
import json
from tools.evaluate_conditional import RACES,green_rows
from src.evaluation.diagnostics import metrics,metric_tables
from src.evaluation.breakdown import no_stop_breakdowns
from tools.report_neutralization_views import balanced_metrics
from tools.evaluate_causal_parameters import comparison,breakdown_compare
root=Path('docs/evaluation/development_parameters_offsets');base={};current={}
for race in RACES:
 base[race]=green_rows([json.loads(x) for x in Path(f'docs/evaluation/development_parameters_wear/{race}/predictions.jsonl').read_text().splitlines()])
 current[race]=green_rows([json.loads(x) for x in (root/race/'predictions.jsonl').read_text().splitlines()])
old={r:metrics(v) for r,v in base.items()};new={r:metrics(v) for r,v in current.items()}
old['pooled_prediction']=metrics([x for rows in base.values() for x in rows]);new['pooled_prediction']=metrics([x for rows in current.values() for x in rows])
old['pooled_equal_race']=balanced_metrics(base);new['pooled_equal_race']=balanced_metrics(current)
lines=['','## Cumulative comparison to starting wear baseline (02341a7)','', 'These tables compare the final joint trend/offset fit directly with the run approved at the start of this request. Earlier tables isolate offsets against the trend commit. Same matched green cohorts.']
for race,m in new.items():lines+=['',f'### Starting baseline -> final: {race}','',*comparison(m,old[race])]
breakdowns={}
for race,rows in {**current,'pooled_prediction':[x for rows in current.values() for x in rows]}.items():
 before=base[race] if race in base else [x for rows in base.values() for x in rows]
 a,b=no_stop_breakdowns(before),no_stop_breakdowns(rows);breakdowns[race]={'baseline':a,'current':b}
 lines+=['',f'### Starting baseline -> final compound/age: {race}','',*breakdown_compare(a,b)]
(root/'baseline_metrics.json').write_text(json.dumps({'baseline':old,'current':new},indent=2)+'\n')
(root/'baseline_no_stop_breakdowns.json').write_text(json.dumps(breakdowns,indent=2)+'\n')
report=root/'REPORT.md'
existing=report.read_text()
before,_,after=existing.partition('\n## Cumulative comparison to starting wear baseline')
tail='\n## Interpretation and parameter availability'+after.split('\n## Interpretation and parameter availability',1)[1] if '\n## Interpretation and parameter availability' in after else ''
report.write_text(before+'\n'.join(lines)+'\n'+tail)
import hashlib
inputs=[Path(f'docs/evaluation/development_parameters_wear/{r}/predictions.jsonl') for r in RACES]+[root/r/'predictions.jsonl' for r in RACES]+[Path(__file__)]
(root/'baseline_manifest.json').write_text(json.dumps({'source_and_inputs_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}},indent=2)+'\n')
