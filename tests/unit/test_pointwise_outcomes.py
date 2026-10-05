import json
import subprocess
from tools.export_historical import OUTPUT, outcome_record, ROOT, RACES, physical_stops

def test_all_outcomes_use_exact_boundary_and_signed_next_stop():
    for race in RACES:
        stops=physical_stops(json.loads((ROOT/'data/cache/evaluation'/race/'session.json').read_bytes()))
        for path in (OUTPUT/'outcomes'/race).rglob('*.json'):
            o=json.loads(path.read_bytes())
            r=json.loads((OUTPUT/'causal'/path.relative_to(OUTPUT/'outcomes')).read_bytes())
            own=[s for s in stops if s['driver_number']==o['driver_number']]
            action='BOX' if any(s['boundary_lap']==o['lap'] for s in own) else 'STAY'
            assert o['team_action_this_lap']==action
            assert o['formula_agrees_with_team']==(('BOX' if r['call']=='BOX_NOW' else 'STAY')==action)
            future=[s for s in own if s['entry_session_s']>o['cutoff_session_s']]
            if future:
                assert o['next_team_stop']['stop_id']==future[0]['stop_id']
                assert o['next_team_stop']['laps_from_cutoff']==future[0]['boundary_lap']-o['lap']
            else:assert o['next_team_stop'] is None

def test_hamilton_lap11_stay_agrees_and_next_stop_is_one_lap_later():
    o=json.loads((OUTPUT/'outcomes/bahrain_2021/44/11.json').read_bytes())
    assert o['team_action_this_lap']=='STAY' and o['formula_agrees_with_team']
    assert o['next_team_stop']['laps_from_cutoff']==1 and not o['near_miss']

def test_near_miss_earlier_and_later_and_same_lap_action():
    c={'driver_number':'1','lap':10,'cutoff_session_s':1000,'call':'BOX_NOW'}
    for boundary,entry in [(9,999),(11,1100)]:
        o=outcome_record('bahrain_2021',c,[{'driver_number':'1','boundary_lap':boundary,'entry_session_s':entry}],{'matches':[]},[],None)
        assert o['team_action_this_lap']=='STAY' and o['near_miss']
        assert o['near_miss_stop']['boundary_lap']==boundary
    o=outcome_record('bahrain_2021',c,[{'driver_number':'1','boundary_lap':10,'entry_session_s':1100}],{'matches':[]},[],None)
    assert o['team_action_this_lap']=='BOX' and not o['near_miss']

def test_static_geometry_and_synthetic_fixture_are_exact_copies():
    for name in ('bahrain','barcelona','barcelona_2023','paul_ricard'):
        assert (ROOT/'data/tracks'/f'{name}.json').read_bytes()==(ROOT/'static/tracks'/f'{name}.json').read_bytes()
    assert (ROOT/'design/fixture.json').read_bytes()==(ROOT/'tests/fixtures/projection_lap18.json').read_bytes()

def test_all_2409_causal_hashes_equal_the_accepted_foundation():
    old=json.loads(subprocess.check_output(['git','show','0db5d57:static/historical/manifest.json'],cwd=ROOT))
    current=json.loads((OUTPUT/'manifest.json').read_bytes())
    causal={p:h for p,h in old['output_sha256'].items() if p.startswith('causal/')}
    assert len(causal)==2409
    assert causal=={p:h for p,h in current['output_sha256'].items() if p.startswith('causal/')}

def test_methodology_report_copies_are_exact_and_all_local_links_exist():
    sources={'agreement-plan':'docs/evaluation/AGREEMENT_PLAN.md','agreement':'docs/evaluation/agreement/REPORT.md','development-prediction':'docs/evaluation/calibration/REPORT.md','held-out-prediction':'docs/evaluation/held_out/REPORT.md','comparison':'docs/evaluation/held_out/COMPARISON.md','disagreement':'docs/evaluation/disagreement/REPORT.md'}
    for name,source in sources.items():assert (OUTPUT/'reports'/f'{name}.md').read_bytes()==(ROOT/source).read_bytes()
    import re
    for link in re.findall(r'href="([^"]+)"',(OUTPUT/'methodology.html').read_text(encoding='utf-8')):
        if not link.startswith('https:'):assert (OUTPUT/link).is_file()
