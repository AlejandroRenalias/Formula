"""Known-slope fitting, compound fallback and cutoff-proof integration."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from src.core.models import LapObservation,TireCompound,TrackStatus
from src.calculators.tyre_model import TyreModel
from src.calculators.projection import ProjectionConfig,Policy,Scenario,simulate_policy
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.evaluation.snapshot import clock,median_pace_anchor
from src.evaluation.wear_parameters import estimate_wear


def histories(rate=.2):
    result={}
    for driver,base in (('1',90.),('2',115.)):
        result[driver]={'history':[LapObservation(lap_number=n,lap_time_s=base+rate*(n+10)
            +.15*max(0,n+10-15)-.05*n,tyre_age_laps=n+10,compound=TireCompound.SOFT,
            timestamp=clock(n*100.)) for n in range(5,16)]}
    return result


def test_within_stint_pooling_recovers_slope_despite_driver_offsets_and_cliff():
    rates,audit=estimate_wear({'events':[]},histories(),1600.)
    a=audit['SOFT']
    assert a['raw_slope_s_per_lap']==pytest.approx(.2)
    assert a['sample_count']==22 and a['driver_count']==2
    assert rates['SOFT']==pytest.approx((60*.12+22*.2)/82)
    assert a['prior_weight']==pytest.approx(60/82)
    assert not a['fallback_used'] and a['latest_source_session_s']==1500.
    assert rates['HARD']==.04 and audit['HARD']['fallback_used']
    assert audit['HARD']['sample_count']==0 and audit['HARD']['latest_source_session_s']==0.


def test_future_lap_and_pit_event_poisoning_and_truncation_leave_estimates_equal():
    data={'events':[]};past=histories();before=estimate_wear(data,past,900.)
    poisoned=deepcopy(past)
    for p in poisoned.values():
        for r in p['history']:
            if r.timestamp.timestamp()>900:r.lap_time_s=99999.;r.tyre_age_laps=999
    future={'events':[{'Driver':'1','Time':9999.,'NumberOfLaps':999,'InPit':True}]}
    assert estimate_wear(future,poisoned,900.)==before
    prefix={d:{'history':[r for r in p['history'] if r.timestamp.timestamp()<=900]} for d,p in past.items()}
    assert estimate_wear(data,prefix,900.)==before
    assert all(r['latest_source_session_s']<=900 for r in before[1].values())


def test_thin_data_falls_back_and_negative_empirical_wear_is_constrained_then_shrunk():
    rates,audit=estimate_wear({'events':[]},histories(),600.)
    assert rates['SOFT']==.12 and audit['SOFT']['fallback_used']
    assert audit['SOFT']['available_clean_lap_count']==4 and audit['SOFT']['sample_count']==0
    rates,audit=estimate_wear({'events':[]},histories(-.2),1600.)
    assert audit['SOFT']['clipped_to_nonnegative']
    assert rates['SOFT']==pytest.approx(60*.12/82)


def test_pit_in_and_out_laps_do_not_pollute_regression():
    p=histories();data={'events':[{'Driver':'1','Time':900.,'NumberOfLaps':9},
        {'Driver':'1','Time':950.,'InPit':True},{'Driver':'1','Time':1010.,'InPit':False}]}
    for r in p['1']['history']:
        if r.lap_number in (10,11):r.lap_time_s+=1000.
    _,a=estimate_wear(data,p,1600.)
    assert a['SOFT']['raw_slope_s_per_lap']==pytest.approx(.2)
    assert a['SOFT']['sample_count']==20
    assert a['SOFT']['qualifying_stint_count']==3


def test_fitted_curve_reanchors_observed_median_and_projection_uses_compound_rate():
    rows=[LapObservation(lap_number=n,tyre_age_laps=n,compound=TireCompound.MEDIUM,
        lap_time_s=100.+.4+.2*n-.05*n,timestamp=clock(n*100.)) for n in range(5,9)]
    base,_,_=median_pace_anchor(rows,8,{'MEDIUM':.2})
    assert base==pytest.approx(99.6)
    s=SyntheticRaceAdapter.create_race_state(current_lap=18)
    subject=s.subject_driver.model_copy(update={'current_compound':TireCompound.MEDIUM,'stint_length_laps':10})
    s=s.model_copy(update={'subject_driver':subject,'total_laps':21,'competitors':[],'track_status':TrackStatus.GREEN})
    c=ProjectionConfig(base_pace_s=100.,degradation_scale=1.,degradation_rates_s_per_lap={'MEDIUM':.2})
    trace=simulate_policy(s,Policy(id='hold',label='Hold',max_stops=0,react_to_weather=False),Scenario(None,0.,1.),c,fixed_schedule=True)
    lap_times=[b-a for a,b in zip(trace.times,trace.times[1:])]
    assert lap_times[1]-lap_times[0]==pytest.approx(.2-.05)


@pytest.mark.parametrize('rates',[{'MEDIUM':-.1},{'SOFT':float('inf')},{'UNKNOWN':.1}])
def test_invalid_rate_overrides_are_rejected(rates):
    with pytest.raises(ValueError):ProjectionConfig(degradation_rates_s_per_lap=rates)
