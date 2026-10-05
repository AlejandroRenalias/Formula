"""Agreement event matching, censoring and causal decision isolation."""
from copy import deepcopy
import pytest
from tools.agreement_scoring import match,episodes,score
from src.evaluation.offline import network_blocked
from src.evaluation.snapshot import build_snapshot,crossings
from src.calculators.projection import project
from tests.unit.test_evaluation import dataset


def test_matching_maximizes_cardinality_before_nearest_distance():
    assert match([{'lap':10},{'lap':11}],[{'lap':9},{'lap':10}],1)==[(0,0),(1,1)]
    assert match([{'lap':10},{'lap':12}],[{'lap':11}],1)==[(0,0)]
    assert match([{'lap':5}],[{'lap':8}],1)==[]


def test_episode_first_alert_is_not_shifted_toward_team_stop_and_gaps_censor():
    calls=[{'lap':n,'call':c,'cutoff_session_s':n*100,'directional_stratum':False} for n,c in
           ((5,'STAY_OUT'),(6,'BOX_NOW'),(7,'BOX_NOW'),(9,'BOX_NOW'),(10,'STAY_OUT'),(11,'BOX_NOW'))]
    es=episodes(calls)
    assert [(e['lap'],e['left_censored']) for e in es]==[(6,False),(9,True),(11,False)]
    assert match(es,[{'lap':8}],1)==[(1,0)]


def test_missing_snapshot_is_not_stay_and_phase_recall_uses_team_phase():
    def c(n,call):return {'driver_number':'1','lap':n,'call':call,'cutoff_session_s':n*100,
        'directional_stratum':False,'recommended':'box_now' if call=='BOX_NOW' else 'wait', 'stay_to_finish_available':False}
    calls=[c(13,'STAY_OUT'),c(14,'BOX_NOW'),c(16,'STAY_OUT')]
    data={'scheduled_laps':56,'laps':[{'Driver':'1','NumberOfLaps':16,'PitInTime':1550},
                                    {'Driver':'1','NumberOfLaps':41,'PitInTime':4050}]}
    m,a=score(calls,data)
    assert m['all']['precision']==m['all']['recall']==1
    assert m['all']['unobservable_team_stops']==1
    assert m['phase']['5-14']['tp_precision']==1
    assert m['phase']['15-29']['tp_recall']==1
    assert m['timing']['1']['all']['mean_laps']==-1
    assert m['timing']['1']['post_observed_matches']==0


def test_causal_projection_survives_future_poisoning_and_truncation():
    data=dataset();base=build_snapshot(data,'1',8)
    poisoned=deepcopy(data)
    for key in ('events','tyres','weather','track_status'):
        poisoned[key]=[r for r in poisoned[key] if r['Time']<=800]
    for row in poisoned['laps']:
        if row['Time']>800:
            row['LapTime']='00:00:01';row['PitInTime']=99999
    changed=build_snapshot(poisoned,'1',8)
    truncated=deepcopy(data)
    for key in ('events','tyres','weather','track_status','laps'):
        truncated[key]=[r for r in truncated[key] if r['Time']<=800]
    prefix=build_snapshot(truncated,'1',8,cutoff_s=800,gap_proxy={'2':crossings(data,'2')[8]})
    assert base==changed==prefix
    config=base.config.model_copy(update={'samples_per_weather_branch':2})
    with network_blocked():
        outputs=[project(s.state.model_copy(update={'total_laps':20}),config=config,include_flips=False) for s in (base,changed,prefix)]
    assert outputs[0]==outputs[1]==outputs[2]


def test_actual_future_plan_is_not_consumed_by_decision_call(monkeypatch):
    from tools.evaluate_agreement import call
    snap=build_snapshot(dataset(),'1',8)
    record={'driver_number':'1','lap':8,'state':snap.state.model_dump(mode='json'),
            'config':snap.config.model_copy(update={'samples_per_weather_branch':2}).model_dump(mode='json'),
            'audit':snap.audit,'actual_subject_plan':[{'lap':10,'compound':'HARD'}]}
    changed=deepcopy(record);changed['actual_subject_plan']=[{'lap':9,'compound':'SOFT'},{'lap':20,'compound':'MEDIUM'}]
    with network_blocked():
        a,rawa=call(record,'test');b,rawb=call(changed,'test')
    assert rawa==rawb
    assert a['call']==b['call'] and a['recommended']==b['recommended']
