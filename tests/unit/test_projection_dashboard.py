"""Fixture UI contract and default app entrypoint checks."""
import json
import re
from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.ui.projection_dashboard import projection_document

ROOT = Path(__file__).resolve().parents[2]


def test_default_app_uses_projection_document_without_legacy_score_chart():
    app = AppTest.from_file(str(ROOT / 'app.py')).run()
    assert not app.exception
    document = projection_document()
    assert 'projection-fixture' in document
    assert 'Show the maths' in document
    assert 'What drives the call.' not in document
    assert 'Weighted strategy score / points' not in document
    assert 'assets/pitwall.js' not in document  # Self-contained embedded entrypoint.
    payload = re.search(r'id="projection-fixture" type="application/json">(.*?)</script>', document, re.S).group(1)
    assert json.loads(payload) == json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))


def test_ui_examples_use_the_same_best_action_policies_and_separate_group_bands():
    fixture = json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))
    ui = fixture['ui']['display']
    assert ui['base']['call'] == 'STAY OUT'
    assert ui['base']['margin'].startswith(f"+{fixture['display']['call_margin_s']:.1f}")
    assert 'Too close to call if it stays dry' in ui['base']['confidence']
    assert len(ui['chart']['scenarios']) == 2
    for scenario in ui['chart']['scenarios']:
        assert {p['policy_id'] for p in scenario['plans']} == set(fixture['best_policies_by_call'].values())
        assert all(p['gain_s'][0] == 0 for p in scenario['plans'])
        assert all(len(p['laps']) == len(p['gain_s']) for p in scenario['plans'])
    assert ui['chart']['observed'][-1] == {'lap': fixture['cutoff_lap'], 'gain_s': 0}
    assert ui['radio'][1]['vote'] == 'STAY OUT'  # Preserve the scorer's weather tie vote.


def test_every_ui_sweep_point_uses_the_engine_display_margin_and_call():
    fixture = json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))
    raw = {s['assumption']: s for s in fixture['flip_thresholds']}
    for sweep in fixture['ui']['display']['sweeps']:
        points = {p['value']: p for p in raw[sweep['assumption']]['sweep']}
        for point in sweep['points']:
            if point['value'] is None:
                continue
            expected = points[point['value']]
            assert f"+{expected['display']['call_margin_s']:.1f} s" in point['display']['margin']
            assert point['display']['call'] == ('BOX NOW' if expected['call'] == 'BOX_NOW' else 'STAY OUT')
