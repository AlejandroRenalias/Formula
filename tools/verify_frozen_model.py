"""Offline identity check of the frozen default against the chosen saved run."""
import hashlib
import json
from pathlib import Path
from src.evaluation.model_configurations import FREEZE_PATH,resolve_configuration
from src.evaluation.snapshot import load_dataset,build_snapshot
from src.evaluation.prediction import ActualPlan,predict
from src.evaluation.offline import network_blocked
from src.calculators.projection import Stop
from tools.evaluate_conditional import RACES
from tools.evaluate_causal_parameters import root


def verify():
    freeze=json.loads(FREEZE_PATH.read_text());selected=freeze['configuration']
    assert resolve_configuration()[0]==selected
    selection_root=Path('docs/evaluation/development_ablation')
    for filename,key in (('metrics.json','selection_metrics_sha256'),('selection.json','selection_json_sha256'),('PROTOCOL.md','protocol_sha256')):
        assert hashlib.sha256((selection_root/filename).read_bytes()).hexdigest()==freeze[key]
    n=checked_predictions=0;hashes={};per_race={}
    with network_blocked():
        for race in RACES:
            manifest=json.loads((root(selected)/race/'manifest.json').read_text())
            data,digest=load_dataset(Path(manifest['dataset_path']));assert digest==manifest['dataset_sha256']
            records=[json.loads(x) for x in Path(manifest['snapshot_path']).read_text().splitlines()]
            old_rows=[json.loads(x) for x in (root(selected)/race/'predictions.jsonl').read_text().splitlines()]
            checks={0,len(records)//2,len(records)-1};scored=0
            for i,r in enumerate(records):
                snapshot=build_snapshot(data,r['driver_number'],r['lap'],cutoff_s=r['audit']['cutoff_session_s'])
                state=snapshot.state.model_dump(mode='json');config=snapshot.config.model_dump(mode='json')
                assert state==r['state'],(race,i,'state')
                assert all(config[k]==v for k,v in r['config'].items()),(race,i,'config')
                if selected=='wear':assert config['race_trend_s_per_lap'] is None and config['compound_offsets_s']=={}
                assert all(t<=snapshot.audit['cutoff_session_s'] for t in snapshot.audit['parameter_source_session_s'].values())
                assert snapshot.audit['configuration']==selected
                n+=1
                if i in checks:
                    plan=ActualPlan(tuple(Stop.model_validate(s) for s in r['actual_subject_plan']))
                    values=predict(snapshot,plan)
                    for old in old_rows:
                        if (old['driver_number'],old['lap'])!=(r['driver_number'],r['lap']):continue
                        for k,v in values[old['target_lap']].items():assert v==old[k],(race,i,k,v,old[k])
                        scored+=1;checked_predictions+=1
                if (i+1)%100==0:print(race,i+1,'frozen snapshots verified',flush=True)
            per_race[race]={'snapshot_count':len(records),'representative_predictions_verified':scored}
            for p in (Path(manifest['dataset_path']),Path(manifest['snapshot_path']),root(selected)/race/'predictions.jsonl'):
                hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    result={'configuration':selected,'network_blocked':True,'all_saved_snapshots_match':n,
        'representative_predictions_match':checked_predictions,'per_race':per_race,'source_and_inputs_sha256':hashes}
    hashes[str(FREEZE_PATH)]=hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest()
    hashes[str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (selection_root/'frozen_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_and_inputs_sha256'},indent=2))


if __name__=='__main__':verify()
