"""Report-only observable disagreement tags; all decisions are saved inputs."""
from collections import Counter
from itertools import combinations
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

from src.evaluation.offline import network_blocked
from tools.agreement_inputs import RACES,inputs,read_rows,sha

SOURCE=Path('docs/evaluation/agreement')
OUTPUT=Path('docs/evaluation/disagreement')
TAGS=('neutralisation','undercut_cover','compound_outside_candidates','strategy_count','late_race')
NEUTRAL={'4':'SC','6':'VSC','7':'VSC'}

def write(p,value):p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def valid(x):return isinstance(x,(int,float)) and not isinstance(x,bool)
def key(c):return c['driver_number'],c['lap']
def status_at(data,t):
    rows=[r for r in data['track_status'] if valid(r.get('Time')) and r['Time']<=t]
    return NEUTRAL.get(str(max(rows,key=lambda r:r['Time'])['Status'])) if rows else None

def episodes(data):
    result=[];current=None
    for r in sorted((r for r in data['track_status'] if valid(r.get('Time'))),key=lambda r:r['Time']):
        kind=NEUTRAL.get(str(r['Status']))
        if kind and current is None:current={'start_session_s':r['Time'],'end_session_s':None,'kinds':[kind]}
        elif kind and kind not in current['kinds']:current['kinds'].append(kind)
        elif not kind and current is not None:
            current['end_session_s']=r['Time'];result.append(current);current=None
    if current is not None:result.append(current)
    return result

def physical_stops(data):
    finish={}
    for r in data['laps']:
        if valid(r.get('Time')) and r['NumberOfLaps']>0:
            finish.setdefault(r['Driver'],{})[int(r['NumberOfLaps'])]=r['Time']
    ends={d:times[max(times)] for d,times in finish.items()}
    result=[]
    for r in data['laps']:
        entry=r.get('PitInTime');d=r['Driver']
        if not valid(entry) or entry<=0 or entry>ends.get(d,float('-inf')):continue
        exits=sorted((q for q in data['laps'] if q['Driver']==d and valid(q.get('PitOutTime')) and q['PitOutTime']>entry),key=lambda q:q['PitOutTime'])
        out=exits[0] if exits else None
        labels=[q for q in data.get('actual_tyres',[]) if str(q['DriverNumber'])==d and out and q['LapNumber']==out['NumberOfLaps']]
        compound=labels[-1].get('Compound') if labels else None
        if compound not in ('SOFT','MEDIUM','HARD','INTERMEDIATE','WET'):compound=None
        cross=[q['Time'] for q in data['laps'] if q['Driver']==d and valid(q.get('Time')) and q['NumberOfLaps']>0 and q['Time']<entry]
        result.append({'driver_number':d,'lap':int(r['NumberOfLaps'])-1,'entry_session_s':entry,
            'in_lap_start_session_s':max(cross) if cross else None,'exit_session_s':out['PitOutTime'] if out else None,
            'out_lap':int(out['NumberOfLaps']) if out else None,'fitted_compound':compound,'finish_session_s':ends[d]})
    return sorted(result,key=lambda s:(s['entry_session_s'],s['driver_number']))

def neutral_details(stop,data,neutral):
    if stop is None:return {'tag':None,'reason':'no_physical_team_stop_context','active_at_entry':None,'starts_in_lap':None,'episodes':[]}
    entry=stop['entry_session_s'];start=stop['in_lap_start_session_s']
    rows=[r for r in data['track_status'] if valid(r.get('Time')) and r['Time']<=entry]
    active=status_at(data,entry) if rows else None
    began=[e for e in neutral if start is not None and start<=e['start_session_s']<=entry]
    active_episodes=[e for e in neutral if e['start_session_s']<=entry and (e['end_session_s'] is None or entry<e['end_session_s'])]
    relevant={e['start_session_s']:e for e in began+active_episodes}
    tag=True if active or began else False if rows and start is not None else None
    return {'tag':tag,'active_at_entry':active,'starts_in_lap':bool(began) if start is not None else None,
            'episodes':list(relevant.values()),'in_lap_start_session_s':start,'entry_session_s':entry}

def confidence(c):
    q=c.get('call_confidence')
    if not q:return 'unavailable'
    if c['call']=='STAY_OUT' and q['stay_clearly_better']>=.8:return 'confident_STAY'
    if c['call']=='BOX_NOW' and q['box_clearly_better']>=.8:return 'confident_BOX'
    return 'too_close' if q['too_close_to_call']>=.5 else 'mixed_uncertain'

