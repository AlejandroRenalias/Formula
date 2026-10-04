from copy import deepcopy
import pytest
from src.core.models import LapObservation,TireCompound
from src.evaluation.snapshot import clock,median_pace_anchor
from src.evaluation.joint_parameters import estimate_joint
from src.calculators.tyre_model import TyreModel
from src.calculators.projection import ProjectionConfig


def streams(driver_count=30):
    p={};rates={'SOFT':.2,'MEDIUM':.13,'HARD':.09}
    for d in range(driver_count):
        rs=[]
        for n in range(3,91):
            index=(n+d*3)//22;c=TireCompound(('SOFT','MEDIUM','HARD')[index%3]);age=(n+d*3)%22+1
            specs=TyreModel.get_compound_specs(c)
            rs.append(LapObservation(lap_number=n,tyre_age_laps=age,compound=c,
                lap_time_s=100+d+specs.base_pace_delta_s+rates[c.value]*age-.15*n+.15*max(0,age-specs.cliff_lap_threshold),timestamp=clock(n*100.)))
        p[str(d)]={'history':rs}
    return p


def test_joint_fit_separates_race_trend_and_wear_despite_driver_offsets():
    rates,audit,trend,t=estimate_joint({'events':[]},streams(),9000.)
    assert not t['fallback_used'] and t['sample_count']==2640
    assert trend==pytest.approx(-.15,abs=.01)
    for c,target in {'SOFT':.2,'MEDIUM':.13,'HARD':.09}.items():
        assert rates[c]==pytest.approx(target,abs=.01)
        assert not audit[c]['fallback_used'] and audit[c]['latest_source_session_s']==9000.
    shifted=streams()
    for p in shifted.values():
        for r in p['history']:r.lap_time_s+=100.
    other=estimate_joint({'events':[]},shifted,9000.)
    assert other[0]==pytest.approx(rates) and other[2]==pytest.approx(trend)


def test_joint_fit_future_poison_and_truncation_equal():
    p=streams();base=estimate_joint({'events':[]},p,4500.);bad=deepcopy(p)
    for driver in bad.values():
        for r in driver['history']:
            if r.timestamp.timestamp()>4500:r.lap_time_s=99999.;r.tyre_age_laps=999
    assert estimate_joint({'events':[{'Driver':'0','Time':99999.,'InPit':True}]},bad,4500.)==base
    truncated={d:{'history':[r for r in p['history'] if r.timestamp.timestamp()<=4500.]} for d,p in p.items()}
    assert estimate_joint({'events':[]},truncated,4500.)==base
    assert all(a['latest_source_session_s']<=4500 for a in base[1].values())


def test_collinear_early_stint_falls_back_and_unused_compounds_have_counts():
    p={'1':{'history':[LapObservation(lap_number=n,tyre_age_laps=n,compound=TireCompound.SOFT,
        lap_time_s=100+.2*n-.15*n,timestamp=clock(n*100.)) for n in range(3,13)]}}
    rates,a,trend,t=estimate_joint({'events':[]},p,1200.)
    assert t['fallback_used'] and trend==-.05 and t['sample_count']==0
    assert a['HARD']['fallback_used'] and a['HARD']['sample_count']==0 and rates['HARD']==.04
    assert a['SOFT']['sample_count']==10


def test_trend_reanchors_median_consistently_and_invalid_trend_rejected():
    rows=[LapObservation(lap_number=n,tyre_age_laps=n,compound=TireCompound.MEDIUM,
        lap_time_s=100+.4+.2*n-.15*n,timestamp=clock(n*100.)) for n in range(5,9)]
    base,_,_=median_pace_anchor(rows,8,{'MEDIUM':.2},-.15)
    assert base==pytest.approx(98.8)
    with pytest.raises(ValueError):ProjectionConfig(race_trend_s_per_lap=float('nan'))

def test_offsets_use_multi_compound_contrasts_with_default_gauge_and_shrinkage():
    p=streams(300);truth={'SOFT':0.,'MEDIUM':1.4,'HARD':2.6}
    for driver in p.values():
        for r in driver['history']:r.lap_time_s+=truth[r.compound.value]-TyreModel.get_compound_specs(r.compound).base_pace_delta_s
    rates,a,trend,t,offsets,o=estimate_joint({'events':[]},p,9000.,fit_offsets=True)
    assert offsets['SOFT']==0. and o['SOFT']['fallback_reason']=='reference_gauge'
    for c in ('MEDIUM','HARD'):
        assert not o[c]['fallback_used'] and o[c]['sample_count']>0 and o[c]['driver_count']==300
        assert o[c]['latest_source_session_s']==9000.
        assert offsets[c]==pytest.approx(truth[c],abs=.4)
    assert trend==pytest.approx(-.15,abs=.02)
    assert rates['SOFT']==pytest.approx(.2,abs=.025)


