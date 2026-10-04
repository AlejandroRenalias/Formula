"""Causal ongoing duration and neutralization lifecycle tests."""
from copy import deepcopy
import pytest
from src.evaluation.neutralization_prior import remaining_seconds,ongoing_inputs
from src.calculators.projection import ProjectionConfig,_status
from src.core.models import TrackStatus
from src.adapters.synthetic_adapter import SyntheticRaceAdapter


def test_remaining_duration_conditions_on_survival_and_uses_documented_tail():
    prior={"sc_durations_s":[60.,180.,300.],"tail_remaining_assumption_s":{"SC":90.}}
    assert remaining_seconds(prior,"SC",0)==180
    assert remaining_seconds(prior,"SC",100)==140
    assert remaining_seconds(prior,"SC",200)==100
    assert remaining_seconds(prior,"SC",400)==90


def test_ongoing_onset_uses_only_prefix_and_merges_vsc_ending_code():
    track=[{"Time":0.,"Status":"1"},{"Time":100.,"Status":"6"},{"Time":140.,"Status":"7"},{"Time":190.,"Status":"1"}]
    expected=ongoing_inputs(track,160.,TrackStatus.VSC,100.)
    changed=deepcopy(track);changed[-1]["Time"]=99999.;changed.append({"Time":170.,"Status":"4"})
    assert ongoing_inputs(changed,160.,TrackStatus.VSC,100.)==expected
    assert expected[1]["onset_session_s"]==100.
    assert expected[1]["elapsed_s"]==60.


@pytest.mark.parametrize("status",[TrackStatus.SAFETY_CAR,TrackStatus.VSC])
def test_neutralization_ends_at_finite_expected_boundary(status):
    s=SyntheticRaceAdapter.create_race_state(current_lap=18).model_copy(update={"track_status":status})
    c=ProjectionConfig(ongoing_neutralization_laps=2)
    assert _status(s,19,c)==status and _status(s,20,c)==status
    assert _status(s,21,c)==TrackStatus.GREEN

def test_zero_risk_preserves_original_draws_and_timelines():
    from src.calculators.projection import sample_scenarios
    s=SyntheticRaceAdapter.create_race_state(current_lap=18)
    c=ProjectionConfig()
    assert all(not x.neutralization_events for x in sample_scenarios(s,c))
    assert sample_scenarios(s,c)==sample_scenarios(s,c.model_copy(update={'sc_duration_prior_s':(300.,)}))


@pytest.mark.parametrize('kind',['SC','VSC'])
def test_forced_sampled_events_end_price_actual_stops_and_apply_pace(kind):
    from src.calculators.projection import sample_scenarios,simulate_policy,Policy,Stop,_pit_loss
    from src.core.models import TireCompound
    s=SyntheticRaceAdapter.create_race_state(current_lap=18).model_copy(update={'competitors':[],'total_laps':23,'track_status':TrackStatus.GREEN})
    c=ProjectionConfig(samples_per_weather_branch=4,base_pace_s=100.,pit_loss_spread_s=0.,
        degradation_spread_fraction=0.,pit_in_lap_fraction=.5,
        **({'future_sc_probability':1.,'sc_duration_prior_s':(200.,),'sc_pace_multiplier':1.4}
           if kind=='SC' else {'future_vsc_probability':1.,'vsc_duration_prior_s':(200.,),'vsc_pace_multiplier':1.4}))
    draws=sample_scenarios(s,c)
    assert draws==sample_scenarios(s,c)
    event=draws[0].neutralization_events[0]
    assert event==(19,kind,2)
    assert all(b[0]>=a[0]+a[2] for a,b in zip(draws[0].neutralization_events,draws[0].neutralization_events[1:]))
    plan=Policy(id='fixed',label='Fixed',react_to_weather=False,dry_stops=(Stop(lap=18,compound=TireCompound.HARD),))
    trace=simulate_policy(s,plan,draws[0],c,fixed_schedule=True)
    expected=s.pit_loss.sc_pit_loss_s if kind=='SC' else s.pit_loss.vsc_pit_loss_s
    assert trace.stops[0]['pit_loss_s']==expected
    assert trace.stops[0]['in_lap_loss_s']==trace.stops[0]['out_lap_loss_s']==expected/2
    assert _pit_loss(s,draws[0],19,c)==expected
    green=simulate_policy(s,plan,draws[0].__class__(None,0.,1.),ProjectionConfig(base_pace_s=100.,pit_in_lap_fraction=.5),fixed_schedule=True)
    assert trace.times[-1]>green.times[-1]


def test_sampling_does_not_overlap_ongoing_and_preserves_other_random_sources():
    from src.calculators.projection import sample_scenarios
    s=SyntheticRaceAdapter.create_race_state(current_lap=18).model_copy(update={'track_status':TrackStatus.SAFETY_CAR})
    c=ProjectionConfig(ongoing_neutralization_laps=3,base_pace_sigma_s=.2,lap_noise_sigma_s=.4)
    risk=c.model_copy(update={'future_sc_probability':1.,'sc_duration_prior_s':(120.,),'sc_pace_multiplier':1.3})
    before,after=sample_scenarios(s,c),sample_scenarios(s,risk)
    for a,b in zip(before,after):
        assert (a.rain_lap,a.pit_offset_s,a.weight,a.degradation_multiplier,a.base_pace_offset_s,a.lap_noise_s)==(b.rain_lap,b.pit_offset_s,b.weight,b.degradation_multiplier,b.base_pace_offset_s,b.lap_noise_s)
        assert b.neutralization_events[0][0]==22

def test_sc_pack_compression_preserves_subject_clock_and_ignores_slow_rival_anchor():
    from src.calculators.projection import sample_scenarios,simulate_policy,Policy
    s=SyntheticRaceAdapter.create_race_state(current_lap=18)
    rivals=[r.model_copy(update={'gap_to_subject_s':1000.,'last_lap_time_s':1000.}) for r in s.competitors]
    s=s.model_copy(update={'competitors':rivals,'track_status':TrackStatus.GREEN,'total_laps':23})
    c=ProjectionConfig(base_pace_s=100.,future_sc_probability=1.,sc_duration_prior_s=(10000.,),
                       sc_pace_multiplier=1.3,pit_loss_spread_s=0.,degradation_spread_fraction=0.)
    scenario=sample_scenarios(s,c)[0]
    plan=Policy(id='hold',label='Hold',max_stops=0,react_to_weather=False)
    crowded=simulate_policy(s,plan,scenario,c,fixed_schedule=True)
    alone=simulate_policy(s.model_copy(update={'competitors':[]}),plan,scenario,c,fixed_schedule=True)
    assert crowded.times==pytest.approx(alone.times)
    assert all(b>a for a,b in zip(crowded.times,crowded.times[1:]))
    assert crowded.times[1]<200.
