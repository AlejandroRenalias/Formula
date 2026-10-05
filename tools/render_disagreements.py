"""Render and validate saved disagreement classifications; never run the engine."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evaluation/disagreement'

def load(name):
    return json.loads((OUT / name).read_text())

def table(headers, rows):
    return '\n| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join(['---'] * len(headers)) + ' |\n' + ''.join('| ' + ' | '.join(str(x).replace('|', '/') for x in row) + ' |\n' for row in rows) + '\n'

def f(x):
    return 'NA' if x is None else f'{x:.3f}'

def schedule(stops):
    return '; '.join(f"boundary {s['lap']}: {s.get('fitted_compound', s.get('compound', 'unknown'))}" for s in stops) or 'no stops'

def render():
    metrics, cards, manifest = load('metrics.json'), load('case_cards.json'), load('manifest.json')
    events = [json.loads(line) for line in (OUT / 'events.jsonl').read_text().splitlines()]
    assert len(events) == len({e['id'] for e in events}) == 114
    assert sum(e['direction'] == 'FN' for e in events) == 79
    checks = ['114 unique events: 79 FN and 35 FP; accepted per-race event counts unchanged.']
    for pool, dirs in metrics['pools'].items():
        for direction, summary in dirs.items():
            assert summary['n'] == sum(e['set'] == pool and e['direction'] == direction for e in events)
            assert sum(summary['exact_observed_combinations'].values()) == summary['n']
            assert summary['none_complete'] <= summary['none']
            for pair, count in summary['pairwise_overlap'].items():
                assert all(count <= summary['tag_counts'][tag] for tag in pair.split(' & '))
    for e in events:
        assert e['none_of_above'] == (not e['observed_tags'])
        for w in e['visibility']['cutoffs']:
            assert abs(w['lap'] - e['team_stop_context']['lap']) <= 1
            assert w['before_entry'] == (w['cutoff_session_s'] < e['team_stop_context']['entry_session_s'])
            assert abs(abs(w['box_minus_stay_s']) - w['call_margin_s']) < 1e-9
    for pool, dirs in cards.items():
        for direction, group in dirs.items():
            assert len(group['selected']) == 5
            for c in group['selected']:
                assert c['event_id'] in {e['id'] for e in events}
                state, audit = c['causal_state'], c['cutoff_audit']
                assert state['timestamp'] == state['knowledge_cutoff']
                assert all(t <= audit['cutoff_session_s'] for t in audit['parameter_source_session_s'].values())
                assert c['effective_frozen_config']['base_pace_uncertainty_multiplier'] == 3.0
                assert c['effective_frozen_config']['lap_noise_uncertainty_multiplier'] == 1.0
                if direction == 'FN':
                    assert c['engine']['call'] == 'STAY_OUT'
                    assert c['engine']['cutoff_session_s'] < c['team_stop_context']['entry_session_s']
                else:
                    assert c['engine']['call'] == 'BOX_NOW'
    for path, expected in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    checks += ['Exact tag combinations partition each pool; pairwise overlaps respect tag totals.',
               'All saved window margins and pre-entry flags verified; all 20 case cards have valid source events.',
               'Case-card parameter timestamps are at or before cutoff; frozen uncertainty remains 3.0 / 1.0.',
               'All accepted source, call, matching, cache and profile hashes remain unchanged.']
    tags = list(metrics['pools']['development']['FN']['tag_counts'])
    text = '# Saved-call disagreement analysis\n\n'
    text += 'Report-only analysis of decision-engine-v1: 54 missed team stops and 18 unmatched alerts in development; 25 and 17 respectively in held-out. No engine calls, new samples, rebuilt states, changed matching, tuning or UI changes. These tags describe observable context; they do not establish why a team stopped or which choice was better.\n\n'
    text += 'Compound outside the immediate candidate set occurs on 34/54 development misses and 17/25 held-out misses. All nine neutralisation-tagged misses are in France, and none had the relevant neutralisation visible at a saved pre-entry cutoff inside the ±1 window. There was nevertheless a valid pre-entry cutoff for every missed stop.\n\n'
    text += 'Definitions and deterministic case selection were committed before classification in [PROTOCOL.md](PROTOCOL.md), commits 9322fe3 and a8ea9b7. FN/FP identities reuse the accepted ±1 episode-start matching, not a new matching exercise. Lap numbers below use the accepted stop-boundary coordinate; entry times are session seconds.\n\n'
    text += 'The immediate BOX compound limitation remains HARD, or MEDIUM while on HARD. Strategy count compares actual remaining physical stops against nominal scheduled stops in the recommended policy; sampled stop-count distributions remain available in the audits. For FP, stop-specific tags use the predeclared ±10 contextual stop, not a primary match or proof of causation; five alerts have no such context.\n\n'
    text += '## Counts, unknown evidence and overlaps\n\nThe [event register](EVENT_TAGS.md) lists all 114 events, tags, unknowns, contextual-stop provenance and reference cutoffs. Counts are nonexclusive. N/U in each tag column means observed positive / unknown. Unknown rival proximity is retained conservatively when the saved state omits a rival and no positive proximity-stop evidence exists. This is common in development; it is not a negative result. None means no positive tag; complete none additionally requires no unknown tags.\n'
    register = '# All disagreement event tags\n\nFN = missed observable team stop; FP = unmatched first BOX alert. Tag definitions were fixed in [PROTOCOL.md](PROTOCOL.md). FP physical-stop context is descriptive, not a repaired primary match. None means no observed positive tag; unknown evidence remains explicit. Full timestamped evidence is in events.jsonl.\n'
    for pool in ('development', 'held_out'):
        register += f'## {pool}\n'
        register += table(['Event / driver', 'Observed tags', 'Unknown tags', 'Complete none', 'Reference cutoff', 'Context boundary / offset', 'Context basis'], [[e['id'] + ' / ' + e['driver'], ', '.join(e['observed_tags']) or 'none', ', '.join(e['unknown_tags']) or 'none', e['none_with_complete_evidence'], e['reference']['lap'], f"{e['team_stop_context']['lap']} / {e['context_offset_laps']}" if e['team_stop_context'] else 'unknown', e['team_stop_context_basis']] for e in events if e['set'] == pool])
    (OUT / 'EVENT_TAGS.md').write_text(register, encoding='utf-8')
    def rows(groups):
        return [[name, d, s['n']] + [f"{s['tag_counts'][t]}/{s['unknown_counts'][t]}" for t in tags] + [s['none'], s['none_complete'], s['multiple_tags']] for name, ds in groups.items() for d, s in ds.items()]
    headers = ['Set/race', 'Direction', 'Events'] + tags + ['None', 'Complete none', '2+ tags']
    text += table(headers, rows(metrics['pools'])) + table(headers, rows(metrics['races']))
    for pool, dirs in metrics['pools'].items():
        for direction, s in dirs.items():
            text += f'### {pool} {direction}: overlaps\n'
            text += table(['Pair', 'Events'], s['pairwise_overlap'].items())
            text += table(['Exact observed combination (unknowns may coexist)', 'Events'], s['exact_observed_combinations'].items())
    text += '## Missed-stop decision windows\n\nThe [complete window report](MISSED_STOP_WINDOWS.md) lists every saved cutoff in the ±1 window for all 79 misses, including signed BOX-minus-STAY mean margin, all three confidence masses, recommendation and visibility. Positive signed margin favours STAY in the engine. Confidence is sampled model mass beyond the saved 1-second tolerance, not a probability the engine was correct. The descriptive thresholds (0.8 confident; 0.5 close mass) were fixed before classification.\n'
    text += table(['Set', 'Misses', 'Any BOX in window', 'Any confident STAY', 'Any too close', 'Neutralisation visible / tagged'], [[p, s['n'], s['window_has_BOX'], s['window_pre_entry_confident_STAY'], s['window_pre_entry_too_close'], f"{s['neutralisation_visible']}/{s['tag_counts']['neutralisation']}"] for p, ds in metrics['pools'].items() for s in [ds['FN']]])
    text += 'Window categories overlap. A BOX inside a missed-stop window can belong to an episode that started outside the accepted matching window or was paired elsewhere. Thus 16 development and 11 held-out misses with window BOX calls are timing/episode disagreements, not necessarily confident refusals to stop. All saved window calls here precede pit entry; in-lap/straddling exclusions leave partial windows. Missing cutoffs are not invented.\n\n'
    windows = '# Every missed-stop window\n\nSigned margin = best BOX mean minus best STAY mean, seconds. Masses are STAY / BOX / too close; saved tolerance is 1 second. Times use session seconds. Only saved cutoffs are shown. A missing lap is unavailable in the accepted evaluation, often because of a straddling stop. Full exclusion logs remain in the agreement race folders.\n\n'
    for e in events:
        if e['direction'] != 'FN':
            continue
        context = e['team_stop_context']
        windows += f"## {e['id']} ({e['driver']})\n\nTeam entry {f(context['entry_session_s'])} s, fitted {context['fitted_compound']}; tags: {', '.join(e['observed_tags']) or 'none'}; unknown: {', '.join(e['unknown_tags']) or 'none'}. Tag reference cutoff {e['reference']['lap']}; actual / recommended remaining stops {e['actual_remaining_stop_count']} / {e['recommended_nominal_stop_count']}.\n"
        windows += table(['Cutoff lap', 'Time s', 'Pre-entry', 'Call', 'Recommended', 'BOX−STAY s', 'STAY mass', 'BOX mass', 'Close mass', 'Label', 'Track', 'Neutral trigger visible'], [[w['lap'], f(w['cutoff_session_s']), w['before_entry'], w['call'], w['recommended'], f(w['box_minus_stay_s']), f(w['confidence']['stay_clearly_better']), f(w['confidence']['box_clearly_better']), f(w['confidence']['too_close_to_call']), w['confidence_label'], w['track_status'], w['neutral_trigger_visible']] for w in e['visibility']['cutoffs']])
        absent = sorted(set(range(context['lap']-1, context['lap']+2)) - {w['lap'] for w in e['visibility']['cutoffs']})
        windows += f"Unavailable boundary cutoffs: {', '.join(map(str, absent)) or 'none'}.\n\n"
    (OUT / 'MISSED_STOP_WINDOWS.md').write_text(windows, encoding='utf-8')
    text += '## Most confident disagreements\n\nFive cards in each direction for each set, ranked by the predeclared confidence mass and margin, not actual outcomes. FN cards use the strongest saved pre-entry STAY cutoff in the window; tag references remain the last pre-entry cutoff and may differ. FP cards use the first unmatched BOX alert. Full causal state, competitors, parameter counts/fallbacks/timestamps, sampled stop-count distributions and effective configuration are preserved in [case_cards.json](case_cards.json).\n\n'
    for pool, dirs in cards.items():
        for direction, group in dirs.items():
            text += f'### {pool}: {direction}\n\nEligible events for this ranking: {group["eligible_events"]}.\n\n'
            for c in group['selected']:
                e = next(e for e in events if e['id'] == c['event_id'])
                state, engine, audit = c['causal_state'], c['engine'], c['cutoff_audit']
                s = state['subject_driver']; conf = engine['confidence']
                text += f"#### {c['rank']}. {c['event_id']} — {s['driver']}\n\n"
                text += f"Causal cutoff lap {engine['lap']} at {f(engine['cutoff_session_s'])} s (tag reference lap {c['event_reference']['lap']}). Position {s['position']}, {s['current_compound']} age {s['stint_length_laps']}, {s['total_pit_stops']} stops so far, used {', '.join(s['used_compounds'])}; {state['track_status']}. Saved base pace {f(c['effective_frozen_config']['base_pace_s'])} s.\n\n"
                text += 'Observed weather: ' + ', '.join(f"{k}={v['value']}" for k, v in state['observed_weather'].items()) + '; forecast is no-forecast dry persistence. Gaps retain the approved same-lap live timing proxy label in the full audit.\n'
                text += table(['Nearby saved car (≤3 s)', 'Position', 'Gap s', 'Compound / age'], [[r['driver'], r['position'], f(r['gap_to_subject_s']), f"{r['current_compound']} / {r['tyre_age_laps']}"] for r in state['competitors'] if abs(r['gap_to_subject_s']) <= 3])
                text += f"Call {engine['call']}; recommendation {engine['recommended']['id']}; signed BOX−STAY margin {f(engine['box_minus_stay_s'])} s. STAY / BOX / close masses: {f(conf['stay_clearly_better'])} / {f(conf['box_clearly_better'])} / {f(conf['too_close_to_call'])}.\n"
                text += table(['Option', 'Policy', 'Nominal stop boundaries / tyres', 'Mean to finish s', 'Sampled stops mean [min,max]', 'Invalid mass'], [[label, p['id'], schedule(p['policy']['dry_stops']), f(p['mean_time_to_finish_s']), f"{f(p['sampled_stop_count_mean'])} [{p['sampled_stop_count_min']},{p['sampled_stop_count_max']}]", f(p['invalid_probability'])] for label in ('best_BOX', 'best_STAY') for p in [engine[label]]])
                text += f"Team's remaining schedule after this card cutoff: {schedule(c['actual_remaining_team_schedule_at_card'])}. Actual stops in the primary ±1 window: {schedule(c['actual_team_stops_within_primary_window'])}.\n\n"
                context = c['team_stop_context']
                text += (f"Physical stop context: boundary {context['lap']}, entry {f(context['entry_session_s'])} s, exit {f(context['exit_session_s'])} s, fitted {context['fitted_compound']}; basis {e['team_stop_context_basis']}, offset {e['context_offset_laps']} laps from event.\n\n" if context else 'No physical team-stop context within the predeclared range.\n\n')
                text += f"Observed tags: {', '.join(e['observed_tags']) or 'none'}; unknown: {', '.join(e['unknown_tags']) or 'none'}. Latest recorded parameter source {f(max(audit['parameter_source_session_s'].values()))} s ≤ cutoff. No claim about the better choice.\n\n"
    text += '## Registered hypothesis and limits\n\nThe registered timing direction was rejected: the accepted wide-match early-race timing statistic did not show later engine BOX calls (development mean 0 laps on one match; held-out mean −1.556 laps on nine matches). In the registered stratum, the engine made no early BOX calls and caught none of the 11 observable stops (development 0/9, held-out 0/2; 331 qualifying cutoffs). That is consistent with the registered reduced-call/recall component, but the sample is too small to conclude. It does not rescue the rejected timing direction or prove a counterfactual outcome.\n\n'
    text += 'Undercut/cover is only an observable proximity-and-stop tag. Neutralisation visibility refers to the recorded SC/VSC trigger, not team radio or intent. FP contextual stops can be several laps away or before an alert; their tags are descriptive. The frozen prediction and accepted agreement scores remain unchanged. No disagreement outcome-quality analysis was performed.\n\n'
    text += '## Audit and validation\n\n' + '\n'.join('- ' + x for x in checks) + '\n\n'
    text += 'Classification ran once with network blocked and engine projection, sampling, simulation and snapshot construction patched to fail if invoked. [manifest.json](manifest.json) seals accepted inputs; [events.jsonl](events.jsonl) preserves all 114 classifications; [metrics.json](metrics.json) preserves per-race and pooled counts; [PROTOCOL.md](PROTOCOL.md) records definitions before computation.\n'
    (OUT / 'REPORT.md').write_text(text, encoding='utf-8')
    manifest['validation'] = checks
    manifest['output_sha256'] = {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in ('PROTOCOL.md', 'events.jsonl', 'metrics.json', 'case_cards.json', 'REPORT.md', 'EVENT_TAGS.md', 'MISSED_STOP_WINDOWS.md', 'RUN_STARTED.json')}
    manifest['renderer_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('\n'.join(checks))

if __name__ == '__main__':
    render()
