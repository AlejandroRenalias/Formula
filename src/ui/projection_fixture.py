"""Build presentation fields offline; the browser performs no strategy modelling."""
from math import ceil, floor


def build_projection_view(result, state):
    plans = {p['id']: p for p in result['plans']}
    subject = state.subject_driver
    assumption = {a['name']: a['value'] for a in result['assumptions']}
    action = lambda call: 'BOX NOW' if call == 'BOX_NOW' else 'STAY OUT'
    seconds = lambda value: f'{value:.1f}'
    compound_name = {'HARD': 'hards', 'MEDIUM': 'mediums', 'SOFT': 'softs', 'INTERMEDIATE': 'inters', 'WET': 'wets'}

    def flips(sweep):
        if not sweep['transitions']:
            return 'No call flip in range.'
        if sweep['assumption'] == 'rain_arrival_lap':
            first = next((t for t in sweep['transitions'] if t['to_call'] == 'BOX_NOW'), None)
            if first:
                return f"Flips to BOX if rain arrives after lap {first['from_value']}. Later reversals are shown in the maths."
        return ' · '.join(f"{action(t['from_call'])} → {action(t['to_call'])} between {t['from_value']} and {t['to_value']}"
                          for t in sweep['transitions'])

    def view(point, sweep=None):
        call = point['call']
        groups = {g['id']: g for g in point['scenario_group_margins']}
        phrases = []
        for key, condition in (('rain', 'if it rains'), ('no_rain', 'if it stays dry')):
            if key not in groups:
                continue
            confidence = groups[key]['confidence']
            own = confidence['stay_clearly_better' if call == 'STAY_OUT' else 'box_clearly_better']
            phrase = 'Clear' if own >= .75 else 'Too close to call' if confidence['too_close_to_call'] >= .5 else 'Mixed outcomes'
            phrases.append(f'{phrase} {condition}.')
        recommended = plans[point['recommended']]
        dry = recommended['policy']['dry_stops']
        fallback = next((s for s in dry if s['lap'] > result['cutoff_lap']), None)
        plan = (f"Plan: stop for {compound_name[fallback['compound']]} around lap {fallback['lap']} if it stays dry."
                if fallback and call == 'STAY_OUT' else recommended['label'])
        eta = assumption['rain_arrival_lap'] - result['cutoff_lap'] if assumption['rain_arrival_lap'] is not None else None
        rain_sweep = next(s for s in result['flip_thresholds'] if s['assumption'] == 'rain_arrival_lap')
        confidence = point['call_confidence'] or {}
        return {'call': action(call), 'margin': f"+{seconds(point['display']['call_margin_s'])} s vs {'boxing now' if call == 'STAY_OUT' else 'staying out'}",
                'reason': (f'Rain is likely within {eta} laps, and boxing now would mean a second stop for inters.'
                           if call == 'STAY_OUT' and assumption['rain_probability'] >= .5 and eta is not None
                           else 'This call has the best expected race time across the sampled weather scenarios.'),
                'confidence': ' '.join(phrases), 'plan': plan,
                'flip': flips(sweep or rain_sweep),
                'shares': [{'name': label, 'value': f"{confidence.get(key, 0) * 100:.1f}%", 'fraction': confidence.get(key, 0)}
                           for key, label in (('stay_clearly_better', 'STAY clearly better'),
                                              ('too_close_to_call', 'Too close to call'), ('box_clearly_better', 'BOX clearly better'))],
                'chief': f"{action(call)}. Projection overrules the legacy scorer: expected advantage {seconds(point['display']['call_margin_s'])} s. Rain risk makes an extra slick stop costly."
                         if call != result['scorer']['pit_action'] else f"{action(call)}. Projection agrees with the scorer on this assumption: {seconds(point['display']['call_margin_s'])} s expected advantage."}

    base = view(result)
    sweeps = []
    for sweep in result['flip_thresholds']:
        current = sweep['current']
        points = [{'value': p['value'], 'label': ('No rain' if p['value'] == 'no rain' else
                   f"{seconds(p['value'])} s" if sweep['assumption'] == 'pit_loss_s' else
                   f"{p['value'] * 100:.0f}%" if sweep['assumption'] == 'rain_probability' else f"Lap {p['value']}"),
                   'display': view(p, sweep)} for p in sweep['sweep']]
        if current is None:
            points.insert(0, {'value': None, 'label': 'None · base', 'display': base})
        base_index = next((i for i, p in enumerate(points) if p['value'] == current), 0)
        sweeps.append({'assumption': sweep['assumption'], 'base_index': base_index, 'points': points,
                       'range': f"{sweep['range']} · resolution {sweep['resolution'] or 'mixed grid'} {sweep['units']}"})

    # Observed pace residuals, centered at the cutoff; no future rows included.
    history = [lap for lap in state.lap_history if lap.lap_number <= result['cutoff_lap']
               and (lap.timestamp is None or lap.timestamp <= state.knowledge_cutoff)]
    anchor = sum(l.lap_time_s for l in history) / len(history)
    residual, observed = 0.0, [{'lap': 0, 'gain_s': 0.0}]
    for lap in history:
        residual += anchor - lap.lap_time_s
        observed.append({'lap': lap.lap_number, 'gain_s': residual})
    end = observed[-1]['gain_s']
    observed = [{'lap': p['lap'], 'gain_s': round(p['gain_s'] - end, 1)} for p in observed]
    scenarios = []
    group_map = {g['id']: g for g in result['scenario_group_margins']}
    chart_values = [p['gain_s'] for p in observed]
    for scenario in result['scenarios']:
        paths = scenario['plans']
        # Shared reference is average running time of both example policies,
        # stripping their charged pit costs. This makes stops visible drops.
        reference = [sum(p['cumulative_time'][i] - sum(s['pit_loss_s'] for s in p['stops']
                         if s['charged_on_lap'] <= lap) for p in paths) / len(paths)
                     for i, lap in enumerate(paths[0]['laps'])]
        display_paths = []
        for p in paths:
            call = 'STAY OUT' if p['policy_id'] == result['best_policies_by_call']['STAY_OUT'] else 'BOX NOW'
            gain = [round(a - b, 1) for a, b in zip(reference, p['cumulative_time'])]
            chart_values.extend(gain)
            stop_label = ' → '.join(f"{compound_name[s['compound']]} after {s['lap']}" for s in p['stops'])
            display_paths.append({'policy_id': p['policy_id'], 'call': call, 'laps': p['laps'], 'gain_s': gain,
                                  'stops': [{'lap': s['lap'], 'charged_on_lap': s['charged_on_lap'],
                                             'label': compound_name[s['compound']], 'loss_s': s['display']['pit_loss_s']} for s in p['stops']],
                                  'stop_label': stop_label})
        group = group_map['rain' if scenario['id'] == 'rain_at_eta' else 'no_rain']['display']
        scenarios.append({'id': scenario['id'], 'label': f"Rain at lap {scenario['rain_lap']}" if scenario['rain_lap'] else 'Stays dry',
                          'plans': display_paths,
                          'margin_label': f"{float(group['expected_stay_advantage_s']):+.1f} s ({seconds(group['p10_stay_advantage_s'])} to {seconds(group['p90_stay_advantage_s'])})",
                          'group_label': 'Rain samples' if scenario['id'] == 'rain_at_eta' else 'Dry samples'})
    low, high = floor(min(chart_values) / 10) * 10 - 10, ceil(max(chart_values) / 10) * 10 + 10
    y_ticks = list(range(low, high + 1, 10))
    x_ticks = sorted(set([0, result['cutoff_lap'], result['horizon_lap']] + list(range(10, result['horizon_lap'], 10))))
    field = [{'driver': subject.driver, 'team': subject.team, 'position': subject.position,
              'gap': 'LEAD', 'compound': subject.current_compound.value, 'selected': True}]
    field += [{'driver': c.driver, 'team': c.team, 'position': c.position,
               'gap': f"{-c.gap_to_subject_s:+.1f} s", 'compound': c.current_compound.value, 'selected': False} for c in state.competitors]
    radio = []
    candidates = {c['candidate_id']: c for c in result['scorer']['all_candidates']}
    for evaluation in result['scorer']['specialist_evaluations']:
        candidate = candidates[evaluation['recommended_candidate_id']]
        radio.append({'role': evaluation['agent_name'].replace(' Specialist', ''),
                      'vote': action(candidate['pit_action']), 'text': evaluation['rationale'],
                      'candidate': candidate['candidate_id']})
    policy_rows = [{'id': p['id'], 'policy': p['label'], 'time': seconds(p['display']['mean_time_to_finish_s']),
                   'stops': str(p['policy']['max_stops']),
                   'status': 'Recommended' if p['id'] == result['recommended'] else 'Legal'} for p in result['plans']]
    sweep_rows = [{'assumption': s['assumption'], 'range': f"{s['range']} · {s['resolution'] or 'mixed'} {s['units']}",
                   'status': s['status'], 'rows': [{'value': str(p['value']), 'call': action(p['call']),
                    'margin': seconds(p['display']['call_margin_s']), 'policy': p['recommended']} for p in s['sweep']]}
                  for s in result['flip_thresholds']]
    factor_rows = [{'factor': key.replace('_', ' '), 'points': f'{value:+.2f}'} for key, value in result['scorer']['score_breakdown'].items()]
    assumption_rows = [{'name': a['name'].replace('_', ' '), 'value': str(a['value']), 'kind': a['kind']} for a in result['assumptions']]
    spread = assumption['rain_eta_spread_laps']
    return {'display': {'base': base, 'operating': f"{subject.driver} · LAP {result['cutoff_lap']} / {result['horizon_lap']}",
                       'tyres': f"{subject.current_compound.value} · {subject.stint_length_laps} laps old · {state.track_status.value}",
                       'field': field, 'radio': radio, 'policy_rows': policy_rows, 'factor_rows': factor_rows,
                       'plan_margin': f"{result['display']['plan_margin_s']:.1f} s", 'sweep_rows': sweep_rows,
                       'assumptions': assumption_rows, 'rain_timing': f"Rain timing ±{spread} laps · uniform · uncalibrated",
                       'policy_flips': [{'assumption': s['assumption'], 'text': str(s['transitions']) if s['transitions'] else s['status']}
                                        for s in result['policy_flip_thresholds']],
                       'sweeps': sweeps, 'chart': {'observed': observed, 'scenarios': scenarios,
                           'x_ticks': x_ticks, 'y_ticks': y_ticks, 'cutoff': result['cutoff_lap'],
                           'finish': result['horizon_lap'], 'low': low, 'high': high,
                           'flip_lap': next((t['from_value'] for s in result['flip_thresholds'] if s['assumption'] == 'rain_arrival_lap'
                                            for t in s['transitions'] if t['to_call'] == 'BOX_NOW'), None)}}}
