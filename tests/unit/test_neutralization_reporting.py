"""Report weighting uses row errors, never model fitting."""
import pytest
from tools.report_neutralization_views import balanced_summary,balanced_metrics,weighted_median


def row(error):
    return {'error_s':error,'horizon_laps':5,'horizon':'5','covered':error==0.,
            'actual_s':100.,'p10_s':99.+error,'p90_s':101.+error,'width_s':2.,'contains_subject_pit_stop':False}


def test_equal_race_weights_ignore_unequal_prediction_counts():
    a=balanced_summary({'small':[row(0.)],'large':[row(10.)]*9})
    assert a['n']==10 and a['contributing_races']==2
    assert a['bias_s']==pytest.approx(5.)
    assert a['median_error_s']==5.
    assert a['coverage']==pytest.approx(.5)
    assert a['mean_error_per_lap_s']==pytest.approx(1.)
    assert a['lower_misses']==9 and a['upper_misses']==0
    assert a['lower_miss_rate']==pytest.approx(.5)


def test_missing_race_and_pit_stratum_get_no_zero_weight_observations():
    a=balanced_metrics({'empty':[],'present':[row(2.)]})['5']
    assert a['race_weights']=={'present':1.}
    assert a['by_subject_pit_stop']['with_stop']['n']==0
    assert a['by_subject_pit_stop']['without_stop']['contributing_races']==1
    assert balanced_metrics({'empty':[]})=={}


def test_weighted_median_uses_individual_errors_and_handles_exact_half():
    assert weighted_median([(1.,.25),(3.,.25),(9.,.5)])==6.
    assert weighted_median([(1.,.1),(3.,.6),(9.,.3)])==3.
