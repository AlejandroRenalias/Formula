from copy import deepcopy
import pytest
from src.core.models import LapObservation,TireCompound
from src.evaluation.snapshot import clock,median_pace_anchor
from src.evaluation.joint_parameters import estimate_joint
from src.calculators.tyre_model import TyreModel
from src.calculators.projection import ProjectionConfig


def streams():
    p={};rates={'SOFT':.2,'MEDIUM':.13,'HARD':.09}
    for d in range(30):
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