def test_offset_future_poison_truncation_and_single_compound_default():
    p=streams();base=estimate_joint({'events':[]},p,4500.,fit_offsets=True);bad=deepcopy(p)
    for driver in bad.values():
        for r in driver['history']:
            if r.timestamp.timestamp()>4500:r.lap_time_s=99999.;r.compound=TireCompound.HARD;r.tyre_age_laps=999
    assert estimate_joint({'events':[{'Driver':'0','Time':99999.,'InPit':True}]},bad,4500.,fit_offsets=True)==base
    truncated={d:{'history':[r for r in p['history'] if r.timestamp.timestamp()<=4500.]} for d,p in p.items()}
    assert estimate_joint({'events':[]},truncated,4500.,fit_offsets=True)==base
    for prefix in p.values():prefix['history']=[r for r in prefix['history'] if r.compound==TireCompound.MEDIUM]
    *_,offsets,o=estimate_joint({'events':[]},p,9000.,fit_offsets=True)
    assert offsets=={'SOFT':0.,'MEDIUM':.4,'HARD':.9}
    assert all(v['fallback_used'] and v['sample_count']==0 for v in o.values())
    one=streams(1)
    one['0']['history']=[r for r in one['0']['history'] if r.lap_number<=35]
    *_,offsets,o=estimate_joint({'events':[]},one,3500.,fit_offsets=True)
    assert o['MEDIUM']['fallback_reason']=='rank_deficient_contrast' and offsets['MEDIUM']==.4



def test_disconnected_soft_keeps_defaults_and_medium_reference():
    p=streams()
    for prefix in p.values():prefix['history']=[r for r in prefix['history'] if r.compound!=TireCompound.SOFT]
    *_,offsets,o=estimate_joint({'events':[]},p,9000.,fit_offsets=True)
    assert offsets['SOFT']==0. and o['SOFT']['fallback_used'] and o['SOFT']['latest_source_session_s']==0.
    assert offsets['MEDIUM']==.4 and o['MEDIUM']['fallback_reason']=='reference_gauge'
    assert o['HARD']['reference_compound']=='MEDIUM' and not o['HARD']['fallback_used']


def test_offset_override_and_anchor_consistency_and_validation():
    rows=[LapObservation(lap_number=n,tyre_age_laps=n,compound=TireCompound.MEDIUM,
        lap_time_s=100+1.4+.2*n-.15*n,timestamp=clock(n*100.)) for n in range(5,9)]
    base,_,_=median_pace_anchor(rows,8,{'MEDIUM':.2},-.15,{'MEDIUM':1.4})
    assert base==pytest.approx(98.8)
    assert TyreModel.lap_delta_s(TireCompound.HARD,10,degradation_rate_s_per_lap=.09,compound_offset_s=2.6)==pytest.approx(3.5)
    from src.adapters.synthetic_adapter import SyntheticRaceAdapter
    from src.calculators.projection import Policy,Stop,Scenario,simulate_policy
    from src.core.models import TrackStatus
    state=SyntheticRaceAdapter.create_race_state(current_lap=18)
    subject=state.subject_driver.model_copy(update={'current_compound':TireCompound.MEDIUM,'stint_length_laps':10})
    state=state.model_copy(update={'subject_driver':subject,'total_laps':22,'competitors':[],'track_status':TrackStatus.GREEN})
    policy=Policy(id='switch',label='Switch',dry_stops=(Stop(lap=19,compound=TireCompound.HARD),),react_to_weather=False)
    a=ProjectionConfig(base_pace_s=100.,degradation_scale=1.)
    b=a.model_copy(update={'compound_offsets_s':{'HARD':2.6}})
    before=simulate_policy(state,policy,Scenario(None,0.,1.),a,fixed_schedule=True)
    after=simulate_policy(state,policy,Scenario(None,0.,1.),b,fixed_schedule=True)
    assert after.times[1]==before.times[1]
    assert after.times[-1]-before.times[-1]==pytest.approx(3*(2.6-.9))
    for offsets in ({'SOFT':float('inf')},{'UNKNOWN':1.}):
        with pytest.raises(ValueError):ProjectionConfig(compound_offsets_s=offsets)
