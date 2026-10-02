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


def test_map_and_tyre_display_use_cutoff_fixture_and_embedded_assets():
    fixture = json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))
    ui = fixture['ui']['display']
    assert ui['lap_counter'] == {'current': str(fixture['cutoff_lap']), 'total': str(fixture['horizon_lap'])}
    assert ui['current_tyre']['health'] == 1 - 17 / 28
    assert ui['map']['rejoin_label'] == fixture['track']['ghost_rejoin']['label']
    assert '70%' in ui['map']['rain_label'] and 'lap 22' in ui['map']['rain_label']
    document = projection_document()
    assert 'id="circuit"' in document and 'id="tyre-ring"' in document
    assert 'assets/circuit-map.js' not in document
    assert 'data:font/ttf;base64,' in document


def test_polish_display_preserves_raw_reasoning_and_zoomed_example_data():
    fixture = json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))
    ui = fixture['ui']['display']
    assert (ui['chart']['window_start'], ui['chart']['window_end']) == (12, 32)
    groups = {g['id']: g['display'] for g in fixture['scenario_group_margins']}
    for scenario in ui['chart']['scenarios']:
        group = groups['rain' if scenario['rain_lap'] is not None else 'no_rain']
        assert scenario['finish_margin_s'] == group['expected_stay_advantage_s']
        visible = [p['gain_s'] for p in ui['chart']['observed'] if 12 <= p['lap'] <= 32]
        visible += [v for plan in scenario['plans'] for lap, v in zip(plan['laps'], plan['gain_s']) if 12 <= lap <= 32]
        assert scenario['low'] <= min(visible) < max(visible) <= scenario['high']
    assert all(re.fullmatch(r'\d+%', share['value']) for share in ui['base']['shares'])
    for short, raw, evaluation in zip(ui['radio'], ui['radio_raw'], fixture['scorer']['specialist_evaluations']):
        assert short['vote'] == raw['vote']
        assert raw['text'] == evaluation['rationale']
        assert raw['candidate'] not in short['text']
    assert ui['map']['ghost_template'] == 'If you box: P{position}'


def test_archivo_is_bundled_for_both_styles_and_forecast_start_is_explicit():
    document = projection_document()
    # The embedded app must work offline with upright and italic font files.
    assert document.count('data:font/ttf;base64,') == 2
    assert 'Archivo-Variable.ttf' not in document
    assert 'Archivo-VariableItalic.ttf' not in document
    assert 'Barlow' not in document and 'monospace' not in document
    fixture = json.loads((ROOT / 'tests/fixtures/projection_lap18.json').read_text(encoding='utf-8'))
    assert fixture['ui']['display']['map']['rain_start_label'] == 'Forecast rain starts here'
    assert fixture['track']['rain_overlay']['kind'] == 'forecast'
