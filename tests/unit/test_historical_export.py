from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from tools.export_historical import ROOT, OUTPUT, RACES, COUNTS, causal_record, physical_stops, outcome_record, encode, verify_sources
from src.evaluation.offline import network_blocked

def source(race):
    folder=ROOT/'docs/evaluation/agreement'/race
    snapshots=ROOT/'data/cache/evaluation'/race/('snapshots_held_out.jsonl' if race in RACES[3:] else 'snapshots_parameters_wear.jsonl')
    records={(str(r['driver_number']),r['lap']):r for r in map(json.loads,snapshots.read_text().splitlines())}
    calls={(str(c['driver_number']),c['lap']):c for c in map(json.loads,(folder/'calls.jsonl').read_text().splitlines())}
    return folder,records,calls

def test_all_2409_records_match_saved_calls_plans_and_states_without_engine():
    total=0
    with network_blocked(),patch('src.calculators.projection.project',side_effect=AssertionError('No engine')),patch('src.calculators.projection.sample_scenarios',side_effect=AssertionError('No samples')),patch('src.evaluation.snapshot.build_snapshot',side_effect=AssertionError('No replay')):
        verify_sources()
        for race,count in zip(RACES,COUNTS):
            folder,records,calls=source(race)
            assert len(calls)==count
            with gzip.open(folder/'raw_calls.jsonl.gz','rt') as stream:
                for line in stream:
                    raw=json.loads(line);k=(str(raw['driver_number']),raw['lap']);c=calls[k];s=records[k]['state']
                    actual=json.loads((OUTPUT/'causal'/race/k[0]/f'{k[1]}.json').read_text())
                    assert actual['call']==c['call']==raw['result']['call']
                    assert actual['margin_s']==c['call_margin_s']
                    assert actual['subject']==s['subject_driver'] and actual['field']==s['competitors']
                    assert actual['track_status']==s['track_status'] and actual['observed_weather']==s['observed_weather']
                    assert actual['stay_to_finish_available']==c['stay_to_finish_available']
                    assert actual['recommended_policy_id']==c['recommended']
                    for name,side in [('best_box','BOX_NOW'),('best_stay','STAY_OUT')]:
                        p=next(p for p in raw['result']['plans'] if p['id']==c['best_policies_by_call'][side])
                        assert actual[name]['policy']==p['policy']
                        assert actual[name]['mean_time_to_finish_s']==p['mean_time_to_finish_s']
                        assert actual[name]['invalid_probability']==p['invalid_probability']
                    for name in actual['confidence']:assert actual['confidence'][name]==c['call_confidence'][name]
                    assert abs(actual['box_minus_stay_s'])==pytest.approx(actual['margin_s'],abs=1e-9)
                    label=json.loads((OUTPUT/'outcomes'/race/k[0]/f'{k[1]}.json').read_text())
                    assert label['id']==actual['id']
                    assert label['formula_agrees_with_team']==(actual['call']==label['team_action_within_one_lap'])
                    for stop in label['future_stops_in_window']:
                        assert stop['entry_session_s']>actual['cutoff_session_s']
                        assert abs(stop['boundary_lap']-actual['lap'])<=1
                    total+=1
    assert total==2409

def example():
    folder,records,calls=source('bahrain_2021')
    with gzip.open(folder/'raw_calls.jsonl.gz','rt') as stream:
        raw=json.loads(next(stream))
    k=(str(raw['driver_number']),raw['lap'])
    return calls[k],records[k],{p['id']:p for p in raw['result']['plans']}

def test_future_outcome_poisoning_and_truncation_leave_causal_bytes_identical():
    c,r,p=example();base=encode(causal_record('bahrain_2021',c,r,p))
    for future in ({'stops':[{'lap':999,'compound':'WET'}],'results':[1]},None):
        changed=deepcopy(r);changed['actual_subject_plan']=future
        changed['future_results']={'position':1,'lap_time':1,'neutralisation':'SC'}
        changed['state']['future_results']={'position':1,'lap_time':1}
        cc=deepcopy(c);cc['record_sha256']=hashlib.sha256(json.dumps(changed,sort_keys=True).encode()).hexdigest()
        cc['directional_stratum']=not c['directional_stratum']
        assert encode(causal_record('bahrain_2021',cc,changed,p))==base
    # Another record or outcome file is never an argument to causal conversion.
    assert 'actual_subject_plan' not in json.loads(base)

def test_future_parameter_and_snapshot_corruption_fail_closed():
    c,r,p=example();changed=deepcopy(c)
    changed['parameter_source_session_s']['base_pace']=c['cutoff_session_s']+1
    with pytest.raises(ValueError,match='timestamp'):causal_record('bahrain_2021',changed,r,p)
    r['state']['subject_driver']['position']=99
    with pytest.raises(ValueError,match='Snapshot'):causal_record('bahrain_2021',c,r,p)

def test_no_outcome_keys_or_files_in_public_causal_records():
    forbidden={'actual_subject_plan','actual_tyres','results','actual_remaining_stops','team_stop','accepted_episode','formula_agrees_with_team','tags','future_stops_in_window','directional_stratum'}
    def inspect(value):
        if isinstance(value,dict):
            assert not forbidden.intersection(value)
            for v in value.values():inspect(v)
        elif isinstance(value,list):
            for v in value:inspect(v)
    for p in (OUTPUT/'causal').rglob('*.json'):inspect(json.loads(p.read_text()))
    assert len(list((OUTPUT/'causal').rglob('*.json')))==len(list((OUTPUT/'outcomes').rglob('*.json')))==2409
    assert not list(OUTPUT.glob('*.jsonl'))

def test_export_manifest_hashes_and_no_result_ranking_in_catalog():
    m=json.loads((OUTPUT/'manifest.json').read_text())
    assert m['records_verified']==2409 and m['engine_runs']==0 and m['network_blocked']
    for p,h in m['output_sha256'].items():assert hashlib.sha256((OUTPUT/p).read_bytes()).hexdigest()==h
    catalog=json.loads((OUTPUT/'catalog.json').read_text())
    assert catalog['selector_label']=='Archive: top-ten finishers from five races, decision-engine v1'
    for race in catalog['races']:
        assert len(race['drivers'])==10
        assert all(set(d)=={'number','abbreviation','team'} for d in race['drivers'])

def test_no_already_observed_stop_can_earn_pointwise_box_agreement():
    c={'driver_number':'1','lap':10,'cutoff_session_s':1000,'call':'BOX_NOW'}
    stop={'driver_number':'1','boundary_lap':9,'entry_session_s':999}
    label=outcome_record('bahrain_2021',c,[stop],{'matches':[]},[],None)
    assert label['team_action_within_one_lap']=='STAY_OUT' and label['team_stop'] is None

def test_all_classified_missed_stop_labels_match_physical_cached_stops():
    events=[json.loads(line) for line in (ROOT/'docs/evaluation/disagreement/events.jsonl').read_text().splitlines()]
    for race in RACES:
        data=json.loads((ROOT/'data/cache/evaluation'/race/'session.json').read_text());stops=physical_stops(data)
        for e in events:
            if e['race']==race and e['direction']=='FN':
                s=next(s for s in stops if s['driver_number']==e['driver_number'] and s['entry_session_s']==e['event']['entry_session_s'])
                assert s['boundary_lap']==e['event']['lap']
                assert s['compound']==e['team_stop_context']['fitted_compound']
