"""Outcome-only report labels cannot alter the causal replay."""
from tools.report_development_evaluation import actual_neutralization


def test_neutralization_label_includes_cutoff_status_but_not_after_target():
    data={"laps":[{"Driver":"1","NumberOfLaps":lap,"Time":100*lap} for lap in (5,6,10)],
          "track_status":[{"Time":0.,"Status":"1"},{"Time":700.,"Status":"4"},
                          {"Time":800.,"Status":"1"}]}
    assert not actual_neutralization(data,{"driver_number":"1","lap":5,"target_lap":6})
    assert actual_neutralization(data,{"driver_number":"1","lap":5,"target_lap":10})
    data["track_status"]=[{"Time":0.,"Status":"6"},{"Time":550.,"Status":"1"}]
    assert actual_neutralization(data,{"driver_number":"1","lap":5,"target_lap":6})
