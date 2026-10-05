"""Offline, per-record saved-call export. No predictive engine imports or runs."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
from src.evaluation.offline import network_blocked
from tools.reservation_gate import authorize, archive_path

ROOT = Path(__file__).resolve().parents[1]
RACES = ('bahrain_2021','spain_2022','france_2022','spain_2023','bahrain_2024')
COUNTS = (429,542,429,550,459)
CIRCUITS = ('bahrain','barcelona','paul_ricard','barcelona_2023','bahrain')
TAG = 'decision-engine-v1'
COMMIT = '18e1bb0b093b4f7e175af8e962702737b8676a8e'
OUTPUT = ROOT / 'static/historical'

def encode(value):
    return (json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines()]

def key(row):
    return str(row['driver_number']), row['lap']

def plan_summary(plan):
    return {k:deepcopy(plan[k]) for k in ('id','label','policy','mean_time_to_finish_s','invalid_probability')}

def causal_record(race, call, snapshot, plans):
    """Allowlisted transformation; deliberately accepts no outcomes/session labels."""
    state, audit = snapshot['state'], snapshot['audit']
    cutoff = call['cutoff_session_s']
    if state['timestamp'] != state['knowledge_cutoff'] or cutoff != audit['cutoff_session_s']:
        raise ValueError('Inconsistent saved cutoff')
    if any(not math.isfinite(t) or t > cutoff for t in call['parameter_source_session_s'].values()):
        raise ValueError('Parameter timestamp after cutoff')
    if hashlib.sha256(json.dumps(snapshot,sort_keys=True).encode()).hexdigest() != call['record_sha256']:
        raise ValueError('Snapshot does not match scored call')
    best_box = plan_summary(plans[call['best_policies_by_call']['BOX_NOW']])
    best_stay = plan_summary(plans[call['best_policies_by_call']['STAY_OUT']])
    for p in (best_box,best_stay):
        if p['mean_time_to_finish_s'] != call['candidate_means_s'][p['id']]:
            raise ValueError('Saved plan/call disagreement')
    signed = best_box['mean_time_to_finish_s'] - best_stay['mean_time_to_finish_s']
    if not math.isclose(abs(signed),call['call_margin_s'],abs_tol=1e-9):
        raise ValueError('Saved margin disagreement')
    field = deepcopy(state['competitors'])
    confidence = {k:call['call_confidence'][k] for k in ('tolerance_s','stay_clearly_better','box_clearly_better','too_close_to_call')}
    side = 'box_clearly_better' if call['call']=='BOX_NOW' else 'stay_clearly_better'
    label = 'strong_model_preference' if confidence[side]>=0.8 else 'close_in_model' if confidence['too_close_to_call']>=0.5 else 'mixed_model_samples'
    return {'schema_version':1,'id':f'{race}:{call["driver_number"]}:{call["lap"]}',
        'engine':{'tag':TAG,'commit':COMMIT,'prediction_profile':'frozen-development-model-calibrated'},
        'race_key':race,'driver_number':str(call['driver_number']),'lap':call['lap'],
        'cutoff_session_s':cutoff,'phase':call['phase'],'scheduled_laps':state['total_laps'],
        'call':call['call'],'margin_s':call['call_margin_s'],'box_minus_stay_s':signed,
        'confidence':confidence,'recommended_policy_id':call['recommended'],
        'best_box':best_box,'best_stay':best_stay,
        'stay_to_finish_available':call['stay_to_finish_available'],
        'stay_to_finish_selected':call['recommended']=='stay_to_finish',
        'subject':deepcopy(state['subject_driver']),'field':field,
        'field_count':len(field)+1,'field_complete':not bool(audit.get('omitted_rivals')),
        'track_status':state['track_status'],'observed_weather':deepcopy(state['observed_weather']),
        'forecast_mode':'no_forecast_dry_persistence',
        'causal_pace':deepcopy(state['derived_pace']),'pit_loss':deepcopy(state['pit_loss']),
        'reliability':{'phase_note':call['phase'] if state['track_status']=='GREEN' else 'non_green_uncertain','model_preference':label},
        'provenance':{'causal_state_sha256':hashlib.sha256(encode({k:state[k] for k in ('subject_driver','competitors','track_status','observed_weather','derived_pace','pit_loss')})).hexdigest(),'parameter_source_session_s':deepcopy(call['parameter_source_session_s']),
            'gaps':deepcopy(call['gaps_audit']),'omitted_rivals':deepcopy(audit.get('omitted_rivals',[])),
            'gap_exception':'approved same-lap live timing proxy only'}}

def physical_stops(data):
    """Same saved coordinate/compound convention as accepted disagreement report."""
    def valid(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
    crossings={}
    for r in data['laps']:
        if valid(r.get('Time')) and r['NumberOfLaps']>0:
            crossings.setdefault(r['Driver'],{})[int(r['NumberOfLaps'])]=r['Time']
    ends={d:t[max(t)] for d,t in crossings.items()}
    stops=[]
    for r in data['laps']:
        entry=r.get('PitInTime');d=r['Driver']
        if not valid(entry) or entry<=0 or entry>ends.get(d,float('-inf')):continue
        exits=sorted((q for q in data['laps'] if q['Driver']==d and valid(q.get('PitOutTime')) and q['PitOutTime']>entry),key=lambda q:q['PitOutTime'])
        out=exits[0] if exits else None
        labels=[q for q in data.get('actual_tyres',[]) if str(q['DriverNumber'])==d and out and q['LapNumber']==out['NumberOfLaps']]
        compound=labels[-1].get('Compound') if labels else None
        if compound not in ('SOFT','MEDIUM','HARD','INTERMEDIATE','WET'):compound=None
        stops.append({'stop_id':f'{d}:{entry}','driver_number':d,'boundary_lap':int(r['NumberOfLaps'])-1,
            'physical_entry_lap':int(r['NumberOfLaps']),'entry_session_s':entry,
            'exit_session_s':out['PitOutTime'] if out else None,'out_lap':int(out['NumberOfLaps']) if out else None,'compound':compound})
    return sorted(stops,key=lambda s:(s['entry_session_s'],s['driver_number']))

def event_summary(event):
    return {k:deepcopy(event[k]) for k in ('id','direction','tags','unknown_tags','team_stop_context_basis','context_offset_laps')}

def outcome_record(race,call,stops,audit,events,episode):
    future=[s for s in stops if s['driver_number']==str(call['driver_number']) and s['entry_session_s']>call['cutoff_session_s']]
    window=[s for s in future if abs(s['boundary_lap']-call['lap'])<=1]
    selected=window[0] if window else future[0] if future else None
    action='BOX_NOW' if window else 'STAY_OUT'
    tags=[event_summary(e) for e in events if e['direction']=='FN' and selected and e['event']['entry_session_s']==selected['entry_session_s']]
    matching=next((m for m in audit['matches'] if episode and m['alert']['lap']==episode['lap']),None)
    fp=[event_summary(e) for e in events if e['direction']=='FP' and episode and e['event']['lap']==episode['lap']]
    return {'schema_version':1,'id':f'{race}:{call["driver_number"]}:{call["lap"]}',
        'race_key':race,'driver_number':str(call['driver_number']),'lap':call['lap'],
        'cutoff_session_s':call['cutoff_session_s'],'team_action_within_one_lap':action,
        'formula_agrees_with_team':call['call']==action,'scorable':True,
        'team_stop':deepcopy(selected),'future_stops_in_window':deepcopy(window),
        'stop_disagreement_tags':tags,'tag_status':'unmatched_stop_classified' if tags else 'no_unmatched_stop_classification',
        'accepted_episode':deepcopy(episode),'accepted_episode_match':deepcopy(matching),
        'unmatched_alert_context':fp,
        'matching_note':'Pointwise action agreement is separate from scored one-to-one episode matching.',
        'choice_quality_note':'No claim about who was right.'}

def verify_sources():
    manifest=read(ROOT/'docs/evaluation/agreement/manifest.json')
    exception={}
    for path,expected in manifest['source_sha256'].items():
        p=ROOT/path
        if digest(p)==expected:continue
        if path.replace('\\','/')!='src/adapters/fastf1_adapter.py':raise ValueError(f'Frozen source changed: {path}')
        blob=p.read_bytes()
        insertion="        from tools.reservation_gate import authorize\n        authorize(year, race_name, purpose='adapter', session=session_type)\n"
        restored=blob.replace(insertion.encode(),b'').replace(insertion.replace('\n','\r\n').encode(),b'')
        normalized=restored.replace(b'\r\n',b'\n')
        if expected not in {hashlib.sha256(normalized).hexdigest(),hashlib.sha256(normalized.replace(b'\n',b'\r\n')).hexdigest()}:
            raise ValueError('Adapter changed beyond approved access guard')
        exception[path]={'accepted_sha256':expected,'current_sha256':digest(p),'reason':'approved operational reservation guard only'}
    return exception

def export(output=OUTPUT):
    for race in RACES:authorize(key=race,purpose='archive')
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('Export directory must be empty; refusing stale mixed assets')
    exceptions=verify_sources();hashes={};sources={};sizes={};catalog=[];total=0
    def save(path,value):
        blob=encode(value);target=output/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(blob)
        hashes[path.as_posix()]=hashlib.sha256(blob).hexdigest()
        return len(blob),len(gzip.compress(blob,mtime=0))
    disagreement=ROOT/'docs/evaluation/disagreement'
    dm=read(disagreement/'manifest.json')
    for name,h in dm['output_sha256'].items():
        if digest(disagreement/name)!=h:raise ValueError('Disagreement output hash changed')
    all_events=rows(disagreement/'events.jsonl')
    sources[str((disagreement/'events.jsonl').relative_to(ROOT))]=digest(disagreement/'events.jsonl')
    with network_blocked():
        for race,count,circuit in zip(RACES,COUNTS,CIRCUITS):
            folder=ROOT/'docs/evaluation/agreement'/race;m=read(folder/'manifest.json')
            for path,h in m['input_sha256'].items():
                if 'data/cache/evaluation/' in path.replace('\\','/'):
                    archive_path(ROOT/path)
                if digest(ROOT/path)!=h:raise ValueError(f'Accepted input changed: {path}')
                sources[path]=h
            for name,h in m['output_sha256'].items():
                if digest(folder/name)!=h:raise ValueError(f'Accepted output changed: {name}')
                sources[(folder/name).relative_to(ROOT).as_posix()]=h
            snapshot_path=ROOT/'data/cache/evaluation'/race/('snapshots_held_out.jsonl' if race in RACES[3:] else 'snapshots_parameters_wear.jsonl')
            archive_path(snapshot_path)
            snapshots={key(r):r for r in rows(snapshot_path)}
            calls={key(c):c for c in rows(folder/'calls.jsonl')}
            if len(calls)!=count:raise ValueError('Accepted cohort count mismatch')
            data=read(archive_path(snapshot_path.parent/'session.json'))
            stops=physical_stops(data)
            audits={str(a['driver_number']):a for a in read(folder/'matching_audit.json') if a['tolerance_laps']==1}
            events=[e for e in all_events if e['race']==race]
            episode_by_key={}
            for driver in audits:
                previous=None;episode=None
                for c in sorted((c for c in calls.values() if str(c['driver_number'])==driver),key=lambda c:c['lap']):
                    if c['call']=='STAY_OUT':episode=None
                    elif previous is None or c['lap']!=previous['lap']+1 or previous['call']=='STAY_OUT':
                        episode=next(a for a in audits[driver]['alerts'] if a['lap']==c['lap'])
                    episode_by_key[key(c)]=episode;previous=c
            sizes[race]={'records':count,'causal_bytes':0,'causal_gzip_bytes':0,'outcome_bytes':0,'outcome_gzip_bytes':0}
            seen=set()
            with gzip.open(folder/'raw_calls.jsonl.gz','rt',encoding='utf-8') as stream:
                for line in stream:
                    raw=json.loads(line);k=key(raw);call=calls[k];snapshot=snapshots[k]
                    if k in seen:raise ValueError('Duplicate raw call')
                    seen.add(k);plans={p['id']:p for p in raw['result']['plans']}
                    if raw['result']['call']!=call['call']:raise ValueError('Raw call mismatch')
                    causal=causal_record(race,call,snapshot,plans)
                    outcome=outcome_record(race,call,stops,audits[k[0]],[e for e in events if e['driver_number']==k[0]],episode_by_key[k])
                    suffix=Path(race)/k[0]/f'{k[1]}.json'
                    for kind,value in (('causal',causal),('outcomes',outcome)):
                        n,z=save(Path(kind)/suffix,value);prefix='causal' if kind=='causal' else 'outcome'
                        sizes[race][prefix+'_bytes']+=n;sizes[race][prefix+'_gzip_bytes']+=z
            if seen!=set(calls):raise ValueError('Missing raw record')
            driver_states={str(c['driver_number']):snapshots[key(c)]['state']['subject_driver'] for c in calls.values()}
            catalog.append({'key':race,'name':f"{data['race']} {data['year']}",'circuit':circuit,'scheduled_laps':data['scheduled_laps'],
                'drivers':sorted([{'number':d,'abbreviation':s['driver'],'team':s['team']} for d,s in driver_states.items()],key=lambda d:d['abbreviation'])})
            total+=count
    save(Path('catalog.json'),{'schema_version':1,'selector_label':'Archive: top-ten finishers from five races, decision-engine v1',
        'engine_tag':TAG,'races':catalog,'causal_path':'causal/{race}/{driver}/{lap}.json','outcome_path':'outcomes/{race}/{driver}/{lap}.json',
        'unavailable_message':'No archived decision at this cutoff','spoiler_boundary':'Accidental-spoiler prevention only; records are directly accessible.'})
    if total!=2409:raise ValueError('Expected all 2409 calls')
    if any(digest(ROOT/p)!=h for p,h in sources.items()):raise ValueError('Source changed during export')
    manifest={'schema_version':1,'engine_tag':TAG,'engine_commit':COMMIT,'records_verified':total,'engine_runs':0,'network_blocked':True,
        'source_sha256':sources,'output_sha256':hashes,'sizes':sizes,'operational_source_exception':exceptions,
        'exporter_sha256':digest(__file__),'reservation_policy_sha256':digest(ROOT/'data/access/reservations.json')}
    (output/'manifest.json').write_bytes(encode(manifest))
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUTPUT)
    print(json.dumps(export(parser.parse_args().output)['sizes'],indent=2))
