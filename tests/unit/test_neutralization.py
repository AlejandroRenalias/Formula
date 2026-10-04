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
