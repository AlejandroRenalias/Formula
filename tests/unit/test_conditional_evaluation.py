"""Same-sample conditioning and outcome-only new-event calibration."""
from types import SimpleNamespace
import pytest
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.calculators.projection import ProjectionConfig,Scenario,Trace
from src.core.models import TrackStatus
from src.evaluation import prediction
from src.evaluation.prediction import ActualPlan
from tools.evaluate_conditional import observed_start,calibration,green_rows


def test_conditional_quantiles_renormalize_same_traces_and_use_horizon_prefix(monkeypatch):
    state=SyntheticRaceAdapter.create_race_state(current_lap=18).model_copy(update={'total_laps':23,'track_status':TrackStatus.GREEN})
    scenarios=(Scenario(None,0.,.6,neutralization_events=((19,'SC',2),)),
               Scenario(None,0.,.3,neutralization_events=((22,'VSC',1),)),
               Scenario(None,0.,.1,neutralization_events=((23,'SC',1),)))
    calls=[]
    monkeypatch.setattr(prediction,'sample_scenarios',lambda s,c:scenarios)
    def simulate(s,p,scenario,c,**kwargs):
        calls.append(scenario)
        n=scenarios.index(scenario)+1
        return Trace([0.]+[n*100.+i for i in range(5)],[],[],True)
    monkeypatch.setattr(prediction,'simulate_policy',simulate)
    result=prediction.predict(SimpleNamespace(state=state,config=ProjectionConfig(future_sc_probability=.1,future_vsc_probability=.2,sc_duration_prior_s=(100.,),vsc_duration_prior_s=(100.,))),ActualPlan(()))
    assert calls==list(scenarios)
    assert result[19]['median_s']==100.
    assert result[19]['green_median_s']==200.
    assert result[19]['green_p10_s']==200. and result[19]['green_p90_s']==300.
    assert result[19]['green_sample_count']==2
    assert result[19]['green_probability_mass']==pytest.approx(.4)
    assert result[19]['sampled_neutralization_start_probability']==pytest.approx(.6)
    assert result[19]['neutralization_start_probability']==pytest.approx(.3)
    assert result[22]['green_median_s']==303.
    assert result[22]['sampled_neutralization_start_probability']==pytest.approx(.9)
    assert result[22]['neutralization_start_probability']==pytest.approx(1-.7**4)
    assert result[23]['green_median_s'] is None
    assert result[23]['green_sample_count']==0
    assert result[23]['sampled_neutralization_start_probability']==pytest.approx(1.)
    assert result[23]['neutralization_start_probability']==pytest.approx(1-.7**5)


def test_known_ongoing_event_is_not_new_start_and_green_prediction_is_unavailable():
    state=SyntheticRaceAdapter.create_race_state(current_lap=18).model_copy(update={'total_laps':23,'track_status':TrackStatus.VSC})
    result=prediction.predict(SimpleNamespace(state=state,config=ProjectionConfig(ongoing_neutralization_laps=2)),ActualPlan(()))
    assert result[19]['green_median_s'] is None
    assert result[19]['neutralization_start_probability']==0.
    assert result[21]['green_median_s'] is None  # Horizon still contains the initial VSC.


def test_observed_starts_merge_vsc_codes_and_exclude_ongoing_at_cutoff():
    track=[{'Time':0.,'Status':'1'},{'Time':10.,'Status':'6'},
           {'Time':20.,'Status':'7'},{'Time':30.,'Status':'1'},
           {'Time':40.,'Status':'4'},{'Time':45.,'Status':'4'}]
    assert observed_start(track,0.,10.)
    assert not observed_start(track,10.,30.)
    assert observed_start(track,30.,40.)
    assert not observed_start(track,40.,45.)
    assert observed_start(track,0.,10.)==observed_start(track+[{'Time':999.,'Status':'4'}],0.,10.)


def test_calibration_brier_and_deciles_include_zero_one_and_empty_bins():
    rows=[{'horizon':'5','neutralization_start_probability':p,'actual_neutralization_start':y}
          for p,y in ((0.,False),(1.,True),(.25,True))]
    m=calibration(rows)['5']
    assert m['brier_score']==pytest.approx(.1875)
    assert m['reliability'][0]['n']==1 and m['reliability'][9]['n']==1
    assert m['reliability'][2]['observed_frequency']==1.
    assert m['reliability'][3]['observed_frequency'] is None
    assert sum(b['n'] for b in m['reliability'])==3

def test_exact_onset_probability_excludes_known_ongoing_laps():
    state=SyntheticRaceAdapter.create_race_state(current_lap=18).model_copy(update={'total_laps':23,'track_status':TrackStatus.SAFETY_CAR})
    config=ProjectionConfig(ongoing_neutralization_laps=3,future_sc_probability=.1,sc_duration_prior_s=(120.,))
    result=prediction.predict(SimpleNamespace(state=state,config=config),ActualPlan(()))
    assert result[21]['neutralization_start_probability']==0.
    assert result[22]['neutralization_start_probability']==pytest.approx(.1)
    assert result[23]['neutralization_start_probability']==pytest.approx(1-.9**2)


def test_green_metrics_never_substitute_combined_or_include_actual_neutralized_outcomes():
    base={'green_only_outcome':True,'green_median_s':105.,'green_p10_s':101.,'green_p90_s':110.,
          'median_s':999.,'p10_s':900.,'p90_s':1100.,'actual_s':104.,'horizon_laps':5,
          'contains_subject_pit_stop':True,'subject_pit_stop_count':1}
    rows=[base,{**base,'green_only_outcome':False},{**base,'green_median_s':None}]
    selected=green_rows(rows)
    assert len(selected)==1
    assert selected[0]['median_s']==105. and selected[0]['error_s']==1.
    assert selected[0]['error_per_lap_s']==.2 and selected[0]['covered']
    assert selected[0]['contains_subject_pit_stop']
    assert base['median_s']==999.