def margin(c):
    box=c['best_policies_by_call']['BOX_NOW'];stay=c['best_policies_by_call']['STAY_OUT']
    if not box or not stay:return None
    return c['candidate_means_s'][box]-c['candidate_means_s'][stay]

def window(stop,calls,details):
    if stop is None:return {'cutoffs':[],'pre_entry_opportunity':None,'neutralisation_visible_before_entry':None,'post_entry_cutoff':None}
    cc=sorted((c for c in calls if c['driver_number']==stop['driver_number'] and abs(c['lap']-stop['lap'])<=1),key=lambda c:c['cutoff_session_s'])
    out=[]
    for c in cc:
        before=c['cutoff_session_s']<stop['entry_session_s']
        visible=before and c['track_status'] in ('SAFETY_CAR','VSC') and any(e['start_session_s']<=c['cutoff_session_s'] and
             (e['end_session_s'] is None or c['cutoff_session_s']<e['end_session_s']) for e in details['episodes'])
        out.append({'lap':c['lap'],'cutoff_session_s':c['cutoff_session_s'],'before_entry':before,'call':c['call'],
            'recommended':c['recommended'],'best_policies_by_call':c['best_policies_by_call'],'box_minus_stay_s':margin(c),
            'call_margin_s':c['call_margin_s'],'confidence':c['call_confidence'],'confidence_label':confidence(c),
            'track_status':c['track_status'],'neutral_trigger_visible':visible,'record_sha256':c['record_sha256']})
    return {'cutoffs':out,'pre_entry_opportunity':any(c['before_entry'] for c in out),
            'neutralisation_visible_before_entry':any(c['neutral_trigger_visible'] for c in out) if details['tag'] is not None else None,
            'post_entry_cutoff':any(not c['before_entry'] for c in out)}

def plan_summary(p):
    if p is None:return None
    scenarios=p['scenario_stops'];mass=sum(s['weight'] for s in scenarios)
    counts=Counter()
    for s in scenarios:counts[s.get('stop_count',len(s.get('stops',[])))]+=s['weight']/mass
    return {'id':p['id'],'label':p['label'],'policy':p['policy'],'mean_time_to_finish_s':p['mean_time_to_finish_s'],
            'invalid_probability':p['invalid_probability'],'representative_stops':p['stops'],
            'nominal_future_stops':len(p['policy']['dry_stops']),'sampled_stop_count_mass':dict(sorted(counts.items())),
            'sampled_stop_count_mean':sum(n*w for n,w in counts.items()),'sampled_stop_count_min':min(counts),'sampled_stop_count_max':max(counts)}

def reference_evidence(c,records,raw):
    if c is None:return None
    r=records[key(c)];result=raw[key(c)];lookup={p['id']:p for p in result['plans']}
    options=sorted({s['compound'] for p in result['plans'] if p['policy']['max_stops']>0 for s in p['policy']['dry_stops'] if s['lap']==c['lap']})
    return {'driver_number':c['driver_number'],'lap':c['lap'],'cutoff_session_s':c['cutoff_session_s'],
        'call':c['call'],'confidence':c['call_confidence'],'confidence_label':confidence(c),'box_minus_stay_s':margin(c),
        'immediate_box_compounds':options,'recommended':plan_summary(lookup[c['recommended']]),
        'best_BOX':plan_summary(lookup.get(c['best_policies_by_call']['BOX_NOW'])),
        'best_STAY':plan_summary(lookup.get(c['best_policies_by_call']['STAY_OUT'])),
        'snapshot_key':{'driver_number':c['driver_number'],'lap':c['lap']},'track_status':c['track_status']}

