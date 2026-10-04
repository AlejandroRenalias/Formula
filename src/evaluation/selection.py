"""Predeclared two-horizon development selection; no post-hoc weighting."""

def select_configuration(summaries, *, bias_rule='absolute'):
    if bias_rule not in ('absolute','signed'):raise ValueError('Unknown bias rule')
    baseline=summaries['wear']['pooled_prediction']['finish']['bias_s']
    def passes(bias):return abs(bias)<=abs(baseline) if bias_rule=='absolute' else bias>=baseline
    eligible=['wear']+[c for c in ('ablation_a','ablation_b') if passes(summaries[c]['pooled_prediction']['finish']['bias_s'])]
    minimum={h:min(summaries[c]['pooled_equal_race'][h]['mae_s'] for c in eligible) for h in ('10','finish')}
    winners=[c for c in eligible if all(summaries[c]['pooled_equal_race'][h]['mae_s']==minimum[h] for h in minimum)]
    selected=winners[0] if winners else 'wear'
    return {'selected_configuration':selected,'bias_rule':bias_rule,'baseline_bias_s':baseline,
        'eligible_configurations':eligible,'minimum_equal_race_mae_s':minimum,'joint_minimum_winners':winners,
        'reason':'minimum at both horizons' if winners else 'different horizon winners; retain pit+wear',
        'tie_order':['wear','ablation_a','ablation_b']}
