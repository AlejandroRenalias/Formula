import numpy as np
import pytest
from pydantic import ValidationError
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.calculators.projection import ProjectionConfig, sample_scenarios, simulate_policy, Stop
from src.core.models import TireCompound, CompetitorState
from src.evaluation.prediction import ActualPlan
from src.evaluation.calibration import GRID, replay_grid, green_quantiles, select_candidate


def state():
    return SyntheticRaceAdapter.create_race_state(current_lap=18, total_laps=35,
        stint_length_laps=17, rain_probability=0, competitors=[CompetitorState(
            driver='HAM', team='Mercedes', position=1, current_compound=TireCompound.MEDIUM,
            tyre_age_laps=17, gap_to_subject_s=.5, last_lap_time_s=91)])


def test_multipliers_share_draws_preserve_other_sources_and_zero_scatter():
    s = state()
    c = ProjectionConfig(base_pace_sigma_s=.4, lap_noise_sigma_s=.8)
    before = sample_scenarios(s,c)
    after = sample_scenarios(s,c.model_copy(update={'base_pace_uncertainty_multiplier': 2,
                                                 'lap_noise_uncertainty_multiplier': 3}))
    for a,b in zip(before,after):
        assert b.base_pace_offset_s == a.base_pace_offset_s*2
        assert b.lap_noise_s == tuple(v*3 for v in a.lap_noise_s)
        assert (a.rain_lap,a.pit_offset_s,a.degradation_multiplier,a.weight,a.neutralization_events) == (
            b.rain_lap,b.pit_offset_s,b.degradation_multiplier,b.weight,b.neutralization_events)
    zero = sample_scenarios(s,ProjectionConfig(base_pace_uncertainty_multiplier=4,lap_noise_uncertainty_multiplier=4))
    assert all(x.base_pace_offset_s == 0 and not x.lap_noise_s for x in zero)


@pytest.mark.parametrize('field',['base_pace_uncertainty_multiplier','lap_noise_uncertainty_multiplier'])
@pytest.mark.parametrize('value',[0,-1,float('nan'),float('inf')])
def test_invalid_multipliers(field,value):
    with pytest.raises(ValidationError): ProjectionConfig(**{field:value})


def test_grid_replays_engine_with_traffic_pits_and_independent_rivals():
    s = state()
    c = ProjectionConfig(base_pace_sigma_s=.6,lap_noise_sigma_s=.8,pit_in_lap_fraction=.12)
    plan = ActualPlan((Stop(lap=20,compound=TireCompound.HARD),))
    paths = []
    for scenario in sample_scenarios(s,c):
        segments=[]
        trace=simulate_policy(s,plan,scenario,c,fixed_schedule=True,green_segments=segments)
        paths.append(replay_grid(segments,scenario,c))
        np.testing.assert_array_equal(paths[-1][0],trace.times)
    for a,b in ((1,4),(4,1),(4,4),(2.25,3.5)):
        cell=GRID.index((a,b))
        changed=c.model_copy(update={'base_pace_uncertainty_multiplier':a,'lap_noise_uncertainty_multiplier':b})
        for scenario,path in zip(sample_scenarios(s,changed),paths):
            trace=simulate_policy(s,plan,scenario,changed,fixed_schedule=True)
            np.testing.assert_array_equal(path[cell],trace.times)
    assert green_quantiles(paths,5).shape==(169,3)


def test_selection_equal_race_equal_horizon_and_width_tiebreak():
    rows=[{'race_key':race,'horizon':h,'actual_s':0} for h in ('1','5','10','finish')
          for race in ('a','b') for _ in range(1 if race=='a' else 9)]
    q=np.zeros((3,len(rows),3));q[:,:,0]=-1;q[:,:,2]=1
    # First candidate fails the small race, regardless of the larger row count.
    q[0,[i for i,r in enumerate(rows) if r['race_key']=='a'],0]=.1
    q[1,:,0]=-2;q[1,:,2]=2
    selected,candidates=select_candidate(q,rows,grid=((1,1),(1,2),(2,1)))
    assert candidates[0]['coverage']['1']==.5
    assert selected==2  # same objective as candidate 1, smaller width


def test_green_quantiles_exclude_sampled_event_prefix_and_step_quantiles():
    paths=[np.array([[0,1,2,3]]),np.array([[0,100]])]
    np.testing.assert_array_equal(green_quantiles(paths,2),[[2,2,2]])


def test_engine_recorder_stops_at_first_neutralisation_without_changing_trace():
    s=state()
    c=ProjectionConfig(safety_car_lap=22,safety_car_duration_laps=2,
                       base_pace_sigma_s=.4,lap_noise_sigma_s=.8)
    plan=ActualPlan(())
    scenario=sample_scenarios(s,c)[0]
    segments=[]
    recorded=simulate_policy(s,plan,scenario,c,fixed_schedule=True,green_segments=segments)
    ordinary=simulate_policy(s,plan,scenario,c,fixed_schedule=True)
    assert recorded==ordinary
    assert len(segments)==3
    np.testing.assert_array_equal(replay_grid(segments,scenario,c)[0],ordinary.times[:4])


def test_frozen_calibration_only_applies_to_default_profile(monkeypatch):
    from src.evaluation import model_configurations
    from src.evaluation.snapshot import build_snapshot
    from tests.unit.test_evaluation import dataset
    class Freeze:
        def exists(self): return True
        def read_text(self):
            return ('{"configuration":"wear","pace_uncertainty_multipliers":'
                    '{"base_pace_uncertainty_multiplier":2.5,"lap_noise_uncertainty_multiplier":3.0}}')
    freeze = Freeze()
    monkeypatch.setattr(model_configurations,'FREEZE_PATH',freeze)
    calibrated = build_snapshot(dataset(),'1',8)
    historical = build_snapshot(dataset(),'1',8,configuration='wear')
    assert calibrated.state == historical.state
    assert calibrated.config.base_pace_sigma_s == historical.config.base_pace_sigma_s
    assert calibrated.config.lap_noise_sigma_s == historical.config.lap_noise_sigma_s
    assert calibrated.config.base_pace_uncertainty_multiplier == 2.5
    assert calibrated.config.lap_noise_uncertainty_multiplier == 3
    assert historical.config.base_pace_uncertainty_multiplier == historical.config.lap_noise_uncertainty_multiplier == 1