def classify(race,direction,event,context,context_basis,calls,records,raw,stops,data,neutral,names):
    driver=event['driver_number']
    if direction=='FN':
        previous=[c for c in calls if c['driver_number']==driver and c['cutoff_session_s']<event['entry_session_s']]
        reference=max(previous,key=lambda c:c['cutoff_session_s']) if previous else None
    else:reference=next(c for c in calls if key(c)==(driver,event['lap']))
    evidence=reference_evidence(reference,records,raw);nd=neutral_details(context,data,neutral);wi=window(context,calls,nd)
    hits=[];rival_unknown=None
    if reference is not None:
        record=records[key(reference)];competitors=record['state']['competitors'];omitted=record['audit']['omitted_rivals']
        for rival in competitors:
            if abs(rival['gap_to_subject_s'])>3:continue
            number=names.get(rival['driver'],rival['driver'])
            for s in stops:
                if s['driver_number']==number and abs(s['lap']-event['lap'])<=2:
                    hits.append({'driver_number':number,'driver':rival['driver'],'gap_s':rival['gap_to_subject_s'],
                                 'direction':'ahead' if rival['gap_to_subject_s']>0 else 'behind' if rival['gap_to_subject_s']<0 else 'level',
                                 'rival_stop_boundary':s['lap'],'offset_laps':s['lap']-event['lap'],'rival_entry_session_s':s['entry_session_s']})
        rival_unknown=not competitors or bool(omitted)
    else:competitors=[];omitted=None;rival_unknown=True
    cover=True if hits else None if rival_unknown else False
    fitted=context['fitted_compound'] if context else None
    outside=fitted not in evidence['immediate_box_compounds'] if fitted and evidence and evidence['immediate_box_compounds'] else None
    remaining=[s for s in stops if s['driver_number']==driver and reference and s['entry_session_s']>reference['cutoff_session_s']]
    nominal=evidence['recommended']['nominal_future_stops'] if evidence else None
    tags={'neutralisation':nd['tag'],'undercut_cover':cover,'compound_outside_candidates':outside,
          'strategy_count':len(remaining)!=nominal if evidence else None,
          'late_race':evidence['recommended']['id']=='stay_to_finish' if evidence else None}
    observed=[t for t in TAGS if tags[t] is True];unknown=[t for t in TAGS if tags[t] is None]
    event_id=f"{race}:{direction}:{driver}:{event['lap']}"
    return {'id':event_id,'race':race,'set':'development' if race in RACES[:3] else 'held_out','direction':direction,
        'driver_number':driver,'driver':next((d['Abbreviation'] for d in data['drivers'] if d['DriverNumber']==driver),driver),
        'event':event,'team_stop_context':context,'team_stop_context_basis':context_basis,
        'context_offset_laps':context['lap']-event['lap'] if context else None,
        'tags':tags,'observed_tags':observed,'unknown_tags':unknown,'none_of_above':not observed,
        'none_with_complete_evidence':not observed and not unknown,'reference':evidence,
        'reference_lap_distance_to_event':event['lap']-reference['lap'] if reference else None,
        'reference_age_to_entry_s':context['entry_session_s']-reference['cutoff_session_s'] if reference and context else None,
        'neutralisation_evidence':nd,'alert_track_status':reference['track_status'] if reference and direction=='FP' else None,
        'visibility':wi,'rival_stop_evidence':hits,'omitted_rivals':omitted,
        'observed_competitor_count':len(competitors),'actual_remaining_stops':remaining,
        'actual_remaining_stop_count':len(remaining) if evidence else None,'recommended_nominal_stop_count':nominal,
        'window_has_BOX':any(c['call']=='BOX_NOW' for c in wi['cutoffs']) if direction=='FN' else None,
        'window_has_confident_STAY':any(c['confidence_label']=='confident_STAY' for c in wi['cutoffs']) if direction=='FN' else None,
        'window_pre_entry_confident_STAY':any(c['before_entry'] and c['confidence_label']=='confident_STAY' for c in wi['cutoffs']) if direction=='FN' else None,
        'window_has_too_close':any(c['confidence_label']=='too_close' for c in wi['cutoffs']) if direction=='FN' else None,
        'window_pre_entry_too_close':any(c['before_entry'] and c['confidence_label']=='too_close' for c in wi['cutoffs']) if direction=='FN' else None}

def summarise(events):
    combinations_count=Counter('+'.join(e['observed_tags']) if e['observed_tags'] else 'none' for e in events)
    out={'n':len(events),'tag_counts':{t:sum(e['tags'][t] is True for e in events) for t in TAGS},
         'unknown_counts':{t:sum(e['tags'][t] is None for e in events) for t in TAGS},
         'none':sum(e['none_of_above'] for e in events),'none_complete':sum(e['none_with_complete_evidence'] for e in events),
         'pairwise_overlap':{a+' & '+b:sum(e['tags'][a] is True and e['tags'][b] is True for e in events) for a,b in combinations(TAGS,2)},
         'exact_observed_combinations':dict(sorted(combinations_count.items())),
         'multiple_tags':sum(len(e['observed_tags'])>1 for e in events),
         'neutralisation_visible':sum(e['tags']['neutralisation'] is True and e['visibility']['neutralisation_visible_before_entry'] is True for e in events),
         'neutralisation_not_visible':sum(e['tags']['neutralisation'] is True and e['visibility']['neutralisation_visible_before_entry'] is False for e in events),
         'no_pre_entry_opportunity':sum(e['visibility']['pre_entry_opportunity'] is False for e in events),
         'missing_team_stop_context':sum(e['team_stop_context'] is None for e in events)}
    if events and events[0]['direction']=='FN':
        for field in ('window_has_BOX','window_has_confident_STAY','window_pre_entry_confident_STAY','window_has_too_close','window_pre_entry_too_close'):
            out[field]=sum(e[field] for e in events)
        out['no_pre_entry_window_call']=sum(not e['visibility']['pre_entry_opportunity'] for e in events)
        out['window_call_labels']=dict(Counter(c['confidence_label'] for e in events for c in e['visibility']['cutoffs']))
        out['pre_entry_window_call_labels']=dict(Counter(c['confidence_label'] for e in events for c in e['visibility']['cutoffs'] if c['before_entry']))
    return out

