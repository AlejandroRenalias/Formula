"""Predeclared offline decision benchmark and one-pass agreement evaluation."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import statistics
import subprocess
import time
from src.calculators.projection import project,default_policies
from src.calculators.tyre_model import TyreModel
from src.core.models import TireCompound,TrackStatus
from src.evaluation.offline import network_blocked
from src.orchestrator.projection_pipeline import run_projection_cycle
from tools.agreement_inputs import RACES,ROOT,inputs,causal,phase,sha,read_rows
from tools.agreement_scoring import score

PHASES=('5-14','15-29','30+')
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def dump_gzip(p,v):
    with gzip.open(p,'wt',encoding='utf-8') as f:json.dump(v,f,allow_nan=False)
def identity(r):return (r['driver_number'],r['lap'])
def selected(records,total):
    chosen=[]
    for ph,mid in zip(PHASES,(9.5,22,(30+total-5)/2)):
        rr=[r for r in records if phase(r['lap'])==ph]
        chosen.append(min(rr,key=lambda r:(-len(default_policies(*causal(r))),abs(r['lap']-mid),int(r['driver_number']),r['lap'])))
    chosen.append(min(records,key=lambda r:(len(default_policies(*causal(r))),-r['lap'],int(r['driver_number']))))
    sc=[r for r in records if r['state']['track_status']=='SAFETY_CAR']
    if sc:chosen.append(min(sc,key=lambda r:(abs(r['lap']-19),int(r['driver_number']))))
    return list({identity(r):r for r in chosen}.values())
def call(record,race):
    state,config=causal(record)
    start=time.perf_counter();result=project(state,config=config,include_flips=False);elapsed=time.perf_counter()-start
    target='MEDIUM' if state.subject_driver.current_compound==TireCompound.HARD else 'HARD'
    age=state.subject_driver.stint_length_laps
    cliff=TyreModel.get_compound_specs(state.subject_driver.current_compound).cliff_lap_threshold
    slim={'race':race,'driver_number':record['driver_number'],'lap':record['lap'],'phase':phase(record['lap']),
          'cutoff_session_s':record['audit']['cutoff_session_s'],'call':result['call'],'recommended':result['recommended'],
          'ranking':result['ranking'],'best_policies_by_call':result['best_policies_by_call'],
          'call_margin_s':result['call_margin_s'],'call_confidence':result['call_confidence'],
          'candidate_means_s':{p['id']:p['mean_time_to_finish_s'] for p in result['plans']},
          'candidate_invalid_probability':{p['id']:p['invalid_probability'] for p in result['plans']},
          'candidate_count':len(result['plans']),'stay_to_finish_available':any(p['id']=='stay_to_finish' for p in result['plans']),
          'directional_stratum':phase(record['lap'])=='5-14' and record['audit']['wear_estimates'][target]['prior_weight']>=.5 and age+4<=cliff,
          'target_compound':target,'current_age':age,'current_cliff':cliff,'target_wear_audit':record['audit']['wear_estimates'][target],
          'used_compounds':record['state']['subject_driver']['used_compounds'],'track_status':state.track_status.value,
          'parameter_source_session_s':record['audit']['parameter_source_session_s'],
          'gaps_audit':record['audit']['gaps'],'runtime_s':elapsed,'record_sha256':__import__('hashlib').sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()}
    return slim,result

def engine_check():
    tag=subprocess.check_output(['git','rev-parse','decision-engine-v1^{}'],text=True).strip()
    subprocess.run(['git','diff','--exit-code','decision-engine-v1','--','src','data/priors','data/evaluation/frozen_model.json'],check=True)
    assert json.loads((ROOT/'prediction_parity.json').read_text())['decision_calls']==0
    return tag

def benchmark():
    tag=engine_check(); assert not (ROOT/'benchmark_started.json').exists(),'Benchmark already started; do not rerun.'
    all_inputs={race:inputs(race) for race in RACES}
    selections={race:selected(records,data['scheduled_laps']) for race,(records,rows,data,hashes) in all_inputs.items()}
    write(ROOT/'benchmark_started.json',{'decision_tag':tag,'protocol_sha256':sha('docs/evaluation/AGREEMENT_PLAN.md'),
        'selection':{race:[{'driver_number':r['driver_number'],'lap':r['lap'],'phase':phase(r['lap']),
                            'track_status':r['state']['track_status'],'candidate_count':len(default_policies(*causal(r)))} for r in rr] for race,rr in selections.items()},
        'input_sha256':{p:h for records,rows,data,hashes in all_inputs.values() for p,h in hashes.items()}})
    timings={};cache={}
    with network_blocked():
        for race,rr in selections.items():
            cache[race]={}
            for r in rr:
                slim,raw=call(r,race);cache[race][identity(r)]=slim
                dump_gzip(ROOT/'benchmark_raw'/f"{race}_{r['driver_number']}_{r['lap']}.json.gz",raw)
                print('benchmark',race,r['driver_number'],r['lap'],round(slim['runtime_s'],3),'s',flush=True)
            records,rows,data,hashes=all_inputs[race]
            estimate=sum(sum(phase(r['lap'])==ph for r in records)*statistics.mean(c['runtime_s'] for c in cache[race].values() if c['phase']==ph) for ph in PHASES)
            timings[race]={'predicted_every_lap_runtime_s':estimate,'stride':2 if estimate>1800 else 1,
                           'benchmark_call_only_s':sum(c['runtime_s'] for c in cache[race].values()),'phase_counts':dict(Counter(phase(r['lap']) for r in records))}
        parity=[]
        parity_records=[('bahrain_2021',selections['bahrain_2021'][0]),
                        ('france_2022',next(r for r in selections['france_2022'] if r['state']['track_status']=='SAFETY_CAR')),
                        ('bahrain_2024',selections['bahrain_2024'][2])]
        for race,r in parity_records:
            state,config=causal(r);start=time.perf_counter();full=run_projection_cycle(state,config=config);elapsed=time.perf_counter()-start
            base=cache[race][identity(r)]
            for k in ('call','recommended','ranking','best_policies_by_call','call_margin_s','call_confidence'):assert full[k]==base[k],(race,k)
            assert {p['id']:p['mean_time_to_finish_s'] for p in full['plans']}==base['candidate_means_s']
            dump_gzip(ROOT/'benchmark_raw'/f"wrapper_{race}_{r['driver_number']}_{r['lap']}.json.gz",full)
            parity.append({'race':race,'driver_number':r['driver_number'],'lap':r['lap'],'full_wrapper_runtime_s':elapsed,'parity':True})
            print('full wrapper parity',race,r['lap'],round(elapsed,2),'s',flush=True)
    write(ROOT/'benchmark.json',{'timings':timings,'wrapper_parity':parity,'network_blocked':True})
    (ROOT/'benchmark_calls.jsonl').write_text(''.join(json.dumps(c,allow_nan=False)+'\n' for rr in cache.values() for c in rr.values()))
    print(json.dumps(timings,indent=2),flush=True)

def run():
    tag=engine_check(); benchmark=json.loads((ROOT/'benchmark.json').read_text());bench=read_rows(ROOT/'benchmark_calls.jsonl')
    cache={(c['race'],c['driver_number'],c['lap']):c for c in bench}
    ledger=json.loads((ROOT/'benchmark_started.json').read_text())
    for p,h in ledger['input_sha256'].items():assert sha(p)==h
    manifests={}
    with network_blocked():
        for race in RACES:
            out=ROOT/race;out.mkdir(exist_ok=True)
            assert not (out/'RUN_STARTED.json').exists(),'Race already started; explicit resume required, never rerun.'
            records,rows,data,hashes=inputs(race);stride=benchmark['timings'][race]['stride']
            chosen=[r for r in records if (r['lap']-5)%stride==0]
            write(out/'RUN_STARTED.json',{'tag':tag,'stride':stride,'input_sha256':hashes,'started_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
            start=time.perf_counter();calls=[]
            with gzip.open(out/'raw_calls.jsonl.gz','wt',encoding='utf-8') as rawf, (out/'calls.jsonl').open('w',encoding='utf-8') as slimf:
                for i,r in enumerate(chosen):
                    key=(race,r['driver_number'],r['lap'])
                    if key in cache:
                        c=cache[key]
                        with gzip.open(ROOT/'benchmark_raw'/f"{race}_{r['driver_number']}_{r['lap']}.json.gz",'rt',encoding='utf-8') as f:raw=json.load(f)
                    else:c,raw=call(r,race)
                    rawf.write(json.dumps({'driver_number':r['driver_number'],'lap':r['lap'],'result':raw},allow_nan=False)+'\n')
                    slimf.write(json.dumps(c,allow_nan=False)+'\n');slimf.flush();calls.append(c)
                    if (i+1)%50==0:print(race,i+1,'/',len(chosen),'calls',round(time.perf_counter()-start,1),'s',flush=True)
            # Outcomes enter only after every causal call has been persisted.
            metrics,audits=score(calls,data,stride)
            write(out/'metrics.json',metrics);write(out/'matching_audit.json',audits)
            drivers={r['driver_number'] for r in records}
            existing={(r['driver_number'],r['lap']) for r in records}
            missing=[{'driver_number':d,'lap':lap,'reason':'accepted_snapshot_exclusion'} for d in sorted(drivers) for lap in range(5,data['scheduled_laps']-4,stride) if (d,lap) not in existing]
            write(out/'excluded_cutoffs.json',missing)
            m={'race':race,'set':'development' if race in RACES[:3] else 'held_out','decision_tag':tag,'stride':stride,'valid_cutoffs':len(calls),
               'excluded_cutoffs':len(missing),'unselected_stride_cutoffs':len(records)-len(chosen),'runtime_s':time.perf_counter()-start,
               'benchmark_reused':sum((race,r['driver_number'],r['lap']) in cache for r in chosen),'network_blocked':True,
               'input_sha256':hashes,'output_sha256':{p.name:sha(p) for p in out.iterdir() if p.name!='manifest.json'}}
            assert all(sha(p)==h for p,h in hashes.items());write(out/'manifest.json',m);manifests[race]=m
            print('COMPLETE',race,len(calls),'calls',metrics['all'],flush=True)
    write(ROOT/'manifest.json',{'decision_tag':tag,'network_blocked':True,'protocol_sha256':sha('docs/evaluation/AGREEMENT_PLAN.md'),'races':manifests,
        'runner_sha256':sha(__file__),'scorer_sha256':sha('tools/agreement_scoring.py')})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('benchmark','run'));args=parser.parse_args()
    (ROOT/'benchmark_raw').mkdir(parents=True,exist_ok=True)
    benchmark() if args.stage=='benchmark' else run()
