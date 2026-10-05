import json
from datetime import datetime
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from tools.acquire_historical_geometry import geometry,acquire,ROOT,TRACKS
from src.calculators.circuit_map import CircuitMap

def test_static_geometry_profile_is_monotonic_and_closes():
    t=np.linspace(0,100,201)
    telemetry=pd.DataFrame({'Time':pd.to_timedelta(t,unit='s'),'Distance':t*50,'X':np.cos(t/100*2*np.pi)*1000,'Y':np.sin(t/100*2*np.pi)*1000})
    asset=geometry('bahrain',telemetry,100,30,40,{'session':'Q'})
    model=CircuitMap(asset)
    assert asset['polyline'][0]['x']==asset['polyline'][-1]['x']
    assert model.position(0,100)['lap_offset']==-1
    assert [s['end_distance_m'] for s in asset['sectors']]==pytest.approx([1500,3500,5000])

def test_unknown_track_and_race_session_never_open_fastf1():
    with patch('fastf1.get_session') as access:
        with pytest.raises(ValueError):acquire('monza')
        access.assert_not_called()

@pytest.mark.parametrize('track',list(TRACKS))
def test_committed_assets_are_pre_race_and_valid_offline(track):
    asset=json.loads((ROOT/'data/tracks'/f'{track}.json').read_text())
    CircuitMap(asset)
    s=asset['source']
    assert s['session']=='Q' and s['year']==TRACKS[track][0]
    assert datetime.fromisoformat(s['date'])<datetime.fromisoformat(s['race_start_date'])
    assert len(asset['polyline'])==len(asset['time_profile'])==501
    assert asset['pit_entry']['kind']==asset['pit_exit']['kind']=='config'
    assert s['telemetry_sha256'] and s['reservation_gate']

def test_incomplete_or_nonmonotonic_reference_rejected():
    t=np.linspace(1,100,201)
    telemetry=pd.DataFrame({'Time':pd.to_timedelta(t,unit='s'),'Distance':t*50,'X':t,'Y':t})
    with pytest.raises(ValueError,match='complete'):geometry('bahrain',telemetry,100,30,40,{})
