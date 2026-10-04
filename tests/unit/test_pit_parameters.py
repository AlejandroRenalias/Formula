"""Completed-stop causality and pre-evaluation fallback tests."""
from copy import deepcopy
import pytest
from src.core.models import LapObservation,TireCompound
from src.calculators.tyre_model import TyreModel
from src.evaluation.snapshot import clock
from src.evaluation.pit_parameters import completed_stop_samples,pit_inputs,load_pit_prior


def observations():
    rows=[]
    for n in range(3,10):
        compound=TireCompound.MEDIUM if n<=7 else TireCompound.HARD
        age=n if n<=7 else n-7
        extra=3. if n==7 else 20. if n==8 else 0.
        rows.append(LapObservation(lap_number=n,compound=compound,tyre_age_laps=age,
            lap_time_s=90.+TyreModel.lap_delta_s(compound,age)-.05*n+extra,
            is_pit_in_lap=n==7,is_pit_out_lap=n==8,timestamp=clock(n*100.)))
    return {'1':{'history':rows}}


def data():
    return {'session_start_s':0.,'events':[{'Driver':'1','Time':600.,'NumberOfLaps':6},
       {'Driver':'1','Time':650.,'InPit':True},{'Driver':'1','Time':700.,'NumberOfLaps':7},
       {'Driver':'1','Time':710.,'InPit':False},{'Driver':'1','Time':800.,'NumberOfLaps':8}]}


def test_update_requires_completed_received_out_lap_and_exit():
    d,p=data(),observations()
    assert not completed_stop_samples(d,p,799.)
    samples=completed_stop_samples(d,p,800.)
    assert len(samples)==1
    assert samples[0]['in_lap_loss_s']==pytest.approx(3.)
    assert samples[0]['out_lap_loss_s']==pytest.approx(20.)
    assert samples[0]['source_session_s']==800.
    d['events']=[r for r in d['events'] if r.get('InPit') is not False]
    assert not completed_stop_samples(d,p,850.)


def test_future_poisoning_and_truncation_do_not_change_pit_inputs():
    d,p=data(),observations();before=pit_inputs(d,p,850.)
    changed=deepcopy(p)
    for r in changed['1']['history']:
        if r.timestamp.timestamp()>850:r.lap_time_s=99999.
    poison=deepcopy(d);poison['events'].append({'Driver':'1','Time':9999.,'InPit':True})
    assert pit_inputs(poison,changed,850.)==before
    prefix={'1':{'history':[r for r in p['1']['history'] if r.timestamp.timestamp()<=850.]}}
    assert pit_inputs(d,prefix,850.)==before
    assert before[2]['sample_count']==1 and not before[2]['fallback_used']
    assert before[2]['latest_source_session_s']<=850.


def test_external_fallback_is_pre_evaluation_and_same_race_update_is_shrunk():
    prior,_=load_pit_prior();total,share,audit=pit_inputs(data(),observations(),600.)
    assert audit['fallback_used'] and audit['sample_count']==0
    assert prior['latest_available_year']==2019
    assert total==pytest.approx(prior['green_total_loss_s'])
    assert share==pytest.approx(prior['in_lap_fraction'])
    _,_,updated=pit_inputs(data(),observations(),850.)
    assert updated['prior_weight']==pytest.approx(5/6)
    assert updated['in_lap_loss_s']==pytest.approx((5*prior['in_lap_loss_s']+3)/6)

def test_venue_specific_prior_preserves_france_entry_heavy_timing():
    prior,_=load_pit_prior()
    a=pit_inputs({**data(),'race':'Bahrain'},observations(),600.)
    b=pit_inputs({**data(),'race':'France'},observations(),600.)
    assert a[1]<.2 and b[1]>.8
    assert a[2]['prior_venue']=='Bahrain' and b[2]['prior_venue']=='France'
    assert b[0]==pytest.approx(prior['by_venue']['France']['green_total_loss_s'])
