import pytest
from src.evaluation.races import DEVELOPMENT_RACES, race_key
from tools import evaluate_held_out as runner


def test_held_out_authorization_is_scoped_and_does_not_admit_wet_races():
    original=dict(DEVELOPMENT_RACES)
    with pytest.raises(ValueError):race_key({'year':2023,'race':'Spain'})
    with runner.authorized_datasets():
        assert race_key({'year':2023,'race':'Spain'})=='spain_2023'
        assert race_key({'year':2024,'race':'Bahrain'})=='bahrain_2024'
        with pytest.raises(ValueError):race_key({'year':2021,'race':'Russia'})
    assert DEVELOPMENT_RACES==original
    with pytest.raises(ValueError):race_key({'year':2024,'race':'Bahrain'})


def test_once_ledger_refuses_repeated_prediction_before_reading_dataset(monkeypatch,tmp_path):
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner,'assert_frozen',lambda:{})
    output=tmp_path/'spain_2023';output.mkdir();(output/'RUN_STARTED.json').write_text('{}')
    monkeypatch.setattr(runner,'load_dataset',lambda p:pytest.fail('Repeated run read dataset'))
    with pytest.raises(ValueError,match='One-run ledger'):runner.race_run('spain_2023')
