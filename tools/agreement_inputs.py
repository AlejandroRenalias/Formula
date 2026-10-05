"""Immutable accepted snapshot inputs shared by agreement verification and runner."""
import hashlib
import json
from pathlib import Path
from src.calculators.projection import ProjectionConfig
from src.core.models import RaceState
from tools.evaluation_cache import load_dataset
from src.evaluation.races import DEVELOPMENT_RACES
from unittest.mock import patch

RACES=('bahrain_2021','spain_2022','france_2022','spain_2023','bahrain_2024')
ROOT=Path('docs/evaluation/agreement')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_rows(p): return [json.loads(x) for x in Path(p).read_text().splitlines()]
def inputs(race):
    from tools.reservation_gate import authorize
    authorize(key=race, purpose='archive')
    held=race in RACES[3:]
    folder=Path('docs/evaluation/held_out')/(race if held else 'development_reference/'+race)
    manifest=json.loads((folder/'manifest.json').read_text())
    snapshot=Path('data/cache/evaluation')/race/('snapshots_held_out.jsonl' if held else 'snapshots_parameters_wear.jsonl')
    predictions=folder/'predictions.jsonl'
    if held:
        assert sha(snapshot)==manifest['snapshot_sha256']
        assert sha(predictions)==manifest['prediction_sha256']
    else:
        for name,h in manifest['input_sha256'].items(): assert sha(name)==h
    with patch.dict(DEVELOPMENT_RACES, {'spain_2023':{'year':2023,'race':'Spain','scheduled_laps':66},'bahrain_2024':{'year':2024,'race':'Bahrain','scheduled_laps':57}}):
        data,_=load_dataset(snapshot.parent/'session.json')
    records=read_rows(snapshot)
    hashes={str(p):sha(p) for p in (snapshot,predictions,folder/'manifest.json',snapshot.parent/'session.json')}
    return records,read_rows(predictions),data,hashes

def causal(record):
    state=RaceState.model_validate(record['state'])
    config=ProjectionConfig.model_validate(record['config']).model_copy(update={
        'base_pace_uncertainty_multiplier':3.0,'lap_noise_uncertainty_multiplier':1.0})
    assert state.timestamp==state.knowledge_cutoff
    assert all(t<=record['audit']['cutoff_session_s'] for t in record['audit']['parameter_source_session_s'].values())
    assert state.weather_forecast.rain_probability.value==0
    assert state.weather_forecast.expected_arrival_laps.value is None
    assert not state.observed_weather.rainfall.value
    return state,config

def phase(lap):return '5-14' if lap<15 else '15-29' if lap<30 else '30+'