def select_cards(events,calls_by_race,records_by_race,raw_by_race,stops_by_race):
    result={}
    for group in ('development','held_out'):
        result[group]={}
        for direction in ('FN','FP'):
            candidates=[]
            for e in events:
                if e['set']!=group or e['direction']!=direction:continue
                call_lookup=calls_by_race[e['race']]
                if direction=='FN':
                    cc=[call_lookup[(e['driver_number'],c['lap'])] for c in e['visibility']['cutoffs'] if c['before_entry'] and c['call']=='STAY_OUT' and c['confidence'] is not None]
                    if not cc:continue
                    c=max(cc,key=lambda c:(c['call_confidence']['stay_clearly_better'],margin(c) if margin(c) is not None else float('-inf'),c['lap']))
                    prob=c['call_confidence']['stay_clearly_better'];strength=margin(c)
                else:
                    c=call_lookup[(e['driver_number'],e['event']['lap'])]
                    if c['call_confidence'] is None:continue
                    prob=c['call_confidence']['box_clearly_better'];strength=-margin(c) if margin(c) is not None else None
                candidates.append(((-prob,-strength if strength is not None else float('inf'),e['race'],int(e['driver_number']),e['event']['lap']),e,c))
            cards=[]
            for ranking,e,c in sorted(candidates,key=lambda x:x[0])[:5]:
                record=records_by_race[e['race']][key(c)]
                config=dict(record['config']);config.update(json.loads(Path('data/evaluation/frozen_model.json').read_text())['pace_uncertainty_multipliers'])
                cards.append({'event_id':e['id'],'set':group,'direction':direction,'rank':len(cards)+1,
                    'ranking_confidence_mass':-ranking[0],'ranking_margin_strength_s':-ranking[1],
                    'causal_state':record['state'],'effective_frozen_config':config,'cutoff_audit':record['audit'],
                    'engine':reference_evidence(c,records_by_race[e['race']],raw_by_race[e['race']]),
                    'event_reference':e['reference'],'actual_remaining_team_schedule_at_card':[s for s in stops_by_race[e['race']] if s['driver_number']==e['driver_number'] and s['entry_session_s']>c['cutoff_session_s']],
                    'actual_team_stops_within_primary_window':[s for s in stops_by_race[e['race']] if s['driver_number']==e['driver_number'] and abs(s['lap']-e['event']['lap'])<=1],
                    'team_stop_context':e['team_stop_context'],'actual_event':e['event'],'tags':e['tags']})
            result[group][direction]={'eligible_events':len(candidates),'selected':cards}
    return result

