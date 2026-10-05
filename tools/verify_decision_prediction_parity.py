"""Pre-agreement frozen actual-plan parity; never calls decision search."""
import ast
import json
from pathlib import Path
import subprocess
import time
from src.calculators.projection import Stop
from src.evaluation.prediction import ActualPlan,predict
from src.evaluation.snapshot import Snapshot
from src.evaluation.offline import network_blocked
from tools.agreement_inputs import RACES,ROOT,inputs,causal,sha

def run():
    ROOT.mkdir(parents=True,exist_ok=True)
    old=subprocess.check_output(['git','show','frozen-development-model-calibrated:src/calculators/projection.py'],text=True)
    new=Path('src/calculators/projection.py').read_text()
    def funcs(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    a,b=funcs(old),funcs(new)
    changed=[k for k in a if a[k]!=b[k]]
    assert changed==['default_policies','project'],changed
    subprocess.run(['git','diff','--exit-code','frozen-development-model-calibrated','--','src/evaluation','data/priors','data/evaluation/frozen_model.json'],check=True)
    report={'network_blocked':True,'changed_definitions':changed,'decision_calls':0,'races':{}}
    begin=time.perf_counter()
    with network_blocked():
        for race in RACES:
            records,rows,data,hashes=inputs(race); groups={}
            for row in rows:groups.setdefault((row['driver_number'],row['lap']),[]).append(row)
            n=fields=0;maxdiff=0.; exact=0
            for record in records:
                state,config=causal(record)
                result=predict(Snapshot(state,config,record['audit']),ActualPlan(tuple(Stop.model_validate(s) for s in record['actual_subject_plan'])))
                for row in groups.get((record['driver_number'],record['lap']),[]):
                    for k,value in result[row['target_lap']].items():
                        expected=row[k]; fields+=1
                        if value==expected:exact+=1
                        elif value is not None and expected is not None:
                            diff=abs(value-expected); maxdiff=max(maxdiff,diff)
                            assert diff<=1e-9,(race,record['lap'],k,value,expected)
                        else: raise AssertionError((race,k,value,expected))
                    n+=1
            assert all(sha(p)==h for p,h in hashes.items())
            report['races'][race]={'snapshots':len(records),'scored_predictions':n,'fields_checked':fields,'bit_exact_fields':exact,'maximum_absolute_difference':maxdiff,'input_sha256':hashes}
            print(race,n,'scores parity; max difference',maxdiff,flush=True)
    report['runtime_s']=time.perf_counter()-begin
    (ROOT/'prediction_parity.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':run()
