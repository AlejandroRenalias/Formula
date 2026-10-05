import json
from pathlib import Path
from unittest.mock import patch
import pytest
from tools.reservation_gate import AccessDenied, POLICY, authorize, archive_path, guarded_session

@pytest.mark.parametrize('year,event', [(2023,'italy_2023'), (2023,'MONZA'), (2023,'Italian GP'), (2023,14), (2024,'Hungaroring'), (2024,13), (2025,'Sakhir'), (2025,4), (2021,'Sochi'), (2023,'Zandvoort'), (2024,'Canadian Grand Prix')])
@pytest.mark.parametrize('purpose', ['evaluation','archive','geometry','adapter','prior'])
def test_reserved_aliases_denied_for_every_access(year,event,purpose,tmp_path):
    with patch('fastf1.Cache.enable_cache') as cache, patch('fastf1.get_session') as session:
        with pytest.raises(AccessDenied):
            guarded_session(year,event,purpose=purpose,session='Q',cache_dir=tmp_path/'cache',offline=True)
        cache.assert_not_called();session.assert_not_called()
        assert not (tmp_path/'cache').exists()

@pytest.mark.parametrize('contents', [None, '{}', '{', json.dumps({'schema_version':2}), '[]', json.dumps({'schema_version':True,'allowed':[],'reserved':[]})])
def test_missing_or_invalid_policy_is_fail_closed(contents,tmp_path):
    p=tmp_path/'policy.json'
    if contents is not None:p.write_text(contents)
    with pytest.raises(AccessDenied):authorize(2021,'Bahrain',purpose='geometry',session='Q',policy_path=p)

def test_incomplete_and_ambiguous_policy_denied(tmp_path):
    for mutate in ('remove','alias','round'):
        d=json.loads(POLICY.read_text())
        if mutate=='remove':d['reserved'].pop()
        elif mutate=='alias':d['allowed'][-1]['aliases'].append('Sakhir')
        else:d['allowed'][-1]['round']=1
        p=tmp_path/'policy.json';p.write_text(json.dumps(d))
        with pytest.raises(AccessDenied):authorize(2021,'Bahrain',purpose='geometry',session='Q',policy_path=p)

@pytest.mark.parametrize('args', [(2024,'Unknown'), (2024,True), (2024,99), ('2024','Bahrain'), (2023,'bahrain_2025')])
def test_unknown_identity_denied(args):
    with pytest.raises(AccessDenied):authorize(*args,purpose='adapter')

def test_cache_helper_denies_before_read(tmp_path):
    from tools.evaluation_cache import load_dataset
    with patch.object(Path,'read_bytes',side_effect=AssertionError('cache was touched')):
        with pytest.raises(AccessDenied):load_dataset(tmp_path/'italy_2023'/'session.json')

def test_direct_adapter_cannot_bypass_gate():
    from src.adapters.fastf1_adapter import FastF1Adapter
    with patch('fastf1.get_session') as access, patch('fastf1.Cache.enable_cache') as cache:
        with pytest.raises(AccessDenied):FastF1Adapter.load_session(2025,'Bahrain')
        access.assert_not_called();cache.assert_not_called()

def test_prior_loop_checks_all_before_cache(monkeypatch):
    from tools import acquire_neutralization_prior as tool
    monkeypatch.setattr(tool,'RACES',['Bahrain','Unknown'])
    with patch('fastf1.Cache.enable_cache') as cache:
        with pytest.raises(AccessDenied):tool.run(offline=True)
        cache.assert_not_called()

def test_cli_allowlist_mutation_cannot_bypass_shared_gate(monkeypatch):
    from tools import acquire_bahrain_evaluation as tool
    monkeypatch.setitem(tool.DEVELOPMENT_RACES,'bahrain_2025',{'year':2025,'race':'Bahrain','scheduled_laps':57})
    monkeypatch.setattr('sys.argv',['acquire','--race','bahrain_2025','--offline'])
    with patch('fastf1.Cache.enable_cache') as cache,patch('fastf1.get_session') as session:
        with pytest.raises(AccessDenied):tool.main()
        cache.assert_not_called();session.assert_not_called()

@pytest.mark.parametrize('year,event,key', [(2021,'Sakhir','bahrain_2021'), (2022,'Barcelona','spain_2022'), (2022,'Paul Ricard','france_2022')])
def test_only_pre_race_geometry_sessions_authorized(year,event,key):
    assert authorize(year,event,purpose='geometry',session='Qualifying')['key']==key
    with pytest.raises(AccessDenied):authorize(year,event,purpose='geometry',session='Race')
    assert archive_path(Path(key)/'session.json').parent.name==key

def test_known_prior_and_existing_archive_access():
    assert authorize(2019,'French Grand Prix',purpose='prior')['event']=='France'
    assert authorize(key='spain_2023',purpose='archive')['year']==2023
    with pytest.raises(AccessDenied):authorize(2024,'Silverstone',purpose='geometry',session='Q')