def run():
    OUTPUT.mkdir(exist_ok=True);assert (OUTPUT/'PROTOCOL.md').exists()
    assert not (OUTPUT/'RUN_STARTED.json').exists(),'Report ledger exists; do not reclassify without explicit review.'
    protocol_hash=sha(OUTPUT/'PROTOCOL.md');source_hashes={}
    write(OUTPUT/'RUN_STARTED.json',{'protocol_sha256':protocol_hash,'protocol_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          'report_only':True,'engine_calls':0})
    source_manifest=json.loads((SOURCE/'manifest.json').read_text())
    for name,h in source_manifest['source_sha256'].items():assert sha(name)==h
    source_hashes[str(SOURCE/'manifest.json')]=sha(SOURCE/'manifest.json')
    events=[];records_by_race={};raw_by_race={};calls_by_race={};stops_by_race={}
    with network_blocked(),patch('src.calculators.projection.project',side_effect=AssertionError('Report only')),\
         patch('src.calculators.projection.sample_scenarios',side_effect=AssertionError('No sample reruns')),\
         patch('src.calculators.projection.simulate_policy',side_effect=AssertionError('No simulator reruns')),\
         patch('src.evaluation.snapshot.build_snapshot',side_effect=AssertionError('No state rebuilding')):
        for race in RACES:
            folder=SOURCE/race;m=json.loads((folder/'manifest.json').read_text())
            for name,h in m['output_sha256'].items():assert sha(folder/name)==h
            records,unused,data,input_hashes=inputs(race)
            source_hashes.update(input_hashes)
            calls=read_rows(folder/'calls.jsonl');calls_by_race[race]={key(c):c for c in calls}
            records_by_race[race]={key(r):r for r in records};raw={}
            with gzip.open(folder/'raw_calls.jsonl.gz','rt',encoding='utf-8') as f:
                for line in f:
                    r=json.loads(line)
                    plans=[]
                    for p in r['result']['plans']:
                        minimal={k:p[k] for k in ('id','label','policy','mean_time_to_finish_s','invalid_probability','stops')}
                        minimal['scenario_stops']=[{'weight':s['weight'],'stop_count':len(s['stops'])} for s in p['scenario_stops']]
                        plans.append(minimal)
                    raw[(r['driver_number'],r['lap'])]={'plans':plans}
            raw_by_race[race]=raw
            for c in calls:
                if margin(c) is not None:assert abs(abs(margin(c))-c['call_margin_s'])<1e-9
            stops=physical_stops(data);stops_by_race[race]=stops;neutral=episodes(data)
            names={d['Abbreviation']:d['DriverNumber'] for d in data['drivers']}
            audits=json.loads((folder/'matching_audit.json').read_text());wide={a['driver_number']:a for a in audits if a['tolerance_laps']==10}
            for a in audits:
                if a['tolerance_laps']!=1:continue
                eligible=[s for s in a['all_stops'] if s['observable']]
                for j in a['unmatched_eligible_stop_indices']:
                    event=eligible[j]
                    context=next(s for s in stops if s['driver_number']==event['driver_number'] and s['entry_session_s']==event['entry_session_s'])
                    events.append(classify(race,'FN',event,context,'missed_team_stop',calls,records_by_race[race],raw,stops,data,neutral,names))
                for i in a['unmatched_alert_indices']:
                    event=a['alerts'][i]
                    paired=next((p['stop'] for p in wide[a['driver_number']]['matches'] if p['alert']['lap']==event['lap']),None)
                    context=next((s for s in stops if paired and s['driver_number']==event['driver_number'] and s['entry_session_s']==paired['entry_session_s']),None)
                    basis='accepted_wide_match' if context else None
                    if context is None:
                        cc=[s for s in stops if s['driver_number']==event['driver_number'] and abs(s['lap']-event['lap'])<=10]
                        context=min(cc,key=lambda s:(abs(s['lap']-event['lap']),s['entry_session_s'])) if cc else None
                        basis='nearest_physical_stop_within_10' if context else 'unavailable'
                    events.append(classify(race,'FP',dict(event,driver_number=a['driver_number']),context,basis,calls,records_by_race[race],raw,stops,data,neutral,names))
            accepted=json.loads((folder/'metrics.json').read_text())['all']
            assert sum(e['race']==race and e['direction']=='FN' for e in events)==accepted['fn']
            assert sum(e['race']==race and e['direction']=='FP' for e in events)==accepted['fp']
            for name in ('manifest.json','matching_audit.json','calls.jsonl','raw_calls.jsonl.gz','metrics.json'):source_hashes[str(folder/name)]=sha(folder/name)
            print(race,'classified accepted unmatched events',flush=True)
        summaries={g:{d:summarise([e for e in events if e['set']==g and e['direction']==d]) for d in ('FN','FP')} for g in ('development','held_out')}
        per_race={race:{d:summarise([e for e in events if e['race']==race and e['direction']==d]) for d in ('FN','FP')} for race in RACES}
        cards=select_cards(events,calls_by_race,records_by_race,raw_by_race,stops_by_race)
        assert sha(OUTPUT/'PROTOCOL.md')==protocol_hash
        assert all(sha(p)==h for p,h in source_hashes.items())
        write(OUTPUT/'metrics.json',{'pools':summaries,'races':per_race})
        write(OUTPUT/'case_cards.json',cards)
        (OUTPUT/'events.jsonl').write_text(''.join(json.dumps(e,allow_nan=False)+'\n' for e in events))
        write(OUTPUT/'manifest.json',{'report_only':True,'network_blocked':True,'engine_calls':0,
             'protocol_sha256':protocol_hash,'source_sha256':source_hashes,'reporter_sha256':sha(__file__),
             'events':len(events),'decision_engine_tag':'decision-engine-v1','scoring_unchanged':True,
             'registered_hypothesis':{'timing_direction':'rejected','stratum_observable_stops':11,'stratum_caught_stops':0,'stratum_early_BOX_calls':0}})
    print(json.dumps(summaries,indent=2))

if __name__=='__main__':run()
